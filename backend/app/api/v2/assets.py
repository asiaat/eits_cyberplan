"""Assets API v2."""
import csv
import hashlib
import io
import uuid
from typing import Optional
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, CurrentUserV2, LocalUser
from app.core.config import get_settings
from app.models.asset import Asset
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.process_asset import ProcessAsset
from app.models.business_process import BusinessProcess
from app.models.asset_relation import AssetRelation
from app.models.user import User
from app.models.local_user import EITSRole, UserRole
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetListItem,
    LinkedProcessInfo,
)
from app.core.audit import log_audit as audit_log


settings = get_settings()


class AssetImportResult(BaseModel):
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped_scoped: int = 0
    duplicate_file: bool = False
    file_storage_path: str = ""
    errors: list[dict] = Field(default_factory=list)

router = APIRouter()


def _can_manage_asset_links(db: Session, asset: Asset, current_user: LocalUser) -> bool:
    """Check if user can manage asset-process links (is owner or has admin/ISM role)."""
    # Asset owner can always manage links
    if asset.owner_user_id == current_user.id:
        return True
    
    # Check if user has admin, ISM, or infoturbejuht role via user_roles
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == current_user.id
    ).all()
    
    if user_roles:
        role_ids = [str(ur.role_id) for ur in user_roles]
        if role_ids:
            eits_roles = db.query(EITSRole).filter(EITSRole.id.in_(role_ids)).all()
            for role in eits_roles:
                if role.role_name.lower() in {"admin", "ism", "infoturbejuht"}:
                    return True
    
    # Also check memberships for legacy roles (using global_user_id)
    from app.models.membership import Membership
    memberships = db.query(Membership).filter(Membership.user_id == current_user.global_user_id).all()
    legacy_roles = [m.role_id for m in memberships if m.role_id]
    if legacy_roles:
        allowed_roles = {"admin", "ism", "infoturbejuht"}
        if any(r.lower() in allowed_roles for r in legacy_roles):
            return True
    
    return False


def _get_linked_processes(db: Session, asset_id: UUID) -> list[LinkedProcessInfo]:
    """Get list of linked business processes for an asset."""
    links = db.query(ProcessAsset).filter(
        ProcessAsset.asset_id == asset_id
    ).all()

    processes = []
    for link in links:
        bp = db.query(BusinessProcess).filter(
            BusinessProcess.id == link.business_process_id
        ).first()
        if bp:
            processes.append(LinkedProcessInfo(
                id=bp.id,
                name=bp.name,
                status=bp.status
            ))
    return processes


