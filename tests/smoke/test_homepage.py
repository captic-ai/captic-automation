import pytest
from playwright.sync_api import Page, expect

@pytest.mark.smoke
def test_homepage_loads(page: Page):
    """Captic.ai homepage should load successfully"""
    page.goto("https://captic.ai")
    
    # Assert the page URL loaded correctly
    assert "captic" in page.url.lower(), f"Unexpected URL: {page.url}"
    
    print(f"\n✓ Page loaded: {page.title()}")
    print(f"✓ URL: {page.url}")
    
    
    