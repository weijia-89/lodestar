"""Subprocess CLI smoke tests for `python -m voc.dedup`.

These tests catch the class of bug where the documented CLI surface
diverges from what argparse actually accepts. The bug we are guarding
against: README documented `--input`/`--output` but argparse only
accepted `--in`/`--out`, breaking the documented Quick start.

Tests run the actual CLI as a subprocess so a regression in the flag
surface fails CI rather than passing because internal Python tests
called `run_dedup()` directly.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# When mutmut runs this suite from inside `mutants/`, subprocess calls to
# `python -m voc.dedup` import the trampolined module without mutmut.config
# initialized; that crashes with NoneType.max_stack_depth. Skip the
# subprocess tests in that context; the in-process tests still cover the
# same code paths via direct run_dedup() invocation.
_UNDER_MUTMUT = Path.cwd().name == "mutants"
pytestmark = pytest.mark.skipif(
    _UNDER_MUTMUT, reason="subprocess + mutmut trampoline incompatible"
)


def _run(args, timeout=30):
    return subprocess.run(
        [sys.executable, "-m", "voc.dedup", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


FIXTURE = Path(__file__).parent.parent / "fixtures" / "aider_smoke_66.parquet"


def test_cli_accepts_canonical_input_output_flags(tmp_path):
    """The canonical flags --input and --output must work."""
    out = tmp_path / "out.parquet"
    result = _run(["--input", str(FIXTURE), "--output", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_cli_accepts_legacy_in_out_aliases(tmp_path):
    """The legacy --in and --out aliases must also work (backward compat)."""
    out = tmp_path / "out.parquet"
    result = _run(["--in", str(FIXTURE), "--out", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_cli_rejects_missing_input(tmp_path):
    """Missing --input must error with non-zero exit."""
    out = tmp_path / "out.parquet"
    result = _run(["--output", str(out)])
    assert result.returncode != 0
    assert "required" in result.stderr.lower() or "input" in result.stderr.lower()


def test_cli_threshold_flags_pass_through(tmp_path):
    """--fuzzy-threshold and --semantic-threshold are accepted."""
    out = tmp_path / "out.parquet"
    result = _run(
        [
            "--input",
            str(FIXTURE),
            "--output",
            str(out),
            "--fuzzy-threshold",
            "90",
            "--semantic-threshold",
            "0.6",
        ]
    )
    assert result.returncode == 0, result.stderr
