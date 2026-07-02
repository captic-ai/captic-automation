"""API auth contract, negative, and permissions checks.

Most are prod-safe because they only probe rejection behavior with bad/missing
credentials (no valid data is created). They protect the two things that hurt
most in an agent product: broken login (nobody can work) and broken authz
(one tenant sees another's agents/data).

The happy-path login check already lives in tests/api/smoke/test_api_auth.py;
these cover the failure and boundary cases.
"""

import pytest

from config.settings import is_api_login_ready
from utils.assertions import (
    assert_json,
    assert_rejects_bad_input,
    assert_requires_auth,
    assert_status,
)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_login_rejects_wrong_password(api_client, settings) -> None:
    """A wrong password must be rejected, never accepted or 500."""
    if not settings.api_login_path:
        pytest.skip("Set API_LOGIN_PATH to enable login negative tests.")

    payload = dict(settings.api_login_extra_payload)
    payload[settings.api_login_identifier_field] = "nobody+captic-test@example.com"
    payload[settings.api_login_password_field] = "definitely-not-the-password"

    response = api_client.post(settings.api_login_path, json=payload)
    assert response.status_code in (400, 401, 403, 422), (
        f"Wrong-password login returned {response.status_code}; expected a clean rejection."
    )


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_login_rejects_malformed_request(api_client, settings) -> None:
    """Empty/garbage login body should be a 4xx validation error, not a crash."""
    if not settings.api_login_path:
        pytest.skip("Set API_LOGIN_PATH to enable login negative tests.")

    response = api_client.post(settings.api_login_path, json={"garbage": "value"})
    assert_rejects_bad_input(response)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.permissions
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_protected_endpoint_requires_auth(api_client, settings) -> None:
    """Hitting an authenticated endpoint with no token must be refused, not served."""
    protected_path = settings.agent_api_list_path
    if not protected_path:
        pytest.skip("Set AGENT_API_LIST_PATH (or another protected path) to enable this check.")

    response = api_client.get(protected_path)  # note: unauthenticated client on purpose
    assert_requires_auth(response)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.contract
@pytest.mark.data_validation
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_login_success_contract(api_client, settings, api_login_payload) -> None:
    """A successful login returns the token field the frontend/clients depend on."""
    if not is_api_login_ready(settings):
        pytest.skip("Configure API login + test account to enable the login contract test.")

    response = api_client.post(settings.api_login_path, json=api_login_payload)
    assert_status(response, settings.api_login_expected_statuses)
    if settings.api_login_success_field:
        body = assert_json(response)
        assert settings.api_login_success_field in body, (
            f"Login contract broken: '{settings.api_login_success_field}' missing from response."
        )
