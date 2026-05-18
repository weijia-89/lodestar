# Pass 5A — TDD task plan (Tasks T1–T8)

**Date:** 2026-05-17 evening
**Scope:** Schema + Ingest + Parquet + Fuzzy-dedup
**Honest framing (per Wei's README edits):** Full-observed-population descriptive ranker. No sampling claim. No statistical-inference claim. v0 portfolio demonstration.
**Discipline:** Red → Verify-Red → Green → Verify-Green → Refactor → Commit. One commit per task.
**Pre-flight:** ensure `~/Projects/lodestar/.venv` is the active env; `pip install pydantic>=2.7 pyarrow>=15 httpx>=0.27 tenacity>=8.3 rapidfuzz>=3.9 scikit-learn>=1.5 pytest>=8 pytest-asyncio>=0.23`. Add to `pyproject.toml` under `[project.dependencies]` before T1.
**Test layout:** mirror `voc/` under `tests/`. e.g. `voc/schema/issue.py` → `tests/schema/test_issue.py`.
**Run tests:** `pytest --timeout=30 -x` (timeouts mandatory per Wei's safe-terminal iron law #6).

---

## T1 — Issue pydantic schema

**Component:** `voc/schema/issue.py`
**Risk tier:** vibe-light
**Risks:** dtype drift on parquet round-trip (A8); timezone normalization

### Red

`tests/schema/test_issue.py`:

```python
from datetime import datetime, timezone
import pytest
from voc.schema.issue import Issue

def test_issue_requires_core_fields():
    with pytest.raises(ValueError):
        Issue(tool="aider")  # missing required fields

def test_issue_normalizes_timestamps_to_utc():
    issue = Issue(
        id="aider:1234",
        tool="aider",
        repo="Aider-AI/aider",
        number=1234,
        title="Crash on empty file",
        body="repro: open empty file",
        url="https://github.com/Aider-AI/aider/issues/1234",
        state="open",
        created_at="2026-05-01T12:00:00-04:00",
        updated_at="2026-05-02T08:00:00Z",
        closed_at=None,
        labels=["bug"],
        author_login_sha256="anon-abc123",
        comments_count=3,
        reactions_count=5,
    )
    assert issue.created_at.tzinfo == timezone.utc
    assert issue.updated_at.tzinfo == timezone.utc
    assert issue.closed_at is None
    assert issue.tool == "aider"

def test_issue_rejects_unknown_tool():
    with pytest.raises(ValueError):
        Issue(
            id="x:1", tool="windsurf", repo="x/x", number=1, title="t", body="",
            url="https://x", state="open",
            created_at="2026-05-01T00:00:00Z", updated_at="2026-05-01T00:00:00Z",
            closed_at=None, labels=[], author_login_sha256="a",
            comments_count=0, reactions_count=0,
        )
```

### Verify-Red

```bash
pytest tests/schema/test_issue.py -x
# Expected: ModuleNotFoundError: No module named 'voc.schema'
```

### Green

`voc/schema/__init__.py`: empty.
`voc/schema/issue.py`:

```python
"""Common Issue model. Single source of truth for ingest + dedup + ranker."""
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

Tool = Literal["aider", "cline", "continue"]
State = Literal["open", "closed"]


class Issue(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Stable id, e.g. 'aider:1234'")
    tool: Tool
    repo: str
    number: int
    title: str
    body: str = ""
    url: str
    state: State
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    labels: list[str] = Field(default_factory=list)
    author_login_sha256: str = Field(..., description="SHA-256 of login for privacy")
    comments_count: int = 0
    reactions_count: int = 0

    @field_validator("created_at", "updated_at", "closed_at", mode="before")
    @classmethod
    def to_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
```

### Verify-Green

```bash
pytest tests/schema/test_issue.py -x
# Expected: 3 passed in <1s
```

### Refactor

None.

### Commit

`schema: Issue pydantic v2 model with UTC normalization + frozen/extra=forbid`

---

## T2 — GitHub Issues HTTP client

**Component:** `voc/ingest/github_client.py`
**Risk tier:** vibe-careful
**Risks:** rate-limit 429; pagination off-by-one; auth-token leak in logs

### Red

`tests/ingest/test_github_client.py`:

```python
from datetime import datetime, timezone
import httpx
import pytest
import respx
from voc.ingest.github_client import GitHubIssuesClient

@respx.mock
def test_fetch_issues_since_paginates_until_empty():
    base = "https://api.github.com/repos/Aider-AI/aider/issues"
    page1 = [{"number": i, "title": f"i{i}", "state": "open"} for i in range(1, 101)]
    page2 = [{"number": i, "title": f"i{i}", "state": "open"} for i in range(101, 150)]
    respx.get(base, params={"page": "1", "per_page": "100", "state": "all", "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=page1)
    respx.get(base, params={"page": "2", "per_page": "100", "state": "all", "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=page2)
    respx.get(base, params={"page": "3", "per_page": "100", "state": "all", "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=[])

    client = GitHubIssuesClient(token=None)
    since = datetime(2026, 4, 19, tzinfo=timezone.utc)
    out = list(client.fetch_issues_since("Aider-AI/aider", since))
    assert len(out) == 149
    assert out[0]["number"] == 1
    assert out[-1]["number"] == 149

@respx.mock
def test_fetch_issues_retries_on_429():
    base = "https://api.github.com/repos/Aider-AI/aider/issues"
    route = respx.get(base).mock(side_effect=[
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(200, json=[{"number": 1, "title": "ok", "state": "open"}]),
        httpx.Response(200, json=[]),
    ])
    client = GitHubIssuesClient(token=None)
    since = datetime(2026, 4, 19, tzinfo=timezone.utc)
    out = list(client.fetch_issues_since("Aider-AI/aider", since))
    assert len(out) == 1
    assert route.call_count == 3
```

Add to `pyproject.toml [project.optional-dependencies] dev`: `respx>=0.21`.

### Verify-Red

```bash
pytest tests/ingest/test_github_client.py -x
# Expected: ModuleNotFoundError: No module named 'voc.ingest.github_client'
```

### Green

`voc/ingest/__init__.py`: empty.
`voc/ingest/github_client.py`:

```python
"""Thin GitHub Issues client. Pagination + 429 retry. Pull-requests filtered out."""
from datetime import datetime
from typing import Iterator, Optional
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

API = "https://api.github.com/repos/{repo}/issues"


class GitHubIssuesClient:
    def __init__(self, token: Optional[str] = None, timeout: float = 15.0):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "lodestar/0.1"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(headers=headers, timeout=timeout)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    def _get(self, url: str, params: dict) -> httpx.Response:
        r = self._client.get(url, params=params)
        if r.status_code == 429 or r.status_code >= 500:
            r.raise_for_status()
        return r

    def fetch_issues_since(self, repo: str, since: datetime) -> Iterator[dict]:
        page = 1
        url = API.format(repo=repo)
        while True:
            params = {
                "page": str(page),
                "per_page": "100",
                "state": "all",
                "since": since.isoformat(),
            }
            r = self._get(url, params)
            r.raise_for_status()
            batch = r.json()
            if not batch:
                return
            for item in batch:
                if "pull_request" in item:  # GitHub conflates PRs and issues
                    continue
                yield item
            page += 1
```

### Verify-Green

```bash
pytest tests/ingest/test_github_client.py -x
# Expected: 2 passed
```

### Refactor

None.

### Commit

`ingest: GitHub Issues HTTP client with pagination + 429/5xx retry`

---

## T3 — Aider issue mapper

**Component:** `voc/ingest/aider.py`
**Risk tier:** vibe-light
**Risks:** schema drift in GH issue JSON; missing optional fields

### Red

`tests/ingest/test_aider.py`:

```python
import json
from pathlib import Path
from voc.ingest.aider import to_issue

SAMPLE = {
    "number": 1234,
    "title": "Crash when opening empty file",
    "body": "Steps:\n1. open empty.py\n2. aider crashes",
    "html_url": "https://github.com/Aider-AI/aider/issues/1234",
    "state": "open",
    "created_at": "2026-05-01T12:00:00Z",
    "updated_at": "2026-05-02T08:00:00Z",
    "closed_at": None,
    "labels": [{"name": "bug"}, {"name": "needs-repro"}],
    "user": {"login": "alice"},
    "comments": 3,
    "reactions": {"total_count": 5},
}

def test_to_issue_maps_aider_fields():
    issue = to_issue(SAMPLE)
    assert issue.id == "aider:1234"
    assert issue.tool == "aider"
    assert issue.repo == "Aider-AI/aider"
    assert issue.title == "Crash when opening empty file"
    assert issue.labels == ["bug", "needs-repro"]
    assert issue.comments_count == 3
    assert issue.reactions_count == 5
    assert issue.author_login_sha256 != "alice"  # hashed
    assert len(issue.author_login_sha256) == 64  # SHA-256 hex

def test_to_issue_handles_missing_optionals():
    raw = {**SAMPLE, "body": None, "reactions": None, "labels": []}
    issue = to_issue(raw)
    assert issue.body == ""
    assert issue.reactions_count == 0
    assert issue.labels == []
```

### Verify-Red

```bash
pytest tests/ingest/test_aider.py -x
# Expected: ModuleNotFoundError: No module named 'voc.ingest.aider'
```

### Green

`voc/ingest/_mapper.py` (shared base):

```python
"""Shared raw-GH-issue → Issue mapper. Per-tool wrappers pin repo + tool."""
import hashlib
from voc.schema.issue import Issue

def hash_login(login: str | None) -> str:
    if not login:
        login = "_anon"
    return hashlib.sha256(login.encode("utf-8")).hexdigest()

def map_raw(raw: dict, tool: str, repo: str) -> Issue:
    return Issue(
        id=f"{tool}:{raw['number']}",
        tool=tool,
        repo=repo,
        number=raw["number"],
        title=raw["title"],
        body=raw.get("body") or "",
        url=raw["html_url"],
        state=raw["state"],
        created_at=raw["created_at"],
        updated_at=raw["updated_at"],
        closed_at=raw.get("closed_at"),
        labels=[l["name"] for l in (raw.get("labels") or [])],
        author_login_sha256=hash_login((raw.get("user") or {}).get("login")),
        comments_count=raw.get("comments", 0),
        reactions_count=(raw.get("reactions") or {}).get("total_count", 0),
    )
```

`voc/ingest/aider.py`:

```python
"""Aider-specific issue ingestion."""
from voc.ingest._mapper import map_raw
from voc.schema.issue import Issue

REPO = "Aider-AI/aider"
TOOL = "aider"

def to_issue(raw: dict) -> Issue:
    return map_raw(raw, tool=TOOL, repo=REPO)
```

### Verify-Green

```bash
pytest tests/ingest/test_aider.py -x
# Expected: 2 passed
```

### Commit

`ingest: Aider mapper via shared map_raw with SHA-256 author hash`

---

## T4 — Cline + Continue mappers

**Component:** `voc/ingest/cline.py`, `voc/ingest/continue_.py`
**Risk tier:** vibe-light
**Risks:** `continue` is a Python keyword; module name must be `continue_.py`

### Red

`tests/ingest/test_cline_continue.py`:

```python
from voc.ingest.cline import to_issue as cline_to_issue
from voc.ingest.continue_ import to_issue as continue_to_issue

RAW = {
    "number": 42,
    "title": "T",
    "body": "B",
    "html_url": "https://x",
    "state": "closed",
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-02T00:00:00Z",
    "closed_at": "2026-05-02T00:00:00Z",
    "labels": [],
    "user": {"login": "u"},
    "comments": 0,
    "reactions": {"total_count": 0},
}

def test_cline_mapper_pins_repo_and_tool():
    issue = cline_to_issue(RAW)
    assert issue.tool == "cline"
    assert issue.repo == "cline/cline"
    assert issue.id == "cline:42"

def test_continue_mapper_pins_repo_and_tool():
    issue = continue_to_issue(RAW)
    assert issue.tool == "continue"
    assert issue.repo == "continuedev/continue"
    assert issue.id == "continue:42"
```

### Verify-Red

```bash
pytest tests/ingest/test_cline_continue.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/ingest/cline.py`:

```python
"""Cline-specific issue ingestion."""
from voc.ingest._mapper import map_raw
from voc.schema.issue import Issue

REPO = "cline/cline"
TOOL = "cline"

def to_issue(raw: dict) -> Issue:
    return map_raw(raw, tool=TOOL, repo=REPO)
```

`voc/ingest/continue_.py`:

```python
"""Continue-specific issue ingestion. Module name is continue_ because 'continue' is a Python keyword."""
from voc.ingest._mapper import map_raw
from voc.schema.issue import Issue

REPO = "continuedev/continue"
TOOL = "continue"

def to_issue(raw: dict) -> Issue:
    return map_raw(raw, tool=TOOL, repo=REPO)
```

### Verify-Green

```bash
pytest tests/ingest/test_cline_continue.py -x
# Expected: 2 passed
```

### Commit

`ingest: Cline + Continue mappers (continue_ module name avoids keyword collision)`

---

## T5 — Parquet round-trip writer/reader

**Component:** `voc/ingest/parquet_io.py`
**Risk tier:** vibe-careful
**Risks:** dtype drift on round-trip (A8); list-of-string column handling; datetime tz drop

### Red

`tests/ingest/test_parquet_io.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
import pytest
from voc.ingest.parquet_io import write_issues, read_issues
from voc.schema.issue import Issue

def _make_issue(n: int) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=f"t{n}", body=f"b{n}", url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
        closed_at=None, labels=["bug", "ux"] if n % 2 else [],
        author_login_sha256="a" * 64, comments_count=n, reactions_count=n * 2,
    )

def test_parquet_round_trip_preserves_all_fields(tmp_path: Path):
    originals = [_make_issue(i) for i in range(50)]
    path = tmp_path / "out.parquet"
    write_issues(originals, path)
    loaded = list(read_issues(path))
    assert len(loaded) == 50
    for a, b in zip(originals, loaded):
        assert a == b  # pydantic frozen __eq__

def test_parquet_round_trip_preserves_empty_corpus(tmp_path: Path):
    path = tmp_path / "empty.parquet"
    write_issues([], path)
    loaded = list(read_issues(path))
    assert loaded == []
```

### Verify-Red

```bash
pytest tests/ingest/test_parquet_io.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/ingest/parquet_io.py`:

```python
"""Parquet round-trip for Issue model. Closes A8 assumption tax."""
from datetime import timezone
from pathlib import Path
from typing import Iterator, Iterable
import pyarrow as pa
import pyarrow.parquet as pq
from voc.schema.issue import Issue


def write_issues(issues: Iterable[Issue], path: Path) -> None:
    rows = [i.model_dump(mode="json") for i in issues]
    if not rows:
        # write an empty file with the right schema for round-trip
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("tool", pa.string()),
            pa.field("repo", pa.string()),
            pa.field("number", pa.int64()),
            pa.field("title", pa.string()),
            pa.field("body", pa.string()),
            pa.field("url", pa.string()),
            pa.field("state", pa.string()),
            pa.field("created_at", pa.string()),
            pa.field("updated_at", pa.string()),
            pa.field("closed_at", pa.string()),
            pa.field("labels", pa.list_(pa.string())),
            pa.field("author_login_sha256", pa.string()),
            pa.field("comments_count", pa.int64()),
            pa.field("reactions_count", pa.int64()),
        ])
        table = pa.Table.from_pylist([], schema=schema)
    else:
        table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression="zstd")


def read_issues(path: Path) -> Iterator[Issue]:
    table = pq.read_table(path)
    for row in table.to_pylist():
        yield Issue.model_validate(row)
```

### Verify-Green

```bash
pytest tests/ingest/test_parquet_io.py -x
# Expected: 2 passed
```

### Refactor

If the empty-file branch feels heavy, leave a TODO; not a v0 blocker.

### Commit

`ingest: parquet round-trip via pydantic.model_dump(mode='json') with empty-corpus fallback`

---

## T6 — Idempotent ingest CLI

**Component:** `voc/ingest/__main__.py`
**Risk tier:** vibe-careful
**Risks:** non-deterministic file order; mtime-based idempotency races; mixing live API calls with tests

### Red

`tests/ingest/test_cli_idempotency.py`:

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from voc.ingest.__main__ import run_ingest

FAKE_BATCH = [
    {"number": 1, "title": "t", "body": "b", "html_url": "https://x/1", "state": "open",
     "created_at": "2026-05-01T00:00:00Z", "updated_at": "2026-05-02T00:00:00Z",
     "closed_at": None, "labels": [], "user": {"login": "u"},
     "comments": 0, "reactions": {"total_count": 0}},
]

class _FakeClient:
    def fetch_issues_since(self, repo, since):
        yield from FAKE_BATCH

def test_cli_writes_parquet_and_is_idempotent(tmp_path: Path):
    out = tmp_path / "aider.parquet"
    with patch("voc.ingest.__main__.GitHubIssuesClient", _FakeClient):
        run_ingest(tool="aider", window_days=28, output=out)
        mtime1 = out.stat().st_mtime_ns
        run_ingest(tool="aider", window_days=28, output=out)  # same window, no force
        mtime2 = out.stat().st_mtime_ns
    assert mtime1 == mtime2  # no rewrite on duplicate run

def test_cli_force_rewrites(tmp_path: Path):
    out = tmp_path / "aider.parquet"
    with patch("voc.ingest.__main__.GitHubIssuesClient", _FakeClient):
        run_ingest(tool="aider", window_days=28, output=out)
        mtime1 = out.stat().st_mtime_ns
        import time; time.sleep(0.01)
        run_ingest(tool="aider", window_days=28, output=out, force=True)
        mtime2 = out.stat().st_mtime_ns
    assert mtime2 > mtime1
```

### Verify-Red

```bash
pytest tests/ingest/test_cli_idempotency.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/ingest/__main__.py`:

```python
"""Idempotent ingest CLI. python -m voc.ingest --tool aider --window 28 --out aider.parquet"""
from __future__ import annotations
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from voc.ingest.github_client import GitHubIssuesClient
from voc.ingest import aider, cline, continue_
from voc.ingest.parquet_io import write_issues

TOOLS = {"aider": aider, "cline": cline, "continue": continue_}


def run_ingest(tool: str, window_days: int, output: Path, *, force: bool = False) -> int:
    if not force and output.exists():
        age_s = (datetime.now(timezone.utc).timestamp() - output.stat().st_mtime)
        if age_s < 3600:  # <1h old → skip rewrite
            return 0
    if tool not in TOOLS:
        raise SystemExit(f"unknown tool: {tool}")
    mod = TOOLS[tool]
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    client = GitHubIssuesClient(token=os.environ.get("GITHUB_TOKEN"))
    issues = [mod.to_issue(raw) for raw in client.fetch_issues_since(mod.REPO, since)]
    issues.sort(key=lambda i: i.id)  # deterministic order
    write_issues(issues, output)
    return len(issues)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tool", required=True, choices=list(TOOLS))
    p.add_argument("--window", type=int, default=28)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    n = run_ingest(args.tool, args.window, args.out, force=args.force)
    print(f"ingested {n} issues for {args.tool} → {args.out}")


if __name__ == "__main__":
    main()
```

### Verify-Green

```bash
pytest tests/ingest/test_cli_idempotency.py -x
# Expected: 2 passed
```

### Commit

`ingest: idempotent CLI with --force; mtime-based <1h skip; deterministic sort by id`

---

## T7 — Fuzzy title dedup

**Component:** `voc/dedup/fuzzy.py`
**Risk tier:** vibe-careful
**Risks:** false-merge (different bugs same title); false-split (same bug different wording); threshold tuning

### Red

`tests/dedup/test_fuzzy.py`:

```python
from datetime import datetime, timezone
from voc.dedup.fuzzy import cluster_by_title
from voc.schema.issue import Issue


def _i(n: int, title: str) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="", url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a"*64,
        comments_count=0, reactions_count=0,
    )


def test_fuzzy_clusters_near_duplicate_titles():
    issues = [
        _i(1, "Aider crashes when opening empty file"),
        _i(2, "Crash on opening empty file in aider"),
        _i(3, "Add support for Rust language"),
        _i(4, "Remove support for Y language"),
    ]
    clusters = cluster_by_title(issues, threshold=85)
    # 1 and 2 should share a cluster; 3 and 4 should NOT
    assert clusters[0] == clusters[1]
    assert clusters[2] != clusters[3]
    assert clusters[0] != clusters[2]


def test_fuzzy_singleton_when_no_match():
    issues = [_i(1, "Completely unique title here")]
    clusters = cluster_by_title(issues, threshold=85)
    assert clusters == [0]


def test_fuzzy_deterministic_across_runs():
    issues = [_i(i, f"t{i%3}") for i in range(20)]
    c1 = cluster_by_title(issues, threshold=85)
    c2 = cluster_by_title(issues, threshold=85)
    assert c1 == c2
```

### Verify-Red

```bash
pytest tests/dedup/test_fuzzy.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/dedup/__init__.py`: empty.
`voc/dedup/fuzzy.py`:

```python
"""Fuzzy title dedup via rapidfuzz token_set_ratio + union-find clustering.
Deterministic given fixed input order. No randomness."""
from typing import Sequence
from rapidfuzz import fuzz
from voc.schema.issue import Issue


def _find(parent: list[int], x: int) -> int:
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _union(parent: list[int], a: int, b: int) -> None:
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)  # always merge to lower id (determinism)


