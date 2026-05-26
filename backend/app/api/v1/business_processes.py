"""Business Processes API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import DB, TenantUserDep
from app.models.business_process import BusinessProcess
from app.models.asset import Asset
from app.models.process_asset import ProcessAsset
from app.models.user import User
from app.schemas.business_process import (
    BusinessProcessCreate,
    BusinessProcessUpdate,
    BusinessProcessResponse,
    BusinessProcessListItem,
    ProcessAssetLinkCreate,
    ProcessAssetLinkUpdate,
)
from app.core.audit import log_audit as audit_log

router = APIRouter()


@router.get("/", response_model=list[BusinessProcessListItem])
def list_business_processes(
    db: DB,
    tenant_user: TenantUserDep,
    status_filter: Optional[str] = Query(None, alias="status"),
    owner_id: Optional[UUID] = Query(None, alias="owner_id"),
    division_id: Optional[str] = Query(None, alias="division_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List business processes for the current tenant."""
    query = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == tenant_user.tenant_id
    )

    if status_filter:
        query = query.filter(BusinessProcess.status == status_filter)
    if owner_id:
        query = query.filter(BusinessProcess.owner_user_id == owner_id)
    if division_id:
        query = query.filter(BusinessProcess.division_id == division_id)

    processes = query.order_by(BusinessProcess.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for bp in processes:
        owner = None
        if bp.owner_user_id:
            user = db.query(User).filter(User.id == bp.owner_user_id).first()
            if user:
                owner = {"id": user.id, "name": user.name, "email": user.email}

        asset_count = db.query(ProcessAsset).filter(
            ProcessAsset.business_process_id == bp.id
        ).count()

        item = BusinessProcessListItem(
            id=bp.id,
            name=bp.name,
            status=bp.status,
            confidentiality_need=bp.confidentiality_need,
            integrity_need=bp.integrity_need,
            availability_need=bp.availability_need,
            division_id=bp.division_id,
            owner=owner,
            asset_count=asset_count,
            created_at=bp.created_at,
        )
        result.append(item)

    return result


@router.post("/", response_model=BusinessProcessResponse, status_code=status.HTTP_201_CREATED)
def create_business_process(
    db: DB,
    tenant_user: TenantUserDep,
    data: BusinessProcessCreate,
):
    """Create a new business process."""
    bp = BusinessProcess(
        tenant_id=tenant_user.tenant_id,
        name=data.name,
        description=data.description,
        purpose=data.purpose,
        inputs=data.inputs,
        outputs=data.outputs,
        status=data.status.value,
        confidentiality_need=data.confidentiality_need.value,
        integrity_need=data.integrity_need.value,
        availability_need=data.availability_need.value,
        division_id=data.division_id,
        owner_user_id=data.owner_user_id,
    )
    db.add(bp)
    db.flush()

    for asset_id in (data.asset_ids or []):
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_user.tenant_id
        ).first()
        if not asset:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        link = ProcessAsset(
            tenant_id=tenant_user.tenant_id,
            business_process_id=bp.id,
            asset_id=asset_id,
        )
        db.add(link)

    db.commit()
    db.refresh(bp)

    audit_log(
        db=db,
        tenant_id=str(tenant_user.tenant_id),
        actor_user_id=str(tenant_user.id),
        action="create",
        entity_type="business_process",
        entity_id=bp.id,
        after_json={"business_process": bp.name},
    )

    return _build_response(db, bp)


@router.get("/{process_id}", response_model=BusinessProcessResponse)
def get_business_process(
    db: DB,
    tenant_user: TenantUserDep,
    process_id: UUID,
):
    """Get a business process by ID."""
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == tenant_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    return _build_response(db, bp)


