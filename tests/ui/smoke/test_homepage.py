import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.prod_safe
def test_homepage_loads(page: Page, settings) -> None:
    if not settings.base_url:
        pytest.skip("UI_BASE_URL is not configured for UI tests.")

    home_page = HomePage(page, settings.base_url)

    home_page.open()
    home_page.assert_loaded()
