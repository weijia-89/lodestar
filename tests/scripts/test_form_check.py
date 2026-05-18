"""T32: Smoke test for the form-check pre-score scaffold.

This script is a planning artifact: it structures the entry Wei (or Cascade in
adversarial-review mode) writes. It does NOT auto-compute scores — that's the
discipline failure form-check Section 5 warns against. It just lays out the JSON.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "form_check_score.py"


def test_script_exists():
    assert SCRIPT.exists()


def test_script_dry_run():
    """Dry-run: prints proposed entry JSON to stdout, doesn't append to log."""
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--tier", "vibe-careful",
            "--code-read", "90",
            "--test-verif", "89",
            "--hallucination", "94",
            "--bug-class", "86",
            "--adversarial", "90",
            "--reversibility", "95",
            "--doc-accuracy", "90",
            "--blast-radius", "85",
            "--threat-model", "82",
            "--subject", "test-subject",
            "--dry-run",
        ],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stderr
    entry = json.loads(result.stdout)
    assert entry["tier"] == "vibe-careful"
    assert entry["headline_score"] >= 85
    assert entry["minima_passed"] is True
