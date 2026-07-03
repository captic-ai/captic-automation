"""Agent health + auth-enforcement checks (prod-safe, read-only, no LLM cost).

These need no token and cost nothing, so they run daily against prod. They are
pure bug-hunting: they assert the *intended* behavior and let real deviations
show up red.
"""

import pytest

from utils.assertions import assert_json, assert_requires_auth
from utils.known_issues import known_bug


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.read_only
@pytest.mark.prod_safe
@known_bug(
    "CAP-HEALTH-AUTH",
    "GET / (health) requires a token because auth.py PUBLIC_PATHS is empty; "
    "Cloud Run health checks are meant to be unauthenticated. Remove marker when fixed.",
)
def test_health_root_is_public_and_ok(unauth_agent_client) -> None:
    """The root health endpoint should be public and return {"status":"ok"}.

    Currently expected to FAIL (xfail) due to the empty PUBLIC_PATHS bug — when
    the app is fixed this will xpass, signaling the fix landed.
    """
    response = unauth_agent_client.health()
    assert response.status_code == 200, (
        f"Health endpoint returned {response.status_code}; expected a public 200."
    )
    body = assert_json(response)
    assert body.get("status") == "ok", f"Expected status 'ok', got: {body}"


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.permissions
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_models_requires_auth(unauth_agent_client) -> None:
    """An unauthenticated call to a protected endpoint must be rejected (401/403)."""
    response = unauth_agent_client.get_models()
    assert_requires_auth(response)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.permissions
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_chat_requires_auth(unauth_agent_client, sample_trade) -> None:
    """The chatbot must not be usable without authentication."""
    response = unauth_agent_client.chat(
        message="Hello", trade=sample_trade, offer_id="unauth-probe"
    )
    assert_requires_auth(response)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.permissions
@pytest.mark.negative
@pytest.mark.read_only
@pytest.mark.prod_safe
def test_invalid_token_is_rejected(settings, sample_trade) -> None:
    """A malformed/garbage bearer token must be rejected, never accepted."""
    if not settings.api_base_url:
        pytest.skip("API_BASE_URL is not configured for agent tests.")
    from clients.agent_client import AgentClient

    client = AgentClient(
        settings.api_base_url,
        settings=settings,
        auth_token="not-a-real-firebase-token",
        timeout_seconds=settings.api_timeout_seconds,
    )
    try:
        response = client.get_models()
        assert_requires_auth(response)
    finally:
        client.close()