def _build_response(db: Session, asset: Asset, current_user: LocalUser = None) -> AssetResponse:
    """Build an AssetResponse from a model instance."""
    owner = None
    if asset.owner_user_id:
        user = db.query(User).filter(User.id == asset.owner_user_id).first()
        if user:
            owner = {"id": str(user.id), "name": getattr(user, 'name', '') or getattr(user, 'full_name', ''), "email": getattr(user, 'email', '') or ''}
        else:
            local_user = db.query(LocalUser).filter(LocalUser.id == asset.owner_user_id).first()
            if local_user:
                owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

    linked_processes = _get_linked_processes(db, asset.id)
    can_manage = _can_manage_asset_links(db, asset, current_user) if current_user else False

    return AssetResponse(
        id=asset.id,
        tenant_id=asset.tenant_id,
        name=asset.name,
        asset_type=asset.asset_type,
        description=asset.description,
        remarks=asset.remarks,
        criticality=asset.criticality,
        confidentiality_need=asset.confidentiality_need,
        integrity_need=asset.integrity_need,
        availability_need=asset.availability_need,
        lifecycle_status=asset.lifecycle_status,
        owner_user_id=asset.owner_user_id,
        person_id=asset.person_id,
        owner=owner,
        linked_process_count=len(linked_processes),
        linked_processes=linked_processes,
        can_manage_links=can_manage,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("/", response_model=list[AssetListItem])
def list_assets_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    owner_id: Optional[UUID] = Query(None, alias="owner_id"),
    person_id: Optional[UUID] = Query(None, alias="person_id"),
    search: Optional[str] = Query(None, description="Search by name"),
    sort: Optional[str] = Query(None, description="Sort field: name, asset_type, lifecycle_status, criticality, created_at"),
    dir: Optional[str] = Query("desc", description="Sort direction: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List assets for the current tenant."""
    query = db.query(Asset).filter(
        Asset.tenant_id == current_user.tenant_id
    )

    if type_filter:
        query = query.filter(Asset.asset_type == type_filter)
    if status_filter:
        query = query.filter(Asset.lifecycle_status == status_filter)
    if owner_id:
        query = query.filter(Asset.owner_user_id == owner_id)
    if person_id:
        query = query.filter(Asset.person_id == person_id)
    if search:
        query = query.filter(Asset.name.ilike(f"%{search}%"))

    # Apply sorting
    sort_field = sort or "created_at"
    sort_direction = dir.lower() if dir else "desc"
    
    # Map sort field to column
    sort_column_map = {
        "name": Asset.name,
        "asset_type": Asset.asset_type,
        "lifecycle_status": Asset.lifecycle_status,
        "criticality": Asset.criticality,
        "created_at": Asset.created_at,
    }
    sort_col = sort_column_map.get(sort_field, Asset.created_at)
    
    if sort_direction == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    assets = query.offset(skip).limit(limit).all()

    result = []
    for asset in assets:
        owner = None
        if asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user:
                owner = {"id": str(user.id), "name": getattr(user, 'name', '') or getattr(user, 'full_name', ''), "email": getattr(user, 'email', '') or ''}
            else:
                local_user = db.query(LocalUser).filter(LocalUser.id == asset.owner_user_id).first()
                if local_user:
                    owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

        linked_processes = _get_linked_processes(db, asset.id)
        can_manage = _can_manage_asset_links(db, asset, current_user)
        
        mapping_count = db.query(AssetModuleMapping).filter(
            AssetModuleMapping.asset_id == asset.id,
            AssetModuleMapping.tenant_id == current_user.tenant_id
        ).count()

        item = AssetListItem(
            id=asset.id,
            tenant_id=asset.tenant_id,
            name=asset.name,
            asset_type=asset.asset_type,
            criticality=asset.criticality,
            confidentiality_need=asset.confidentiality_need,
            integrity_need=asset.integrity_need,
            availability_need=asset.availability_need,
            lifecycle_status=asset.lifecycle_status,
            owner_user_id=asset.owner_user_id,
            person_id=asset.person_id,
            owner=owner,
            linked_process_count=len(linked_processes),
            linked_processes=linked_processes,
            can_manage_links=can_manage,
            created_at=asset.created_at,
            module_mapping_count=mapping_count,
        )
        result.append(item)

    return result


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    data: AssetCreate = None,
):
    """Create a new asset."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    asset = Asset(
        tenant_id=current_user.tenant_id,
        name=data.name,
        asset_type=data.asset_type.value if hasattr(data.asset_type, 'value') else data.asset_type,
        description=data.description,
        remarks=data.remarks,
        criticality=data.criticality.value if hasattr(data.criticality, 'value') else data.criticality,
        confidentiality_need=data.confidentiality_need.value if hasattr(data.confidentiality_need, 'value') else data.confidentiality_need,
        integrity_need=data.integrity_need.value if hasattr(data.integrity_need, 'value') else data.integrity_need,
        availability_need=data.availability_need.value if hasattr(data.availability_need, 'value') else data.availability_need,
        lifecycle_status=data.lifecycle_status.value if hasattr(data.lifecycle_status, 'value') else data.lifecycle_status,
        owner_user_id=data.owner_user_id,
        person_id=data.person_id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="asset",
        entity_id=str(asset.id),
        after_json={"asset": asset.name, "type": asset.asset_type},
    )

    return _build_response(db, asset, current_user)


@router.post("/import-csv")
def import_assets_csv(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    file: UploadFile = File(...),
    on_conflict: str = Form("update"),
):
    """Import assets from CSV file with MinIO storage and SHA-256 dedup.

    CSV columns: name (required), asset_type (required), description,
    criticality, confidentiality_need, integrity_need, availability_need,
    lifecycle_status, quantity, group_name, remarks, is_core

    Matching: by asset name (case-insensitive, per tenant).
    - on_conflict="update" (default): overwrite fields on unscoped assets
    - on_conflict="skip": skip any asset whose name already exists

    Scoped assets (with module mappings) are never modified.

    Files are stored in MinIO at imports/{tenant_id}/{sha256}.csv
    to detect duplicate file uploads via SHA-256 hash.
    """
    result = AssetImportResult()

    # Read raw bytes for hashing + MinIO storage
    raw_bytes = file.file.read()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    csv_content = raw_bytes.decode("utf-8-sig")

    # MinIO setup
    s3_config = Config(signature_version="s3")
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=s3_config,
        region_name="us-east-1",
    )
    bucket = settings.MINIO_BUCKET
    storage_key = f"imports/{current_user.tenant_id}/{file_hash}.csv"

    # Ensure bucket exists
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        try:
            s3.create_bucket(Bucket=bucket)
        except Exception:
            pass

    # Check if file was already imported (SHA-256 dedup)
    try:
        s3.head_object(Bucket=bucket, Key=storage_key)
        result.duplicate_file = True
        result.file_storage_path = storage_key
        return result
    except ClientError:
        pass

    # Store file in MinIO
    try:
        s3.put_object(
            Bucket=bucket,
            Key=storage_key,
            Body=raw_bytes,
            ContentType=file.content_type or "text/csv",
            Metadata={"original_filename": file.filename or "import.csv", "imported_by": str(current_user.id)},
        )
        result.file_storage_path = storage_key
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file in MinIO: {str(e)}")

    # Parse and process CSV rows
    reader = csv.DictReader(io.StringIO(csv_content))

    for row_idx, row in enumerate(reader, 2):
        name = (row.get("name") or "").strip()
        asset_type = (row.get("asset_type") or "").strip()

        if not name or not asset_type:
            result.errors.append({"row": row_idx, "message": "Missing required fields 'name' and 'asset_type'"})
            continue

        valid_asset_types = {"information_asset", "software", "hardware", "service", "data", "other", "APP", "SYS", "NET", "INF", "IND"}
        valid_criticality = {"low", "normal", "high", "critical"}
        valid_protection = {"normal", "high", "very_high", "unknown"}
        valid_lifecycle = {"active", "inactive", "deprecated", "retired"}

        asset_type = asset_type.lower().replace(" ", "_")
        if asset_type not in valid_asset_types:
            result.errors.append({"row": row_idx, "message": f"Invalid asset_type '{asset_type}'. Must be one of: {', '.join(sorted(valid_asset_types))}"})
            continue

        criticality = (row.get("criticality") or "normal").lower()
        if criticality not in valid_criticality:
            result.errors.append({"row": row_idx, "message": f"Invalid criticality '{criticality}'. Must be one of: {', '.join(valid_criticality)}"})
            continue

        confidentiality_need = (row.get("confidentiality_need") or "normal").lower()
        integrity_need = (row.get("integrity_need") or "normal").lower()
        availability_need = (row.get("availability_need") or "normal").lower()
        protection_fields = [("confidentiality_need", confidentiality_need), ("integrity_need", integrity_need), ("availability_need", availability_need)]
        has_invalid = False
        for label, val in protection_fields:
            if val not in valid_protection:
                result.errors.append({"row": row_idx, "message": f"Invalid {label} '{val}'. Must be one of: {', '.join(valid_protection)}"})
                has_invalid = True
        if has_invalid:
            continue

        lifecycle_status = (row.get("lifecycle_status") or "active").lower()
        if lifecycle_status not in valid_lifecycle:
            result.errors.append({"row": row_idx, "message": f"Invalid lifecycle_status '{lifecycle_status}'. Must be one of: {', '.join(valid_lifecycle)}"})
            continue

        try:
            existing = db.query(Asset).filter(
                Asset.tenant_id == current_user.tenant_id,
                func.lower(Asset.name) == name.lower(),
            ).first()

            if existing:
                mapping_count = db.query(AssetModuleMapping).filter(
                    AssetModuleMapping.asset_id == existing.id,
                ).count()
                if mapping_count > 0:
                    result.skipped_scoped += 1
                    continue

                if on_conflict == "skip":
                    result.skipped_scoped += 1
                    continue

                update_fields = {
                    "asset_type": asset_type,
                    "description": row.get("description") or None,
                    "remarks": row.get("remarks") or None,
                    "criticality": criticality,
                    "confidentiality_need": confidentiality_need,
                    "integrity_need": integrity_need,
                    "availability_need": availability_need,
                    "lifecycle_status": lifecycle_status,
                    "quantity": int(row["quantity"]) if row.get("quantity", "").strip() else existing.quantity,
                    "group_name": row.get("group_name") or None,
                    "is_core": (row.get("is_core") or "false").lower() in ("true", "1", "yes"),
                }
                for key, value in update_fields.items():
                    setattr(existing, key, value)
                existing.updated_at = func.now()
                db.commit()
                result.updated += 1
            else:
                asset = Asset(
                    tenant_id=current_user.tenant_id,
                    name=name,
                    asset_type=asset_type,
                    description=row.get("description") or None,
                    remarks=row.get("remarks") or None,
                    criticality=criticality,
                    confidentiality_need=confidentiality_need,
                    integrity_need=integrity_need,
                    availability_need=availability_need,
                    lifecycle_status=lifecycle_status,
                    quantity=int(row["quantity"]) if row.get("quantity", "").strip() else 1,
                    group_name=row.get("group_name") or None,
                    is_core=(row.get("is_core") or "false").lower() in ("true", "1", "yes"),
                )
                db.add(asset)
                db.commit()
                result.created += 1

            result.total += 1
        except Exception as e:
            result.errors.append({"row": row_idx, "message": str(e)})
            db.rollback()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="import_csv",
        entity_type="asset",
        entity_id=str(uuid.uuid4()),
        after_json=result.model_dump(),
    )

    return result


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """Get an asset by ID."""
    if asset_id is None or (isinstance(asset_id, str) and asset_id == "undefined"):
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return _build_response(db, asset, current_user)


@router.patch("/{asset_id}/", response_model=AssetResponse)
def update_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    data: AssetUpdate = None,
):
    """Update an asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    before = {
        "name": asset.name,
        "asset_type": asset.asset_type,
        "criticality": asset.criticality,
    }

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    enum_fields = ("asset_type", "criticality", "confidentiality_need", "integrity_need", "availability_need", "lifecycle_status")

    for field, value in update_data.items():
        if field in enum_fields and hasattr(value, 'value'):
            value = value.value
        if hasattr(asset, field):
            setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="update",
        entity_type="asset",
        entity_id=str(asset.id),
        before_json=before,
        after_json={"asset": asset.name},
    )

    return _build_response(db, asset, current_user)


