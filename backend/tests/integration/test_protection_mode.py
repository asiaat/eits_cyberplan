"""Protection Mode API v2 Tests.

Test suite for V2 Protection Mode API endpoints and schemas.
"""
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient
from app.main import app


MOCK_TENANT_ID = uuid4()
MOCK_USER_ID = uuid4()
MOCK_SEL_ID = uuid4()


def _make_user():
    user = MagicMock()
    user.id = MOCK_USER_ID
    user.tenant_id = MOCK_TENANT_ID
    user.global_user_id = uuid4()
    user.full_name = "Test User"
    user.is_active = True
    return user


class FakeModel:
    """Simple object with real Python values, not MagicMock proxies."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def soft_delete(self, by_user_id=None):
        self.deleted_at = datetime.now(timezone.utc)
        if by_user_id:
            self.deleted_by = by_user_id


def _make_selection(**overrides):
    now = datetime.now(timezone.utc)
    return FakeModel(
        id=overrides.get("id", MOCK_SEL_ID),
        tenant_id=overrides.get("tenant_id", MOCK_TENANT_ID),
        catalog_version_id=overrides.get("catalog_version_id"),
        security_approach=overrides.get("security_approach", "BASIC"),
        evidence_id=overrides.get("evidence_id"),
        approved_by=overrides.get("approved_by"),
        approved_at=overrides.get("approved_at"),
        notes=overrides.get("notes"),
        is_active=overrides.get("is_active", True),
        created_at=overrides.get("created_at", now),
        updated_at=overrides.get("updated_at", now),
    )


class TestSecurityApproachEnum:
    def test_valid_values(self):
        from app.api.v2.protection_mode import SecurityApproach
        for v in ["BASIC", "STANDARD", "CORE"]:
            assert SecurityApproach(v).value == v

    def test_rejects_invalid(self):
        from app.api.v2.protection_mode import SecurityApproach
        with pytest.raises(ValueError):
            SecurityApproach("INVALID")


class TestProtectionModeSchemas:
    def test_response_has_expected_fields(self):
        from app.api.v2.protection_mode import ProtectionModeSelectionResponse
        expected = {
            "id", "tenant_id", "catalog_version_id", "catalog_version_name",
            "security_approach", "approach_display", "evidence_id", "evidence",
            "approved_by", "approved_by_name", "approved_at", "notes",
            "is_active", "created_at", "updated_at",
        }
        actual = set(ProtectionModeSelectionResponse.model_fields.keys())
        assert actual == expected

    def test_create_defaults_to_basic(self):
        from app.api.v2.protection_mode import ProtectionModeSelectionCreate
        inst = ProtectionModeSelectionCreate()
        assert inst.security_approach.value == "BASIC"
        assert inst.catalog_version_id is None
        assert inst.notes is None

    def test_create_with_values(self):
        from app.api.v2.protection_mode import ProtectionModeSelectionCreate, SecurityApproach
        uid = uuid4()
        inst = ProtectionModeSelectionCreate(
            security_approach=SecurityApproach.CORE,
            catalog_version_id=uid,
            notes="test note",
        )
        assert inst.security_approach.value == "CORE"
        assert inst.catalog_version_id == uid
        assert inst.notes == "test note"

    def test_update_all_optional(self):
        from app.api.v2.protection_mode import ProtectionModeSelectionUpdate
        inst = ProtectionModeSelectionUpdate()
        assert inst.security_approach is None
        assert inst.evidence_id is None
        assert inst.notes is None
        assert inst.is_active is None

    def test_linked_evidence_info(self):
        from app.api.v2.protection_mode import LinkedEvidenceInfo
        uid = uuid4()
        ev = LinkedEvidenceInfo(id=uid, title="test.pdf", evidence_type="document")
        assert ev.id == uid
        assert ev.title == "test.pdf"
        assert ev.evidence_type == "document"
        assert ev.file_hash is None

    def test_evidence_link_request_requires_id(self):
        from app.api.v2.protection_mode import EvidenceLinkRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            EvidenceLinkRequest()

    def test_from_attributes_config(self):
        from app.api.v2.protection_mode import ProtectionModeSelectionResponse
        assert ProtectionModeSelectionResponse.model_config.get("from_attributes") is True

    def test_build_selection_response(self):
        from app.api.v2.protection_mode import _build_selection_response, ProtectionModeSelectionResponse
        sel = _make_selection(notes="test note")
        db = MagicMock()
        resp = _build_selection_response(sel, db)
        assert isinstance(resp, ProtectionModeSelectionResponse)
        assert resp.id == MOCK_SEL_ID
        assert resp.tenant_id == MOCK_TENANT_ID
        assert resp.security_approach == "BASIC"
        assert resp.notes == "test note"
        assert resp.is_active is True


class TestProtectionModeAuth:
    """Verify all endpoints return 401 without auth."""

    @pytest.fixture(autouse=True)
    def mock_db(self):
        with patch("app.db.session.get_engine"), \
             patch("app.db.session.get_session_maker"):
            yield

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v2/protection-mode/", "GET"),
        ("/api/v2/protection-mode/", "POST"),
        ("/api/v2/protection-mode/approaches/list", "GET"),
        ("/api/v2/protection-mode/{id}", "GET"),
        ("/api/v2/protection-mode/{id}", "PATCH"),
        ("/api/v2/protection-mode/{id}", "DELETE"),
        ("/api/v2/protection-mode/{id}/link-evidence", "POST"),
        ("/api/v2/protection-mode/{id}/unlink-evidence", "DELETE"),
    ])
    def test_401(self, endpoint, method):
        ep = endpoint.replace("{id}", str(uuid4()))
        with TestClient(app) as client:
            if method == "GET":
                resp = client.get(ep)
            elif method == "POST":
                resp = client.post(ep, json={})
            elif method == "PATCH":
                resp = client.patch(ep, json={})
            elif method == "DELETE":
                resp = client.delete(ep)
            assert resp.status_code in [401, 422]


class TestProtectionModeAPI:
    """Authenticated API tests with mocked auth and DB."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("app.db.session.get_engine"), \
             patch("app.db.session.get_session_maker") as mock_maker:
            self.mock_session = MagicMock()
            now = datetime.now(timezone.utc)

            def _fake_refresh(obj):
                if not hasattr(obj, "created_at") or obj.created_at is None:
                    obj.created_at = now
                if not hasattr(obj, "updated_at") or obj.updated_at is None:
                    obj.updated_at = now
                obj.id = obj.id or uuid4()

            self.mock_session.refresh.side_effect = _fake_refresh

            mock_maker.return_value = MagicMock(return_value=self.mock_session)

            from app.api.v2.auth import get_current_user_v2
            self._mock_user = _make_user()
            app.dependency_overrides[get_current_user_v2] = lambda: self._mock_user

            yield

            app.dependency_overrides.clear()

    def _client(self):
        return TestClient(app)

    def test_list_approaches(self):
        resp = self._client().get("/api/v2/protection-mode/approaches/list")
        assert resp.status_code == 200
        data = resp.json()
        codes = {a["code"] for a in data["approaches"]}
        assert codes == {"BASIC", "STANDARD", "CORE"}

    def test_list_empty(self):
        self.mock_session.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        resp = self._client().get("/api/v2/protection-mode/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self):
        sel = _make_selection(notes="test")
        self.mock_session.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [sel]
        resp = self._client().get("/api/v2/protection-mode/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["notes"] == "test"

    def test_create_new(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().post(
            "/api/v2/protection-mode/",
            json={"security_approach": "STANDARD"},
        )
        assert resp.status_code == 201

    def test_create_defaults_basic(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().post("/api/v2/protection-mode/", json={})
        assert resp.status_code == 201

    def test_create_activates_existing(self):
        sel = _make_selection()
        self.mock_session.query.return_value.filter.return_value.first.return_value = sel
        resp = self._client().post(
            "/api/v2/protection-mode/",
            json={"security_approach": "BASIC"},
        )
        assert resp.status_code == 201

    def test_get_not_found(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().get(f"/api/v2/protection-mode/{uuid4()}")
        assert resp.status_code == 404

    def test_get_found(self):
        sel = _make_selection()
        self.mock_session.query.return_value.filter.return_value.first.return_value = sel
        resp = self._client().get(f"/api/v2/protection-mode/{MOCK_SEL_ID}")
        assert resp.status_code == 200
        assert resp.json()["security_approach"] == "BASIC"

    def test_update(self):
        sel = _make_selection()
        self.mock_session.query.return_value.filter.return_value.first.return_value = sel
        resp = self._client().patch(
            f"/api/v2/protection-mode/{MOCK_SEL_ID}",
            json={"notes": "updated"},
        )
        assert resp.status_code == 200

    def test_update_not_found(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().patch(
            f"/api/v2/protection-mode/{uuid4()}",
            json={"notes": "updated"},
        )
        assert resp.status_code == 404

    def test_delete(self):
        sel = _make_selection()
        self.mock_session.query.return_value.filter.return_value.first.return_value = sel
        resp = self._client().delete(f"/api/v2/protection-mode/{MOCK_SEL_ID}")
        assert resp.status_code == 204

    def test_delete_not_found(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().delete(f"/api/v2/protection-mode/{uuid4()}")
        assert resp.status_code == 404

    def test_link_evidence(self):
        sel = _make_selection()
        evidence = FakeModel(id=uuid4(), title="ev", evidence_type="doc", file_hash=None)
        self.mock_session.query.return_value.filter.return_value.first.side_effect = [sel, evidence, evidence]
        resp = self._client().post(
            f"/api/v2/protection-mode/{MOCK_SEL_ID}/link-evidence",
            json={"evidence_id": str(uuid4())},
        )
        assert resp.status_code == 200

    def test_link_evidence_selection_not_found(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().post(
            f"/api/v2/protection-mode/{uuid4()}/link-evidence",
            json={"evidence_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_link_evidence_evidence_not_found(self):
        sel = _make_selection()
        self.mock_session.query.return_value.filter.return_value.first.side_effect = [sel, None]
        resp = self._client().post(
            f"/api/v2/protection-mode/{MOCK_SEL_ID}/link-evidence",
            json={"evidence_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_unlink_evidence(self):
        sel = _make_selection(evidence_id=uuid4())
        self.mock_session.query.return_value.filter.return_value.first.return_value = sel
        resp = self._client().delete(
            f"/api/v2/protection-mode/{MOCK_SEL_ID}/unlink-evidence"
        )
        assert resp.status_code == 200

    def test_unlink_evidence_not_found(self):
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        resp = self._client().delete(
            f"/api/v2/protection-mode/{uuid4()}/unlink-evidence"
        )
        assert resp.status_code == 404
