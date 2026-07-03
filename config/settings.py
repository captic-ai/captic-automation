from __future__ import annotations

import os
from json import JSONDecodeError, loads
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

SUPPORTED_EXECUTION_PROFILES = {"prod_safe", "staging_full"}
TARGET_ENV_TO_PROFILE = {
    "prod": "prod_safe",
    "production": "prod_safe",
    "staging": "staging_full",
    "stage": "staging_full",
    "qa": "staging_full",
    "uat": "staging_full",
    "sandbox": "staging_full",
    "dev": "staging_full",
    "local": "staging_full",
}


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_target_env() -> str:
    value = os.getenv("TARGET_ENV", "prod").strip().lower()
    return value or "prod"


def _resolve_execution_profile(target_env: str) -> str:
    explicit = os.getenv("EXECUTION_PROFILE")
    if explicit:
        return explicit.strip().lower()
    return TARGET_ENV_TO_PROFILE.get(target_env, "staging_full")


@dataclass(frozen=True)
class Settings:
    target_env: str
    execution_profile: str
    environment: str
    base_url: str | None
    api_base_url: str | None
    api_health_path: str | None
    api_timeout_seconds: float
    viewport_width: int
    viewport_height: int
    artifacts_dir: Path
    google_chat_webhook_url: str | None
    enable_destructive_tests: bool
    allow_unsafe_targets: bool
    test_user_email: str | None
    test_user_password: str | None
    ui_login_path: str | None
    ui_login_email_selector: str | None
    ui_login_password_selector: str | None
    ui_login_submit_selector: str | None
    ui_login_success_selector: str | None
    api_login_path: str | None
    api_login_identifier_field: str
    api_login_password_field: str
    api_login_expected_statuses: tuple[int, ...]
    api_login_success_field: str | None
    api_login_extra_payload: dict[str, object]
    # --- Agent-specific config (added for Captic agent coverage) ---
    # All optional so account/agent tests skip cleanly until wired to real routes.
    agent_ui_path: str | None = None
    agent_api_list_path: str | None = None
    agent_api_detail_path: str | None = None
    agent_api_run_path: str | None = None
    agent_run_poll_path: str | None = None
    agent_run_timeout_seconds: float = 120.0
    agent_expected_run_statuses: tuple[int, ...] = (200, 201, 202)
    api_health_strict: bool = False


SAFE_ENVIRONMENT_KEYWORDS = {
    "local",
    "dev",
    "development",
    "qa",
    "test",
    "testing",
    "stage",
    "staging",
    "sandbox",
    "uat",
}
UNSAFE_ENVIRONMENT_KEYWORDS = {"prod", "production", "live"}
SAFE_HOST_KEYWORDS = {
    "localhost",
    "127.0.0.1",
    "qa",
    "test",
    "staging",
    "sandbox",
    "uat",
    "dev",
}
UNSAFE_HOST_KEYWORDS = {"prod", "production", "live"}


def _normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    # Strip stray whitespace/newlines (common when pasting into .env or CI vars),
    # then drop any trailing slash.
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned.rstrip("/")


