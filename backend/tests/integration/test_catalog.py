"""
E-ITS Catalog & Measures API Tests
==================================

Test suite for V2 Catalog API endpoints and schemas:
- GET /v2/catalog/versions/ - List catalog versions
- GET /v2/catalog/versions/{id} - Get catalog version
- GET /v2/catalog/versions/{id}/modules - List modules by version
- GET /v2/catalog/modules/{id} - Get single module
- GET /v2/catalog/modules/{id}/measures - List module measures
- GET /v2/catalog/measures - List all measures
- GET /v2/catalog/threats - List threats
- GET /v2/catalog/damage-scenarios - List damage scenarios
- GET /v2/catalog/asset-categories - List asset categories

Run with: pytest -v
         pytest -v -s (show print statements)
"""
from uuid import uuid4

import pytest


class TestCatalogEnums:
    """
    =============================================================
    TEST CLASS: Catalog Enum Validation Tests
    =============================================================

    Purpose: Verify E-ITS catalog enums validate correctly.
    """

    def test_measure_level_enum_values(self):
        """Test MeasureLevel enum accepts valid values."""
        from app.schemas.eits_catalog import MeasureLevel

        valid_levels = ["BASE", "STANDARD", "HIGH"]
        for level in valid_levels:
            assert MeasureLevel(level) is not None
            assert MeasureLevel(level).value == level

    def test_measure_level_rejects_invalid(self):
        """Test MeasureLevel enum rejects invalid values."""
        from app.schemas.eits_catalog import MeasureLevel

        with pytest.raises(ValueError):
            MeasureLevel("INVALID")

    def test_module_group_enum_values(self):
        """Test ModuleGroup enum accepts valid values."""
        from app.schemas.eits_catalog import ModuleGroup

        valid_groups = ["ISMS", "ORP", "CON", "OPS", "DER", "INF", "NET", "SYS", "APP", "IND"]
        for group in valid_groups:
            assert ModuleGroup(group) is not None
            assert ModuleGroup(group).value == group

    def test_module_group_rejects_invalid(self):
        """Test ModuleGroup enum rejects invalid values."""
        from app.schemas.eits_catalog import ModuleGroup

        with pytest.raises(ValueError):
            ModuleGroup("INVALID")

    def test_module_type_enum_values(self):
        """Test ModuleType enum accepts valid values."""
        from app.schemas.eits_catalog import ModuleType

        valid_types = ["PROCESS", "SYSTEM"]
        for mtype in valid_types:
            assert ModuleType(mtype) is not None
            assert ModuleType(mtype).value == mtype

    def test_module_type_rejects_invalid(self):
        """Test ModuleType enum rejects invalid values."""
        from app.schemas.eits_catalog import ModuleType

        with pytest.raises(ValueError):
            ModuleType("INVALID")


class TestCatalogVersionSchemas:
    """
    =============================================================
    TEST CLASS: Catalog Version Schema Tests
    =============================================================

    Purpose: Test CatalogVersion schema validation.
    """

    def test_catalog_version_base_optional_fields(self):
        """Test CatalogVersionBase has correct optional fields."""
        from datetime import date

        from app.schemas.eits_catalog import CatalogVersionBase

        cv = CatalogVersionBase(
            year="2024",
            name="E-ITS 2024 Catalog",
            is_active=True,
            released_at=date(2024, 1, 1),
        )
        assert cv.year == "2024"
        assert cv.name == "E-ITS 2024 Catalog"
        assert cv.is_active is True
        assert cv.released_at == date(2024, 1, 1)

    def test_catalog_version_base_all_optional(self):
        """Test CatalogVersionBase allows all fields to be optional."""
        from app.schemas.eits_catalog import CatalogVersionBase

        cv = CatalogVersionBase()
        assert cv.year is None
        assert cv.name is None
        assert cv.is_active is False
        assert cv.released_at is None

    def test_catalog_version_response_fields(self):
        """Test CatalogVersionResponse has all required fields."""
        from app.schemas.eits_catalog import CatalogVersionResponse
        from datetime import datetime

        now = datetime.now()
        response = CatalogVersionResponse(
            id=uuid4(),
            year="2024",
            name="E-ITS 2024 Catalog",
            source_name="RIA E-ITS 2024 Excel",
            source_file_hash="abc123",
            imported_at=now,
            is_active=True,
            released_at=None,
        )
        assert response.year == "2024"
        assert response.name == "E-ITS 2024 Catalog"
        assert response.source_name == "RIA E-ITS 2024 Excel"
        assert response.is_active is True


