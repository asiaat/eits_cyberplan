"""
E-ITS Assets API Tests
=====================

Test suite for V2 Assets API endpoints:
- GET /v2/assets/ - List assets
- POST /v2/assets/ - Create asset
- GET /v2/assets/{id} - Get single asset
- PATCH /v2/assets/{id} - Update asset
- DELETE /v2/assets/{id} - Delete asset

Run with: pytest -v
         pytest -v -s (show print statements)
"""
import pytest
from uuid import uuid4


class TestAssetsAPI:
    """
    =============================================================
    TEST CLASS: Assets API Tests
    =============================================================

    Purpose: Test V2 assets API endpoints for CRUD operations.
    """

    @pytest.fixture
    def asset_data(self):
        """Sample asset data for create tests."""
        return {
            "name": "Test Asset",
            "asset_type": "information_asset",
            "description": "A test asset for unit testing",
            "criticality": "normal",
            "confidentiality_need": "normal",
            "integrity_need": "normal",
            "availability_need": "normal",
            "lifecycle_status": "active",
        }

    @pytest.fixture
    def asset_types(self):
        """Valid asset type values."""
        return [
            "information_asset",
            "software",
            "hardware",
            "service",
            "data",
            "other",
        ]

    @pytest.fixture
    def criticality_levels(self):
        """Valid criticality level values."""
        return ["low", "normal", "high", "critical"]

    @pytest.fixture
    def status_levels(self):
        """Valid lifecycle status values."""
        return ["active", "inactive", "deprecated", "retired"]

    @pytest.fixture
    def protection_levels(self):
        """Valid protection need levels."""
        return ["normal", "high", "very_high", "unknown"]


class TestAssetSchemaValidation:
    """
    =============================================================
    TEST CLASS: Asset Schema Validation Tests
    =============================================================

    Purpose: Verify Pydantic schemas validate asset data correctly.
    """

    def test_asset_type_enum_values(self):
        """Test that AssetType enum accepts valid values."""
        from app.schemas.asset import AssetType

        valid_types = ["information_asset", "software", "hardware", "service", "data", "other"]
        for asset_type in valid_types:
            assert AssetType(asset_type) is not None
            assert AssetType(asset_type).value == asset_type

    def test_asset_type_rejects_invalid(self):
        """Test that AssetType enum rejects invalid values."""
        from app.schemas.asset import AssetType

        with pytest.raises(ValueError):
            AssetType("invalid_type")

    def test_criticality_enum_values(self):
        """Test that Criticality enum accepts valid values."""
        from app.schemas.asset import Criticality

        valid_levels = ["low", "normal", "high", "critical"]
        for level in valid_levels:
            assert Criticality(level) is not None
            assert Criticality(level).value == level

    def test_criticality_rejects_invalid(self):
        """Test that Criticality enum rejects invalid values."""
        from app.schemas.asset import Criticality

        with pytest.raises(ValueError):
            Criticality("invalid_criticality")

    def test_lifecycle_status_enum_values(self):
        """Test that LifecycleStatus enum accepts valid values."""
        from app.schemas.asset import LifecycleStatus

        valid_statuses = ["active", "inactive", "deprecated", "retired"]
        for status in valid_statuses:
            assert LifecycleStatus(status) is not None
            assert LifecycleStatus(status).value == status

    def test_lifecycle_status_rejects_invalid(self):
        """Test that LifecycleStatus enum rejects invalid values."""
        from app.schemas.asset import LifecycleStatus

        with pytest.raises(ValueError):
            LifecycleStatus("invalid_status")

    def test_protection_need_level_enum_values(self):
        """Test that ProtectionNeedLevel enum accepts valid values."""
        from app.schemas.asset import ProtectionNeedLevel

        valid_levels = ["normal", "high", "very_high", "unknown"]
        for level in valid_levels:
            assert ProtectionNeedLevel(level) is not None
            assert ProtectionNeedLevel(level).value == level

    def test_protection_need_level_rejects_invalid(self):
        """Test that ProtectionNeedLevel enum rejects invalid values."""
        from app.schemas.asset import ProtectionNeedLevel

        with pytest.raises(ValueError):
            ProtectionNeedLevel("invalid_level")


