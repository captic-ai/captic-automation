# Captic Test Strategy (business-focused)

_Last updated: 2026-07-02. Automation-only repo — never modifies Captic app code._

## 1. Goal

Give product, ops, and stakeholders **confidence**, not just coverage. Every test
should map to a business question: "Can customers log in? Can they create and run
an agent? Do they get correct output? Is anyone's data exposed? Is it fast?"

## 2. Two execution profiles (already in the framework)

| Profile | When | What runs | Risk posture |
|---|---|---|---|
| `prod_safe` | Nightly against production | `unit` + `prod_safe` only; `destructive` always blocked | Read-only / non-mutating; must never create business data |
| `staging_full` | Pre-release + nightly once staging exists | Full regression incl. `destructive` (with `ENABLE_DESTRUCTIVE_TESTS=true`) | Free to create/run/delete on a throwaway environment |

Switch by changing `TARGET_ENV` (`prod` → `staging`). One switch, no code edits.

## 3. Test pyramid tailored for Captic

```
              /\
             /  \   UI journeys (few, business-critical)
            /----\   - login -> working dashboard
           /      \  - create/run agent -> see output (staging)
          /--------\  API + agent behavior (the bulk of business validation)
         /          \  - auth contracts, agent list/detail/run, permissions,
        /            \   negative input, data integrity, resilience
       /--------------\ Unit / framework (fast, safety + reporting logic)
      /________________\
```

Rationale: UI is expensive and flaky, so keep it thin and reserved for journeys
a human would call "the product working." Push most business validation into the
API/agent layer where it is fast and stable. Unit tests guard the framework's own
safety and reporting logic so the harness itself never lies to stakeholders.

## 4. Categories

For each: **why it matters**, **profile**, **test data**, **risks**, **priority**.

### A. Core smoke (health, homepage, login)
- **Why:** the "is the lights on" check; a red here means customers are blocked.
- **Profile:** `prod_safe` (read-only) + `staging_full`.
- **Data:** none beyond the dedicated test account.
- **Risks:** health path may differ from `/health`; homepage assertion is generic.
- **Priority:** P0. _Already partly implemented._

### B. Business-critical journeys (login → dashboard; create/run agent → output)
- **Why:** these are the moments of truth; failure = churn and lost trust.
- **Profile:** login→dashboard is `prod_safe` (read-only nav); create/run agent is
  `staging_full` only (creates data).
- **Data:** dedicated test account; a deterministic run input for stable assertions.
- **Risks:** selectors/routes unknown until wired; run output shape must be confirmed.
- **Priority:** P0/P1. _Scaffolded, skips until wired._

### C. Agent behavior (list, detail, run lifecycle, output correctness)
- **Why:** the agent *is* the product; correctness and completion are the core value.
- **Profile:** list/detail read-only `prod_safe`; run lifecycle `staging_full`.
- **Data:** at least one seeded agent for read checks; deterministic payload for runs.
- **Risks:** run cost/time; terminal-state vocabulary; idempotency of runs.
- **Priority:** P0. _Scaffolded via `AgentClient`, skips until routes set._

### D. API contract + auth (login success shape, token presence)
- **Why:** the frontend and integrations break silently when contracts drift.
- **Profile:** `prod_safe` (login is non-mutating) + `staging_full`.
- **Data:** dedicated test account.
- **Risks:** token field name assumption (`token`); expected-status assumptions.
- **Priority:** P0. _Implemented (happy path) + contract test added._

### E. Read-only production validations (availability, latency budgets)
- **Why:** stakeholders want daily proof prod is healthy *and responsive*, not just up.
- **Profile:** `prod_safe`.
- **Data:** none.
- **Risks:** latency thresholds need tuning to real baselines.
- **Priority:** P1. _Resilience probe added._

### F. Negative + permissions (bad password, malformed input, unauthorized access)
- **Why:** the highest-severity failures are silent acceptance of bad input and
  cross-tenant data exposure. Cheap to test, catastrophic if missed.
- **Profile:** `prod_safe` (only sends bad/absent creds — creates nothing).
- **Data:** none (uses intentionally invalid input).
- **Risks:** must ensure these never accidentally use valid creds.
- **Priority:** P0. _Added._

### G. Data integrity (returned payloads well-formed and correct)
- **Why:** a 200 with wrong/empty data still breaks the customer experience.
- **Profile:** `prod_safe` for read shapes; `staging_full` for post-write correctness.
- **Data:** known seeded records with expected values.
- **Priority:** P1. _Partly added (list shape); deepen once schemas known._

### H. Observability / reporting (stakeholder summary)
- **Why:** testing is only valuable if the right people see results daily.
- **Profile:** both; runs in CI after every suite.
- **Data:** JUnit XML.
- **Risks:** webhook secret handling; summary must state profile + scope clearly.
- **Priority:** P0. _Enhanced: pass rate, profile, prod-safe scope note._

### I. Regression expansion plan (staging)
- **Why:** deeper coverage (create/update/delete, multi-user, edge cases) is unsafe
  in prod and should grow behind `staging_full`.
- **Profile:** `staging_full`.
- **Priority:** P2, unblocked when staging URLs exist.

## 5. What to validate daily vs before releases

- **Daily (prod_safe, nightly):** health, homepage, login, login→dashboard nav,
  agent list/detail read, auth negatives, permissions, latency budget. Report to
  Google Chat with pass rate + scope.
- **Before releases (staging_full):** everything above **plus** agent create/run
  lifecycle, output correctness, data mutations, and broader negative/edge cases.

## 6. Standing assumptions (verify with the team)

1. Captic is an agent product with an authenticated dashboard + REST API.
2. `/health` is the real health route (could not verify from the sandbox network).
3. Login returns a bearer `token` field; adjust `API_LOGIN_SUCCESS_FIELD` if not.
4. Agent routes in `.env.example` are placeholders pending confirmation.
5. The dedicated test account is safe to authenticate against production read-only.