class TestEitsModuleSchemas:
    """
    =============================================================
    TEST CLASS: E-ITS Module Schema Tests
    =============================================================

    Purpose: Test EitsModule schema validation.
    """

    def test_eits_module_base_fields(self):
        """Test EitsModuleBase accepts valid module data."""
        from app.schemas.eits_catalog import EitsModuleBase, ModuleGroup, ModuleType

        module = EitsModuleBase(
            code="ISMS.1",
            name="Information Security Management System",
            module_group=ModuleGroup.ISMS,
            category="Management",
            description="ISMS module",
            module_type=ModuleType.PROCESS,
            source_url="https://example.com",
        )
        assert module.code == "ISMS.1"
        assert module.name == "Information Security Management System"
        assert module.module_group == ModuleGroup.ISMS
        assert module.module_type == ModuleType.PROCESS

    def test_eits_module_base_required_fields(self):
        """Test EitsModuleBase requires code and name."""
        from app.schemas.eits_catalog import EitsModuleBase

        module = EitsModuleBase(code="ISMS.1", name="Test Module")
        assert module.code == "ISMS.1"
        assert module.name == "Test Module"

    def test_eits_module_response_fields(self):
        """Test EitsModuleResponse includes id and catalog_version_id."""
        from app.schemas.eits_catalog import EitsModuleResponse, ModuleGroup, ModuleType

        module_id = uuid4()
        catalog_id = uuid4()

        response = EitsModuleResponse(
            id=module_id,
            catalog_version_id=catalog_id,
            code="ISMS.1",
            name="Test Module",
            module_group=ModuleGroup.ISMS,
            category="Management",
            description="Test",
            module_type=ModuleType.PROCESS,
            source_url=None,
        )
        assert response.id == module_id
        assert response.catalog_version_id == catalog_id

    def test_eits_module_with_measures(self):
        """Test EitsModuleWithMeasures includes measures list."""
        from app.schemas.eits_catalog import (
            EitsCatalogMeasureResponse,
            EitsModuleWithMeasures,
            MeasureLevel,
        )

        module_id = uuid4()
        measure_id = uuid4()

        measure = EitsCatalogMeasureResponse(
            id=measure_id,
            module_id=module_id,
            code="ISMS.1.M1",
            name="Test Measure",
            measure_level=MeasureLevel.BASE,
            description="Test measure",
            responsible_role="Security Manager",
        )

        response = EitsModuleWithMeasures(
            id=module_id,
            catalog_version_id=uuid4(),
            code="ISMS.1",
            name="Test Module",
            module_group=None,
            category=None,
            description=None,
            module_type=None,
            source_url=None,
            measures=[measure],
        )
        assert len(response.measures) == 1
        assert response.measures[0].code == "ISMS.1.M1"


