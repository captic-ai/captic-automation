"""Authenticated, read-only agent checks (prod-safe, no LLM cost).

Need a Firebase token but only READ, so they are safe to run daily against prod.
"""

import pytest

from config.settings import is_agent_authenticated_ready
from utils.assertions import assert_has_fields, assert_json, assert_status


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.contract
@pytest.mark.data_validation
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_models_contract(agent_client, settings) -> None:
    """GET /models returns the provider/model catalogue the UI picker relies on."""
    if not is_agent_authenticated_ready(settings):
        pytest.skip("Set FIREBASE_API_KEY + test account to enable authenticated agent reads.")

    response = agent_client.get_models()
    assert_status(response, (200,))
    body = assert_json(response)
    assert_has_fields(body, ["default_provider", "default_model", "available"])
    assert body["default_provider"], "default_provider must not be empty."
    assert body["default_model"], "default_model must not be empty."
    assert isinstance(body["available"], dict), "'available' should be a provider->models map."


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.contract
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_history_read_contract(agent_client, settings) -> None:
    """GET /history/{offer_id} returns a well-formed, user-scoped history object."""
    if not is_agent_authenticated_ready(settings):
        pytest.skip("Set FIREBASE_API_KEY + test account to enable authenticated agent reads.")

    response = agent_client.get_history(settings.agent_test_offer_id)
    assert_status(response, (200,))
    body = assert_json(response)
    assert_has_fields(body, ["offer_id", "user_id", "history"])
    assert body["offer_id"] == settings.agent_test_offer_id
    assert isinstance(body["history"], list), "history must be a list of messages."
    for msg in body["history"]:
        assert_has_fields(msg, ["role", "content"])
