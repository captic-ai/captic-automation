import pytest

from utils.notifications import build_google_chat_payload
from utils.reporting import RegressionSummary


def make_summary(**overrides) -> RegressionSummary:
    base = dict(
        total=10,
        passed=7,
        failed=1,
        skipped=2,
        errors=0,
        duration_seconds=42.0,
        failed_tests=["suite::test_x"],
    )
    base.update(overrides)
    return RegressionSummary(**base)


@pytest.mark.unit
def test_pass_rate_excludes_skipped_from_denominator() -> None:
    summary = make_summary(total=10, passed=8, failed=0, skipped=2, errors=0)
    # 8 passed out of 8 executed (10 - 2 skipped) = 100%
    assert summary.executed == 8
    assert summary.pass_rate == 100.0
    assert summary.is_green is True


@pytest.mark.unit
def test_pass_rate_reflects_failures() -> None:
    summary = make_summary(total=10, passed=7, failed=1, skipped=2, errors=0)
    # 7 / 8 executed = 87.5
    assert summary.pass_rate == 87.5
    assert summary.is_green is False


@pytest.mark.unit
def test_pass_rate_handles_all_skipped() -> None:
    summary = make_summary(total=3, passed=0, failed=0, skipped=3, errors=0)
    assert summary.executed == 0
    assert summary.pass_rate == 100.0


@pytest.mark.unit
def test_payload_includes_profile_and_scope_for_prod_safe() -> None:
    payload = build_google_chat_payload(
        summary=make_summary(),
        environment="production",
        suite_name="nightly-regression",
        execution_profile="prod_safe",
    )
    text = payload["text"]
    assert "Profile: prod_safe" in text
    assert "Pass rate:" in text
    assert "read-only" in text
