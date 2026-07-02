from __future__ import annotations

"""Reusable, business-readable assertions for API responses.

These keep test bodies short and make failures explain *what business rule*
broke, not just which status code differed. Import into any API/agent test.
"""

from typing import Any, Iterable

import httpx


def assert_status(response: httpx.Response, expected: int | Iterable[int]) -> None:
    allowed = {expected} if isinstance(expected, int) else set(expected)
    assert response.status_code in allowed, (
        f"Expected status in {sorted(allowed)} but got {response.status_code}. "
        f"URL={response.request.url} Body={response.text[:500]}"
    )


def assert_json(response: httpx.Response) -> Any:
    ctype = response.headers.get("content-type", "")
    assert "json" in ctype.lower(), f"Expected JSON response but content-type was '{ctype}'."
    try:
        return response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise AssertionError(f"Response body was not valid JSON: {response.text[:500]}") from exc


def assert_has_fields(body: dict[str, Any], fields: Iterable[str]) -> None:
    missing = [f for f in fields if f not in body]
    assert not missing, f"Response is missing required field(s): {missing}. Got keys: {list(body)}"


def assert_no_server_error(response: httpx.Response) -> None:
    assert response.status_code < 500, (
        f"Server error {response.status_code} from {response.request.url}: {response.text[:500]}"
    )


def assert_requires_auth(response: httpx.Response) -> None:
    """A protected endpoint hit without/with-bad credentials must reject, not leak."""
    assert response.status_code in (401, 403), (
        f"Expected 401/403 for an unauthorized request but got {response.status_code}. "
        "A protected resource may be exposed without authentication."
    )


def assert_rejects_bad_input(response: httpx.Response) -> None:
    """Invalid input should be a clean client error, never a 5xx or silent 2xx."""
    assert 400 <= response.status_code < 500, (
        f"Expected a 4xx validation error for bad input but got {response.status_code}. "
        "Invalid input should be rejected cleanly, not accepted or crash the server."
    )


def assert_responds_within(response: httpx.Response, max_seconds: float) -> None:
    elapsed = response.elapsed.total_seconds()
    assert elapsed <= max_seconds, (
        f"Response took {elapsed:.2f}s, exceeding the {max_seconds:.2f}s budget for "
        f"{response.request.url}. Slow responses hurt user-facing experience."
    )