def _normalize_path(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped if stripped.startswith("/") else f"/{stripped}"


def _read_target_override(target_env: str, suffix: str) -> str | None:
    namespaced = os.getenv(f"{target_env.upper()}_{suffix}")
    generic = os.getenv(suffix)
    return generic if generic is not None else namespaced


def _read_csv_ints(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    raw = os.getenv(name)
    if not raw:
        return default

    values: list[int] = []
    for piece in raw.split(","):
        candidate = piece.strip()
        if not candidate:
            continue
        values.append(int(candidate))
    return tuple(values) or default


def _read_json_object(name: str) -> dict[str, object]:
    raw = os.getenv(name)
    if not raw:
        return {}
    try:
        parsed = loads(raw)
    except JSONDecodeError as exc:
        raise ValueError(f"{name} must contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return parsed


def _is_safe_environment_name(name: str) -> bool:
    normalized = name.strip().lower()
    if any(token in normalized for token in UNSAFE_ENVIRONMENT_KEYWORDS):
        return False
    return any(token in normalized for token in SAFE_ENVIRONMENT_KEYWORDS)


def _is_safe_target_url(url: str | None) -> bool:
    if not url:
        return True

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if any(token in host for token in UNSAFE_HOST_KEYWORDS):
        return False
    return any(token in host for token in SAFE_HOST_KEYWORDS)


def validate_safe_targets(settings: "Settings") -> list[str]:
    issues: list[str] = []
    if settings.execution_profile not in SUPPORTED_EXECUTION_PROFILES:
        issues.append(
            f"EXECUTION_PROFILE='{settings.execution_profile}' is not supported."
        )

    if settings.execution_profile == "staging_full":
        if not _is_safe_environment_name(settings.environment):
            issues.append(
                f"TEST_ENVIRONMENT='{settings.environment}' is not recognized as a safe non-production environment."
            )
        if settings.base_url and not _is_safe_target_url(settings.base_url):
            issues.append(
                f"UI_BASE_URL='{settings.base_url}' does not look like a test/staging target."
            )
        if settings.api_base_url and not _is_safe_target_url(settings.api_base_url):
            issues.append(
                f"API_BASE_URL='{settings.api_base_url}' does not look like a test/staging target."
            )

    if settings.execution_profile == "prod_safe" and settings.enable_destructive_tests:
        issues.append(
            "ENABLE_DESTRUCTIVE_TESTS cannot be true when EXECUTION_PROFILE is 'prod_safe'."
        )
    return issues


def validate_auth_configuration(settings: "Settings") -> list[str]:
    issues: list[str] = []
    if settings.ui_login_path and not settings.base_url:
        issues.append("UI login configuration is present but UI_BASE_URL is not set.")
    if settings.api_login_path and not settings.api_base_url:
        issues.append("API login configuration is present but API_BASE_URL is not set.")
    return issues


def is_ui_login_ready(settings: "Settings") -> bool:
    required = (
        settings.base_url,
        settings.ui_login_path,
        settings.ui_login_email_selector,
        settings.ui_login_password_selector,
        settings.ui_login_submit_selector,
        settings.ui_login_success_selector,
        settings.test_user_email,
        settings.test_user_password,
    )
    return all(required)


def is_api_login_ready(settings: "Settings") -> bool:
    required = (
        settings.api_base_url,
        settings.api_login_path,
        settings.api_login_identifier_field,
        settings.api_login_password_field,
        settings.test_user_email,
        settings.test_user_password,
    )
    return all(required)


def is_agent_api_read_ready(settings: "Settings") -> bool:
    """Ready to run read-only agent API checks (list/detail).

    Requires an authenticated API session, so it also depends on API login.
    """
    return bool(
        settings.api_base_url
        and settings.agent_api_list_path
        and is_api_login_ready(settings)
    )


def is_agent_run_ready(settings: "Settings") -> bool:
    """Ready to run data-changing agent-run checks (staging_full only)."""
    return bool(
        settings.api_base_url
        and settings.agent_api_run_path
        and is_api_login_ready(settings)
    )


@lru_cache(maxsize=1)
def _base_settings() -> Settings:
    target_env = _read_target_env()
    return Settings(
        target_env=target_env,
        execution_profile=_resolve_execution_profile(target_env),
        environment=os.getenv("TEST_ENVIRONMENT", target_env),
        base_url=_normalize_url(_read_target_override(target_env, "UI_BASE_URL")),
        api_base_url=_normalize_url(_read_target_override(target_env, "API_BASE_URL")),
        api_health_path=_normalize_path(os.getenv("API_HEALTH_PATH")) or "/health",
        api_timeout_seconds=float(os.getenv("API_TIMEOUT_SECONDS", "20")),
        viewport_width=int(os.getenv("VIEWPORT_WIDTH", "1440")),
        viewport_height=int(os.getenv("VIEWPORT_HEIGHT", "900")),
        artifacts_dir=ROOT_DIR / "test-results" / "artifacts",
        google_chat_webhook_url=os.getenv("GOOGLE_CHAT_WEBHOOK_URL"),
        enable_destructive_tests=_read_bool("ENABLE_DESTRUCTIVE_TESTS", False),
        allow_unsafe_targets=_read_bool("ALLOW_UNSAFE_TARGETS", False),
        test_user_email=os.getenv("TEST_USER_EMAIL"),
        test_user_password=os.getenv("TEST_USER_PASSWORD"),
        ui_login_path=_normalize_path(os.getenv("UI_LOGIN_PATH")),
        ui_login_email_selector=os.getenv("UI_LOGIN_EMAIL_SELECTOR"),
        ui_login_password_selector=os.getenv("UI_LOGIN_PASSWORD_SELECTOR"),
        ui_login_submit_selector=os.getenv("UI_LOGIN_SUBMIT_SELECTOR"),
        ui_login_success_selector=os.getenv("UI_LOGIN_SUCCESS_SELECTOR"),
        api_login_path=_normalize_path(os.getenv("API_LOGIN_PATH")),
        api_login_identifier_field=os.getenv("API_LOGIN_IDENTIFIER_FIELD", "email"),
        api_login_password_field=os.getenv("API_LOGIN_PASSWORD_FIELD", "password"),
        api_login_expected_statuses=_read_csv_ints(
            "API_LOGIN_EXPECTED_STATUSES",
            (200,),
        ),
        api_login_success_field=os.getenv("API_LOGIN_SUCCESS_FIELD"),
        api_login_extra_payload=_read_json_object("API_LOGIN_EXTRA_PAYLOAD"),
        agent_ui_path=_normalize_path(os.getenv("AGENT_UI_PATH")),
        agent_api_list_path=_normalize_path(os.getenv("AGENT_API_LIST_PATH")),
        agent_api_detail_path=_normalize_path(os.getenv("AGENT_API_DETAIL_PATH")),
        agent_api_run_path=_normalize_path(os.getenv("AGENT_API_RUN_PATH")),
        agent_run_poll_path=_normalize_path(os.getenv("AGENT_RUN_POLL_PATH")),
        agent_run_timeout_seconds=float(os.getenv("AGENT_RUN_TIMEOUT_SECONDS", "120")),
        agent_expected_run_statuses=_read_csv_ints(
            "AGENT_EXPECTED_RUN_STATUSES",
            (200, 201, 202),
        ),
        api_health_strict=_read_bool("API_HEALTH_STRICT", False),
    )


def get_settings(
    *,
    ui_base_url: str | None = None,
    api_base_url: str | None = None,
    environment: str | None = None,
) -> Settings:
    base = _base_settings()
    return Settings(
        target_env=base.target_env,
        execution_profile=base.execution_profile,
        environment=environment or base.environment,
        base_url=_normalize_url(ui_base_url) if ui_base_url is not None else base.base_url,
        api_base_url=_normalize_url(api_base_url) if api_base_url is not None else base.api_base_url,
        api_health_path=base.api_health_path,
        api_timeout_seconds=base.api_timeout_seconds,
        viewport_width=base.viewport_width,
        viewport_height=base.viewport_height,
        artifacts_dir=base.artifacts_dir,
        google_chat_webhook_url=base.google_chat_webhook_url,
        enable_destructive_tests=base.enable_destructive_tests,
        allow_unsafe_targets=base.allow_unsafe_targets,
        test_user_email=base.test_user_email,
        test_user_password=base.test_user_password,
        ui_login_path=base.ui_login_path,
        ui_login_email_selector=base.ui_login_email_selector,
        ui_login_password_selector=base.ui_login_password_selector,
        ui_login_submit_selector=base.ui_login_submit_selector,
        ui_login_success_selector=base.ui_login_success_selector,
        api_login_path=base.api_login_path,
        api_login_identifier_field=base.api_login_identifier_field,
        api_login_password_field=base.api_login_password_field,
        api_login_expected_statuses=base.api_login_expected_statuses,
        api_login_success_field=base.api_login_success_field,
        api_login_extra_payload=base.api_login_extra_payload,
        agent_ui_path=base.agent_ui_path,
        agent_api_list_path=base.agent_api_list_path,
        agent_api_detail_path=base.agent_api_detail_path,
        agent_api_run_path=base.agent_api_run_path,
        agent_run_poll_path=base.agent_run_poll_path,
        agent_run_timeout_seconds=base.agent_run_timeout_seconds,
        agent_expected_run_statuses=base.agent_expected_run_statuses,
        api_health_strict=base.api_health_strict,
    )
