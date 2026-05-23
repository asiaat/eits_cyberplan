"""Protection Inheritance Service.

This service calculates inherited protection needs for assets based on:
1. The asset's own baseline protection needs
2. Protection needs from linked business processes
3. Protection needs from assets that depend on this asset (upstream propagation)

Uses the Maximum Principle: inherited need = max(baseline, all propagated needs)
"""
from typing import Optional, Any
from uuid import UUID
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_relation import AssetRelation
from app.models.asset_relation_type import AssetRelationType
from app.models.process_asset import ProcessAsset
from app.models.business_process import BusinessProcess


class ProtectionInheritanceService:
    PROTECTION_LEVELS = {"normal": 1, "high": 2, "very_high": 3, "unknown": 0}

    def __init__(self, db: Session):
        self.db = db

    def _level_to_int(self, level: str) -> int:
        """Convert protection level string to integer for comparison."""
        return self.PROTECTION_LEVELS.get(level.lower() if level else "normal", 0)

    def _int_to_level(self, value: int) -> str:
        """Convert integer back to protection level string."""
        if value >= 3:
            return "very_high"
        elif value >= 2:
            return "high"
        elif value >= 1:
            return "normal"
        return "unknown"

    def _max_level(self, *levels: str) -> str:
        """Return the maximum protection level from a list."""
        max_val = max(self._level_to_int(l) for l in levels)
        return self._int_to_level(max_val)

    def get_inherited_protection_needs(self, asset_id: UUID) -> Optional[dict[str, Any]]:
        """Calculate the inherited protection needs for an asset.

        Formula: Inherited = max(baseline, process_needs, upstream_assets)
        Where upstream_assets are those that this asset depends on.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None

        baseline_c = asset.confidentiality_need or "normal"
        baseline_i = asset.integrity_need or "normal"
        baseline_a = asset.availability_need or "normal"

        # Get process protection needs (what processes use this asset)
        process_links = self.db.query(ProcessAsset).filter(
            ProcessAsset.asset_id == asset_id
        ).all()
        process_c = [baseline_c]
        process_i = [baseline_i]
        process_a = [baseline_a]

        for link in process_links:
            bp = self.db.query(BusinessProcess).filter(
                BusinessProcess.id == link.business_process_id
            ).first()
            if bp:
                process_c.append(bp.confidentiality_need or "normal")
                process_i.append(bp.integrity_need or "normal")
                process_a.append(bp.availability_need or "normal")

        # Get upstream protection needs (assets this asset depends on)
        # source_asset_id depends on target_asset_id
        upstream_links = self.db.query(AssetRelation).filter(
            AssetRelation.source_asset_id == asset_id
        ).all()

        upstream_c = [baseline_c]
        upstream_i = [baseline_i]
        upstream_a = [baseline_a]

        for link in upstream_links:
            target_asset = self.db.query(Asset).filter(
                Asset.id == link.target_asset_id
            ).first()
            if target_asset:
                # Get the inherited needs from the target
                inherited = self.get_inherited_protection_needs(target_asset.id)
                if inherited:
                    upstream_c.append(inherited["inherited_c"])
                    upstream_i.append(inherited["inherited_i"])
                    upstream_a.append(inherited["inherited_a"])

        # Apply Maximum Principle
        inherited_c = self._max_level(*process_c, *upstream_c)
        inherited_i = self._max_level(*process_i, *upstream_i)
        inherited_a = self._max_level(*process_a, *upstream_a)

        has_inherited = (
            inherited_c != baseline_c or
            inherited_i != baseline_i or
            inherited_a != baseline_a
        )

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "baseline_c": baseline_c,
            "baseline_i": baseline_i,
            "baseline_a": baseline_a,
            "inherited_c": inherited_c,
            "inherited_i": inherited_i,
            "inherited_a": inherited_a,
            "has_inherited": has_inherited,
        }

    def get_upstream_assets(self, asset_id: UUID) -> list[dict[str, Any]]:
        """Get assets that this asset depends on (source -> target means source depends on target)."""
        links = self.db.query(AssetRelation).filter(
            AssetRelation.source_asset_id == asset_id
        ).all()

        result = []
        for link in links:
            target = self.db.query(Asset).filter(Asset.id == link.target_asset_id).first()
            if target:
                inherited = self.get_inherited_protection_needs(target.id)
                rel_type_info = None
                if link.relation_type_code:
                    rel_type = self.db.query(AssetRelationType).filter(
                        AssetRelationType.code == link.relation_type_code
                    ).first()
                    if rel_type:
                        rel_type_info = {"code": rel_type.code, "name": rel_type.name}

                result.append({
                    "asset_id": str(target.id),
                    "asset_name": target.name,
                    "asset_type": target.asset_type,
                    "relation_type": link.relation_type or link.relation_type_code,
                    "relation_type_info": rel_type_info,
                    "inherited_c": inherited["inherited_c"] if inherited else target.confidentiality_need,
                    "inherited_i": inherited["inherited_i"] if inherited else target.integrity_need,
                    "inherited_a": inherited["inherited_a"] if inherited else target.availability_need,
                })

        return result

    def get_downstream_assets(self, asset_id: UUID) -> list[dict[str, Any]]:
        """Get assets that depend on this asset (other assets where this asset is a dependency)."""
        links = self.db.query(AssetRelation).filter(
            AssetRelation.target_asset_id == asset_id
        ).all()

        result = []
        for link in links:
            source = self.db.query(Asset).filter(Asset.id == link.source_asset_id).first()
            if source:
                inherited = self.get_inherited_protection_needs(source.id)
                rel_type_info = None
                if link.relation_type_code:
                    rel_type = self.db.query(AssetRelationType).filter(
                        AssetRelationType.code == link.relation_type_code
                    ).first()
                    if rel_type:
                        rel_type_info = {"code": rel_type.code, "name": rel_type.name}

                result.append({
                    "asset_id": str(source.id),
                    "asset_name": source.name,
                    "asset_type": source.asset_type,
                    "relation_type": link.relation_type or link.relation_type_code,
                    "relation_type_info": rel_type_info,
                    "inherited_c": inherited["inherited_c"] if inherited else source.confidentiality_need,
                    "inherited_i": inherited["inherited_i"] if inherited else source.integrity_need,
                    "inherited_a": inherited["inherited_a"] if inherited else source.availability_need,
                })

        return result

    def get_dependency_tree(self, asset_id: UUID, max_depth: int = 5) -> dict[str, Any]:
        """Get a full dependency tree for an asset."""

        def build_tree(aid: UUID, depth: int = 0, visited: Optional[set[UUID]] = None) -> Optional[dict[str, Any]]:
            if visited is None:
                visited = set()

            if aid in visited or depth > max_depth:
                return None

            visited.add(aid)
            asset = self.db.query(Asset).filter(Asset.id == aid).first()
            if not asset:
                return None

            inherited = self.get_inherited_protection_needs(asset.id)

            node: dict[str, Any] = {
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "baseline_c": inherited["baseline_c"] if inherited else "normal",
                "baseline_i": inherited["baseline_i"] if inherited else "normal",
                "baseline_a": inherited["baseline_a"] if inherited else "normal",
                "inherited_c": inherited["inherited_c"] if inherited else "normal",
                "inherited_i": inherited["inherited_i"] if inherited else "normal",
                "inherited_a": inherited["inherited_a"] if inherited else "normal",
                "has_inherited": inherited["has_inherited"] if inherited else False,
                "depth": depth,
                "upstream": [],
                "downstream": [],
            }

            # Add upstream nodes
            for up in self.get_upstream_assets(aid):
                child = build_tree(UUID(up["asset_id"]), depth + 1, visited.copy())
                if child:
                    node["upstream"].append(child)

            # Add downstream nodes
            for down in self.get_downstream_assets(aid):
                child = build_tree(UUID(down["asset_id"]), depth + 1, visited.copy())
                if child:
                    node["downstream"].append(child)

            return node

        return build_tree(asset_id) or {}

    def validate_relation_type(
        self,
        source_asset_id: UUID,
        target_asset_id: UUID,
        relation_type_code: str
    ) -> tuple[bool, Optional[str]]:
        """Validate if the relation type is allowed between the given assets.

        Returns (is_valid, error_message).
        """
        source = self.db.query(Asset).filter(Asset.id == source_asset_id).first()
        target = self.db.query(Asset).filter(Asset.id == target_asset_id).first()

        if not source or not target:
            return False, "Source or target asset not found"

        rel_type = self.db.query(AssetRelationType).filter(
            AssetRelationType.code == relation_type_code
        ).first()

        if not rel_type:
            return False, f"Unknown relation type: {relation_type_code}"

        # Check if source type is allowed
        if rel_type.source_types:
            allowed_sources = json.loads(rel_type.source_types) if rel_type.source_types else []
            if allowed_sources and source.asset_type not in allowed_sources:
                return False, f"Asset type '{source.asset_type}' is not allowed as source for relation '{relation_type_code}'. Allowed: {allowed_sources}"

        # Check if target type is allowed
        if rel_type.target_types:
            allowed_targets = json.loads(rel_type.target_types) if rel_type.target_types else []
            if allowed_targets and target.asset_type not in allowed_targets:
                return False, f"Asset type '{target.asset_type}' is not allowed as target for relation '{relation_type_code}'. Allowed: {allowed_targets}"

        return True, None

    def check_circular_dependency(
        self,
        tenant_id: UUID,
        source_asset_id: UUID,
        target_asset_id: UUID
    ) -> tuple[bool, Optional[str]]:
        """Check if adding a relation would create a circular dependency.

        Returns (would_create_cycle, error_message).
        """
        # Use recursive CTE to check if target can already reach source
        query = text("""
            WITH RECURSIVE dependency_chain AS (
                SELECT ar.target_asset_id, ar.source_asset_id, ARRAY[ar.target_asset_id] as path, 1 as depth
                FROM asset_relations ar
                WHERE ar.source_asset_id = :target_id
                AND ar.tenant_id = :tenant_id

                UNION ALL

                SELECT ar.target_asset_id, ar.source_asset_id, dc.path || ar.target_asset_id, dc.depth + 1
                FROM asset_relations ar
                JOIN dependency_chain dc ON ar.source_asset_id = dc.target_asset_id
                WHERE NOT ar.target_asset_id = ANY(dc.path)
                AND dc.depth < 50
                AND ar.tenant_id = :tenant_id
            )
            SELECT EXISTS (
                SELECT 1 FROM dependency_chain WHERE target_asset_id = :source_id
            ) as has_cycle;
        """)

        result = self.db.execute(query, {
            "source_id": source_asset_id,
            "target_id": target_asset_id,
            "tenant_id": tenant_id
        }).scalar()

        if result:
            return True, "Adding this relation would create a circular dependency"
        return False, None

    def get_all_relation_types(self) -> list[dict[str, Any]]:
        """Get all available relation types."""
        types = self.db.query(AssetRelationType).all()
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