"""Users API endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import DB, CurrentUser

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[UserResponse])
def list_users(db: DB, current_user: CurrentUser):
    """List all users (admin only)."""
    from app.models.user import User

    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user(user_in: UserCreate, db: DB):
    """Create a new user."""
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: DB, current_user: CurrentUser):
    """Get a user by ID."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_in: UserUpdate, db: DB, current_user: CurrentUser):
    """Update a user."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.name is not None:
        user.name = user_in.name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    db.commit()
    db.refresh(user)
    return user