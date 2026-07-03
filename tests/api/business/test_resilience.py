"""Reliability / resilience checks (prod-safe, read-only).

Stakeholders care that the service is not just "up" but *consistently responsive*.
These probe the health endpoint repeatedly and enforce a latency budget so a
slow-but-200 degradation is caught before users complain.
"""

import pytest

from utils.assertions import assert_no_server_error, assert_responds_within


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.resilience
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_health_is_consistently_fast(api_client, settings) -> None:
    if not settings.api_health_path:
        pytest.skip("API_HEALTH_PATH is not configured.")

    # Resilience smoke: the API responds consistently and quickly. We accept any
    # non-5xx status (200/401/403/404 all prove the server is alive and serving)
    # and only fail on server errors or slow responses.
    for _ in range(3):
        response = api_client.get(settings.api_health_path)
        assert_no_server_error(response)
        assert_responds_within(response, max_seconds=3.0)
