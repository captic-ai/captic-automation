from __future__ import annotations

import re

from playwright.sync_api import Page, expect


class HomePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(self.base_url, wait_until="domcontentloaded")

    def assert_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"captic", re.IGNORECASE))
        expect(self.page).to_have_title(re.compile(r".+"))
        expect(self.page.locator("body")).to_be_visible()
