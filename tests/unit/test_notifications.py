import pytest

from utils.notifications import build_google_chat_payload
from utils.reporting import RegressionSummary


@pytest.mark.unit
def test_build_google_chat_payload_contains_core_summary() -> None:
    summary = RegressionSummary(
        total=8,
        passed=7,
        failed=1,
        skipped=0,
        errors=0,
        duration_seconds=91.2,
        failed_tests=["tests.api.test_login::test_invalid_password"],
    )

    payload = build_google_chat_payload(
        summary=summary,
        environment="staging",
        suite_name="nightly-regression",
        run_url="https://example.com/run/123",
    )

    assert "nightly-regression" in payload["text"]
    assert "Failed: 1" in payload["text"]
    assert "test_invalid_password" in payload["text"]
