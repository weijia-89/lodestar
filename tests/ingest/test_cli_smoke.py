"""Subprocess CLI smoke tests for `python -m voc.ingest`.

Guards against the same class of bug that hit voc.dedup: documented
flags diverging from what argparse accepts.

These tests do NOT make real GitHub API calls. They exercise the
argparse surface using `--help` and intentionally-invalid invocations
so we can verify the flag shape without network dependency.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Same _UNDER_MUTMUT gate as tests/dedup/test_cli_smoke.py and
# tests/rank/test_cli.py: subprocess invocation crashes under mutmut's
# trampoline because mutmut.config is None in the subprocess. voc.ingest
# is in [tool.mutmut].also_copy (not mutated), but its argparse import
# path still hits the trampoline indirectly via voc.* imports.
_UNDER_MUTMUT = Path.cwd().name == "mutants"
pytestmark = pytest.mark.skipif(
    _UNDER_MUTMUT, reason="subprocess + mutmut trampoline incompatible"
)


def _run(args, timeout=10):
    return subprocess.run(
        [sys.executable, "-m", "voc.ingest", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_cli_help_lists_canonical_flags():
    """--help must list --tool, --window, --output."""
    result = _run(["--help"])
    assert result.returncode == 0
    out = result.stdout
    assert "--tool" in out
    assert "--window" in out
    assert "--output" in out


def test_cli_help_lists_legacy_out_alias():
    """The legacy --out alias must still be listed in help."""
    result = _run(["--help"])
    assert result.returncode == 0
    assert "--out" in result.stdout


def test_cli_rejects_missing_required_args():
    """Missing --tool must error with non-zero exit."""
    result = _run(["--output", "/tmp/nope.parquet"])
    assert result.returncode != 0
    assert "tool" in result.stderr.lower() or "required" in result.stderr.lower()


def test_cli_accepts_window_flag():
    """--window must be parsed as an int. Use --help-style probing
    by passing an invalid value and checking the error mentions int."""
    result = _run(["--tool", "aider", "--window", "not_an_int", "--output", "/tmp/x.parquet"])
    assert result.returncode != 0
    assert "int" in result.stderr.lower() or "invalid" in result.stderr.lower()


def test_cli_rejects_unknown_days_flag():
    """The historical --days flag (mistakenly documented in README before
    2026-05-18 fix) must NOT be silently accepted. Catches regression
    if anyone re-introduces --days as a synonym without updating tests."""
    result = _run(["--tool", "aider", "--days", "30", "--output", "/tmp/x.parquet"])
    assert result.returncode != 0
    assert "days" in result.stderr.lower() or "unrecognized" in result.stderr.lower()


def test_cli_tool_choices_enforced():
    """--tool must be one of the supported tools."""
    result = _run(["--tool", "nonexistent_tool", "--output", "/tmp/x.parquet"])
    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower() or "tool" in result.stderr.lower()
