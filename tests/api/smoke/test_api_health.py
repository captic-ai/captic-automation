import pytest


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.prod_safe
def test_api_healthcheck_returns_success(api_client, settings) -> None:
    if not settings.api_health_path:
        pytest.skip("API_HEALTH_PATH is not configured.")

    response = api_client.get(settings.api_health_path)
    assert response.status_code == 200, response.text
