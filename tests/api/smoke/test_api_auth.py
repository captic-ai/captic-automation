import pytest

from config.settings import is_api_login_ready


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_test_account_can_authenticate_via_api(api_client, api_login_payload, settings) -> None:
    if not is_api_login_ready(settings):
        pytest.skip(
            "API auth smoke test requires API_BASE_URL, API_LOGIN_PATH, and test account credentials."
        )

    response = api_client.post(settings.api_login_path, json=api_login_payload)

    assert response.status_code in settings.api_login_expected_statuses, response.text

    if settings.api_login_success_field:
        body = response.json()
        assert settings.api_login_success_field in body, body