@router.delete("/{asset_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """Delete an asset if it has no active process links."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    linked_processes = _get_linked_processes(db, asset_id)
    if linked_processes:
        process_names = [p.name for p in linked_processes]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: asset is linked to {len(linked_processes)} business process(es): {', '.join(process_names)}. Unlink the asset first."
        )

    db.delete(asset)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="asset",
        entity_id=str(asset_id),
        before_json={"asset": asset.name, "type": asset.asset_type},
    )


@router.post("/{asset_id}/processes/{process_id}")
def link_asset_to_process(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    process_id: UUID = None,
):
    """Link an asset to a business process."""
    if asset_id is None or process_id is None:
        raise HTTPException(status_code=400, detail="asset_id and process_id are required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not _can_manage_asset_links(db, asset, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to manage asset links")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    existing = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == asset_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Asset already linked to this process")

    link = ProcessAsset(
        tenant_id=current_user.tenant_id,
        business_process_id=process_id,
        asset_id=asset_id,
    )
    db.add(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link_asset",
        entity_type="asset",
        entity_id=str(asset_id),
        after_json={"process_id": str(process_id), "process_name": bp.name},
    )

    return {"message": "Asset linked to process successfully"}


@router.post("/{asset_id}/link-process/")
def link_asset_to_process_alt(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    data: dict = None,
):
    """Link an asset to a business process (alternate endpoint)."""
    if not data or "process_id" not in data:
        raise HTTPException(status_code=400, detail="process_id is required")
    process_id = data["process_id"]
    
    if asset_id is None or process_id is None:
        raise HTTPException(status_code=400, detail="asset_id and process_id are required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not _can_manage_asset_links(db, asset, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to manage asset links")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    existing = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == asset_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Asset already linked to this process")

    link = ProcessAsset(
        tenant_id=current_user.tenant_id,
        business_process_id=process_id,
        asset_id=asset_id,
    )
    db.add(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link_asset",
        entity_type="asset",
        entity_id=str(asset_id),
        after_json={"process_id": str(process_id), "process_name": bp.name},
    )

    return {"message": "Asset linked to process successfully"}


