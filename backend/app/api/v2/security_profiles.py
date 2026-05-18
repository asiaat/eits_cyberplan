"""Security Profiles API v2."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.security_profile import SecurityProfile
from app.models.eits_catalog_version import EitsCatalogVersion
from app.schemas.eits_catalog import (
    SecurityProfileCreate,
    SecurityProfileUpdate,
    SecurityProfileResponse,
)

router = APIRouter()


@router.get("/", response_model=list[SecurityProfileResponse])
def list_security_profiles(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List security profiles for current tenant."""
    return db.query(SecurityProfile).filter(
        SecurityProfile.tenant_id == current_user.tenant_id
    ).order_by(SecurityProfile.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=SecurityProfileResponse, status_code=status.HTTP_201_CREATED)
def create_security_profile(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: SecurityProfileCreate = None,
):
    """Create a security profile (turbeviisi valik)."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    if data.catalog_version_id:
        version = db.query(EitsCatalogVersion).filter(
            EitsCatalogVersion.id == data.catalog_version_id
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="Catalog version not found")

    profile = SecurityProfile(
        tenant_id=current_user.tenant_id,
        security_approach=data.security_approach.value if hasattr(data.security_approach, 'value') else data.security_approach,
        catalog_version_id=data.catalog_version_id,
        notes=data.notes,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=SecurityProfileResponse)
def get_security_profile(
    profile_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a security profile by ID."""
    profile = db.query(SecurityProfile).filter(
        SecurityProfile.id == profile_id,
        SecurityProfile.tenant_id == current_user.tenant_id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Security profile not found")
    return profile


@router.patch("/{profile_id}", response_model=SecurityProfileResponse)
def update_security_profile(
    profile_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: SecurityProfileUpdate = None,
):
    """Update a security profile."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    profile = db.query(SecurityProfile).filter(
        SecurityProfile.id == profile_id,
        SecurityProfile.tenant_id == current_user.tenant_id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Security profile not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(value, 'value'):
            value = value.value
        if hasattr(profile, field):
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_security_profile(
    profile_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete a security profile."""
    profile = db.query(SecurityProfile).filter(
        SecurityProfile.id == profile_id,
        SecurityProfile.tenant_id == current_user.tenant_id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Security profile not found")
    db.delete(profile)
    db.commit()