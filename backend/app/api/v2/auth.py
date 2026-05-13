"""Auth API v2 - Tier A/B multi-tenancy with MFA support."""
from datetime import timedelta
from typing import Annotated

import pyotp

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_db, DB
from app.core.config import get_settings
from app.core.security import verify_password, create_access_token, decode_token, get_password_hash
from app.models.app_tenant import GlobalUser, TenantUser, AppTenant
from app.models.local_user import LocalUser

router = APIRouter()
settings = get_settings()
bearer = HTTPBearer(auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None
    tenant_id: str | None = None
    organizations: list[str] = []


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    tenant_id: str
    organizations: list[str] = []
    mfa_enabled: bool = False
    roles: list[dict] = []
    permissions: list[str] = []


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_name: str | None = None


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str


def get_current_user_v2(
    authorization: str | None = Header(None, alias="Authorization"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    db: Session = Depends(get_db),
) -> LocalUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    global_user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant")
    
    if not global_user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get local user for this tenant
    local_user = db.query(LocalUser).filter(
        LocalUser.global_user_id == global_user_id,
        LocalUser.tenant_id == tenant_id
    ).first()
    
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in this tenant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not local_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Store tenant context
    local_user._current_tenant_id = tenant_id
    
    return local_user


CurrentUserV2 = Depends(get_current_user_v2)


@router.post("/register", response_model=UserResponse)
def register_v2(db: DB, request: RegisterRequest):
    """Register new user with default tenant."""
    # Check if global user exists
    existing_global = db.query(GlobalUser).filter(GlobalUser.email == request.email).first()
    if existing_global:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Get or create default tenant
    default_tenant = db.query(AppTenant).filter(AppTenant.name == "Default").first()
    if not default_tenant:
        default_tenant = AppTenant(
            name=request.tenant_name or "Default",
            status="active",
            plan="enterprise"
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
    
    # Create global user
    from app.core.security import get_password_hash
    global_user = GlobalUser(
        email=request.email,
        password_hash=get_password_hash(request.password)
    )
    db.add(global_user)
    db.commit()
    db.refresh(global_user)
    
    # Create tenant user mapping
    tenant_user = TenantUser(tenant_id=default_tenant.id, user_id=global_user.id)
    db.add(tenant_user)
    
    # Create local user
    local_user = LocalUser(
        global_user_id=global_user.id,
        tenant_id=default_tenant.id,
        full_name=request.full_name
    )
    db.add(local_user)
    db.commit()
    db.refresh(local_user)
    
    # Generate token
    access_token = create_access_token(
        data={
            "sub": str(global_user.id),
            "tenant": str(default_tenant.id),
            "organizations": []
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return UserResponse(
        id=str(local_user.id),
        email=request.email,
        full_name=request.full_name,
        tenant_id=str(default_tenant.id),
        organizations=[],
        mfa_enabled=False
    )


@router.post("/login", response_model=Token)
def login_v2(db: DB, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email/password. Returns JWT with tenant context."""
    # Find global user
    global_user = db.query(GlobalUser).filter(GlobalUser.email == form_data.username).first()
    if not global_user or not verify_password(form_data.password, global_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user's tenants
    tenant_users = db.query(TenantUser).filter(TenantUser.user_id == global_user.id).all()
    if not tenant_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no active tenants",
        )
    
    # Use first tenant (or select based on request)
    tenant = db.query(AppTenant).filter(AppTenant.id == tenant_users[0].tenant_id).first()
    
    # Check MFA if enabled
    if global_user.mfa_enabled:
        # In production, would require MFA code here
        # For now, just check if it's enabled
        pass
    
    # Get local user for this tenant
    local_user = db.query(LocalUser).filter(
        LocalUser.global_user_id == global_user.id,
        LocalUser.tenant_id == tenant.id
    ).first()
    
    if not local_user or not local_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user in this tenant",
        )
    
    # Get organizations from memberships (tenant-based)
    from app.models.membership import Membership
    memberships = db.query(Membership).filter(
        Membership.user_id == global_user.id,
        Membership.tenant_id == tenant.id
    ).all()
    organization_ids = [str(m.tenant_id) for m in memberships if m.tenant_id]
    
    # Generate token with tenant context
    access_token = create_access_token(
        data={
            "sub": str(global_user.id),
            "tenant": str(tenant.id),
            "organizations": organization_ids
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_v2(current_user: LocalUser = CurrentUserV2):
    """Logout current user."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def read_users_me_v2(db: DB, current_user: LocalUser = CurrentUserV2):
    """Get current user info with tenant context."""
    global_user = db.query(GlobalUser).filter(GlobalUser.id == current_user.global_user_id).first()
    
    # Get organizations from memberships
    from app.models.membership import Membership
    memberships = db.query(Membership).filter(Membership.user_id == current_user.global_user_id).all()
    organizations = [str(m.tenant_id) for m in memberships if m.tenant_id]
    
    # Get user's E-ITS roles
    from app.models.local_user import EITSRole, UserRole
    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = db.query(EITSRole).filter(EITSRole.id.in_(role_ids)).all() if role_ids else []
    
    roles_data = [
        {"id": str(r.id), "role_name": r.role_name, "description": r.description}
        for r in roles
    ]
    
    # Get permissions from role_permissions table
    from app.models.role_permission import RolePermission
    from app.models.permission import Permission
    
    role_codes = [str(r.id) for r in roles]  # E-ITS role UUIDs
    role_perms = db.query(RolePermission).filter(RolePermission.role_id.in_(role_codes)).all() if role_codes else []
    perm_ids = [rp.permission_id for rp in role_perms]
    permissions = db.query(Permission).filter(Permission.id.in_(perm_ids)).all() if perm_ids else []
    permission_codes = [p.code for p in permissions]
    
    return UserResponse(
        id=str(current_user.id),
        email=global_user.email,
        full_name=current_user.full_name,
        tenant_id=str(current_user.tenant_id),
        organizations=organizations,
        mfa_enabled=global_user.mfa_enabled or False,
        roles=roles_data,
        permissions=permission_codes
    )


# MFA Endpoints

@router.post("/mfa/setup", response_model=MFASetupResponse)
def mfa_setup_v2(db: DB, current_user: LocalUser = CurrentUserV2):
    """Setup MFA for current user."""
    global_user = db.query(GlobalUser).filter(GlobalUser.id == current_user.global_user_id).first()
    
    # Generate secret
    secret = pyotp.random_base32()
    otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
        name=global_user.email,
        issuer_name="CyberPlan"
    )
    
    # Store secret (in production, encrypt this!)
    global_user.mfa_secret = secret
    db.commit()
    
    return MFASetupResponse(secret=secret, otpauth_url=otpauth_url)


@router.post("/mfa/verify")
def mfa_verify_v2(db: DB, code: str, current_user: LocalUser = CurrentUserV2):
    """Verify and enable MFA."""
    global_user = db.query(GlobalUser).filter(GlobalUser.id == current_user.global_user_id).first()
    
    if not global_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not setup. Call /mfa/setup first.",
        )
    
    totp = pyotp.TOTP(global_user.mfa_secret)
    if not totp.verify(code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code",
        )
    
    global_user.mfa_enabled = True
    db.commit()
    
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
def mfa_disable_v2(db: DB, password: str, current_user: LocalUser = CurrentUserV2):
    """Disable MFA (requires password)."""
    global_user = db.query(GlobalUser).filter(GlobalUser.id == current_user.global_user_id).first()
    
    if not verify_password(password, global_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    
    global_user.mfa_enabled = False
    global_user.mfa_secret = None
    db.commit()
    
    return {"message": "MFA disabled successfully"}