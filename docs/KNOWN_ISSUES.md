# Known Issues Register

The suite's job is to **find bugs**, not to show green. This file tracks defects
we've already found and reported, so the daily report stays meaningful:

- **PASS (green)** = behavior verified correct.
- **FAIL (red)** = a NEW or unexpected defect — investigate today.
- **xfail** = a known bug from the table below — expected, not noise.
- **xpass** = a known bug that now PASSES — likely fixed; verify and remove the marker.
- **skip** = can't test yet (missing route/config), not a pass.

## How to record a bug

1. Add a row to the table below.
2. Mark the covering test with the helper:
   ```python
   from utils.known_issues import known_bug

   @known_bug("CAP-142", "Agent run returns 500 on empty prompt")
   def test_agent_run_rejects_empty_prompt(...):
       ...
   ```
3. When the team says it's fixed, set `verify_fixed=True` to force a red if it's
   still broken; once it passes, delete the marker and close the row.

## Open known bugs

| Ticket | Area | Summary | Test | Status |
|---|---|---|---|---|
| CAP-HEALTH-AUTH | auth / health | `GET /` health check requires a token because `auth.py` `PUBLIC_PATHS` is empty `{}`; the docstring says `GET /` should be public for Cloud Run health checks. | `test_health_root_is_public_and_ok` (xfail) | Found by code review of captic-agent/auth.py. Confirm with backend, then fix by populating PUBLIC_PATHS. Test xpasses when fixed. |

## Candidate observations (not yet confirmed bugs)

- `MOCK_MODE` is hard-coded `False` in `server.py` with no env toggle, so a deployed
  instance can't be put into mock mode — every `/chat` test hits the real paid LLM.
  Worth adding a `MOCK_MODE` env switch so smoke tests can run without LLM cost.
- The old generic `/health` path returns 403; the real health route is `GET /`.
  Point `API_HEALTH_PATH=/` (or rely on the agent health test) to avoid confusion.
