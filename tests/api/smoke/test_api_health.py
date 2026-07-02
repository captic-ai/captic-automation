import pytest


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.prod_safe
@pytest.mark.read_only
def test_api_is_reachable(api_client, settings) -> None:
    """Liveness smoke: the API server responds and is not erroring.

    We hit the configured health path but treat ANY non-5xx response as "alive",
    because a deployed API that returns 200/301/401/404 is still up and serving.
    A 5xx or a connection failure is a real outage and fails the check.

    If Captic exposes a dedicated health route that returns 200, set
    API_HEALTH_PATH to it and this test will also confirm that exact contract via
    test_api_health_route_returns_200 below.
    """
    path = settings.api_health_path or "/"
    response = api_client.get(path)
    assert response.status_code < 500, (
        f"API at '{path}' returned server error {response.status_code}. "
        f"The service may be down or misconfigured. Body: {response.text[:300]}"
    )


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.prod_safe
@pytest.mark.read_only
def test_api_health_route_returns_200(api_client, settings) -> None:
    """Stricter contract: the dedicated health route returns 200.

    Skips until API_HEALTH_STRICT=true, so it never blocks the pipeline while the
    real health route is still being confirmed. Turn it on once you know the path.
    """
    if not settings.api_health_strict:
        pytest.skip(
            "Set API_HEALTH_STRICT=true (and API_HEALTH_PATH to the real route) "
            "to enforce a 200 health contract."
        )
    if not settings.api_health_path:
        pytest.skip("API_HEALTH_PATH is not configured.")

    response = api_client.get(settings.api_health_path)
    assert response.status_code == 200, response.text
