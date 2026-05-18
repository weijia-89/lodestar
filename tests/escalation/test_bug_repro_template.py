"""T26 TEMPLATE: replace TARGET_URL + scenario with the real bug Wei finds.

Playwrighter discipline (enforced by review, not by lint at v0):
- Locators by role/text/test-id, NEVER raw CSS selectors
- Auto-waiting only (expect().to_be_visible(), to_have_text())
- NO page.wait_for_timeout, NO page.wait_for_load_state("networkidle")
- One assertion per scenario step
- Tracing on for the maintainer handoff
"""
import os

import pytest

pytest.importorskip("playwright", reason="install with: pip install -e '.[escalation]'")

from playwright.sync_api import Page, expect

# REPLACE THESE WHEN REAL BUG IS FOUND
TARGET_URL = os.environ.get("LODESTAR_BUG_TARGET", "https://example.com")
BUG_TITLE = "TEMPLATE: replace with real bug under reproduction"


@pytest.fixture
def page_with_trace(page: Page, request, tmp_path_factory):
    """Auto-trace every test for the maintainer-handoff artifact."""
    trace_dir = tmp_path_factory.mktemp("traces")
    page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield page
    trace_path = trace_dir / f"{request.node.name}.zip"
    page.context.tracing.stop(path=str(trace_path))
    print(f"\n[TRACE] {trace_path}")


def test_bug_repro_template(page_with_trace: Page):
    """SCAFFOLD: edit body to reproduce a real bug; keep the trace fixture.

    Smoke against example.com confirms the harness works end-to-end.
    """
    page = page_with_trace
    page.goto(TARGET_URL)
    expect(page).to_have_title("Example Domain")
    # Real reproductions go here. Example role-based locators:
    # expect(page.get_by_role("button", name="Submit")).to_be_visible()
    # page.get_by_role("button", name="Submit").click()
    # expect(page.get_by_role("alert")).to_have_text("Error: ...")
