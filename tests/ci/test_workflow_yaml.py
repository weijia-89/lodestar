"""T31: CI workflow structural tests (no behave layer at v0; that's deferred)."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CI = REPO / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    assert CI.exists()


def test_ci_workflow_parses_as_yaml():
    with CI.open() as f:
        data = yaml.safe_load(f)
    assert "jobs" in data


def test_ci_runs_required_gates():
    """Required at v0: ruff (lint), mypy (advisory), pytest (tests), pip-audit (deps).

    Behave / BDD layer is deferred; if added later, extend this list.
    """
    text = CI.read_text().lower()
    for gate in ["ruff", "mypy", "pytest", "pip-audit"]:
        assert gate in text, f"missing CI gate: {gate}"


def test_ci_pins_python_version():
    text = CI.read_text()
    assert "python-version:" in text
    assert "3.11" in text or "3.12" in text  # pinned, not "latest"
    assert "latest" not in text.lower().split("python-version:", 1)[1].split("\n", 1)[0]
