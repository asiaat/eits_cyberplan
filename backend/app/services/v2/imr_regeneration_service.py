"""IMR Regeneration Service - E-ITS IMR auto-generation based on protection mode."""
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.imr_item import ImrItem
from app.models.imr_snapshot import ImrSnapshot
from app.models.eits_module import EitsModule
from app.models.eits_catalog_measure import EitsCatalogMeasure


LEVEL_FILTERS = {
    "BASIC": ["BASE"],
    "STANDARD": ["BASE", "STANDARD"],
    "CORE": ["BASE", "STANDARD", "HIGH"],
}


class ImrRegenerationService:

    @staticmethod
    def snapshot_and_regenerate(
        db: Session,
        tenant_id: uuid.UUID,
        approach: str,
        user_id: Optional[uuid.UUID] = None,
        protection_mode_selection_id: Optional[uuid.UUID] = None,
        label: Optional[str] = None,
    ) -> dict[str, Any]:
        """Snapshot current IMR items, then regenerate.

        1. Snapshot all current (imr_snapshot_id IS NULL) IMR items for tenant
        2. Regenerate IMR items based on protection mode
        3. New items have imr_snapshot_id = NULL (current working set)

        Returns dict with snapshot info and regeneration stats.
        """
        current_items = db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).all()

        snapshot_info = None
        if current_items:
            snapshot_label = label or f"Previous state before {approach}"
            snapshot = ImrSnapshot(
                tenant_id=tenant_id,
                protection_mode_selection_id=protection_mode_selection_id,
                label=snapshot_label,
                description=f"Auto-snapshot created before switching to {approach}",
                is_current=False,
                item_count=len(current_items),
                created_by=user_id,
            )
            db.add(snapshot)
            db.flush()

            for item in current_items:
                item.imr_snapshot_id = snapshot.id

            db.flush()
            snapshot_info = {
                "snapshot_id": str(snapshot.id),
                "snapshot_label": snapshot_label,
                "snapshot_item_count": len(current_items),
            }

        db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).delete(synchronize_session=False)

        result = ImrRegenerationService._generate_items(db, tenant_id, approach)

        if snapshot_info:
            result["snapshot"] = snapshot_info
        result["previous_imr_count"] = len(current_items) if current_items else 0
        return result

    @staticmethod
    def regenerate_for_tenant(db: Session, tenant_id: uuid.UUID, approach: str) -> dict[str, Any]:
        """Regenerate all current IMR items for a tenant.

        Only affects items with imr_snapshot_id = NULL (the current working set).
        Snapshot items are preserved.
        """
        existing_count = db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).count()

        db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).delete(synchronize_session=False)

        result = ImrRegenerationService._generate_items(db, tenant_id, approach)
        result["previous_imr_count"] = existing_count
        return result

    @staticmethod
    def snapshot_and_clear(
        db: Session,
        tenant_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        protection_mode_selection_id: Optional[uuid.UUID] = None,
        label: Optional[str] = None,
    ) -> dict[str, Any]:
        """Snapshot all current IMR items and clear the current working set.
        Unlike snapshot_and_regenerate, this does NOT generate new items.
        """
        current_items = db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).all()

        snapshot_info = None
        if current_items:
            snapshot_label = label or "Auto-saved before deactivation"
            snapshot = ImrSnapshot(
                tenant_id=tenant_id,
                protection_mode_selection_id=protection_mode_selection_id,
                label=snapshot_label,
                description="Auto-snapshot created when protection mode was deactivated",
                is_current=False,
                item_count=len(current_items),
                created_by=user_id,
            )
            db.add(snapshot)
            db.flush()

            for item in current_items:
                item.imr_snapshot_id = snapshot.id

            db.flush()
            snapshot_info = {
                "snapshot_id": str(snapshot.id),
                "snapshot_label": snapshot_label,
                "snapshot_item_count": len(current_items),
            }

        db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).delete(synchronize_session=False)

        return {
            "snapshot": snapshot_info,
            "previous_imr_count": len(current_items) if current_items else 0,
        }

    @staticmethod
    def _generate_items(db: Session, tenant_id: uuid.UUID, approach: str) -> dict[str, Any]:
        """Generate IMR items for all modules at the specified protection level."""
        level_filter = LEVEL_FILTERS.get(approach, LEVEL_FILTERS["BASIC"])
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
                    pearo_status="E",
                    priority="P2",
                )
                db.add(imr_item)
                created_count += 1

        db.commit()

        return {
            "approach": approach,
            "modules_count": len(modules),
            "measures_count": measures_count,
            "imr_items_created": created_count,
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

    @staticmethod
    def restore_snapshot(db: Session, tenant_id: uuid.UUID, snapshot_id: uuid.UUID) -> int:
        """Restore a snapshot: delete current items, un-archive snapshot items."""
        current_count = db.query(ImrItem).filter(
            ImrItem.tenant_id == tenant_id,
            ImrItem.imr_snapshot_id.is_(None),
        ).delete(synchronize_session=False)

        snapshot = db.query(ImrSnapshot).filter(
            ImrSnapshot.id == snapshot_id,
            ImrSnapshot.tenant_id == tenant_id,
        ).first()
        if not snapshot:
            raise ValueError("Snapshot not found")

        db.query(ImrItem).filter(
            ImrItem.imr_snapshot_id == snapshot_id,
        ).update({"imr_snapshot_id": None})

        snapshot.restored_from = snapshot_id
        db.commit()

        return current_count