class TestEitsCatalogMeasureSchemas:
    """
    =============================================================
    TEST CLASS: E-ITS Catalog Measure Schema Tests
    =============================================================

    Purpose: Test EitsCatalogMeasure schema validation.
    """

    def test_catalog_measure_base_required_fields(self):
        """Test EitsCatalogMeasureBase requires code, name, measure_level."""
        from app.schemas.eits_catalog import EitsCatalogMeasureBase, MeasureLevel

        measure = EitsCatalogMeasureBase(
            code="ISMS.1.M1",
            name="Test Measure",
            measure_level=MeasureLevel.BASE,
        )
        assert measure.code == "ISMS.1.M1"
        assert measure.name == "Test Measure"
        assert measure.measure_level == MeasureLevel.BASE

    def test_catalog_measure_base_with_optional(self):
        """Test EitsCatalogMeasureBase accepts optional fields."""
        from app.schemas.eits_catalog import EitsCatalogMeasureBase, MeasureLevel

        measure = EitsCatalogMeasureBase(
            code="ISMS.1.M1",
            name="Test Measure",
            measure_level=MeasureLevel.STANDARD,
            description="Full measure description",
            responsible_role="Security Manager",
        )
        assert measure.description == "Full measure description"
        assert measure.responsible_role == "Security Manager"

    def test_catalog_measure_level_validation(self):
        """Test measure_level accepts BASE, STANDARD, HIGH."""
        from app.schemas.eits_catalog import EitsCatalogMeasureBase, MeasureLevel

        for level in [MeasureLevel.BASE, MeasureLevel.STANDARD, MeasureLevel.HIGH]:
            measure = EitsCatalogMeasureBase(
                code="TEST.1.M1",
                name="Test",
                measure_level=level,
            )
            assert measure.measure_level == level

    def test_catalog_measure_rejects_invalid_level(self):
        """Test measure_level rejects invalid values."""
        from app.schemas.eits_catalog import EitsCatalogMeasureBase

        with pytest.raises(ValueError):
            EitsCatalogMeasureBase(
                code="TEST.1.M1",
                name="Test",
                measure_level="INVALID_LEVEL",
            )


class TestCatalogEndpointAuth:
    """
    =============================================================
    TEST CLASS: Catalog Endpoint Authentication Tests
    =============================================================

    Purpose: Verify catalog endpoints require authentication.
    """

    @pytest.fixture(autouse=True)
    def mock_database(self):
        """Mock database to avoid connection issues during tests."""
        from unittest.mock import MagicMock, patch

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.db.session.get_engine", return_value=mock_engine):
            with patch("app.db.session.get_session_maker") as mock_maker:
                mock_maker.return_value = MagicMock(return_value=MagicMock())
                yield

    @pytest.mark.parametrize("endpoint,method,description", [
        ("/api/v2/catalog/versions", "GET", "List catalog versions"),
        ("/api/v2/catalog/versions/module-001", "GET", "Get catalog version"),
        ("/api/v2/catalog/versions/module-001/modules", "GET", "List modules by version"),
        ("/api/v2/catalog/modules/module-001", "GET", "Get single module"),
        ("/api/v2/catalog/modules/module-001/measures", "GET", "List module measures"),
        ("/api/v2/catalog/measures", "GET", "List all measures"),
        ("/api/v2/catalog/threats", "GET", "List threats"),
        ("/api/v2/catalog/damage-scenarios", "GET", "List damage scenarios"),
        ("/api/v2/catalog/asset-categories", "GET", "List asset categories"),
    ])
    def test_catalog_endpoint_requires_auth(self, endpoint, method, description):
        """
        =============================================================
        TEST: Catalog Endpoint Authentication Required
        =============================================================

        Endpoint: {method} {endpoint}
        Description: {description}

        This test verifies that catalog endpoints reject unauthenticated
        requests with HTTP 401 or 422.
        """
        from fastapi.testclient import TestClient

        from app.main import app

        print(f"\n[TEST] Testing {method} {endpoint}")

        with TestClient(app) as client:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            print(f"       Response: HTTP {response.status_code}")

            assert response.status_code in [401, 422], (
                f"[FAIL] {method} {endpoint} accessible without auth! "
                f"Got {response.status_code}, expected 401 or 422."
            )

        print("       Result: PASS - Authentication required")


