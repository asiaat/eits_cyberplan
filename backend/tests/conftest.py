import os
import pytest


def pytest_configure(config):
    """Configure test environment before any imports."""
    os.environ["APP_ENV"] = "test"


@pytest.fixture(autouse=True)
def reset_lru_cache():
    """Reset lru_cache between tests to avoid state leakage."""
    from app.db import session as session_module
    session_module.get_engine.cache_clear()
    session_module.get_session_maker.cache_clear()
    yield
    session_module.get_engine.cache_clear()
    session_module.get_session_maker.cache_clear()


@pytest.fixture
def mock_tenant_id():
    """Default tenant ID for tests."""
    return "test-tenant-001"


@pytest.fixture
def mock_user_id():
    """Default user ID for tests."""
    return "test-user-001"


@pytest.fixture
def sample_user():
    """Sample user data for tests."""
    return {
        "id": "user-001",
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
        "tenant_id": "test-tenant-001",
    }


@pytest.fixture
def sample_role():
    """Sample role data for tests."""
    return {
        "id": "role-001",
        "code": "admin",
        "name": "Administrator",
        "description": "System administrator",
        "is_default": "false",
    }


@pytest.fixture
def sample_tenant():
    """Sample tenant data for tests."""
    return {
        "id": "tenant-001",
        "name": "Test Organization",
        "registry_code": "12345678",
    }


@pytest.fixture
def sample_business_process():
    """Sample business process for tests."""
    return {
        "id": "bp-001",
        "tenant_id": "test-tenant-001",
        "name": "Test Process",
        "description": "A test business process",
        "owner_user_id": "user-001",
        "confidentiality_need": "normal",
        "integrity_need": "normal",
        "availability_need": "normal",
    }


@pytest.fixture
def sample_asset():
    """Sample asset for tests."""
    return {
        "id": "asset-001",
        "tenant_id": "test-tenant-001",
        "name": "Test Asset",
        "asset_type": "information_asset",
        "description": "A test asset",
        "owner_user_id": "user-001",
        "criticality": "normal",
        "confidentiality_need": "normal",
        "integrity_need": "normal",
        "availability_need": "normal",
        "lifecycle_status": "active",
    }


@pytest.fixture
def sample_risk():
    """Sample risk for tests."""
    return {
        "id": "risk-001",
        "tenant_id": "test-tenant-001",
        "title": "Test Risk",
        "scenario": "Test scenario description",
        "target_type": "asset",
        "target_id": "asset-001",
        "threat": "test threat",
        "vulnerability": "test vulnerability",
        "likelihood": "low",
        "impact": "low",
        "risk_level": "low",
        "treatment": "mitigate",
        "owner_user_id": "user-001",
        "status": "open",
    }


@pytest.fixture
def sample_implementation_item():
    """Sample implementation plan item for tests."""
    return {
        "id": "impl-001",
        "tenant_id": "test-tenant-001",
        "measure_id": "measure-001",
        "target_type": "asset",
        "target_id": "asset-001",
        "owner_user_id": "user-001",
        "status": "not_started",
        "priority": "medium",
    }


@pytest.fixture
def sample_eits_module():
    """Sample E-ITS module for tests."""
    return {
        "id": "module-001",
        "catalog_version_id": "cat-001",
        "code": "ISMS.1",
        "name": "Information Security Management System",
        "category": "Management",
        "description": "Test module",
        "module_type": "baseline",
    }


@pytest.fixture
def sample_eits_measure():
    """Sample E-ITS measure for tests."""
    return {
        "id": "measure-001",
        "catalog_version_id": "cat-001",
        "code": "ISMS.1.1",
        "title": "Test Measure",
        "description": "Test measure description",
        "measure_level": "organizational",
        "responsible_role": "Information Security Manager",
    }


@pytest.fixture
def admin_token():
    """JWT token for admin user."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token_placeholder"


@pytest.fixture
def user_token():
    """JWT token for regular user."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_token_placeholder"

@pytest.fixture
def eits_module_id():
    """Return a valid E-ITS module ID from the database for integration tests."""
    # This will be set if there's a module in the database
    # For now, return None and tests will skip module-dependent tests
    return None


@pytest.fixture
def client():
    """Create a test client for API testing with mocked database and auth."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch, MagicMock

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("app.db.session.get_engine", return_value=mock_engine):
        with patch("app.db.session.get_session_maker") as mock_maker:
            mock_maker.return_value = MagicMock(return_value=MagicMock())
            from app.main import app
            from app.api.v2.auth import get_current_user_v2
            from uuid import uuid4

            mock_user = MagicMock()
            mock_user.id = uuid4()
            mock_user.tenant_id = uuid4()
            mock_user.global_user_id = uuid4()
            mock_user.full_name = "Test User"
            mock_user.is_active = True
            mock_user.email = "test@example.com"
            mock_user.roles = []

            app.dependency_overrides[get_current_user_v2] = lambda: mock_user
            client = TestClient(app)
            yield client
            if get_current_user_v2 in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_v2]


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for test client."""
    return {"Authorization": "Bearer test-token-placeholder"}


# Note: For full integration tests, you would need:
# 1. A real database (or test database)
# 2. Proper authentication with valid JWT tokens
# 3. Real E-ITS modules in the catalog
