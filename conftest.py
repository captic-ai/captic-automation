from __future__ import annotations

import re
from pathlib import Path

import pytest

from clients.api_client import ApiClient
from clients.agent_client import AgentClient
from config.settings import (
    Settings,
    get_settings,
    is_api_login_ready,
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
    for marker in (
        "read_only: performs no writes/mutations - safe against any environment",
        "business_critical: covers a revenue- or trust-critical business journey",
        "agent: exercises Captic agent behavior (creation, run, output, lifecycle)",
        "contract: validates API request/response contracts and schemas",
        "negative: validates error handling and rejection of bad input",
        "permissions: validates authz / access-control boundaries",
        "data_validation: validates data integrity and correctness of returned data",
        "resilience: validates reliability under latency, retries, or partial failure",
    ):
        config.addinivalue_line("markers", marker)


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


@pytest.fixture(scope="session")
def api_auth_token(
    api_client: ApiClient,
    settings: Settings,
    api_login_payload: dict[str, object],
) -> str:
    """Log in the dedicated test account and return a bearer token.

    Skips cleanly until API login is configured. Used by any test that needs an
    authenticated session (agent reads, permissions checks, business flows).
    """
    if not is_api_login_ready(settings):
        pytest.skip("Authenticated API session requires API login config + test account.")
    response = api_client.post(settings.api_login_path, json=api_login_payload)
    if response.status_code not in settings.api_login_expected_statuses:
        pytest.skip(f"Test-account login did not succeed (status {response.status_code}).")

    token_field = settings.api_login_success_field or "token"
    try:
        body = response.json()
    except ValueError:
        pytest.skip("Login response was not JSON; cannot extract an auth token.")
    token = body.get(token_field) if isinstance(body, dict) else None
    if not token:
        pytest.skip(
            f"Login succeeded but no '{token_field}' token was found in the response. "
            "Set API_LOGIN_SUCCESS_FIELD to the correct token field."
        )
    return str(token)


@pytest.fixture(scope="session")
def agent_client(settings: Settings, api_auth_token: str) -> AgentClient:
    """Authenticated client for Captic agent endpoints (read + run helpers)."""
    if not settings.api_base_url:
        pytest.skip("API_BASE_URL is not configured for agent tests.")
    client = AgentClient(
        settings.api_base_url,
        settings=settings,
        auth_token=api_auth_token,
        timeout_seconds=settings.api_timeout_seconds,
    )
    yield client
    client.close()


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
