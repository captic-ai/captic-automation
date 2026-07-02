"""Reliability / resilience checks (prod-safe, read-only).

Stakeholders care that the service is not just "up" but *consistently responsive*.
These probe the health endpoint repeatedly and enforce a latency budget so a
slow-but-200 degradation is caught before users complain.
"""

import pytest

from utils.assertions import assert_responds_within, assert_status


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.resilience
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_health_is_consistently_fast(api_client, settings) -> None:
    if not settings.api_health_path:
        pytest.skip("API_HEALTH_PATH is not configured.")

    # A handful of sequential probes catches intermittent slowness/flakiness.
    for _ in range(3):
        response = api_client.get(settings.api_health_path)
        assert_status(response, (200,))
        assert_responds_within(response, max_seconds=3.0)