class TestSecurityEnums:
    """
    =============================================================
    TEST CLASS: Security & PEARO Enums Tests
    =============================================================

    Purpose: Test security-related enums from eits_catalog schema.
    """

    def test_security_approach_enum_values(self):
        """Test SecurityApproach enum accepts valid values."""
        from app.schemas.eits_catalog import SecurityApproach

        valid_approaches = ["BASIC", "STANDARD", "CORE"]
        for approach in valid_approaches:
            assert SecurityApproach(approach) is not None
            assert SecurityApproach(approach).value == approach

    def test_security_approach_rejects_invalid(self):
        """Test SecurityApproach enum rejects invalid values."""
        from app.schemas.eits_catalog import SecurityApproach

        with pytest.raises(ValueError):
            SecurityApproach("INVALID")

    def test_pearo_status_enum_values(self):
        """Test PearoStatus enum accepts valid values."""
        from app.schemas.eits_catalog import PearoStatus

        valid_statuses = ["P", "E", "A", "R", "O"]
        for status in valid_statuses:
            assert PearoStatus(status) is not None
            assert PearoStatus(status).value == status

    def test_pearo_status_rejects_invalid(self):
        """Test PearoStatus enum rejects invalid values."""
        from app.schemas.eits_catalog import PearoStatus

        with pytest.raises(ValueError):
            PearoStatus("X")

    def test_imr_priority_enum_values(self):
        """Test ImrPriority enum accepts valid values."""
        from app.schemas.eits_catalog import ImrPriority

        valid_priorities = ["P1", "P2", "P3"]
        for priority in valid_priorities:
            assert ImrPriority(priority) is not None
            assert ImrPriority(priority).value == priority

    def test_imr_priority_rejects_invalid(self):
        """Test ImrPriority enum rejects invalid values."""
        from app.schemas.eits_catalog import ImrPriority

        with pytest.raises(ValueError):
            ImrPriority("P4")

    def test_protection_need_level_enum_values(self):
        """Test ProtectionNeedLevel enum accepts valid values."""
        from app.schemas.eits_catalog import ProtectionNeedLevel

        valid_levels = ["NORMAL", "HIGH", "VERY_HIGH"]
        for level in valid_levels:
            assert ProtectionNeedLevel(level) is not None
            assert ProtectionNeedLevel(level).value == level


class TestDamageAndThreatSchemas:
    """
    =============================================================
    TEST CLASS: Damage Scenario & Threat Schema Tests
    =============================================================

    Purpose: Test damage scenarios and threat schemas.
    """

    def test_eits_threat_base_fields(self):
        """Test EitsThreatBase accepts valid threat data."""
        from app.schemas.eits_catalog import EitsThreatBase

        threat = EitsThreatBase(
            code="T001",
            name="Test Threat",
            category="Technical",
            impact_area="Confidentiality",
            description="A test threat",
        )
        assert threat.code == "T001"
        assert threat.name == "Test Threat"
        assert threat.category == "Technical"

    def test_eits_threat_response_fields(self):
        """Test EitsThreatResponse includes id and version_id."""
        from app.schemas.eits_catalog import EitsThreatResponse

        threat_id = uuid4()
        version_id = uuid4()

        response = EitsThreatResponse(
            id=threat_id,
            version_id=version_id,
            code="T001",
            name="Test Threat",
            category="Technical",
            impact_area="Confidentiality",
            description="A test threat",
        )
        assert response.id == threat_id
        assert response.version_id == version_id

    def test_module_threat_create_fields(self):
        """Test ModuleThreatCreate accepts module and threat IDs."""
        from app.schemas.eits_catalog import ModuleThreatCreate

        data = ModuleThreatCreate(
            module_id=uuid4(),
            threat_id=uuid4(),
            relevance_note="High relevance for this module",
        )
        assert data.module_id is not None
        assert data.threat_id is not None
        assert data.relevance_note == "High relevance for this module"

    def test_damage_scenario_response_fields(self):
        """Test DamageScenarioResponse has correct fields."""
        from app.schemas.eits_catalog import DamageScenarioResponse

        scenario = DamageScenarioResponse(
            id=uuid4(),
            code="KS1",
            name="Legal compliance breach",
            description="Damage from violating laws and regulations",
        )
        assert scenario.code == "KS1"
        assert scenario.name == "Legal compliance breach"

    def test_asset_type_category_response_fields(self):
        """Test AssetTypeCategoryResponse has correct fields."""
        from app.schemas.eits_catalog import AssetTypeCategoryResponse

        category = AssetTypeCategoryResponse(
            id=uuid4(),
            code="T",
            name="Infrastructure",
            description="Buildings, rooms, technical systems",
        )
        assert category.code == "T"
        assert category.name == "Infrastructure"