def cluster_by_title(issues: Sequence[Issue], threshold: int = 85) -> list[int]:
    """Return list[cluster_id] aligned with issues. Cluster ids are smallest-index-in-cluster."""
    n = len(issues)
    parent = list(range(n))
    titles = [i.title for i in issues]
    for i in range(n):
        for j in range(i + 1, n):
            score = fuzz.token_set_ratio(titles[i], titles[j])
            if score >= threshold:
                _union(parent, i, j)
    return [_find(parent, i) for i in range(n)]
```

### Verify-Green

```bash
pytest tests/dedup/test_fuzzy.py -x
# Expected: 3 passed
```

### Refactor

For n > 5000 the O(n²) sweep becomes a problem (~25M comparisons). Defer optimization until volume warrants; lodestar's per-tool 4-wk pools are ≤162 issues. Leave a TODO comment + benchmark in the docstring.

### Commit

`dedup: fuzzy title clustering via rapidfuzz token_set_ratio + union-find; O(n^2) acceptable at v0 scale`

---

## T8 — Fuzzy dedup CLI integration

**Component:** `voc/dedup/__main__.py`
**Risk tier:** vibe-light
**Risks:** parquet schema mismatch; in-place rewrite races

### Red

`tests/dedup/test_dedup_cli.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from voc.dedup.__main__ import run_dedup
from voc.ingest.parquet_io import write_issues, read_issues
from voc.schema.issue import Issue
import pyarrow.parquet as pq

