# Captic Automation

Stable starter framework for Captic regression coverage across UI and backend APIs, with nightly scheduling and stakeholder notifications.

## Safety first

- This repo does not change Captic application code. It only tests deployed environments from the outside.
- The suite now supports two modes from one central switch: `TARGET_ENV=prod` for tiny `prod_safe` smoke coverage, and `TARGET_ENV=staging` for broader staging-first growth later.
- In `prod` mode, only tests marked `prod_safe` are allowed to run.
- In `staging` mode, the non-production safety checks stay active and broader regression can grow safely.
- Destructive tests are disabled unless `ENABLE_DESTRUCTIVE_TESTS=true`, and they are never allowed in `prod` mode.
- Account-based flows should use `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` for dedicated automation users only.
- If someone truly needs to bypass the target safety check for a temporary manual run, `ALLOW_UNSAFE_TARGETS=true` exists, but it should stay `false` in normal use and in CI.
- Login smoke tests are configurable and stay skipped until their selectors, paths, and dedicated credentials are set.

## What is in place

- `pytest` as the single runner for UI, API, and framework-level tests
- Playwright-based UI smoke coverage
- `httpx` API client and healthcheck example
- JUnit + HTML reporting
- Failure screenshots for browser tests
- Scheduled GitHub Actions workflow
- Google Chat notification script for daily stakeholder updates

## Project layout

- `tests/ui/` for browser flows
- `tests/api/` for backend validations
- `tests/unit/` for fast checks around framework code
- `pages/` for UI page objects
- `clients/` for API wrappers
- `config/` for environment settings
- `utils/` for summary and notification helpers
- `scripts/` for CI-friendly commands

## Local setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

## Useful commands

```bash
pytest -m unit
pytest -m "prod_safe and ui"
pytest -m "prod_safe and api"
pytest -m "smoke and ui"
pytest -m "smoke and api"
pytest --junitxml=test-results/junit.xml --html=reports/pytest-report.html --self-contained-html
```

## Environment variables

- `TARGET_ENV`: central target switch. Use `prod` now, later switch to `staging` in one place.
- `TEST_ENVIRONMENT`: optional label shown in reports. If omitted, it follows `TARGET_ENV`.
- `PROD_UI_BASE_URL`: production frontend URL
- `PROD_API_BASE_URL`: production backend API root URL
- `STAGING_UI_BASE_URL`: staging frontend URL
- `STAGING_API_BASE_URL`: staging backend API root URL
- `UI_BASE_URL`: optional manual override for the active frontend URL
- `API_BASE_URL`: optional manual override for the active API URL
- `API_HEALTH_PATH`: healthcheck route for the starter API smoke test
- `ENABLE_DESTRUCTIVE_TESTS`: leave `false` unless you intentionally allow data-changing tests in a safe environment
- `ALLOW_UNSAFE_TARGETS`: emergency manual override for the environment safety block
- `TEST_USER_EMAIL`: dedicated automation login for non-production testing
- `TEST_USER_PASSWORD`: password for the dedicated automation login
- `UI_LOGIN_PATH`: login route such as `/login`
- `UI_LOGIN_EMAIL_SELECTOR`: selector for the email or username field
- `UI_LOGIN_PASSWORD_SELECTOR`: selector for the password field
- `UI_LOGIN_SUBMIT_SELECTOR`: selector for the submit button
- `UI_LOGIN_SUCCESS_SELECTOR`: selector that is only visible after a successful login
- `API_LOGIN_PATH`: backend login endpoint path
- `API_LOGIN_IDENTIFIER_FIELD`: request field name for the login identifier
- `API_LOGIN_PASSWORD_FIELD`: request field name for the password
- `API_LOGIN_EXPECTED_STATUSES`: comma-separated success status codes, such as `200,201`
- `API_LOGIN_SUCCESS_FIELD`: optional response field that proves login success, such as `token`
- `API_LOGIN_EXTRA_PAYLOAD`: optional JSON object merged into the login request body
- `GOOGLE_CHAT_WEBHOOK_URL`: incoming webhook for stakeholder updates

## GitHub Actions setup

Create these repository variables or secrets before enabling the nightly run:

- Repository variable: `TARGET_ENV`
- Repository variable: `TEST_ENVIRONMENT`
- Repository variable: `PROD_UI_BASE_URL`
- Repository variable: `PROD_API_BASE_URL`
- Repository variable: `STAGING_UI_BASE_URL`
- Repository variable: `STAGING_API_BASE_URL`
- Repository variable: `API_HEALTH_PATH`
- Repository variable: `ENABLE_DESTRUCTIVE_TESTS`
- Repository variable: `TEST_USER_EMAIL`
- Repository variable: `UI_LOGIN_PATH`
- Repository variable: `UI_LOGIN_EMAIL_SELECTOR`
- Repository variable: `UI_LOGIN_PASSWORD_SELECTOR`
- Repository variable: `UI_LOGIN_SUBMIT_SELECTOR`
- Repository variable: `UI_LOGIN_SUCCESS_SELECTOR`
- Repository variable: `API_LOGIN_PATH`
- Repository variable: `API_LOGIN_IDENTIFIER_FIELD`
- Repository variable: `API_LOGIN_PASSWORD_FIELD`
- Repository variable: `API_LOGIN_EXPECTED_STATUSES`
- Repository variable: `API_LOGIN_SUCCESS_FIELD`
- Repository variable: `API_LOGIN_EXTRA_PAYLOAD`
- Repository secret: `GOOGLE_CHAT_WEBHOOK_URL`
- Repository secret: `TEST_USER_PASSWORD`

The workflow lives at `.github/workflows/nightly-regression.yml` and supports both manual runs and a daily cron schedule. Once both prod and staging URLs are stored in repo variables, switching the active target is just changing `TARGET_ENV`.

## Recommended next tests

1. Set the real production test-account login selectors and auth endpoint fields in CI variables.
2. Keep the prod suite limited to read-only or low-risk smoke coverage tagged `prod_safe`.
3. When staging is ready, set the staging URLs once and switch `TARGET_ENV=staging`.
4. Convert your top 3 business-critical user journeys into UI smoke tests.
5. Add API tests for auth, permissions, validation, and core business endpoints.
6. Keep the UI suite lean and push most business validation into API coverage for long-term stability.
