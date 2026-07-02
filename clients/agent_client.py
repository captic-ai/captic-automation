from __future__ import annotations

import time
from typing import Any

import httpx

from clients.api_client import ApiClient
from config.settings import Settings


class AgentClient(ApiClient):
    """Authenticated, agent-aware wrapper around the base ApiClient.

    This centralizes how tests talk to Captic agent endpoints so that when the
    real routes/response shapes are confirmed, they only change in one place.

    SAFETY: `list_agents` / `get_agent` are READ-ONLY and prod-safe. `start_run`
    is DATA-CHANGING and must only be used by tests marked `destructive` /
    staging-only. The base ApiClient never runs unless API_BASE_URL is set.
    """

    def __init__(
        self,
        base_url: str,
        *,
        settings: Settings,
        auth_token: str | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        super().__init__(base_url, timeout_seconds=timeout_seconds)
        self.settings = settings
        if auth_token:
            # Default to Bearer; adjust here if Captic uses a different scheme.
            self._client.headers.update({"Authorization": f"Bearer {auth_token}"})

    # ----- READ-ONLY (prod-safe) ---------------------------------------

    def list_agents(self, **kwargs: Any) -> httpx.Response:
        path = self.settings.agent_api_list_path
        if not path:
            raise ValueError("AGENT_API_LIST_PATH is not configured.")
        return self.get(path, **kwargs)

    def get_agent(self, agent_id: str, **kwargs: Any) -> httpx.Response:
        template = self.settings.agent_api_detail_path
        if not template:
            raise ValueError("AGENT_API_DETAIL_PATH is not configured.")
        # Supports either an "{id}" template or a base path to append to.
        path = template.format(id=agent_id) if "{id}" in template else f"{template}/{agent_id}"
        return self.get(path, **kwargs)

    # ----- DATA-CHANGING (staging_full only) ---------------------------

    def start_run(self, payload: dict[str, Any], **kwargs: Any) -> httpx.Response:
        """Start an agent run. NEVER call from a prod_safe/read_only test."""
        path = self.settings.agent_api_run_path
        if not path:
            raise ValueError("AGENT_API_RUN_PATH is not configured.")
        return self.post(path, json=payload, **kwargs)

    def poll_run(
        self,
        run_id: str,
        *,
        terminal_states: tuple[str, ...] = ("succeeded", "completed", "failed", "error"),
        state_field: str = "status",
        interval_seconds: float = 2.0,
    ) -> httpx.Response:
        """Poll a run until it reaches a terminal state or the timeout elapses.

        Returns the last response. Callers assert on the final state. Read-only
        against the run resource, but only meaningful after a (data-changing)
        start_run, so keep it in staging-only paths.
        """
        template = self.settings.agent_run_poll_path
        if not template:
            raise ValueError("AGENT_RUN_POLL_PATH is not configured.")
        path = template.format(id=run_id) if "{id}" in template else f"{template}/{run_id}"

        deadline = time.monotonic() + self.settings.agent_run_timeout_seconds
        response = self.get(path)
        while time.monotonic() < deadline:
            try:
                state = str(response.json().get(state_field, "")).lower()
            except (ValueError, AttributeError):
                state = ""
            if state in terminal_states:
                return response
            time.sleep(interval_seconds)
            response = self.get(path)
        return response