def _i(n: int, title: str) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="", url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a"*64,
        comments_count=0, reactions_count=0,
    )

def test_dedup_cli_adds_cluster_column(tmp_path: Path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        _i(1, "Aider crashes when opening empty file"),
        _i(2, "Crash on opening empty file in aider"),
        _i(3, "Add support for Rust"),
    ]
    write_issues(issues, src)
    n = run_dedup(input=src, output=dst, threshold=85)
    assert n == 3
    table = pq.read_table(dst)
    assert "cluster_id_fuzzy" in table.column_names
    clusters = table["cluster_id_fuzzy"].to_pylist()
    assert clusters[0] == clusters[1]
    assert clusters[2] != clusters[0]
```

### Verify-Red

```bash
pytest tests/dedup/test_dedup_cli.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/dedup/__main__.py`:

```python
"""Fuzzy dedup CLI. python -m voc.dedup --in aider.parquet --out aider_dedup.parquet --threshold 85"""
from __future__ import annotations
import argparse
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from voc.dedup.fuzzy import cluster_by_title
from voc.ingest.parquet_io import read_issues


def run_dedup(input: Path, output: Path, threshold: int = 85) -> int:
    issues = list(read_issues(input))
    clusters = cluster_by_title(issues, threshold=threshold)
    table = pq.read_table(input)
    table = table.append_column("cluster_id_fuzzy", pa.array(clusters, type=pa.int64()))
    pq.write_table(table, output, compression="zstd")
    return len(issues)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input", type=Path, required=True)
    p.add_argument("--out", dest="output", type=Path, required=True)
    p.add_argument("--threshold", type=int, default=85)
    args = p.parse_args()
    n = run_dedup(args.input, args.output, args.threshold)
    print(f"deduped {n} issues; cluster_id_fuzzy added → {args.output}")


