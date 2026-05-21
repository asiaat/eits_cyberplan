import os
import pytest


def pytest_configure(config):
    """Configure test environment before any imports."""
    import time
    os.environ["APP_ENV"] = "test"
    config._start_time = time.time()


def pytest_sessionstart(session):
    """Record session start time."""
    import time
    if not hasattr(session.config, '_start_time'):
        session.config._start_time = time.time()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add enhanced test summary report at the end of test run."""
    import time

    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_WHITE = "\033[1;37m"
    RESET = "\033[0m"

    start_time = getattr(config, '_start_time', None)
    duration = time.time() - start_time if start_time else 0

    print("\n")
    print(f"{BOLD_CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD_CYAN}E-ITS BACKEND TEST REPORT{RESET}".center(70))
    print(f"{BOLD_CYAN}{'=' * 70}{RESET}")

    stats = terminalreporter.stats

    passed = len(stats.get("passed", []))
    skipped = len(stats.get("skipped", []))
    failed = len(stats.get("failed", []))
    xpassed = len(stats.get("xpassed", []))
    xfailed = len(stats.get("xfailed", []))
    warning_list = stats.get("warning", []) or stats.get("warnings", [])
    total = passed + skipped + failed + xpassed + xfailed

    pass_rate = (passed / total * 100) if total > 0 else 0
    avg_time = (duration / total * 1000) if total > 0 else 0

    print(f"\n{BOLD_WHITE}TOTAL:{RESET} {total} tests {BOLD_WHITE}|{RESET} {BOLD_WHITE}PASS RATE:{RESET} {pass_rate:.1f}% {BOLD_WHITE}|{RESET} {BOLD_WHITE}TIME:{RESET} {duration:.2f}s ({avg_time:.1f}ms avg)")

    print(f"  {GREEN}✓ {passed} passed{RESET} ({passed/total*100:.1f}%)" if total > 0 else f"  {GREEN}✓ 0 passed{RESET}")
    print(f"  {YELLOW}~ {skipped} skipped{RESET} ({skipped/total*100:.1f}%)" if total > 0 else f"  {YELLOW}~ 0 skipped{RESET}")
    if failed > 0:
        print(f"  {RED}✗ {failed} failed{RESET} ({failed/total*100:.1f}%)" if total > 0 else f"  {RED}✗ 0 failed{RESET}")
    if xfailed > 0:
        print(f"  {YELLOW}⚠ {xfailed} xfailed{RESET}")
    if xpassed > 0:
        print(f"  {GREEN}⚠ {xpassed} xpassed{RESET}")

    if warning_list:
        print(f"\n{BOLD_MAGENTA}WARNINGS ({len(warning_list)}):{RESET}")
        for w in warning_list:
            msg = getattr(w, 'message', str(w))
            loc = getattr(w, 'location', '')
            clean_msg = msg.split('\n')[0].strip() if msg else "Unknown warning"
            if "asyncio_mode" in clean_msg:
                source = "pyproject.toml"
                desc = "Unknown config option 'asyncio_mode' - may affect test behavior"
            elif loc:
                parts = str(loc).split(':')
                source = parts[0] if parts else str(loc)
                desc = clean_msg
            else:
                source = "pytest"
                desc = clean_msg
            print(f"  {YELLOW}⚠{RESET} {source}: {desc}")

    print(f"\n{YELLOW}{'-' * 70}{RESET}")
    print(f"{BOLD_BLUE}BY CATEGORY (with actual results):{RESET}".ljust(70))
    print(f"{YELLOW}{'-' * 70}{RESET}")

    file_stats = {}
    for test_list, key in [(stats.get("passed", []), "passed"), (stats.get("skipped", []), "skipped"), (stats.get("failed", []), "failed")]:
        for test in test_list:
            if hasattr(test, 'nodeid'):
                nodeid = test.nodeid
                filepath = nodeid.split("::")[0]
                if filepath not in file_stats:
                    file_stats[filepath] = {"passed": 0, "skipped": 0, "failed": 0}
                file_stats[filepath][key] += 1

    cat_files = {
        "Schema Validation": ["tests/integration/test_assets.py", "tests/integration/test_catalog.py"],
        "API Authentication": ["tests/integration/test_endpoints.py"],
        "ETL Pipeline": ["tests/unit/test_etl.py"],
        "Business Process Service": ["tests/unit/test_business_process_service.py"],
        "Targets API": ["tests/integration/test_targets.py"],
        "Modeling Service": ["tests/integration/test_modeling.py"],
        "Protection Mode": ["tests/integration/test_protection_mode.py"],
    }

    for cat_name, files in cat_files.items():
        cat_passed = 0
        cat_skipped = 0
        cat_failed = 0
        for f in files:
            if f in file_stats:
                cat_passed += file_stats[f]["passed"]
                cat_skipped += file_stats[f]["skipped"]
                cat_failed += file_stats[f]["failed"]

        cat_total = cat_passed + cat_skipped + cat_failed
        cat_pct = (cat_total / total * 100) if total > 0 else 0

        if cat_skipped == cat_total and cat_total > 0:
            icon = f"{YELLOW}~{RESET}"
        elif cat_failed > 0:
            icon = f"{RED}✗{RESET}"
        else:
            icon = f"{GREEN}✓{RESET}"

        print(f"\n{icon} {cat_name}")
        print(f"    {GREEN}✓ {cat_passed} passed{RESET} | {YELLOW}~ {cat_skipped} skipped{RESET} | {RED}✗ {cat_failed} failed{RESET} | {cat_total} total ({cat_pct:.1f}%)")

        for f in files:
            if f in file_stats:
                fs = file_stats[f]
                short_path = f.replace("tests/", "")
                print(f"    → {short_path}: {GREEN}{fs['passed']}{RESET}/{YELLOW}{fs['skipped']}{RESET}/{RED}{fs['failed']}{RESET}")

    if failed > 0:
        print(f"\n{RED}{'-' * 70}{RESET}")
        print(f"{RED}FAILED TESTS ({failed}):{RESET}".ljust(70))
        print(f"{RED}{'-' * 70}{RESET}")
        for rep in stats.get("failed", []):
            if hasattr(rep, "nodeid"):
                print(f"  {RED}✗{RESET} {rep.nodeid}")
    else:
        print(f"\n{GREEN}{'-' * 70}{RESET}")
        print(f"{GREEN}FAILED TESTS: 0 - all good!{RESET}".ljust(70))
        print(f"{GREEN}{'-' * 70}{RESET}")

    if skipped > 0:
        print(f"\n{YELLOW}{'-' * 70}{RESET}")
        print(f"{YELLOW}SKIPPED TESTS ({skipped}):{RESET}".ljust(70))
        print(f"{YELLOW}{'-' * 70}{RESET}")
        for rep in stats.get("skipped", []):
            if hasattr(rep, "nodeid"):
                reason = rep.longrepr if hasattr(rep, "longrepr") else "no reason"
                print(f"  {YELLOW}~{RESET} {rep.nodeid}")
                print(f"    Reason: {reason}")

    print(f"\n{BOLD_CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD_CYAN}E-ITS BACKEND TEST REPORT - END{RESET}".center(70))
    print(f"{BOLD_CYAN}{'=' * 70}{RESET}")
    print()


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
