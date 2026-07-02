"""Prod-safe, READ-ONLY agent availability checks.

These validate that the agent surface is reachable and lists cleanly for the
dedicated test account. No agent is created or run here, so they are safe to run
against production on the nightly schedule.

Wiring needed before they run instead of skip:
  - AGENT_API_LIST_PATH (e.g. /api/agents)
  - API login config so the authenticated session can be established
  - Optionally API_LOGIN_SUCCESS_FIELD so the bearer token is extracted
"""

import pytest

from config.settings import is_agent_api_read_ready
from utils.assertions import (
    assert_json,
    assert_no_server_error,
    assert_responds_within,
    assert_status,
)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_agent_list_is_reachable(agent_client, settings) -> None:
    """The test account can list its agents and the endpoint responds healthily."""
    if not is_agent_api_read_ready(settings):
        pytest.skip("Set AGENT_API_LIST_PATH + API login config to enable agent read checks.")

    response = agent_client.list_agents()

    assert_no_server_error(response)
    assert_status(response, (200,))
    assert_responds_within(response, max_seconds=5.0)


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.read_only
@pytest.mark.data_validation
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_agent_list_returns_wellformed_payload(agent_client, settings) -> None:
    """Listing agents returns JSON in a shape the product/dashboard can render."""
    if not is_agent_api_read_ready(settings):
        pytest.skip("Set AGENT_API_LIST_PATH + API login config to enable agent read checks.")

    response = agent_client.list_agents()
    body = assert_json(response)

    # Accept either a bare list or an envelope like {"data": [...]} / {"agents": [...]}.
    if isinstance(body, dict):
        collection = body.get("data") or body.get("agents") or body.get("items")
        assert collection is not None, (
            f"Expected an agents collection under data/agents/items. Got keys: {list(body)}"
        )
        assert isinstance(collection, list), "Agents collection should be a list."
    else:
        assert isinstance(body, list), "Expected a list of agents or an envelope object."
