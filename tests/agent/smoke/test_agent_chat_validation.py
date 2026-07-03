"""Chat input-validation checks (prod-safe: rejected before any LLM call).

These send authenticated but INVALID /chat requests. FastAPI/pydantic rejects
them (422) or the provider resolver rejects them (400) before run_agent calls the
LLM — so they cost nothing and write nothing, yet catch real contract bugs.
"""

import pytest

from config.settings import is_agent_authenticated_ready


def _skip_if_not_ready(settings) -> None:
    if not is_agent_authenticated_ready(settings):
        pytest.skip("Set FIREBASE_API_KEY + test account to enable chat validation tests.")


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.negative
@pytest.mark.contract
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_chat_rejects_missing_required_fields(agent_client, settings) -> None:
    """A /chat body missing required fields must be a 422, not a 500 or silent 200."""
    _skip_if_not_ready(settings)
    # Missing 'trade' and 'offer_id'
    response = agent_client.chat_raw({"message": "hello"})
    assert response.status_code == 422, (
        f"Expected 422 for missing required fields, got {response.status_code}. "
        f"Body: {response.text[:300]}"
    )


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.negative
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_chat_rejects_invalid_provider(agent_client, settings, sample_trade) -> None:
    """An unknown provider must return 400 (resolved before any LLM call)."""
    _skip_if_not_ready(settings)
    response = agent_client.chat(
        message="Set Gasoil price to $88/MT",
        trade=sample_trade,
        offer_id=settings.agent_test_offer_id,
        provider="totally-bogus-provider",
    )
    assert response.status_code == 400, (
        f"Expected 400 for an invalid provider, got {response.status_code}. "
        f"Body: {response.text[:300]}"
    )
