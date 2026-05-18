"""Damage Assessments and Protection Needs API v2."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.damage_assessment import DamageAssessment
from app.models.protection_need_summary import ProtectionNeedSummary
from app.models.business_process import BusinessProcess
from app.models.damage_scenario import DamageScenario
from app.models.asset import Asset
from app.models.process_asset import ProcessAsset
from app.schemas.eits_catalog import (
    DamageAssessmentCreate,
    DamageAssessmentUpdate,
    DamageAssessmentResponse,
    ProtectionNeedSummaryCreate,
    ProtectionNeedSummaryUpdate,
    ProtectionNeedSummaryResponse,
)

router = APIRouter()


@router.get("/damage-assessments", response_model=list[DamageAssessmentResponse])
def list_damage_assessments(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    business_process_id: Optional[UUID] = Query(None, alias="business_process_id"),
    damage_scenario_id: Optional[UUID] = Query(None, alias="damage_scenario_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List damage assessments for current tenant."""
    query = db.query(DamageAssessment).filter(
        DamageAssessment.tenant_id == current_user.tenant_id
    )
    if business_process_id:
        query = query.filter(DamageAssessment.business_process_id == business_process_id)
    if damage_scenario_id:
        query = query.filter(DamageAssessment.damage_scenario_id == damage_scenario_id)
    return query.offset(skip).limit(limit).all()