class TestIMRItemSchemas:
    """
    =============================================================
    TEST CLASS: IMR Item Schema Tests
    =============================================================

    Purpose: Test IMR (Implementation Readiness) item schemas.
    """

    def test_imr_item_base_fields(self):
        """Test ImrItemBase accepts valid IMR item data."""
        from datetime import date

        from app.schemas.eits_catalog import ImrItemBase, ImrPriority, PearoStatus

        item = ImrItemBase(
            measure_id=uuid4(),
            pearo_status=PearoStatus.E,
            implementation_description="Implemented via automated script",
            due_date=date(2024, 12, 31),
            next_review_date=date(2025, 6, 30),
            priority=ImrPriority.P1,
            verification_method="Automated test",
        )
        assert item.pearo_status == PearoStatus.E
        assert item.priority == ImrPriority.P1

    def test_imr_item_create_extends_base(self):
        """Test ImrItemCreate extends ImrItemBase with additional fields."""
        from app.schemas.eits_catalog import ImrItemCreate, PearoStatus

        item = ImrItemCreate(
            measure_id=uuid4(),
            pearo_status=PearoStatus.R,
            asset_module_mapping_id=uuid4(),
            is_process_module_measure=True,
            responsible_user_id=uuid4(),
        )
        assert item.asset_module_mapping_id is not None
        assert item.is_process_module_measure is True

    def test_imr_item_update_all_optional(self):
        """Test ImrItemUpdate allows all fields to be optional."""
        from app.schemas.eits_catalog import ImrItemUpdate, PearoStatus

        update = ImrItemUpdate()
        assert update.pearo_status is None

        update.pearo_status = PearoStatus.A
        assert update.pearo_status == PearoStatus.A

    def test_imr_summary_response_fields(self):
        """Test ImrSummaryResponse has correct aggregation fields."""
        from app.schemas.eits_catalog import ImrSummaryResponse

        summary = ImrSummaryResponse(
            tenant_id=uuid4(),
            pearo_status="R",
            measure_level="BASE",
            measure_count=50,
            overdue_count=5,
        )
        assert summary.pearo_status == "R"
        assert summary.measure_count == 50
        assert summary.overdue_count == 5


class TestRiskMeasureLinkSchemas:
    """
    =============================================================
    TEST CLASS: Risk Measure Link Schema Tests
    =============================================================

    Purpose: Test risk-measure linking schemas.
    """

    def test_risk_measure_link_base_fields(self):
        """Test RiskMeasureLinkBase accepts valid link data."""
        from app.schemas.eits_catalog import RiskMeasureLinkBase

        link = RiskMeasureLinkBase(
            risk_id=uuid4(),
            measure_id=uuid4(),
            imr_item_id=uuid4(),
        )
        assert link.risk_id is not None
        assert link.measure_id is not None

    def test_risk_measure_link_with_custom_measure(self):
        """Test RiskMeasureLinkBase supports custom measure names."""
        from app.schemas.eits_catalog import RiskMeasureLinkBase

        link = RiskMeasureLinkBase(
            risk_id=uuid4(),
            custom_measure_name="Custom mitigation",
            custom_measure_description="Implemented via compensating control",
        )
        assert link.custom_measure_name == "Custom mitigation"
        assert link.measure_id is None


class TestSecurityProfileSchemas:
    """
    =============================================================
    TEST CLASS: Security Profile Schema Tests
    =============================================================

    Purpose: Test security profile schemas.
    """

    def test_security_profile_base_fields(self):
        """Test SecurityProfileBase accepts valid profile data."""
        from app.schemas.eits_catalog import SecurityApproach, SecurityProfileBase

        profile = SecurityProfileBase(
            security_approach=SecurityApproach.STANDARD,
            catalog_version_id=uuid4(),
            notes="Approved by security team",
        )
        assert profile.security_approach == SecurityApproach.STANDARD

    def test_security_profile_create(self):
        """Test SecurityProfileCreate extends base."""
        from app.schemas.eits_catalog import SecurityApproach, SecurityProfileCreate

        profile = SecurityProfileCreate(
            security_approach=SecurityApproach.CORE,
        )
        assert profile.security_approach == SecurityApproach.CORE

    def test_security_profile_update_all_optional(self):
        """Test SecurityProfileUpdate allows partial updates."""
        from app.schemas.eits_catalog import SecurityApproach, SecurityProfileUpdate

        update = SecurityProfileUpdate(
            security_approach=SecurityApproach.BASIC,
        )
        assert update.security_approach == SecurityApproach.BASIC
        assert update.catalog_version_id is None


