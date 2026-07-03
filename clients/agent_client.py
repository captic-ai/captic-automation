from __future__ import annotations

"""Client for the Captic Agent API, matching the real server.py contract.

Endpoints (from captic-agent/server.py):
  GET    /                     health, public, {"status":"ok","version",...}
  GET    /models              providers/models (auth required)
  POST   /chat                the chatbot (auth required) — PAID + writes history
  GET    /history/{offer_id}  user-scoped chat history (auth required)
  DELETE /history/{offer_id}  clear the caller's history (auth required)

Auth is a Firebase ID token sent as `Authorization: Bearer <token>`.

SAFETY: get_models / get_history / health are read-only. chat() spends real LLM
credits and writes Firestore history — only call it from tests gated behind
AGENT_E2E_ENABLED, using a dedicated test offer_id, with clear_history cleanup.
"""

from typing import Any, Optional

import httpx

from clients.api_client import ApiClient
from config.settings import Settings


class AgentClient(ApiClient):
    def __init__(
        self,
        base_url: str,
        *,
        settings: Settings,
        auth_token: Optional[str] = None,
        timeout_seconds: float = 20,
    ) -> None:
        super().__init__(base_url, timeout_seconds=timeout_seconds)
        self.settings = settings
        if auth_token:
            self._client.headers.update({"Authorization": f"Bearer {auth_token}"})

    # ----- READ-ONLY -----------------------------------------------------

    def health(self, **kwargs: Any) -> httpx.Response:
        """GET / — intended to be public (Cloud Run health check)."""
        return self.get(self.settings.agent_health_path or "/", **kwargs)

    def get_models(self, **kwargs: Any) -> httpx.Response:
        return self.get(self.settings.agent_models_path, **kwargs)

    def get_history(self, offer_id: str, **kwargs: Any) -> httpx.Response:
        return self.get(f"{self.settings.agent_history_path}/{offer_id}", **kwargs)

    # ----- DATA-CHANGING / PAID -----------------------------------------

    def chat(
        self,
        *,
        message: str,
        trade: dict,
        offer_id: str,
        product_name: str = "",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """POST /chat. Spends LLM credits + writes history. Gate behind e2e opt-in."""
        payload: dict[str, Any] = {
            "message": message,
            "trade": trade,
            "offer_id": offer_id,
            "product_name": product_name,
        }
        if provider is not None:
            payload["provider"] = provider
        if model is not None:
            payload["model"] = model
        return self.post(self.settings.agent_chat_path, json=payload, **kwargs)

    def chat_raw(self, payload: dict, **kwargs: Any) -> httpx.Response:
        """POST /chat with an arbitrary payload — for negative/validation tests."""
        return self.post(self.settings.agent_chat_path, json=payload, **kwargs)

    def clear_history(self, offer_id: str, **kwargs: Any) -> httpx.Response:
        """DELETE /history/{offer_id} — cleanup after e2e chat tests."""
        return self._client.delete(
            self.build_url(f"{self.settings.agent_history_path}/{offer_id}"), **kwargs
        )
