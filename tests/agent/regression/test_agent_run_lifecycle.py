"""Staging-only agent RUN lifecycle (DATA-CHANGING).

This is the highest-value business test for an agent product: can a user create/
trigger an agent run and get a correct, complete result? It creates data, so it
is marked `destructive` and is therefore auto-blocked in the prod_safe profile
and skipped unless ENABLE_DESTRUCTIVE_TESTS=true in a safe environment.

Wiring needed before it runs instead of skip:
  - AGENT_API_RUN_PATH  (endpoint that starts a run)
  - AGENT_RUN_POLL_PATH (endpoint to poll run status, supports "{id}")
  - A known-good run payload for the dedicated test account (see run_payload below)
  - Confirm the terminal-state values Captic returns (succeeded/completed/failed)
"""

import pytest

from config.settings import is_agent_run_ready
from utils.assertions import assert_json, assert_status


# TODO(captic): replace with a minimal, deterministic run request for the test
# account (e.g. a fixed prompt / fixed input document that yields a stable result).
RUN_PAYLOAD: dict[str, object] = {}


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.agent
@pytest.mark.business_critical
@pytest.mark.data_validation
@pytest.mark.destructive
@pytest.mark.requires_test_account
def test_agent_run_completes_successfully(agent_client, settings) -> None:
    """A triggered agent run reaches a successful terminal state with output."""
    if not is_agent_run_ready(settings):
        pytest.skip("Set AGENT_API_RUN_PATH + AGENT_RUN_POLL_PATH + API login to enable run tests.")
    if not RUN_PAYLOAD:
        pytest.skip("Provide a deterministic RUN_PAYLOAD for the test account.")

    start = agent_client.start_run(RUN_PAYLOAD)
    assert_status(start, settings.agent_expected_run_statuses)
    run_id = str(assert_json(start).get("id") or assert_json(start).get("run_id"))
    assert run_id and run_id != "None", "Run response did not include a run id to poll."

    final = agent_client.poll_run(run_id)
    body = assert_json(final)
    state = str(body.get("status", "")).lower()
    assert state in ("succeeded", "completed"), (
        f"Agent run ended in state '{state}', expected success. Body={body}"
    )
    # Business assertion: a successful run must actually produce output for the user.
    assert body.get("output") or body.get("result"), "Successful run returned no output/result."