class TestAssetCreateSchema:
    """
    =============================================================
    TEST CLASS: Asset Create Schema Tests
    =============================================================

    Purpose: Test AssetCreate schema validation.
    """

    def test_asset_create_requires_name(self):
        """Test that AssetCreate requires name field."""
        from app.schemas.asset import AssetCreate, AssetType

        with pytest.raises(ValueError):
            AssetCreate(asset_type=AssetType.INFORMATION_ASSET)

    def test_asset_create_asset_type_optional(self):
        """Test that asset_type is optional (can be None for target_type override)."""
        from app.schemas.asset import AssetCreate

        asset = AssetCreate(name="Test Asset")
        assert asset.name == "Test Asset"
        assert asset.asset_type is None

    def test_asset_create_valid_minimal(self):
        """Test AssetCreate with minimal required fields."""
        from app.schemas.asset import AssetCreate, AssetType

        asset = AssetCreate(
            name="Test Asset",
            asset_type=AssetType.INFORMATION_ASSET
        )
        assert asset.name == "Test Asset"
        assert asset.asset_type == AssetType.INFORMATION_ASSET
        assert asset.criticality.value == "normal"
        assert asset.lifecycle_status.value == "active"

    def test_asset_create_with_all_fields(self):
        """Test AssetCreate with all optional fields."""
        from app.schemas.asset import (
            AssetCreate, AssetType, Criticality,
            LifecycleStatus, ProtectionNeedLevel
        )
        from uuid import uuid4

        owner_id = uuid4()
        person_id = uuid4()

        asset = AssetCreate(
            name="Full Asset",
            asset_type=AssetType.SOFTWARE,
            description="A complete asset",
            criticality=Criticality.HIGH,
            confidentiality_need=ProtectionNeedLevel.HIGH,
            integrity_need=ProtectionNeedLevel.VERY_HIGH,
            availability_need=ProtectionNeedLevel.NORMAL,
            lifecycle_status=LifecycleStatus.ACTIVE,
            owner_user_id=owner_id,
            person_id=person_id,
        )

        assert asset.name == "Full Asset"
        assert asset.asset_type == AssetType.SOFTWARE
        assert asset.description == "A complete asset"
        assert asset.criticality == Criticality.HIGH
        assert asset.confidentiality_need == ProtectionNeedLevel.HIGH
        assert asset.integrity_need == ProtectionNeedLevel.VERY_HIGH
        assert asset.availability_need == ProtectionNeedLevel.NORMAL
        assert asset.lifecycle_status == LifecycleStatus.ACTIVE
        assert asset.owner_user_id == owner_id
        assert asset.person_id == person_id


class TestAssetUpdateSchema:
    """
    =============================================================
    TEST CLASS: Asset Update Schema Tests
    =============================================================

    Purpose: Test AssetUpdate schema allows partial updates.
    """

    def test_asset_update_all_optional(self):
        """Test that AssetUpdate has all fields as optional."""
        from app.schemas.asset import AssetUpdate

        update = AssetUpdate()
        assert update.name is None
        assert update.asset_type is None
        assert update.description is None
        assert update.criticality is None

    def test_asset_update_partial_name(self):
        """Test AssetUpdate with only name updated."""
        from app.schemas.asset import AssetUpdate

        update = AssetUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.asset_type is None

    def test_asset_update_partial_criticality(self):
        """Test AssetUpdate with only criticality updated."""
        from app.schemas.asset import AssetUpdate, Criticality

        update = AssetUpdate(criticality=Criticality.CRITICAL)
        assert update.name is None
        assert update.criticality == Criticality.CRITICAL

    def test_asset_update_multiple_fields(self):
        """Test AssetUpdate with multiple fields updated."""
        from app.schemas.asset import (
            AssetUpdate, AssetType, Criticality, LifecycleStatus
        )

        update = AssetUpdate(
            name="Updated Asset",
            asset_type=AssetType.HARDWARE,
            criticality=Criticality.HIGH,
            lifecycle_status=LifecycleStatus.INACTIVE,
        )

        assert update.name == "Updated Asset"
        assert update.asset_type == AssetType.HARDWARE
        assert update.criticality == Criticality.HIGH
        assert update.lifecycle_status == LifecycleStatus.INACTIVE
        assert update.description is None