@router.patch("/{process_id}", response_model=BusinessProcessResponse)
def update_business_process(
    db: DB,
    tenant_user: TenantUserDep,
    process_id: UUID,
    data: BusinessProcessUpdate,
):
    """Update a business process."""
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == tenant_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    before = {
        "name": bp.name,
        "description": bp.description,
        "status": bp.status,
        "confidentiality_need": bp.confidentiality_need,
        "integrity_need": bp.integrity_need,
        "availability_need": bp.availability_need,
    }

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if field in ("status", "confidentiality_need", "integrity_need", "availability_need"):
            if hasattr(value, "value"):
                setattr(bp, field, value.value)
            else:
                setattr(bp, field, value)
        elif field == "owner_user_id":
            setattr(bp, field, value)
        elif field != "asset_ids":
            setattr(bp, field, value)

    db.commit()
    db.refresh(bp)

    audit_log(
        db=db,
        tenant_id=str(tenant_user.tenant_id),
        actor_user_id=str(tenant_user.id),
        action="update",
        entity_type="business_process",
        entity_id=bp.id,
        before_json=before,
        after_json={"business_process": bp.name},
    )

    return _build_response(db, bp)


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_process(
    db: DB,
    tenant_user: TenantUserDep,
    process_id: UUID,
):
    """Delete a business process."""
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == tenant_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id
    ).delete()

    audit_log(
        db=db,
        tenant_id=str(tenant_user.tenant_id),
        actor_user_id=str(tenant_user.id),
        action="delete",
        entity_type="business_process",
        entity_id=bp.id,
        before_json={"business_process": bp.name},
    )

    db.delete(bp)
    db.commit()


@router.post("/{process_id}/assets", status_code=status.HTTP_201_CREATED)
def add_process_asset(
    db: DB,
    tenant_user: TenantUserDep,
    process_id: UUID,
    data: ProcessAssetLinkCreate,
):
    """Link an asset to a business process."""
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == tenant_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    asset = db.query(Asset).filter(
        Asset.id == data.asset_id,
        Asset.tenant_id == tenant_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    existing = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == data.asset_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Asset already linked")

    link = ProcessAsset(
        tenant_id=tenant_user.tenant_id,
        business_process_id=process_id,
        asset_id=data.asset_id,
        relation_description=data.relation_description,
    )
    db.add(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(tenant_user.tenant_id),
        actor_user_id=str(tenant_user.id),
        action="link_asset",
        entity_type="business_process",
        entity_id=process_id,
        after_json={"asset_id": str(data.asset_id)},
    )

    return {"message": "Asset linked successfully"}


@router.delete("/{process_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_process_asset(
    db: DB,
    tenant_user: TenantUserDep,
    process_id: UUID,
    asset_id: UUID,
):
    """Unlink an asset from a business process."""
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == tenant_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

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
        tenant_id=str(tenant_user.tenant_id),
        actor_user_id=str(tenant_user.id),
        action="unlink_asset",
        entity_type="business_process",
        entity_id=process_id,
        after_json={"asset_id": str(asset_id)},
    )


def _build_response(db: Session, bp: BusinessProcess) -> BusinessProcessResponse:
    """Build a BusinessProcessResponse from a model instance."""
    owner = None
    if bp.owner_user_id:
        user = db.query(User).filter(User.id == bp.owner_user_id).first()
        if user:
            owner = {"id": user.id, "name": user.name, "email": user.email}

    asset_links = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == bp.id
    ).all()

    process_asset_links = []
    for link in asset_links:
        asset = db.query(Asset).filter(Asset.id == link.asset_id).first()
        asset_summary = None
        if asset:
            asset_summary = {
                "id": asset.id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "criticality": asset.criticality,
            }
        process_asset_links.append({
            "id": link.id,
            "asset_id": link.asset_id,
            "asset": asset_summary,
            "relation_description": link.relation_description,
        })

    return BusinessProcessResponse(
        id=bp.id,
        tenant_id=bp.tenant_id,
        owner_user_id=bp.owner_user_id,
        division_id=bp.division_id,
        name=bp.name,
        description=bp.description,
        purpose=bp.purpose,
        inputs=bp.inputs,
        outputs=bp.outputs,
        status=bp.status,
        confidentiality_need=bp.confidentiality_need,
        integrity_need=bp.integrity_need,
        availability_need=bp.availability_need,
        owner=owner,
        assets=process_asset_links,
        asset_count=len(process_asset_links),
        created_at=bp.created_at,
        updated_at=bp.updated_at,
    )