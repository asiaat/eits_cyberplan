"""IMR Regeneration Service - E-ITS IMR auto-generation based on protection mode."""
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.imr_item import ImrItem
from app.models.eits_module import EitsModule
from app.models.eits_catalog_measure import EitsCatalogMeasure


LEVEL_FILTERS = {
    "BASIC": ["BASE"],
    "STANDARD": ["BASE", "STANDARD"],
    "CORE": ["BASE", "STANDARD", "HIGH"],
}


class ImrRegenerationService:

    @staticmethod
    def regenerate_for_tenant(db: Session, tenant_id: uuid.UUID, approach: str) -> dict[str, Any]:
        """Regenerate all IMR items for a tenant based on protection mode.

        1. Clear all existing IMR items for tenant
        2. Generate ALL measures from ALL modules at the specified protection level
        3. Create IMR items with PEARO status = "U" (Unknown)

        Args:
            db: Database session
            tenant_id: Tenant UUID
            approach: Security approach (BASIC, STANDARD, CORE)

        Returns:
            dict with approach, modules_count, measures_count, imr_items_created
        """
        level_filter = LEVEL_FILTERS.get(approach, LEVEL_FILTERS["BASIC"])

        existing_count = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id).count()

        db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id).delete(synchronize_session=False)

        modules = db.query(EitsModule).all()

        created_count = 0
        measures_count = 0

        for module in modules:
            measures = db.query(EitsCatalogMeasure).filter(
                EitsCatalogMeasure.module_id == module.id,
                EitsCatalogMeasure.measure_level.in_(level_filter),
            ).all()

            measures_count += len(measures)

            for measure in measures:
                imr_item = ImrItem(
                    tenant_id=tenant_id,
                    measure_id=measure.id,
                    pearo_status="U",
                    priority="P2",
                    mapped_module_id=None,
                )
                db.add(imr_item)
                created_count += 1

        db.commit()

        return {
            "approach": approach,
            "modules_count": len(modules),
            "measures_count": measures_count,
            "imr_items_created": created_count,
            "previous_imr_count": existing_count,
        }

    @staticmethod
    def get_approach_stats(db: Session, approach: str) -> dict[str, int]:
        """Get count of measures that would be generated for an approach."""
        level_filter = LEVEL_FILTERS.get(approach, LEVEL_FILTERS["BASIC"])

        modules = db.query(EitsModule).all()
        modules_count = len(modules)

        measures_count = db.query(EitsCatalogMeasure).filter(
            EitsCatalogMeasure.measure_level.in_(level_filter),
        ).count()

        return {
            "approach": approach,
            "modules_count": modules_count,
            "measures_count": measures_count,
        }