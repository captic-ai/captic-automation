from __future__ import annotations

"""Known-bug tracking for a bug-hunting suite.

Philosophy: green = verified correct, red = a NEW/unexpected defect,
xfail = a bug we already know about and reported. This keeps the daily report
signal-rich: a known bug doesn't spam red every day, but the moment the team
FIXES it, the test "unexpectedly passes" (xpass) and shows up — telling you the
bug is gone and the marker can be removed.

Usage:

    from utils.known_issues import known_bug

    @known_bug("CAP-142", "Agent run returns 500 when prompt is empty")
    def test_agent_run_rejects_empty_prompt(agent_client):
        ...

When you believe a bug is fixed and want the run to go RED if it's still broken
(to force attention), pass verify_fixed=True:

    @known_bug("CAP-142", "...", verify_fixed=True)
"""

import pytest


def known_bug(ticket: str, reason: str, *, verify_fixed: bool = False):
    """Return an xfail marker documenting a known, already-reported bug.

    - Default (verify_fixed=False): non-strict xfail. Known failure = xfailed
      (quiet), a fix = xpassed (visible). Never turns the run red on its own.
    - verify_fixed=True: strict xfail. If the bug is NOT fixed the test fails
      loudly; use this when you expect a fix and want to be alerted if it regresses.
    """
    return pytest.mark.xfail(
        reason=f"[{ticket}] {reason}",
        strict=verify_fixed,
        run=True,
    )