@router.delete("/{asset_id}/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_asset_from_process(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    process_id: UUID = None,
):
    """Unlink an asset from a business process."""
    if asset_id is None or process_id is None:
        raise HTTPException(status_code=400, detail="asset_id and process_id are required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not _can_manage_asset_links(db, asset, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to manage asset links")

    link = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == asset_id,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Asset link not found")

    db.delete(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="unlink_asset",
        entity_type="asset",
        entity_id=str(asset_id),
        after_json={"process_id": str(process_id)},
    )


@router.get("/{asset_id}/unlinked-processes", response_model=list[dict])
def list_unlinked_processes(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """List business processes that are not linked to this asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    linked_process_ids = db.query(ProcessAsset.asset_id).filter(
        ProcessAsset.asset_id == asset_id
    ).all()
    linked_ids = [lp[0] for lp in linked_process_ids]

    query = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == current_user.tenant_id
    )
    if linked_ids:
        query = query.filter(BusinessProcess.id.notin_(linked_ids))

    processes = query.order_by(BusinessProcess.name).all()

    return [
        {"id": str(p.id), "name": p.name, "status": p.status}
        for p in processes
    ]


# Asset Relations Endpoints

@router.get("/{asset_id}/relations", response_model=list[dict])
def list_asset_relations(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """List all relations for an asset (both upstream and downstream)."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Get relations where this asset is source (upstream - asset depends on these)
    upstream_relations = db.query(AssetRelation).filter(
        AssetRelation.source_asset_id == asset_id,
        AssetRelation.tenant_id == current_user.tenant_id,
    ).all()

    # Get relations where this asset is target (downstream - these depend on this asset)
    downstream_relations = db.query(AssetRelation).filter(
        AssetRelation.target_asset_id == asset_id,
        AssetRelation.tenant_id == current_user.tenant_id,
    ).all()

    from app.models.asset_relation_type import AssetRelationType

    result = []

    for rel in upstream_relations:
        target = db.query(Asset).filter(Asset.id == rel.target_asset_id).first()
        if target:
            rel_type_info = None
            if rel.relation_type_code:
                rel_type = db.query(AssetRelationType).filter(
                    AssetRelationType.code == rel.relation_type_code
                ).first()
                if rel_type:
                    rel_type_info = {"code": rel_type.code, "name": rel_type.name}
            result.append({
                "id": str(rel.id),
                "direction": "upstream",
                "relation_type": rel.relation_type or rel.relation_type_code,
                "relation_type_info": rel_type_info,
                "bidirectional": rel.bidirectional,
                "strength": rel.strength,
                "target_asset_id": str(target.id),
                "target_asset_name": target.name,
                "target_asset_type": target.asset_type,
                "description": rel.description,
            })

    for rel in downstream_relations:
        source = db.query(Asset).filter(Asset.id == rel.source_asset_id).first()
        if source:
            rel_type_info = None
            if rel.relation_type_code:
                rel_type = db.query(AssetRelationType).filter(
                    AssetRelationType.code == rel.relation_type_code
                ).first()
                if rel_type:
                    rel_type_info = {"code": rel_type.code, "name": rel_type.name}
            result.append({
                "id": str(rel.id),
                "direction": "downstream",
                "relation_type": rel.relation_type or rel.relation_type_code,
                "relation_type_info": rel_type_info,
                "bidirectional": rel.bidirectional,
                "strength": rel.strength,
                "source_asset_id": str(source.id),
                "source_asset_name": source.name,
                "source_asset_type": source.asset_type,
                "description": rel.description,
            })

    return result


def _relation_type_exists(db, code: str) -> bool:
    """Check if a relation type code exists in the asset_relation_types table."""
    from app.models.asset_relation_type import AssetRelationType
    return db.query(AssetRelationType).filter(AssetRelationType.code == code).first() is not None


class AssetRelationCreate(BaseModel):
    """Schema for creating an asset relation."""
    target_asset_id: UUID
    relation_type_code: str
    description: Optional[str] = None
    bidirectional: bool = False
    strength: str = "weak"


@router.post("/{asset_id}/relations", status_code=status.HTTP_201_CREATED)
def create_asset_relation(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    data: AssetRelationCreate = None,
):
    """Create a new relation from an asset to another asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    # Check asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Check target asset exists and belongs to tenant
    target = db.query(Asset).filter(
        Asset.id == data.target_asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Target asset not found")

    if asset_id == data.target_asset_id:
        raise HTTPException(status_code=400, detail="Asset cannot relate to itself")

    # Validate relation type
    from app.services.protection_inheritance_service import ProtectionInheritanceService
    svc = ProtectionInheritanceService(db)
    is_valid, error = svc.validate_relation_type(asset_id, data.target_asset_id, data.relation_type_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Check for circular dependency
    would_cycle, cycle_msg = svc.check_circular_dependency(
        current_user.tenant_id, asset_id, data.target_asset_id
    )
    if would_cycle:
        raise HTTPException(status_code=400, detail=cycle_msg)

    # Check if relation already exists
    existing = db.query(AssetRelation).filter(
        AssetRelation.source_asset_id == asset_id,
        AssetRelation.target_asset_id == data.target_asset_id,
        AssetRelation.tenant_id == current_user.tenant_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Relation already exists")

    rel = AssetRelation(
        tenant_id=current_user.tenant_id,
        source_asset_id=asset_id,
        target_asset_id=data.target_asset_id,
        relation_type=data.relation_type_code,
        # Only set relation_type_code if it exists in asset_relation_types table
        # For custom/free-text types, leave relation_type_code null
        relation_type_code=data.relation_type_code if _relation_type_exists(db, data.relation_type_code) else None,
        description=data.description,
        bidirectional=data.bidirectional,
        strength=data.strength,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="asset_relation",
        entity_id=str(rel.id),
        after_json={
            "source_asset_id": str(asset_id),
            "target_asset_id": str(data.target_asset_id),
            "relation_type_code": data.relation_type_code,
        },
    )

    return {"id": str(rel.id), "message": "Relation created successfully"}


@router.delete("/{asset_id}/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_relation(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    relation_id: UUID = None,
):
    """Delete an asset relation."""
    if asset_id is None or relation_id is None:
        raise HTTPException(status_code=400, detail="asset_id and relation_id are required")

    rel = db.query(AssetRelation).filter(
        AssetRelation.id == relation_id,
        AssetRelation.tenant_id == current_user.tenant_id,
    ).first()

    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")

    # Verify relation belongs to this asset
    if rel.source_asset_id != asset_id and rel.target_asset_id != asset_id:
        raise HTTPException(status_code=404, detail="Relation not found for this asset")

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="asset_relation",
        entity_id=str(relation_id),
        before_json={
            "source_asset_id": str(rel.source_asset_id),
            "target_asset_id": str(rel.target_asset_id),
        },
    )

    db.delete(rel)
    db.commit()


@router.get("/relation-types")
def list_relation_types(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """List all available asset relation types."""
    from app.services.protection_inheritance_service import ProtectionInheritanceService
    svc = ProtectionInheritanceService(db)
    return svc.get_all_relation_types()


@router.get("/relation-types-fix")
def list_relation_types_fix(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """List all available asset relation types - alternative endpoint."""
    from app.models.asset_relation_type import AssetRelationType
    types = db.query(AssetRelationType).all()
    return [
        {
            "code": t.code,
            "name": t.name,
            "description": t.description,
            "source_types": t.source_types,
            "target_types": t.target_types,
            "bidirectional": t.bidirectional,
            "strength": t.strength,
        }
        for t in types
    ]


@router.get("/{asset_id}/protection-inheritance")
def get_asset_protection_inheritance(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """Get protection inheritance info for an asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    from app.services.protection_inheritance_service import ProtectionInheritanceService
    svc = ProtectionInheritanceService(db)

    inherited = svc.get_inherited_protection_needs(asset_id)
    upstream = svc.get_upstream_assets(asset_id)
    downstream = svc.get_downstream_assets(asset_id)
    dependency_tree = svc.get_dependency_tree(asset_id)

    return {
        "asset_id": str(asset_id),
        "asset_name": asset.name,
        "baseline_c": inherited["baseline_c"],
        "baseline_i": inherited["baseline_i"],
        "baseline_a": inherited["baseline_a"],
        "inherited_c": inherited["inherited_c"],
        "inherited_i": inherited["inherited_i"],
        "inherited_a": inherited["inherited_a"],
        "has_inherited": inherited["has_inherited"],
        "upstream_count": len(upstream),
        "downstream_count": len(downstream),
        "upstream": upstream,
        "downstream": downstream,
        "dependency_tree": dependency_tree,
    }