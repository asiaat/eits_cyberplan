"""Scope Modeling Service - E-ITS modelleerimine."""
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.bp_module_mapping import BusinessProcessModuleMapping
from app.models.business_process import BusinessProcess
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_module import EitsModule
from app.models.imr_item import ImrItem
from app.models.process_asset import ProcessAsset
from app.models.protection_need_summary import ProtectionNeedSummary
from app.models.protectionmode_selection import ProtectionModeSelection


LEVEL_FILTERS = {
    "BASIC": ["BASE"],
    "STANDARD": ["BASE", "STANDARD"],
    "CORE": ["BASE", "STANDARD", "HIGH"],
}


class ModelingService:

    @staticmethod
    def validate_asset_ready_for_modeling(db: Session, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> None:
        process_relations = db.query(ProcessAsset).filter(
            ProcessAsset.asset_id == asset_id,
        ).all()
        if not process_relations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tõrge: Seda vara ei saa modelleerida, sest see on seostamata ühegi äriprotsessiga.",
            )

        for relation in process_relations:
            bp = db.query(BusinessProcess).filter(BusinessProcess.id == relation.business_process_id).first()
            summary = db.query(ProtectionNeedSummary).filter(
                ProtectionNeedSummary.business_process_id == relation.business_process_id,
                ProtectionNeedSummary.tenant_id == tenant_id,
            ).first()
            if summary and summary.approved_by:
                continue
            has_explicit_cia = bp and (
                (bp.confidentiality_need and bp.confidentiality_need not in (None, "", "unknown")) or
                (bp.integrity_need and bp.integrity_need not in (None, "", "unknown")) or
                (bp.availability_need and bp.availability_need not in (None, "", "unknown"))
            )
            if has_explicit_cia:
                continue
            bp_name = bp.name if bp else str(relation.business_process_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tõrge: Seotud äriprotsessi '{bp_name}' kaitsetarve ei ole veel kinnitatud.",
            )

    @staticmethod
    def map_module_to_target(
        db: Session,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        module_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
    ) -> dict[str, Any]:
        module = db.query(EitsModule).filter(EitsModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        if target_type == "asset":
            ModelingService.validate_asset_ready_for_modeling(db, tenant_id, target_id)
            target = db.query(Asset).filter(Asset.id == target_id, Asset.tenant_id == tenant_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Asset not found")
            existing = db.query(AssetModuleMapping).filter(
                AssetModuleMapping.tenant_id == tenant_id,
                AssetModuleMapping.asset_id == target_id,
                AssetModuleMapping.module_id == module_id,
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="This module is already mapped to this asset")
            mapping = AssetModuleMapping(
                tenant_id=tenant_id,
                asset_id=target_id,
                module_id=module_id,
                modeled_by=user_id,
            )
        else:
            target = db.query(BusinessProcess).filter(BusinessProcess.id == target_id, BusinessProcess.tenant_id == tenant_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Business process not found")
            existing = db.query(BusinessProcessModuleMapping).filter(
                BusinessProcessModuleMapping.tenant_id == tenant_id,
                BusinessProcessModuleMapping.business_process_id == target_id,
                BusinessProcessModuleMapping.module_id == module_id,
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="This module is already mapped to this business process")
            mapping = BusinessProcessModuleMapping(
                tenant_id=tenant_id,
                business_process_id=target_id,
                module_id=module_id,
                modeled_by=user_id,
            )

        db.add(mapping)
        db.flush()

        active_mode = db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.tenant_id == tenant_id,
            ProtectionModeSelection.is_active == True,
        ).first()
        approach = active_mode.security_approach if active_mode else "BASIC"
        level_filter = LEVEL_FILTERS.get(approach, LEVEL_FILTERS["BASIC"])

        measures = db.query(EitsCatalogMeasure).filter(
            EitsCatalogMeasure.module_id == module_id,
            EitsCatalogMeasure.measure_level.in_(level_filter),
        ).all()

        generated_count = 0
        for measure in measures:
            if target_type == "asset":
                existing_imr = db.query(ImrItem).filter(
                    ImrItem.asset_module_mapping_id == mapping.id,
                    ImrItem.measure_id == measure.id,
                ).first()
            else:
                existing_imr = db.query(ImrItem).filter(
                    ImrItem.bp_module_mapping_id == mapping.id,
                    ImrItem.measure_id == measure.id,
                ).first()
            if existing_imr:
                continue

            kwargs = {
                "tenant_id": tenant_id,
                "measure_id": measure.id,
                "pearo_status": "P",
                "priority": "P2",
            }
            if target_type == "asset":
                kwargs["asset_module_mapping_id"] = mapping.id
            else:
                kwargs["bp_module_mapping_id"] = mapping.id
            imr_item = ImrItem(**kwargs)
            db.add(imr_item)
            generated_count += 1

        db.commit()
        return {
            "message": "Module successfully mapped to scope",
            f"{target_type}_module_mapping_id": mapping.id,
            "generated_measures_count": generated_count,
        }

    @staticmethod
    def remove_module_from_target(
        db: Session,
        tenant_id: uuid.UUID,
        mapping_id: uuid.UUID,
        target_type: str,
    ) -> dict[str, Any]:
        if target_type == "asset":
            mapping = db.query(AssetModuleMapping).filter(
                AssetModuleMapping.id == mapping_id,
                AssetModuleMapping.tenant_id == tenant_id,
            ).first()
        else:
            mapping = db.query(BusinessProcessModuleMapping).filter(
                BusinessProcessModuleMapping.id == mapping_id,
                BusinessProcessModuleMapping.tenant_id == tenant_id,
            ).first()

        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        if target_type == "asset":
            items = db.query(ImrItem).filter(
                ImrItem.asset_module_mapping_id == mapping_id,
                ImrItem.pearo_status == "P",
            ).all()
        else:
            items = db.query(ImrItem).filter(
                ImrItem.bp_module_mapping_id == mapping_id,
                ImrItem.pearo_status == "P",
            ).all()

        deleted_count = len(items)
        for item in items:
            db.delete(item)
        db.delete(mapping)
        db.commit()

        return {
            "message": "Module removed from scope",
            "deleted_imr_items_count": deleted_count,
        }

    @staticmethod
    def update_process_protection_need(
        db: Session,
        tenant_id: uuid.UUID,
        process_id: uuid.UUID,
        confidentiality: str,
        integrity: str,
        availability: str,
    ) -> dict[str, Any]:
        active_mode = db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.tenant_id == tenant_id,
            ProtectionModeSelection.is_active == True,
        ).first()
        if active_mode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify protection needs when mode of protection ({active_mode.security_approach}) has been set. Deactivate the protection mode first.",
            )

        process = db.query(BusinessProcess).filter(
            BusinessProcess.id == process_id,
            BusinessProcess.tenant_id == tenant_id,
        ).first()
        if not process:
            raise HTTPException(status_code=404, detail="Business process not found")

        process.confidentiality_need = confidentiality
        process.integrity_need = integrity
        process.availability_need = availability
        db.commit()

        return {"message": "Protection needs updated successfully"}
