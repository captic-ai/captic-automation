"""Business-critical UI journey: log in and land on a working dashboard.

This is the "can a customer actually use the product today?" check. It is
prod-safe because it only navigates and reads (login establishes a session but
creates no business data). It stays skipped until the login selectors and a
post-login dashboard signal are configured.

Wiring needed:
  - UI login config (UI_LOGIN_* selectors, UI_BASE_URL, test account)
  - UI_LOGIN_SUCCESS_SELECTOR: an element that only exists once logged in
  - DASHBOARD_KEY_SELECTOR below: a stable element proving the app rendered usable content
"""

import pytest

from config.settings import is_ui_login_ready
from pages.login_page import LoginPage


# TODO(captic): a stable selector for a core dashboard element (e.g. the agents
# list container, nav, or a data-testid). Kept here so the check is meaningful,
# not just "the page didn't error".
DASHBOARD_KEY_SELECTOR = ""


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.business_critical
@pytest.mark.read_only
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_user_reaches_working_dashboard(page, settings, test_account) -> None:
    if not is_ui_login_ready(settings):
        pytest.skip("Configure UI login selectors + test account to enable the dashboard journey.")

    login_page = LoginPage(page, settings)
    login_page.open()
    login_page.login(test_account["email"], test_account["password"])
    login_page.assert_logged_in()

    if not DASHBOARD_KEY_SELECTOR:
        pytest.skip("Set DASHBOARD_KEY_SELECTOR to assert the dashboard actually rendered.")
    from playwright.sync_api import expect

    expect(page.locator(DASHBOARD_KEY_SELECTOR)).to_be_visible()
