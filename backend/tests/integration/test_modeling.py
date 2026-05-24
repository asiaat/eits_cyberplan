"""Scope Modeling API v2 Tests - E-ITS modelleerimine."""
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.v2.modeling_service import ModelingService

MOCK_TENANT_ID = uuid4()
MOCK_USER_ID = uuid4()
MOCK_MODULE_ID = uuid4()
MOCK_TARGET_ID = uuid4()
MOCK_MAPPING_ID = uuid4()


def _make_user():
    user = MagicMock()
    user.id = MOCK_USER_ID
    user.tenant_id = MOCK_TENANT_ID
    user.global_user_id = uuid4()
    user.full_name = "Test User"
    user.is_active = True
    return user


class FakeModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def soft_delete(self, by_user_id=None):
        self.deleted_at = datetime.now(timezone.utc)
        if by_user_id:
            self.deleted_by = by_user_id


def _make_module(**overrides):
    return FakeModel(
        id=overrides.get("id", MOCK_MODULE_ID),
        code=overrides.get("code", "SYS.1.1"),
        name=overrides.get("name", "Test Module"),
    )


def _make_measure(**overrides):
    return FakeModel(
        id=overrides.get("id", uuid4()),
        module_id=overrides.get("module_id", MOCK_MODULE_ID),
        code=overrides.get("code", "SYS.1.1.A1"),
        name=overrides.get("name", "Test Measure"),
        measure_level=overrides.get("measure_level", "BASE"),
    )


def _make_asset(**overrides):
    return FakeModel(
        id=overrides.get("id", MOCK_TARGET_ID),
        tenant_id=overrides.get("tenant_id", MOCK_TENANT_ID),
        name=overrides.get("name", "Test Asset"),
    )


def _make_bp(**overrides):
    return FakeModel(
        id=overrides.get("id", MOCK_TARGET_ID),
        tenant_id=overrides.get("tenant_id", MOCK_TENANT_ID),
        name=overrides.get("name", "Test BP"),
        confidentiality_need=overrides.get("confidentiality_need", "normal"),
        integrity_need=overrides.get("integrity_need", "normal"),
        availability_need=overrides.get("availability_need", "normal"),
    )


class TestModelingAuth:
    """All modeling endpoints require auth."""

    @pytest.fixture(autouse=True)
    def mock_db(self):
        with patch("app.db.session.get_engine"), \
             patch("app.db.session.get_session_maker"):
            yield

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v2/modeling/map?module_id={m}&target_type=asset&target_id={t}", "POST"),
        ("/api/v2/modeling/map/{id}?target_type=asset", "DELETE"),
        ("/api/v2/modeling/bp-mappings", "GET"),
        ("/api/v2/modeling/business-process/{id}/protection-need?confidentiality=high&integrity=high&availability=high", "PATCH"),
    ])
    def test_401(self, endpoint, method):
        uid = str(uuid4())
        ep = endpoint.replace("{m}", str(uuid4())).replace("{t}", str(uuid4())).replace("{id}", uid)
        with TestClient(app) as client:
            if method == "GET":
                resp = client.get(ep)
            elif method == "POST":
                resp = client.post(ep)
            elif method == "DELETE":
                resp = client.delete(ep)
            elif method == "PATCH":
                resp = client.patch(ep)
            assert resp.status_code in [401, 403, 422]


