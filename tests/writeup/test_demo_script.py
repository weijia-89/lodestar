"""T30: 5-minute demo script structure tests."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "docs" / "DEMO_SCRIPT.md"


def test_demo_script_exists():
    assert SCRIPT.exists()


def test_demo_script_has_timed_sections():
    text = SCRIPT.read_text()
    # Five segments totaling ~5 min
    for segment in ["## 0:00", "## 0:30", "## 2:00", "## 4:00", "## 4:30"]:
        assert segment in text, f"missing timed segment: {segment}"


def test_demo_script_targets_pqe_judgment():
    text = SCRIPT.read_text().lower()
    # Demo MUST surface Tier-1 PQE artifacts (priority report + escalation + manifest)
    assert "priority report" in text
    assert "playwright" in text
    assert "manifest" in text


def test_demo_script_does_not_lead_with_pipeline():
    """Pipeline is supporting; Tier-1 artifacts lead."""
    text = SCRIPT.read_text().lower()
    pr_idx = text.find("priority report")
    pipeline_idx = text.find("pipeline")
    assert pr_idx >= 0, "priority report not mentioned"
    if pipeline_idx >= 0:
        assert pr_idx < pipeline_idx, "pipeline should not lead the demo; priority report leads"
