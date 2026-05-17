"""Idempotent ingest CLI.

Usage:
    python -m voc.ingest --tool aider --window 28 --out aider.parquet [--force]

Idempotency rule: if the output file is <1h old, skip; otherwise re-ingest.
Pass --force to override. Output rows are sorted by id for deterministic diffs.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from voc.ingest import aider, cline, continue_
from voc.ingest.github_client import GitHubIssuesClient
from voc.ingest.parquet_io import write_issues


TOOLS = {"aider": aider, "cline": cline, "continue": continue_}
IDEMPOTENCY_WINDOW_SECONDS = 3600  # 1 hour


def run_ingest(
    tool: str,
    window_days: int,
    output: Path,
    *,
    force: bool = False,
) -> int:
    """Ingest issues for a tool, write to parquet. Returns issue count.

    If output is <1h old and force=False, returns 0 without re-fetching.
    """
    if not force and output.exists():
        age_s = datetime.now(timezone.utc).timestamp() - output.stat().st_mtime
        if age_s < IDEMPOTENCY_WINDOW_SECONDS:
            return 0
    if tool not in TOOLS:
        raise SystemExit(f"unknown tool: {tool}")
    mod = TOOLS[tool]
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    client = GitHubIssuesClient(token=os.environ.get("GITHUB_TOKEN"))
    issues = [mod.to_issue(raw) for raw in client.fetch_issues_since(mod.REPO, since)]
    issues.sort(key=lambda i: i.id)  # deterministic order across runs
    write_issues(issues, output)
    return len(issues)


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest GitHub issues to parquet.")
    p.add_argument("--tool", required=True, choices=list(TOOLS))
    p.add_argument("--window", type=int, default=28, help="trailing days (default 28)")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    n = run_ingest(args.tool, args.window, args.out, force=args.force)
    print(f"ingested {n} issues for {args.tool} → {args.out}")


if __name__ == "__main__":
    main()
