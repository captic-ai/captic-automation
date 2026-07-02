import pytest
from playwright.sync_api import Page

from config.settings import is_ui_login_ready
from pages.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.prod_safe
@pytest.mark.requires_test_account
def test_test_account_can_log_in(page: Page, settings, test_account) -> None:
    if not is_ui_login_ready(settings):
        pytest.skip(
            "UI login smoke test requires UI_LOGIN_PATH, selectors, UI_BASE_URL, and test account credentials."
        )

    login_page = LoginPage(page, settings)

    login_page.open()
    login_page.login(test_account["email"], test_account["password"])
    login_page.assert_logged_in()
