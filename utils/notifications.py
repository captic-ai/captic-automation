from __future__ import annotations

from datetime import datetime, timezone

import httpx

from utils.reporting import RegressionSummary


def build_google_chat_payload(
    *,
    summary: RegressionSummary,
    environment: str,
    suite_name: str,
    run_url: str | None = None,
) -> dict[str, str]:
    status = "PASSED" if summary.failed == 0 and summary.errors == 0 else "FAILED"
    lines = [
        f"{suite_name} ({environment})",
        f"Status: {status}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Total: {summary.total}",
        f"Passed: {summary.passed}",
        f"Failed: {summary.failed}",
        f"Errors: {summary.errors}",
        f"Skipped: {summary.skipped}",
        f"Duration: {summary.duration_seconds:.1f}s",
    ]
    if summary.failed_tests:
        lines.append("Failed tests:")
        lines.extend(f"- {test_name}" for test_name in summary.failed_tests)
    if run_url:
        lines.append(f"Run details: {run_url}")
    return {"text": "\n".join(lines)}


def send_google_chat_message(webhook_url: str, payload: dict[str, str]) -> None:
    response = httpx.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        timeout=20,
    )
    response.raise_for_status()
