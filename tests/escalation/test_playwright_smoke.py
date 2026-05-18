"""T25 smoke test: confirm Playwright + Chromium are wired up.

Uses pytest-playwright's `page` fixture rather than raw `sync_playwright()`
because the latter trips on event loops that other plugins (respx/anyio)
may have left running in the test process. The `page` fixture handles
this correctly.

Skipped when the `escalation` optional dep group isn't installed, so this
file doesn't break the default `pytest` run. Run locally after:

    pip install -e ".[escalation]"
    playwright install chromium
"""
import pytest

pytest.importorskip("playwright", reason="install with: pip install -e '.[escalation]'")

from playwright.sync_api import Page


def test_playwright_launches_chromium(page: Page):
    page.set_content("<h1>lodestar smoke</h1>")
    assert page.locator("h1").text_content() == "lodestar smoke"
