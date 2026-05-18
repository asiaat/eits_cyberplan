"""Risks v2 API - E-ITS risk management with full fields."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.risk import Risk
from app.models.eits_threat import EitsThreat
from app.models.risk_measure_link import RiskMeasureLink, DamageCategoryThreshold, ProcessModuleAssignment
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.schemas.eits_catalog import (
    RiskV2Create,
    RiskV2Update,
    RiskV2Response,
    RiskMeasureLinkCreate,
    RiskMeasureLinkResponse,
    DamageCategoryThresholdCreate,
    DamageCategoryThresholdUpdate,
    DamageCategoryThresholdResponse,
    ProcessModuleAssignmentCreate,
    ProcessModuleAssignmentUpdate,
    ProcessModuleAssignmentResponse,
    RiskMatrixCell,
)
from app.core.audit import log_audit as audit_log

router = APIRouter()


@router.get("/", response_model=list[RiskV2Response])
def list_risks_v2(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    status_filter: Optional[str] = Query(None, alias="status"),
    treatment_type: Optional[str] = Query(None, alias="treatment_type"),
    asset_id: Optional[UUID] = Query(None, alias="asset_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List risks for current tenant."""
    query = db.query(Risk).filter(Risk.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.filter(Risk.status == status_filter)
    if treatment_type:
        query = query.filter(Risk.treatment_type == treatment_type)
    if asset_id:
        query = query.filter(Risk.asset_id == asset_id)
    return query.order_by(Risk.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=RiskV2Response, status_code=status.HTTP_201_CREATED)
def create_risk_v2(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: RiskV2Create = None,
):
    """Create a risk."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    if data.threat_id:
        threat = db.query(EitsThreat).filter(EitsThreat.id == data.threat_id).first()
        if not threat:
            raise HTTPException(status_code=404, detail="Threat not found")

    risk = Risk(
        tenant_id=current_user.tenant_id,
        title=data.title,
        scenario=data.scenario,
        threat_id=data.threat_id,
        asset_id=data.asset_id,
        business_process_id=data.business_process_id,
        likelihood=data.likelihood_score,
        impact=data.impact_score,
        likelihood_score=data.likelihood_score,
        impact_score=data.impact_score,
        risk_level=data.risk_rating,
        risk_rating=data.risk_rating,
        treatment=data.treatment_type,
        treatment_type=data.treatment_type,
        owner_user_id=data.owner_user_id,
        status="identified",
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="risk",
        entity_id=str(risk.id),
        after_json={"title": data.title},
    )

    return risk


@router.get("/{risk_id}", response_model=RiskV2Response)
def get_risk_v2(
    risk_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a risk by ID."""
    risk = db.query(Risk).filter(
        Risk.id == risk_id,
        Risk.tenant_id == current_user.tenant_id,
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


@router.patch("/{risk_id}", response_model=RiskV2Response)
def update_risk_v2(
    risk_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: RiskV2Update = None,
):
    """Update a risk."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    risk = db.query(Risk).filter(
        Risk.id == risk_id,
        Risk.tenant_id == current_user.tenant_id,
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    before = {"title": risk.title, "risk_rating": risk.risk_rating, "treatment_type": risk.treatment_type}

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    enum_fields = ["likelihood_score", "impact_score", "risk_rating", "treatment_type"]
    for field, value in update_data.items():
        if hasattr(value, 'value'):
            value = value.value
        if field in enum_fields:
            continue
        if hasattr(risk, field):
            setattr(risk, field, value)

    if "likelihood_score" in update_data:
        risk.likelihood_score = update_data["likelihood_score"]
        risk.likelihood = update_data["likelihood_score"]
    if "impact_score" in update_data:
        risk.impact_score = update_data["impact_score"]
        risk.impact = update_data["impact_score"]
    if "risk_rating" in update_data:
        risk.risk_rating = update_data["risk_rating"]
        risk.risk_level = update_data["risk_rating"]
    if "treatment_type" in update_data:
        risk.treatment_type = update_data["treatment_type"]
        risk.treatment = update_data["treatment_type"]

    db.commit()
    db.refresh(risk)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="update",
        entity_type="risk",
        entity_id=str(risk_id),
        before_json=before,
    )

    return risk


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk_v2(
    risk_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete a risk."""
    risk = db.query(Risk).filter(
        Risk.id == risk_id,
        Risk.tenant_id == current_user.tenant_id,
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    db.query(RiskMeasureLink).filter(RiskMeasureLink.risk_id == risk_id).delete()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="risk",
        entity_id=str(risk_id),
    )

    db.delete(risk)
    db.commit()


@router.post("/{risk_id}/accept")
def accept_risk(
    risk_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Accept a risk (mark as accepted by management)."""
    risk = db.query(Risk).filter(
        Risk.id == risk_id,
        Risk.tenant_id == current_user.tenant_id,
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    risk.treatment_type = "ACCEPT"
    risk.treatment = "ACCEPT"
    risk.status = "accepted"
    risk.accepted_by = current_user.id
    risk.accepted_at = None
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="accept_risk",
        entity_type="risk",
        entity_id=str(risk_id),
    )

    return {"message": "Risk accepted"}


@router.get("/risk-matrix", response_model=list[RiskMatrixCell])
def get_risk_matrix(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get risk matrix data (impact × likelihood)."""
    from sqlalchemy import text
    result = db.execute(text("SELECT * FROM v_risk_matrix WHERE tenant_id = :tid"), {"tid": str(current_user.tenant_id)})
    rows = result.fetchall()
    return [RiskMatrixCell(
        tenant_id=row.tenant_id,
        impact_score=row.impact_score,
        likelihood_score=row.likelihood_score,
        risk_count=row.risk_count,
        risk_titles=list(row.risk_titles) if row.risk_titles else [],
    ) for row in rows]


@router.post("/risk-measure-links", response_model=RiskMeasureLinkResponse, status_code=status.HTTP_201_CREATED)
def create_risk_measure_link(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: RiskMeasureLinkCreate = None,
):
    """Link a measure to a risk."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    link = RiskMeasureLink(
        tenant_id=current_user.tenant_id,
        risk_id=data.risk_id,
        measure_id=data.measure_id,
        imr_item_id=data.imr_item_id,
        custom_measure_name=data.custom_measure_name,
        custom_measure_description=data.custom_measure_description,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("/damage-thresholds", response_model=list[DamageCategoryThresholdResponse])
def list_damage_thresholds(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List damage category thresholds for current tenant."""
    return db.query(DamageCategoryThreshold).filter(
        DamageCategoryThreshold.tenant_id == current_user.tenant_id
    ).all()


@router.post("/damage-thresholds", response_model=DamageCategoryThresholdResponse, status_code=status.HTTP_201_CREATED)
def create_damage_threshold(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: DamageCategoryThresholdCreate = None,
):
    """Create or update damage category thresholds."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    existing = db.query(DamageCategoryThreshold).filter(
        DamageCategoryThreshold.tenant_id == current_user.tenant_id,
        DamageCategoryThreshold.damage_scenario_id == data.damage_scenario_id,
    ).first()

    if existing:
        for field in ['negligible_description', 'limited_description', 'serious_description', 'catastrophic_description']:
            val = getattr(data, field, None)
            if val is not None:
                setattr(existing, field, val)
        db.commit()
        db.refresh(existing)
        return existing

    threshold = DamageCategoryThreshold(
        tenant_id=current_user.tenant_id,
        damage_scenario_id=data.damage_scenario_id,
        negligible_description=data.negligible_description,
        limited_description=data.limited_description,
        serious_description=data.serious_description,
        catastrophic_description=data.catastrophic_description,
    )
    db.add(threshold)
    db.commit()
    db.refresh(threshold)
    return threshold


@router.patch("/damage-thresholds/{threshold_id}", response_model=DamageCategoryThresholdResponse)
def update_damage_threshold(
    threshold_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: DamageCategoryThresholdUpdate = None,
):
    """Update damage category thresholds."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    threshold = db.query(DamageCategoryThreshold).filter(
        DamageCategoryThreshold.id == threshold_id,
        DamageCategoryThreshold.tenant_id == current_user.tenant_id,
    ).first()
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(threshold, field):
            setattr(threshold, field, value)

    db.commit()
    db.refresh(threshold)
    return threshold


@router.get("/process-module-assignments", response_model=list[ProcessModuleAssignmentResponse])
def list_process_module_assignments(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List process module assignments (ISMS, ORP, CON, OPS, DER) for current tenant."""
    from app.models.eits_module import EitsModule
    process_modules = db.query(EitsModule).filter(
        EitsModule.module_type == "PROCESS"
    ).all()
    module_ids = [m.id for m in process_modules]

    return db.query(ProcessModuleAssignment).filter(
        ProcessModuleAssignment.tenant_id == current_user.tenant_id,
        ProcessModuleAssignment.module_id.in_(module_ids),
    ).all()


@router.post("/process-module-assignments", response_model=ProcessModuleAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_process_module_assignment(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ProcessModuleAssignmentCreate = None,
):
    """Assign a process module to the organization."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    from app.models.eits_module import EitsModule
    module = db.query(EitsModule).filter(EitsModule.id == data.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    existing = db.query(ProcessModuleAssignment).filter(
        ProcessModuleAssignment.tenant_id == current_user.tenant_id,
        ProcessModuleAssignment.module_id == data.module_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Module already assigned")

    assignment = ProcessModuleAssignment(
        tenant_id=current_user.tenant_id,
        module_id=data.module_id,
        is_applicable="1" if data.is_applicable else "0",
        non_applicability_justification=data.non_applicability_justification,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.patch("/process-module-assignments/{assignment_id}", response_model=ProcessModuleAssignmentResponse)
def update_process_module_assignment(
    assignment_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ProcessModuleAssignmentUpdate = None,
):
    """Update process module assignment."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    assignment = db.query(ProcessModuleAssignment).filter(
        ProcessModuleAssignment.id == assignment_id,
        ProcessModuleAssignment.tenant_id == current_user.tenant_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if data.is_applicable is not None:
        assignment.is_applicable = "1" if data.is_applicable else "0"
    if data.non_applicability_justification is not None:
        assignment.non_applicability_justification = data.non_applicability_justification

    db.commit()
    db.refresh(assignment)
    return assignment