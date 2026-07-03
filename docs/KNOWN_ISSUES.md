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
| _(candidate)_ | API / health | `GET /health` returns **403** instead of a public 200 | `test_api_health_route_returns_200` | Unconfirmed — confirm with backend whether health should be public |
| | | | | |

## Candidate observations (not yet confirmed bugs)

- `/health` returning 403 (above) — could be intentional (protected) or a misconfig.
  Left as a liveness-tolerant check until confirmed; flip to a `known_bug` once triaged.
