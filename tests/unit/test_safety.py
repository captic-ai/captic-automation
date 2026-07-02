import pytest

from config.settings import (
    Settings,
    is_api_login_ready,
    is_ui_login_ready,
    validate_auth_configuration,
    validate_safe_targets,
)


def build_settings(**overrides) -> Settings:
    base = {
        "target_env": "staging",
        "execution_profile": "staging_full",
        "environment": "staging",
        "base_url": "https://staging.captic.ai",
        "api_base_url": "https://api-staging.captic.ai",
        "api_health_path": "/health",
        "api_timeout_seconds": 20.0,
        "viewport_width": 1440,
        "viewport_height": 900,
        "artifacts_dir": None,
        "google_chat_webhook_url": None,
        "enable_destructive_tests": False,
        "allow_unsafe_targets": False,
        "test_user_email": None,
        "test_user_password": None,
        "ui_login_path": None,
        "ui_login_email_selector": None,
        "ui_login_password_selector": None,
        "ui_login_submit_selector": None,
        "ui_login_success_selector": None,
        "api_login_path": None,
        "api_login_identifier_field": "email",
        "api_login_password_field": "password",
        "api_login_expected_statuses": (200,),
        "api_login_success_field": None,
        "api_login_extra_payload": {},
    }
    base.update(overrides)
    return Settings(**base)


@pytest.mark.unit
def test_validate_safe_targets_accepts_staging_targets() -> None:
    settings = build_settings()
    assert validate_safe_targets(settings) == []


@pytest.mark.unit
def test_validate_safe_targets_rejects_production_like_targets_in_staging_profile() -> None:
    settings = build_settings(
        environment="production",
        base_url="https://captic.ai",
        api_base_url="https://api.captic.ai",
    )

    issues = validate_safe_targets(settings)

    assert any("TEST_ENVIRONMENT" in issue for issue in issues)
    assert any("UI_BASE_URL" in issue for issue in issues)
    assert any("API_BASE_URL" in issue for issue in issues)


@pytest.mark.unit
def test_validate_safe_targets_allows_prod_targets_in_prod_safe_profile() -> None:
    settings = build_settings(
        target_env="prod",
        execution_profile="prod_safe",
        environment="production",
        base_url="https://captic.ai",
        api_base_url="https://api.captic.ai",
    )

    assert validate_safe_targets(settings) == []


@pytest.mark.unit
def test_validate_safe_targets_blocks_destructive_mode_in_prod_safe_profile() -> None:
    settings = build_settings(
        target_env="prod",
        execution_profile="prod_safe",
        environment="production",
        enable_destructive_tests=True,
    )

    issues = validate_safe_targets(settings)

    assert issues == [
        "ENABLE_DESTRUCTIVE_TESTS cannot be true when EXECUTION_PROFILE is 'prod_safe'."
    ]


@pytest.mark.unit
def test_validate_auth_configuration_rejects_orphaned_login_config() -> None:
    settings = build_settings(base_url=None, ui_login_path="/login")

    issues = validate_auth_configuration(settings)

    assert issues == ["UI login configuration is present but UI_BASE_URL is not set."]


@pytest.mark.unit
def test_login_readiness_flags_require_complete_safe_auth_setup() -> None:
    settings = build_settings(
        test_user_email="tester@example.com",
        test_user_password="secret",
        ui_login_path="/login",
        ui_login_email_selector="[name='email']",
        ui_login_password_selector="[name='password']",
        ui_login_submit_selector="button[type='submit']",
        ui_login_success_selector="[data-testid='dashboard']",
        api_login_path="/api/auth/login",
        api_login_success_field="token",
    )

    assert is_ui_login_ready(settings) is True
    assert is_api_login_ready(settings) is True
