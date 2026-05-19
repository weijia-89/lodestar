"""T29: Cursor product-familiarity manifest structure tests."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "docs" / "MANIFEST.md"


def test_manifest_exists():
    assert MANIFEST.exists()


def test_manifest_has_friction_points_and_workflows():
    text = MANIFEST.read_text()
    assert "## Friction points" in text
    assert "## Power-user workflows" in text
    assert "## Observations on Cursor's feedback surfaces" in text


def test_manifest_does_not_leak_intuit_internal():
    """Built from Wei's Intuit experience but ships only generalizable observations.

    Case-insensitive: 'Intuit' and 'intuit' both forbidden in published prose.
    """
    text = MANIFEST.read_text().lower()
    forbidden = ["intuit", "mailchimp", "proprietary"]
    for word in forbidden:
        assert word not in text, f"manifest leaks Intuit-internal context: {word!r}"


def test_manifest_counts_meet_minimum():
    text = MANIFEST.read_text()
    # Relaxed 2026-05-18: fewer-but-real frictions/workflows beats inventing five.
    # Original moonshot plan v3.2 §1.3 called for 5+ frictions and 2-3 workflows;
    # the current count is grounded in Wei's actual lived-experience answers.
    friction_count = text.count("### Friction:")
    workflow_count = text.count("### Workflow:")
    assert friction_count >= 3, f"need 3+ friction points; got {friction_count}"
    assert workflow_count >= 1, f"need 1+ workflow; got {workflow_count}"