if __name__ == "__main__":
    main()
```

### Verify-Green

```bash
pytest tests/dedup/test_dedup_cli.py -x
# Expected: 1 passed
```

### Commit

`dedup: CLI integration; appends cluster_id_fuzzy column to parquet`

---

## 5A summary

**Code lands:** `voc/schema/issue.py`, `voc/ingest/{github_client,_mapper,aider,cline,continue_,parquet_io,__main__}.py`, `voc/dedup/{fuzzy,__main__}.py`.
**Tests land:** `tests/schema/test_issue.py`, `tests/ingest/test_{github_client,aider,cline_continue,parquet_io,cli_idempotency}.py`, `tests/dedup/test_{fuzzy,dedup_cli}.py`.
**Commits:** 8 (one per task).
**Deps added:** pydantic, pyarrow, httpx, tenacity, rapidfuzz, pytest, pytest-asyncio, respx, scikit-learn (5B).
**Real-data smoke (optional, after T6):** `GITHUB_TOKEN=$(gh auth token) python -m voc.ingest --tool aider --window 28 --out /tmp/aider_smoke.parquet` — expect ~53 issues per Pass 4.5.

**Closes:**
- A8 (parquet round-trip) → T5 verified
- F4 (rapidfuzz catches title dupes) → T7 verified

**Gates Pass 5B on:**
- T5 round-trip works on real Aider corpus (smoke test)
- T8 cluster column writes cleanly (no schema collision)

— end Pass 5A —
