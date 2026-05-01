"""Auth API endpoints."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.api.deps import DB, CurrentUser
from app.core.config import get_settings
from app.core.security import verify_password, create_access_token
from app.models.user import User

router = APIRouter()
settings = get_settings()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool


@router.post("/login", response_model=Token)
def login(db: DB, form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: CurrentUser):
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: CurrentUser):
    return current_user