class TestModelingService:

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("app.db.session.get_engine"), \
             patch("app.db.session.get_session_maker") as mock_maker:
            self.mock_session = MagicMock()
            mock_maker.return_value = MagicMock(return_value=self.mock_session)

            from app.api.v2.auth import get_current_user_v2
            self._mock_user = _make_user()
            app.dependency_overrides[get_current_user_v2] = lambda: self._mock_user

            yield

            app.dependency_overrides.clear()



    def _client(self):
        return TestClient(app)

    def _mock_queries(self, first_values, all_values=None, all_side_effect=None):
        """Setup mock query chain with side_effect for .first() and .all().
        
        all_values: single fixed return for .all() (backward compat)
        all_side_effect: list of return values for consecutive .all() calls
        """
        mock_filter = MagicMock()
        mock_filter.first.side_effect = first_values
        if all_side_effect is not None:
            mock_filter.all.side_effect = all_side_effect
        elif all_values is not None:
            mock_filter.all.return_value = all_values
        self.mock_session.query.return_value.filter.return_value = mock_filter
        return mock_filter

    def _setup_validation_mocks(self):
        """Pre-configure validation-passing mocks for asset queries."""
        fake_pa = FakeModel(id=uuid4(), asset_id=MOCK_TARGET_ID, business_process_id=uuid4())
        fake_bp = FakeModel(id=uuid4(), tenant_id=MOCK_TENANT_ID, name="Asset BP")
        fake_pns = FakeModel(id=uuid4(), approved_by=uuid4())
        return fake_pa, fake_bp, fake_pns

    def test_map_module_to_asset(self):
        module = _make_module()
        asset = _make_asset()
        measure = _make_measure()
        fake_pa, fake_bp, fake_pns = self._setup_validation_mocks()

        self._mock_queries(
            first_values=[module, fake_bp, fake_pns, asset, None, None, None],
            all_side_effect=[[fake_pa], [measure]],
        )

        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["generated_measures_count"] == 1
        assert "asset_module_mapping_id" in data

    def test_map_module_to_business_process(self):
        module = _make_module()
        bp = _make_bp()
        measure = _make_measure()

        self._mock_queries(
            first_values=[module, bp, None, None, None],
            all_values=[measure],
        )

        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "business_process", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["generated_measures_count"] == 1
        assert "business_process_module_mapping_id" in data

    def test_map_module_module_not_found(self):
        self._mock_queries(first_values=[None])
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(uuid4()), "target_type": "asset", "target_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_map_module_asset_not_found(self):
        module = _make_module()
        fake_pa, fake_bp, fake_pns = self._setup_validation_mocks()
        self._mock_queries(
            first_values=[module, fake_bp, fake_pns, None],
            all_side_effect=[[fake_pa]],
        )
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_map_module_bp_not_found(self):
        module = _make_module()
        self._mock_queries(first_values=[module, None])
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "business_process", "target_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_map_module_duplicate_asset(self):
        module = _make_module()
        asset = _make_asset()
        fake_pa, fake_bp, fake_pns = self._setup_validation_mocks()
        self._mock_queries(
            first_values=[module, fake_bp, fake_pns, asset, _make_asset()],
            all_side_effect=[[fake_pa]],
        )
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 400
        assert "already mapped" in resp.json()["detail"]

    def test_map_module_duplicate_bp(self):
        module = _make_module()
        bp = _make_bp()
        self._mock_queries(first_values=[module, bp, _make_bp()])
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "business_process", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 400
        assert "already mapped" in resp.json()["detail"]

    def test_map_module_invalid_target_type(self):
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(uuid4()), "target_type": "invalid", "target_id": str(uuid4())},
        )
        assert resp.status_code == 422

    def test_remove_module_asset(self):
        mapping = FakeModel(id=MOCK_MAPPING_ID, tenant_id=MOCK_TENANT_ID)
        imr_item = FakeModel(id=uuid4(), pearo_status="P")
        self._mock_queries(
            first_values=[mapping],
            all_values=[imr_item],
        )
        resp = self._client().delete(
            f"/api/v2/modeling/map/{MOCK_MAPPING_ID}",
            params={"target_type": "asset"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_imr_items_count"] == 1

    def test_remove_module_bp(self):
        mapping = FakeModel(id=MOCK_MAPPING_ID, tenant_id=MOCK_TENANT_ID)
        imr_item = FakeModel(id=uuid4(), pearo_status="P")
        self._mock_queries(
            first_values=[mapping],
            all_values=[imr_item],
        )
        resp = self._client().delete(
            f"/api/v2/modeling/map/{MOCK_MAPPING_ID}",
            params={"target_type": "business_process"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_imr_items_count"] == 1

    def test_remove_module_not_found(self):
        self._mock_queries(first_values=[None])
        resp = self._client().delete(
            f"/api/v2/modeling/map/{uuid4()}",
            params={"target_type": "asset"},
        )
        assert resp.status_code == 404

    def test_update_protection_need_allowed(self):
        """No active protection mode → update succeeds."""
        bp = _make_bp()
        self._mock_queries(first_values=[None, bp])
        resp = self._client().patch(
            f"/api/v2/modeling/business-process/{MOCK_TARGET_ID}/protection-need",
            params={"confidentiality": "high", "integrity": "high", "availability": "high"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Protection needs updated successfully"
        assert bp.confidentiality_need == "high"
        assert bp.integrity_need == "high"
        assert bp.availability_need == "high"

    def test_update_protection_need_locked(self):
        """Active protection mode → 400."""
        active_mode = FakeModel(id=uuid4(), security_approach="STANDARD")
        self._mock_queries(first_values=[active_mode])
        resp = self._client().patch(
            f"/api/v2/modeling/business-process/{MOCK_TARGET_ID}/protection-need",
            params={"confidentiality": "high", "integrity": "high", "availability": "high"},
        )
        assert resp.status_code == 400
        assert "Cannot modify protection needs" in resp.json()["detail"]

    def test_update_protection_need_bp_not_found(self):
        """No active mode but BP not found → 404."""
        self._mock_queries(first_values=[None, None])
        resp = self._client().patch(
            f"/api/v2/modeling/business-process/{uuid4()}/protection-need",
            params={"confidentiality": "high", "integrity": "high", "availability": "high"},
        )
        assert resp.status_code == 404

    def test_list_bp_mappings_empty(self):
        self._mock_queries(first_values=[], all_values=[])
        resp = self._client().get("/api/v2/modeling/bp-mappings")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_validate_asset_missing_bp_link(self):
        """Asset without ProcessAsset relation → 400."""
        self._mock_queries(
            first_values=[_make_module()],
            all_side_effect=[[]],  # ProcessAsset.all() returns empty
        )
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 400
        assert "seostamata" in resp.json()["detail"]

    def test_validate_asset_unapproved_bp(self):
        """Asset linked to BP without approved protection need → 400."""
        module = _make_module()
        process_asset = FakeModel(id=uuid4(), asset_id=MOCK_TARGET_ID, business_process_id=uuid4())
        bp = FakeModel(id=uuid4(), name="Test BP", confidentiality_need=None, integrity_need=None, availability_need=None)
        self._mock_queries(
            first_values=[module, bp, None],  # PNS .first() returns None
            all_side_effect=[[process_asset]],
        )
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 400
        assert "kinnitatud" in resp.json()["detail"]

    def test_validate_asset_ready(self):
        """Asset with linked + approved BP → 201."""
        module = _make_module()
        asset = _make_asset()
        process_asset = FakeModel(id=uuid4(), asset_id=MOCK_TARGET_ID, business_process_id=uuid4())
        bp = FakeModel(id=uuid4(), name="Test BP")
        pns = FakeModel(id=uuid4(), approved_by=uuid4())
        measure = _make_measure()
        self._mock_queries(
            first_values=[module, bp, pns, asset, None, None, None],
            all_side_effect=[[process_asset], [measure]],
        )
        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 201

    def test_validate_asset_ready_for_modeling_estonian_error_no_bp(self):
        """Direct call: no process relations → Estonian error."""
        from fastapi import HTTPException
        from app.services.v2.modeling_service import ModelingService

        mock_filter = MagicMock()
        mock_filter.all.return_value = []
        self.mock_session.query.return_value.filter.return_value = mock_filter

        with pytest.raises(HTTPException) as exc:
            ModelingService.validate_asset_ready_for_modeling(self.mock_session, MOCK_TENANT_ID, MOCK_TARGET_ID)
        assert exc.value.status_code == 400
        assert "seostamata" in exc.value.detail

    def test_validate_asset_ready_for_modeling_estonian_error_unapproved(self):
        """Direct call: unapproved BP → Estonian error."""
        from app.services.v2.modeling_service import ModelingService
        process_asset = FakeModel(id=uuid4(), asset_id=MOCK_TARGET_ID, business_process_id=uuid4())
        bp = FakeModel(id=uuid4(), name="Test BP", confidentiality_need=None, integrity_need=None, availability_need=None)
        self.mock_session.query.return_value.filter.return_value.all.side_effect = [
            [process_asset],  # ProcessAsset.all()
        ]
        self.mock_session.query.return_value.filter.return_value.first.side_effect = [
            bp,              # BusinessProcess.first()
            None,            # ProtectionNeedSummary.first() → no summary
        ]
        with pytest.raises(Exception) as exc:
            ModelingService.validate_asset_ready_for_modeling(self.mock_session, MOCK_TENANT_ID, MOCK_TARGET_ID)
        assert "kinnitatud" in str(exc.value)

    def test_map_module_baseline_level_filter(self):
        """BASIC mode → only BASE measures."""
        module = _make_module()
        asset = _make_asset()
        base_measure = _make_measure(measure_level="BASE")
        fake_pa, fake_bp, fake_pns = self._setup_validation_mocks()

        # Mock only returns BASE measure (simulating SQL-level filter)
        self._mock_queries(
            first_values=[module, fake_bp, fake_pns, asset, None, None, None],
            all_side_effect=[[fake_pa], [base_measure]],
        )

        resp = self._client().post(
            f"/api/v2/modeling/map",
            params={"module_id": str(MOCK_MODULE_ID), "target_type": "asset", "target_id": str(MOCK_TARGET_ID)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["generated_measures_count"] == 1
