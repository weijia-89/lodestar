"""Base page object. Subclasses pin a URL and expose role/text-based locators
per playwrighter discipline (never raw CSS selectors).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


class BasePage:
    URL: str = ""

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        if not self.URL:
            raise ValueError(f"{type(self).__name__}.URL not set")
        self.page.goto(self.URL)
