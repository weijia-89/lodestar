"""T28: HM-facing writeup structure tests."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WRITEUP = REPO / "docs" / "WRITEUP.md"

REQUIRED_SECTIONS = [
    "## What this is",
    "## What this isn't",
    "## Methodology",
    "## What I learned about",
    "## Honest limitations",
    "## What I'd do at Cursor with private telemetry",
]


def test_writeup_exists():
    assert WRITEUP.exists()


def test_writeup_has_required_sections():
    text = WRITEUP.read_text()
    for section in REQUIRED_SECTIONS:
        assert section in text


def test_writeup_excludes_banned_vibe_coding_vocab():
    """No 'leverage', 'utilize', 'robust solution', 'comprehensive analysis'."""
    text = WRITEUP.read_text().lower()
    banned = ["leverage", "utilize", "robust solution", "comprehensive analysis"]
    for word in banned:
        assert word not in text, f"banned vocab: {word!r}"


def test_writeup_honest_framing():
    text = WRITEUP.read_text().lower()
    # Must claim descriptive scope and disclaim statistical inference
    assert "descriptive" in text
    assert (
        "no sampling claim" in text
        or "full observed" in text
        or "observation of the full" in text
    )
    assert "statistically significant" not in text
