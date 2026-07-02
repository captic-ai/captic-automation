from __future__ import annotations

import re
from pathlib import Path

import pytest

from clients.api_client import ApiClient
from config.settings import (
    Settings,
    get_settings,
    validate_auth_configuration,
    validate_safe_targets,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ui-base-url",
        action="store",
        default=None,
        help="Override the UI base URL for browser tests.",
    )
    parser.addoption(
        "--api-base-url",
        action="store",
        default=None,
        help="Override the API base URL for backend tests.",
    )
    parser.addoption(
        "--env-name",
        action="store",
        default=None,
        help="Logical environment label used in reports and notifications.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "destructive: tests that create, update, or delete persistent data",
    )
    config.addinivalue_line(
        "markers",
        "requires_test_account: tests that require dedicated non-production credentials",
    )
    config.addinivalue_line(
        "markers",
        "prod_safe: approved for low-risk production smoke coverage",
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    config = session.config
    settings = get_settings(
        ui_base_url=config.getoption("--ui-base-url"),
        api_base_url=config.getoption("--api-base-url"),
        environment=config.getoption("--env-name"),
    )
    session.config._captic_settings = settings

    if settings.allow_unsafe_targets:
        return

    run_markers = config.getoption("-m")
    if run_markers and "unit" in run_markers and not any(
        marker in run_markers for marker in ("ui", "api", "smoke", "regression", "destructive")
    ):
        return

    issues = validate_safe_targets(settings)
    issues.extend(validate_auth_configuration(settings))
    if issues:
        details = "\n".join(f"- {issue}" for issue in issues)
        raise pytest.UsageError(
            "Unsafe automation target blocked.\n"
            "Configure only dedicated test/staging targets, or explicitly set "
            "ALLOW_UNSAFE_TARGETS=true for a temporary manual override.\n"
            f"{details}"
        )


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    existing = getattr(pytestconfig, "_captic_settings", None)
    if existing:
        return existing
    return get_settings(
        ui_base_url=pytestconfig.getoption("--ui-base-url"),
        api_base_url=pytestconfig.getoption("--api-base-url"),
        environment=pytestconfig.getoption("--env-name"),
    )


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> ApiClient:
    if not settings.api_base_url:
        pytest.skip("API_BASE_URL is not configured for API tests.")
    client = ApiClient(
        settings.api_base_url,
        timeout_seconds=settings.api_timeout_seconds,
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def browser_context_args(settings: Settings) -> dict[str, object]:
    return {
        "ignore_https_errors": True,
        "viewport": {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        },
    }


@pytest.fixture(scope="session")
def test_account(settings: Settings) -> dict[str, str]:
    if not settings.test_user_email or not settings.test_user_password:
        pytest.skip(
            "TEST_USER_EMAIL and TEST_USER_PASSWORD must be configured for account-based tests."
        )
    return {
        "email": settings.test_user_email,
        "password": settings.test_user_password,
    }


@pytest.fixture(scope="session")
def api_login_payload(settings: Settings, test_account: dict[str, str]) -> dict[str, object]:
    payload = dict(settings.api_login_extra_payload)
    payload[settings.api_login_identifier_field] = test_account["email"]
    payload[settings.api_login_password_field] = test_account["password"]
    return payload


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    settings = getattr(config, "_captic_settings", None)
    if settings is None:
        settings = get_settings(
            ui_base_url=config.getoption("--ui-base-url"),
            api_base_url=config.getoption("--api-base-url"),
            environment=config.getoption("--env-name"),
        )

    skip_destructive = pytest.mark.skip(
        reason="Destructive tests are disabled. Set ENABLE_DESTRUCTIVE_TESTS=true for approved test environments."
    )
    skip_prod_destructive = pytest.mark.skip(
        reason="Destructive tests are never allowed in the prod_safe execution profile."
    )
    skip_missing_account = pytest.mark.skip(
        reason="Dedicated test account is not configured. Set TEST_USER_EMAIL and TEST_USER_PASSWORD."
    )
    skip_non_prod_safe = pytest.mark.skip(
        reason="This test is not approved for the prod_safe execution profile."
    )

    for item in items:
        if settings.execution_profile == "prod_safe":
            is_unit = "unit" in item.keywords
            is_prod_safe = "prod_safe" in item.keywords
            if not is_unit and not is_prod_safe:
                item.add_marker(skip_non_prod_safe)

        if "destructive" in item.keywords and settings.execution_profile == "prod_safe":
            item.add_marker(skip_prod_destructive)
        elif "destructive" in item.keywords and not settings.enable_destructive_tests:
            item.add_marker(skip_destructive)
        if "requires_test_account" in item.keywords:
            if not settings.test_user_email or not settings.test_user_password:
                item.add_marker(skip_missing_account)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("page")
    if not page:
        return

    settings = item.funcargs.get("settings")
    artifacts_dir = (
        settings.artifacts_dir
        if settings
        else Path("test-results") / "artifacts"
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", item.nodeid)
    screenshot_path = artifacts_dir / f"{safe_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
