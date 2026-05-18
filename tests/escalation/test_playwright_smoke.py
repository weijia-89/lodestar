"""T25 smoke test: confirm Playwright + Chromium are wired up.

Skipped when the `escalation` optional dep group isn't installed, so this
file doesn't break the default `pytest` run. Run locally after:

    pip install -e ".[escalation]"
    playwright install chromium
"""
import pytest

pytest.importorskip("playwright", reason="install with: pip install -e '.[escalation]'")

from playwright.sync_api import sync_playwright


def test_playwright_launches_chromium():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:  # browser not installed
            pytest.skip(f"chromium not installed; run `playwright install chromium`: {exc}")
        try:
            page = browser.new_page()
            page.set_content("<h1>lodestar smoke</h1>")
            assert page.locator("h1").text_content() == "lodestar smoke"
        finally:
            browser.close()