@router.post("/damage-assessments", response_model=DamageAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_damage_assessment(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: DamageAssessmentCreate = None,
):
    """Create a damage assessment."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == data.business_process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    existing = db.query(DamageAssessment).filter(
        DamageAssessment.tenant_id == current_user.tenant_id,
        DamageAssessment.business_process_id == data.business_process_id,
        DamageAssessment.damage_scenario_id == data.damage_scenario_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Damage assessment already exists for this combination")

    assessment = DamageAssessment(
        tenant_id=current_user.tenant_id,
        business_process_id=data.business_process_id,
        damage_scenario_id=data.damage_scenario_id,
        availability_impact=data.availability_impact,
        confidentiality_impact=data.confidentiality_impact,
        integrity_impact=data.integrity_impact,
        justification=data.justification,
        assessed_by=data.assessed_by or current_user.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/damage-assessments/bulk", response_model=list[DamageAssessmentResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_damage_assessments(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    items: list[DamageAssessmentCreate] = None,
):
    """Bulk create damage assessments."""
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")

    results = []
    for data in items:
        existing = db.query(DamageAssessment).filter(
            DamageAssessment.tenant_id == current_user.tenant_id,
            DamageAssessment.business_process_id == data.business_process_id,
            DamageAssessment.damage_scenario_id == data.damage_scenario_id,
        ).first()
        if existing:
            continue

        assessment = DamageAssessment(
            tenant_id=current_user.tenant_id,
            business_process_id=data.business_process_id,
            damage_scenario_id=data.damage_scenario_id,
            availability_impact=data.availability_impact,
            confidentiality_impact=data.confidentiality_impact,
            integrity_impact=data.integrity_impact,
            justification=data.justification,
            assessed_by=data.assessed_by or current_user.id,
        )
        db.add(assessment)
        results.append(assessment)

    db.commit()
    for r in results:
        db.refresh(r)
    return results


@router.get("/damage-assessments/{assessment_id}", response_model=DamageAssessmentResponse)
def get_damage_assessment(
    assessment_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a damage assessment by ID."""
    assessment = db.query(DamageAssessment).filter(
        DamageAssessment.id == assessment_id,
        DamageAssessment.tenant_id == current_user.tenant_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Damage assessment not found")
    return assessment


@router.patch("/damage-assessments/{assessment_id}", response_model=DamageAssessmentResponse)
def update_damage_assessment(
    assessment_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: DamageAssessmentUpdate = None,
):
    """Update a damage assessment."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    assessment = db.query(DamageAssessment).filter(
        DamageAssessment.id == assessment_id,
        DamageAssessment.tenant_id == current_user.tenant_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Damage assessment not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(assessment, field):
            setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)
    return assessment


@router.delete("/damage-assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_damage_assessment(
    assessment_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete a damage assessment."""
    assessment = db.query(DamageAssessment).filter(
        DamageAssessment.id == assessment_id,
        DamageAssessment.tenant_id == current_user.tenant_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Damage assessment not found")
    db.delete(assessment)
    db.commit()


@router.get("/protection-needs", response_model=list[ProtectionNeedSummaryResponse])
def list_protection_needs(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    business_process_id: Optional[UUID] = Query(None, alias="business_process_id"),
    protection_need: Optional[str] = Query(None, alias="protection_need"),
):
    """List protection need summaries for current tenant."""
    query = db.query(ProtectionNeedSummary).filter(
        ProtectionNeedSummary.tenant_id == current_user.tenant_id
    )
    if business_process_id:
        query = query.filter(ProtectionNeedSummary.business_process_id == business_process_id)
    if protection_need:
        query = query.filter(ProtectionNeedSummary.protection_need == protection_need)
    return query.all()


@router.post("/protection-needs", response_model=ProtectionNeedSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_protection_need(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ProtectionNeedSummaryCreate = None,
):
    """Create or update a protection need summary."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    existing = db.query(ProtectionNeedSummary).filter(
        ProtectionNeedSummary.tenant_id == current_user.tenant_id,
        ProtectionNeedSummary.business_process_id == data.business_process_id,
    ).first()

    if existing:
        for field in ['protection_need', 'confidentiality_need', 'integrity_need', 'availability_need', 'justification']:
            val = getattr(data, field, None)
            if val is not None:
                if hasattr(val, 'value'):
                    val = val.value
                setattr(existing, field, val)
        db.commit()
        db.refresh(existing)
        return existing

    pn = ProtectionNeedSummary(
        tenant_id=current_user.tenant_id,
        business_process_id=data.business_process_id,
        protection_need=data.protection_need.value if hasattr(data.protection_need, 'value') else data.protection_need,
        confidentiality_need=data.confidentiality_need.value if hasattr(data.confidentiality_need, 'value') else data.confidentiality_need,
        integrity_need=data.integrity_need.value if hasattr(data.integrity_need, 'value') else data.integrity_need,
        availability_need=data.availability_need.value if hasattr(data.availability_need, 'value') else data.availability_need,
        justification=data.justification,
    )
    db.add(pn)
    db.commit()
    db.refresh(pn)
    return pn


@router.post("/protection-needs/calculate")
def calculate_protection_needs(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Auto-calculate protection needs from damage assessments."""
    from sqlalchemy import func

    assessments = db.query(
        DamageAssessment.business_process_id,
        func.max(DamageAssessment.damage_category).label('max_damage_category'),
        func.max(DamageAssessment.confidentiality_impact).label('max_conf'),
        func.max(DamageAssessment.integrity_impact).label('max_int'),
        func.max(DamageAssessment.availability_impact).label('max_avail'),
    ).filter(
        DamageAssessment.tenant_id == current_user.tenant_id
    ).group_by(DamageAssessment.business_process_id).all()

    results = []
    for a in assessments:
        protection_need = ProtectionNeedSummary.level_from_damage(a.max_damage_category or 0)

        def level_from_val(val):
            if val is None or val <= 1:
                return "NORMAL"
            elif val == 2:
                return "HIGH"
            else:
                return "VERY_HIGH"

        existing = db.query(ProtectionNeedSummary).filter(
            ProtectionNeedSummary.tenant_id == current_user.tenant_id,
            ProtectionNeedSummary.business_process_id == a.business_process_id,
        ).first()

        if existing:
            existing.protection_need = protection_need
            existing.confidentiality_need = level_from_val(a.max_conf)
            existing.integrity_need = level_from_val(a.max_int)
            existing.availability_need = level_from_val(a.max_avail)
            results.append(existing)
        else:
            pn = ProtectionNeedSummary(
                tenant_id=current_user.tenant_id,
                business_process_id=a.business_process_id,
                protection_need=protection_need,
                confidentiality_need=level_from_val(a.max_conf),
                integrity_need=level_from_val(a.max_int),
                availability_need=level_from_val(a.max_avail),
                justification="Auto-calculated from damage assessments",
            )
            db.add(pn)
            results.append(pn)

    db.commit()
    for r in results:
        db.refresh(r)
    return {"message": f"Updated {len(results)} protection need summaries"}


@router.patch("/protection-needs/{need_id}", response_model=ProtectionNeedSummaryResponse)
def update_protection_need(
    need_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ProtectionNeedSummaryUpdate = None,
):
    """Update a protection need summary."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    pn = db.query(ProtectionNeedSummary).filter(
        ProtectionNeedSummary.id == need_id,
        ProtectionNeedSummary.tenant_id == current_user.tenant_id,
    ).first()
    if not pn:
        raise HTTPException(status_code=404, detail="Protection need summary not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(value, 'value'):
            value = value.value
        if hasattr(pn, field):
            setattr(pn, field, value)

    db.commit()
    db.refresh(pn)
    return pn


@router.delete("/protection-needs/{need_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_protection_need(
    need_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete a protection need summary."""
    pn = db.query(ProtectionNeedSummary).filter(
        ProtectionNeedSummary.id == need_id,
        ProtectionNeedSummary.tenant_id == current_user.tenant_id,
    ).first()
    if not pn:
        raise HTTPException(status_code=404, detail="Protection need summary not found")
    db.delete(pn)
    db.commit()