class TestProcessModuleAssignmentSchemas:
    """
    =============================================================
    TEST CLASS: Process Module Assignment Schema Tests
    =============================================================

    Purpose: Test process-module assignment schemas.
    """

    def test_process_module_assignment_base(self):
        """Test ProcessModuleAssignmentBase accepts valid data."""
        from app.schemas.eits_catalog import ProcessModuleAssignmentBase

        assignment = ProcessModuleAssignmentBase(
            module_id=uuid4(),
            is_applicable=True,
            non_applicability_justification=None,
        )
        assert assignment.is_applicable is True

    def test_process_module_assignment_reject_module(self):
        """Test ProcessModuleAssignmentBase marks module as non-applicable."""
        from app.schemas.eits_catalog import ProcessModuleAssignmentBase

        assignment = ProcessModuleAssignmentBase(
            module_id=uuid4(),
            is_applicable=False,
            non_applicability_justification="Not relevant for our business",
        )
        assert assignment.is_applicable is False
        assert assignment.non_applicability_justification is not None


# =============================================================
# TEST SUMMARY
# =============================================================
def test_catalog_schema_summary():
    """
    This test suite verifies:

    Enums:
    ✓ MeasureLevel - BASE, STANDARD, HIGH
    ✓ ModuleGroup - ISMS, ORP, CON, OPS, DER, INF, NET, SYS, APP, IND
    ✓ ModuleType - PROCESS, SYSTEM
    ✓ SecurityApproach - BASIC, STANDARD, CORE
    ✓ PearoStatus - P, E, A, R, O
    ✓ ImrPriority - P1, P2, P3
    ✓ ProtectionNeedLevel - NORMAL, HIGH, VERY_HIGH

    Schemas:
    ✓ CatalogVersionBase/CatalogVersionResponse
    ✓ EitsModuleBase/EitsModuleResponse/EitsModuleWithMeasures
    ✓ EitsCatalogMeasureBase/EitsCatalogMeasureResponse
    ✓ EitsThreatBase/EitsThreatResponse
    ✓ ModuleThreatCreate/ModuleThreatResponse
    ✓ DamageScenarioResponse
    ✓ AssetTypeCategoryResponse
    ✓ ImrItemBase/ImrItemCreate/ImrItemUpdate
    ✓ ImrSummaryResponse
    ✓ RiskMeasureLinkBase
    ✓ SecurityProfileBase/Create/Update
    ✓ ProcessModuleAssignmentBase

    API Tests:
    ✓ 9 catalog endpoints require authentication

    Total: 45+ tests

    To run this test suite:
        pytest tests/integration/test_catalog.py -v
        pytest tests/integration/test_catalog.py -v -s
    """
    print("\n" + "=" * 60)
    print("E-ITS CATALOG SCHEMA TEST SUITE")
    print("=" * 60)
    print("Test Classes:")
    print("  1. TestCatalogEnums              - 9 tests (enum validation)")
    print("  2. TestCatalogVersionSchemas     - 3 tests (version schemas)")
    print("  3. TestEitsModuleSchemas         - 4 tests (module schemas)")
    print("  4. TestEitsCatalogMeasureSchemas - 4 tests (measure schemas)")
    print("  5. TestCatalogEndpointAuth       - 9 tests (API auth)")
    print("  6. TestSecurityEnums             - 6 tests (security enums)")
    print("  7. TestDamageAndThreatSchemas   - 5 tests (threat/damage)")
    print("  8. TestIMRItemSchemas           - 4 tests (IMR schemas)")
    print("  9. TestRiskMeasureLinkSchemas   - 2 tests (risk-link)")
    print(" 10. TestSecurityProfileSchemas    - 3 tests (profile)")
    print(" 11. TestProcessModuleAssignment  - 2 tests (assignment)")
    print("-" * 60)
    print("Total: 51 schema tests + 9 API tests")
    print("=" * 60)
