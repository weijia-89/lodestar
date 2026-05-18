"""T27: maintainer-handoff Markdown template structure tests."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HANDOFF = REPO / "docs" / "WORKED_ESCALATION.md"

REQUIRED_SECTIONS = [
    "## Bug summary",
    "## Reproduction (Playwright trace)",
    "## Environment",
    "## Expected vs actual behavior",
    "## Reproduction-time budget",
    "## Suggested fix direction",
    "## Maintainer response log",
]


def test_handoff_template_exists():
    assert HANDOFF.exists(), f"missing: {HANDOFF}"


def test_handoff_has_required_sections():
    text = HANDOFF.read_text()
    for section in REQUIRED_SECTIONS:
        assert section in text, f"missing section: {section}"


def test_handoff_disclaims_template_when_unfilled():
    text = HANDOFF.read_text()
    assert "[TEMPLATE" in text or "PENDING" in text or "Wei to fill" in text
