"""End-to-end chatbot behavior (PAID: real LLM + Firestore writes).

This is the "does the chatbot actually work like a chatbot" suite: it sends real
messages and checks the agent responds coherently, keeps conversation history,
and cleans up after itself.

Gated behind AGENT_E2E_ENABLED=true because every test here spends LLM credits
and writes history. Uses a dedicated offer_id and clears history before/after so
it never touches a real trade's conversation.
"""

import pytest

from config.settings import is_agent_e2e_ready
from utils.assertions import assert_json, assert_status


pytestmark = pytest.mark.e2e


def _skip_if_not_ready(settings) -> None:
    if not is_agent_e2e_ready(settings):
        pytest.skip(
            "Paid chat e2e is off. Set FIREBASE_API_KEY + test account and "
            "AGENT_E2E_ENABLED=true to run the real chatbot tests."
        )


@pytest.fixture
def clean_offer(agent_client, settings):
    """Give each e2e test a clean, dedicated offer history; clean up afterwards."""
    offer_id = settings.agent_test_offer_id
    agent_client.clear_history(offer_id)
    yield offer_id
    agent_client.clear_history(offer_id)


@pytest.mark.agent
@pytest.mark.business_critical
@pytest.mark.data_validation
@pytest.mark.requires_test_account
def test_chat_responds_with_text_and_valid_actions(agent_client, settings, sample_trade, clean_offer) -> None:
    """A real message gets a coherent reply and well-formed actions."""
    _skip_if_not_ready(settings)

    response = agent_client.chat(
        message="Set the Gasoil price to $88/MT",
        trade=sample_trade,
        offer_id=clean_offer,
        product_name="Gasoil",
    )
    assert_status(response, (200,))
    body = assert_json(response)

    assert body.get("response", "").strip(), "Chatbot returned an empty response."
    assert isinstance(body.get("actions"), list), "'actions' must be a list."
    for action in body["actions"]:
        assert "type" in action, f"Each action needs a 'type'. Got: {action}"
    assert body.get("provider_used"), "provider_used should be reported."
    assert body.get("model_used"), "model_used should be reported."


@pytest.mark.agent
@pytest.mark.business_critical
@pytest.mark.requires_test_account
def test_chat_keeps_conversation_history(agent_client, settings, sample_trade, clean_offer) -> None:
    """Multi-turn: after two messages, history holds both turns in order (ChatGPT-like)."""
    _skip_if_not_ready(settings)

    agent_client.chat(message="What is the Gasoil price?", trade=sample_trade, offer_id=clean_offer)
    agent_client.chat(message="And the delivery port?", trade=sample_trade, offer_id=clean_offer)

    hist = assert_json(agent_client.get_history(clean_offer))
    messages = hist["history"]
    assert len(messages) >= 4, (
        f"Expected at least 2 user + 2 assistant turns, got {len(messages)}: {messages}"
    )
    roles = [m["role"] for m in messages]
    assert "user" in roles and "assistant" in roles, f"History missing roles: {roles}"
    # First recorded turn should be the user's opening message.
    assert messages[0]["role"] == "user", f"History should start with a user turn: {messages[0]}"


@pytest.mark.agent
@pytest.mark.requires_test_account
def test_clear_history_empties_conversation(agent_client, settings, sample_trade) -> None:
    """DELETE /history clears the caller's conversation for that offer."""
    _skip_if_not_ready(settings)
    offer_id = settings.agent_test_offer_id

    agent_client.chat(message="Summarise this trade", trade=sample_trade, offer_id=offer_id)
    clear = agent_client.clear_history(offer_id)
    assert_status(clear, (200,))

    hist = assert_json(agent_client.get_history(offer_id))
    assert hist["history"] == [], f"History should be empty after clear, got: {hist['history']}"
