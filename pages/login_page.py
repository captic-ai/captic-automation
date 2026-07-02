from __future__ import annotations

from playwright.sync_api import Page, expect

from config.settings import Settings


class LoginPage:
    def __init__(self, page: Page, settings: Settings) -> None:
        self.page = page
        self.settings = settings

    def open(self) -> None:
        if not self.settings.base_url or not self.settings.ui_login_path:
            raise ValueError("Login page requires UI_BASE_URL and UI_LOGIN_PATH.")
        self.page.goto(
            f"{self.settings.base_url}{self.settings.ui_login_path}",
            wait_until="domcontentloaded",
        )

    def login(self, email: str, password: str) -> None:
        if not all(
            [
                self.settings.ui_login_email_selector,
                self.settings.ui_login_password_selector,
                self.settings.ui_login_submit_selector,
            ]
        ):
            raise ValueError("Login selectors are not fully configured.")

        self.page.locator(self.settings.ui_login_email_selector).fill(email)
        self.page.locator(self.settings.ui_login_password_selector).fill(password)
        self.page.locator(self.settings.ui_login_submit_selector).click()

    def assert_logged_in(self) -> None:
        if not self.settings.ui_login_success_selector:
            raise ValueError("UI_LOGIN_SUCCESS_SELECTOR is not configured.")
        expect(self.page.locator(self.settings.ui_login_success_selector)).to_be_visible()
