# Captic Coverage Matrix + Roadmap

_Automation-only repo. "R/O" = read-only, "DC" = data-changing._

## Production-safe vs staging-full matrix

| Area | Test | UI/API | R/O or DC | prod_safe | staging_full | Status |
|---|---|---|---|:---:|:---:|---|
| Health | API healthcheck 200 | API | R/O | ✅ | ✅ | Implemented |
| Health | Latency budget (repeated) | API | R/O | ✅ | ✅ | Added |
| Homepage | Homepage loads | UI | R/O | ✅ | ✅ | Implemented |
| Auth | Test account can log in (UI) | UI | R/O* | ✅ | ✅ | Implemented (skips) |
| Auth | Test account authenticates (API) | API | R/O* | ✅ | ✅ | Implemented (skips) |
| Auth | Wrong password rejected | API | R/O | ✅ | ✅ | Added |
| Auth | Malformed login rejected | API | R/O | ✅ | ✅ | Added |
| Auth | Login success contract (token) | API | R/O | ✅ | ✅ | Added (skips) |
| Permissions | Protected endpoint requires auth | API | R/O | ✅ | ✅ | Added (skips) |
| Journey | Login → working dashboard | UI | R/O | ✅ | ✅ | Scaffolded (skips) |
| Agent | List agents reachable | API | R/O | ✅ | ✅ | Scaffolded (skips) |
| Agent | List payload well-formed | API | R/O | ✅ | ✅ | Scaffolded (skips) |
| Agent | Get agent detail | API | R/O | ✅ | ✅ | Client ready; test TODO |
| Agent | Create/run → success + output | API | DC | ❌ | ✅ | Scaffolded (destructive) |
| Data | Post-write correctness | API | DC | ❌ | ✅ | Roadmap |

\* Login establishes a session but creates no business data, so it is treated as
prod-safe. Anything that creates/updates/deletes business records is `destructive`
and blocked in `prod_safe`.

## Top 10 next tests (ordered by business value × safety)

| # | Test name | Purpose | Env | UI/API | R/O or DC | Blockers / config needed |
|---|---|---|---|---|---|---|
| 1 | `test_api_healthcheck_returns_success` (verify path) | Confirm prod is up daily | prod_safe | API | R/O | Confirm real `API_HEALTH_PATH` |
| 2 | `test_test_account_can_authenticate_via_api` | Login works for customers | prod_safe | API | R/O | `API_LOGIN_PATH`, token field, test acct |
| 3 | `test_protected_endpoint_requires_auth` | No unauthenticated data access | prod_safe | API | R/O | `AGENT_API_LIST_PATH` |
| 4 | `test_agent_list_is_reachable` | Agent surface healthy | prod_safe | API | R/O | `AGENT_API_LIST_PATH` + login |
| 5 | `test_agent_list_returns_wellformed_payload` | Dashboard can render agents | prod_safe | API | R/O | Confirm list response shape |
| 6 | `test_user_reaches_working_dashboard` | Core "product works" journey | prod_safe | UI | R/O | UI login selectors + `DASHBOARD_KEY_SELECTOR` |
| 7 | `test_login_rejects_wrong_password` | No silent bad-auth acceptance | prod_safe | API | R/O | `API_LOGIN_PATH` |
| 8 | `test_login_success_contract` | Frontend token contract intact | prod_safe | API | R/O | `API_LOGIN_SUCCESS_FIELD` |
| 9 | `test_health_is_consistently_fast` | Responsiveness, not just uptime | prod_safe | API | R/O | Tune latency budget to baseline |
| 10 | `test_agent_run_completes_successfully` | The core value: run → correct output | staging_full | API | DC | Staging URL, run+poll paths, deterministic payload, `ENABLE_DESTRUCTIVE_TESTS=true` |

## Open config to provide (non-secret)

- Real `API_HEALTH_PATH` if not `/health`.
- Agent routes: `AGENT_API_LIST_PATH`, `AGENT_API_DETAIL_PATH`, `AGENT_API_RUN_PATH`, `AGENT_RUN_POLL_PATH`, `AGENT_UI_PATH`.
- `DASHBOARD_KEY_SELECTOR` (a stable post-login element) in the dashboard journey test.
- A deterministic `RUN_PAYLOAD` for the agent run lifecycle test.
- Staging URLs (`STAGING_UI_BASE_URL`, `STAGING_API_BASE_URL`) to unlock `staging_full`.

## Secrets to rotate (were committed in `.env.example`)

- The Google Chat webhook key/token — rotate and store only as a CI secret.
- The test-account password — rotate; keep in local `.env` / CI secret only.