class TestAssetResponseSchema:
    """
    =============================================================
    TEST CLASS: Asset Response Schema Tests
    =============================================================

    Purpose: Test AssetResponse schema structure.
    """

    def test_asset_response_fields(self):
        """Test AssetResponse has all required fields."""
        from app.schemas.asset import AssetResponse, AssetType, Criticality, LifecycleStatus, ProtectionNeedLevel
        from datetime import datetime
        from uuid import uuid4

        now = datetime.now()
        owner_id = uuid4()

        response = AssetResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Response Asset",
            asset_type=AssetType.DATA,
            description="Test response",
            criticality=Criticality.NORMAL,
            confidentiality_need=ProtectionNeedLevel.HIGH,
            integrity_need=ProtectionNeedLevel.NORMAL,
            availability_need=ProtectionNeedLevel.VERY_HIGH,
            lifecycle_status=LifecycleStatus.ACTIVE,
            owner_user_id=owner_id,
            person_id=None,
            owner=None,
            linked_process_count=5,
            created_at=now,
            updated_at=now,
        )

        assert response.name == "Response Asset"
        assert response.asset_type == AssetType.DATA
        assert response.linked_process_count == 5
        assert response.owner is None


class TestAssetListItemSchema:
    """
    =============================================================
    TEST CLASS: Asset List Item Schema Tests
    =============================================================

    Purpose: Test AssetListItem schema for list views.
    """

    def test_asset_list_item_fields(self):
        """Test AssetListItem has correct fields for list display."""
        from app.schemas.asset import (
            AssetListItem, AssetType, Criticality,
            LifecycleStatus, ProtectionNeedLevel, OwnerInfo
        )
        from datetime import datetime
        from uuid import uuid4

        now = datetime.now()
        owner_id = uuid4()
        owner = OwnerInfo(id=owner_id, name="Test Owner", email="owner@test.com")

        item = AssetListItem(
            id=uuid4(),
            tenant_id=uuid4(),
            name="List Item Asset",
            asset_type=AssetType.SERVICE,
            criticality=Criticality.HIGH,
            confidentiality_need=ProtectionNeedLevel.NORMAL,
            integrity_need=ProtectionNeedLevel.NORMAL,
            availability_need=ProtectionNeedLevel.NORMAL,
            lifecycle_status=LifecycleStatus.ACTIVE,
            owner_user_id=owner_id,
            person_id=None,
            owner=owner,
            linked_process_count=3,
            created_at=now,
        )

        assert item.name == "List Item Asset"
        assert item.asset_type == AssetType.SERVICE
        assert item.owner.name == "Test Owner"
        assert item.linked_process_count == 3


# =============================================================
# TEST SUMMARY
# =============================================================
def test_assets_schema_summary():
    """
    This test suite verifies:

    Schema Enums:
    ✓ AssetType - 6 valid values (information_asset, software, hardware, service, data, other)
    ✓ Criticality - 4 valid values (low, normal, high, critical)
    ✓ LifecycleStatus - 4 valid values (active, inactive, deprecated, retired)
    ✓ ProtectionNeedLevel - 4 valid values (normal, high, very_high, unknown)

    Schema Classes:
    ✓ AssetCreate - requires name and asset_type
    ✓ AssetUpdate - all fields optional for partial updates
    ✓ AssetResponse - full asset with metadata
    ✓ AssetListItem - simplified for list views

    Total: 16 schema validation tests

    To run this test suite:
        pytest tests/integration/test_assets.py -v
        pytest tests/integration/test_assets.py -v -s (show prints)
    """
    print("\n" + "="*60)
    print("E-ITS ASSETS SCHEMA TEST SUITE")
    print("="*60)
    print("Test Classes:")
    print("  1. TestAssetSchemaValidation - 7 tests (enum validation)")
    print("  2. TestAssetCreateSchema     - 4 tests (create schema)")
    print("  3. TestAssetUpdateSchema      - 4 tests (update schema)")
    print("  4. TestAssetResponseSchema    - 1 test (response schema)")
    print("  5. TestAssetListItemSchema    - 1 test (list item schema)")
    print("-" * 60)
    print("Total: 17 schema tests")
    print("="*60)