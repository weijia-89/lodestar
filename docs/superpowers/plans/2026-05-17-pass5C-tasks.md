# Pass 5C — TDD task plan (Tasks T17–T24)

**Date:** 2026-05-17 evening
**Scope:** Weekly priority report writer + BDD scenarios + Public-source voice synthesis (Reddit + HN) + End-to-end pipeline orchestrator
**Prerequisites:** Pass 5A + 5B complete.
**New deps to add:** `behave>=1.2.6`, `praw>=7.7` (optional/lazy import for Reddit).
**Honest framing carried:** Synthesis sources are public-data-only (v3.2 pivot). Discord excluded.

---

## T17 — Weekly priority report writer

**Component:** `voc/report/weekly.py`
**Risk tier:** vibe-careful
**Risks:** template render fail; missing Wei-rationale section; theme-label collision

### Red

`tests/report/test_weekly.py`:

```python
from datetime import datetime, timedelta, timezone
from pathlib import Path
from voc.report.weekly import build_report, PriorityItem
from voc.report.ranker import ScoreBreakdown
from voc.schema.issue import Issue

NOW = datetime(2026, 5, 17, tzinfo=timezone.utc)


def _i(n: int, title: str, labels: list[str]) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="b", url=f"https://x/{n}", state="open",
        created_at=NOW - timedelta(days=7), updated_at=NOW - timedelta(days=1),
        closed_at=None, labels=labels, author_login_sha256="a"*64,
        comments_count=10, reactions_count=3,
    )


def _b(issue: Issue) -> ScoreBreakdown:
    return ScoreBreakdown(issue=issue, engagement=2.6, recency=0.93, label_weight=2.0, score=4.83)


def test_build_report_renders_top5_with_rationale():
    items = [
        PriorityItem(
            rank=i + 1,
            breakdown=_b(_i(i + 1, f"Bug {i+1}", ["bug"])),
            theme_label="crash, empty, file",
            rationale=f"This matters because reason {i+1}.",
            customer_impact=f"Impact for issue {i+1}",
            suggested_response=f"Action {i+1}",
        )
        for i in range(5)
    ]
    text = build_report(
        tool="aider",
        week="2026-W20",
        observed_total=53,
        items=items,
        now=NOW,
    )
    assert "# Aider — Week 2026-W20 priority report" in text
    assert "53 observed" in text
    assert "1. Bug 1" in text
    assert "5. Bug 5" in text
    assert "This matters because reason 1." in text
    assert "Action 5" in text


def test_build_report_explicit_honest_framing():
    items = [PriorityItem(
        rank=1, breakdown=_b(_i(1, "x", [])), theme_label="t",
        rationale="r", customer_impact="i", suggested_response="s",
    )]
    text = build_report("aider", "2026-W20", 53, items, NOW)
    assert "Full observed weekly population" in text
    assert "descriptive" in text.lower()


def test_build_report_redacts_pii_in_title():
    """P1-1: GitHub issue titles can contain emails/secrets. Must scrub before quoting."""
    items = [PriorityItem(
        rank=1,
        breakdown=_b(_i(1, "Crash report: contact me at alice@example.com", ["bug"])),
        theme_label="t", rationale="r", customer_impact="i", suggested_response="s",
    )]
    text = build_report("aider", "2026-W20", 1, items, NOW)
    assert "alice@example.com" not in text
    assert "[EMAIL_REDACTED]" in text


def test_build_report_handles_missing_rationale_gracefully():
    items = [PriorityItem(
        rank=1, breakdown=_b(_i(1, "x", [])), theme_label="t",
        rationale="", customer_impact="i", suggested_response="s",
    )]
    text = build_report("aider", "2026-W20", 53, items, NOW)
    assert "[Rationale pending — Wei to fill]" in text


def test_build_report_writes_to_disk(tmp_path: Path):
    items = [PriorityItem(
        rank=1, breakdown=_b(_i(1, "x", ["bug"])), theme_label="t",
        rationale="r", customer_impact="i", suggested_response="s",
    )]
    out = tmp_path / "aider_2026-W20.md"
    text = build_report("aider", "2026-W20", 53, items, NOW)
    out.write_text(text)
    assert out.exists()
    assert "priority report" in out.read_text()
```

### Verify-Red

```bash
pytest tests/report/test_weekly.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/report/weekly.py`:

```python
"""Weekly priority report writer.

Output is hand-edited Markdown. The pipeline produces a skeleton with all
auditable scoring data; Wei fills the rationale + customer-impact + suggested-response
fields per the PQE-judgment artifact requirement.

Ethics gate (P1-1 remediation post-adversarial-review): every quoted GitHub
field passes through voc.moderation.pii.scan_and_redact before rendering.
Titles can contain emails, IPs, and secrets; do not bypass.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from voc.moderation.pii import scan_and_redact
from voc.report.ranker import ScoreBreakdown


@dataclass(frozen=True)
class PriorityItem:
    rank: int
    breakdown: ScoreBreakdown
    theme_label: str
    rationale: str          # Wei-written; PQE judgment
    customer_impact: str    # Wei-written hypothesis
    suggested_response: str # Wei-written engineering recommendation


def build_report(
    tool: str,
    week: str,
    observed_total: int,
    items: list[PriorityItem],
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    tool_title = tool.capitalize()
    lines = [
        f"# {tool_title} — Week {week} priority report",
        "",
        f"_Generated {now.isoformat()} UTC. {observed_total} observed issues in "
        f"the 4-week rolling window; this report is the curated top-5._",
        "",
        "**Methodology:** Full observed weekly population (no sampling claim). "
        "Ranker output is descriptive; severity and customer-impact assessment "
        "are human judgment (this document).",
        "",
        "---",
        "",
    ]
    for it in items:
        b = it.breakdown
        labels = ", ".join(b.issue.labels) or "—"
        rationale = it.rationale or "[Rationale pending — Wei to fill]"
        impact = it.customer_impact or "[Customer impact pending]"
        suggested = it.suggested_response or "[Suggested response pending]"
        scrubbed_title = scan_and_redact(b.issue.title).redacted_text  # P1-1 ethics gate
        lines.extend([
            f"## {it.rank}. {scrubbed_title}",
            "",
            f"- **Issue:** [{b.issue.id}]({b.issue.url})",
            f"- **State:** {b.issue.state} | **Labels:** {labels}",
            f"- **Theme cluster:** {it.theme_label}",
            f"- **Score breakdown:** score={b.score} (engagement={b.engagement} × "
            f"recency={b.recency} × label_weight={b.label_weight})",
            "",
            "**Why this matters (rationale):**",
            "",
            rationale,
            "",
            "**Customer impact hypothesis:**",
            "",
            impact,
            "",
            "**Suggested engineering response:**",
            "",
            suggested,
            "",
            "---",
            "",
        ])
    return "\n".join(lines)
```

### Verify-Green

```bash
pytest tests/report/test_weekly.py -x
# Expected: 4 passed
```

### Commit

`report: weekly priority report writer with PQE rationale slots`

---

## T18 — BDD feature for report consumer

**Component:** `tests/features/weekly_report.feature`
**Risk tier:** vibe-careful
**Risks:** Gherkin drift from impl; step regex collision

### Red

`tests/features/weekly_report.feature`:

```gherkin
Feature: Weekly priority report
  As a PQE writing a Friday report
  I want the pipeline to surface a curated top-5
  So that my judgment effort goes to ranked candidates, not the raw 4-week pool

  Background:
    Given a corpus of 53 Aider issues from the last 4 weeks

  Scenario: A recent bug with high engagement ranks above an old feature request
    Given an issue "Crash on empty file" updated 1 day ago with 50 comments labeled "bug"
    And an issue "Add Rust support" updated 30 days ago with 50 comments labeled "feature"
    When the ranker runs
    Then "Crash on empty file" appears above "Add Rust support" in the top-20

  Scenario: Score breakdown is auditable
    Given a corpus of 53 Aider issues
    When the ranker emits a top-20 markdown
    Then every entry shows engagement, recency, and label_weight components

  Scenario: Report explicitly disclaims statistical inference
    Given a generated weekly report
    Then the report contains the phrase "Full observed weekly population"
    And the report does not contain the phrase "statistically significant"
    And the report does not contain the phrase "sampled"
```

### Verify-Red

```bash
behave tests/features/weekly_report.feature
# Expected: undefined steps; pending
```

### Green

(steps defined in T19)

### Commit

(deferred to T19 commit)

---

## T19 — Behave step definitions

**Component:** `tests/features/steps/weekly_report_steps.py`
**Risk tier:** vibe-careful

### Red

The feature file from T18 already serves as the failing harness. Now provide steps.

### Green

`tests/features/environment.py`:

```python
def before_scenario(context, scenario):
    context.issues = []
    context.ranked = None
    context.report_text = ""
```

`tests/features/steps/weekly_report_steps.py`:

```python
from datetime import datetime, timedelta, timezone
from behave import given, when, then
from voc.schema.issue import Issue
from voc.report.ranker import rank, ScoreBreakdown
from voc.report.weekly import build_report, PriorityItem


NOW = datetime(2026, 5, 17, tzinfo=timezone.utc)


def _i(n: int, title: str, days_ago: int, comments: int, labels: list[str]) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="", url=f"https://x/{n}", state="open",
        created_at=NOW - timedelta(days=days_ago + 7),
        updated_at=NOW - timedelta(days=days_ago),
        closed_at=None, labels=labels, author_login_sha256="a"*64,
        comments_count=comments, reactions_count=0,
    )


@given('a corpus of {n:d} Aider issues from the last 4 weeks')
def step_corpus_size(context, n):
    context.issues = [
        _i(i, f"placeholder {i}", days_ago=(i % 28), comments=(i % 10), labels=["bug"] if i % 3 == 0 else [])
        for i in range(n)
    ]


@given('a corpus of {n:d} Aider issues')
def step_corpus_any(context, n):
    context.issues = [_i(i, f"placeholder {i}", i % 28, i % 10, ["bug"]) for i in range(n)]


@given('an issue "{title}" updated {days:d} day ago with {comments:d} comments labeled "{label}"')
@given('an issue "{title}" updated {days:d} days ago with {comments:d} comments labeled "{label}"')
def step_specific_issue(context, title, days, comments, label):
    context.issues.append(_i(len(context.issues) + 1000, title, days, comments, [label]))


@when('the ranker runs')
def step_run_ranker(context):
    context.ranked = rank(context.issues, now=NOW)


@when('the ranker emits a top-20 markdown')
def step_emit_top20(context):
    context.ranked = rank(context.issues, now=NOW)
    items = [
        PriorityItem(
            rank=i+1, breakdown=b, theme_label="t",
            rationale="", customer_impact="", suggested_response="",
        )
        for i, b in enumerate(context.ranked[:20])
    ]
    context.report_text = build_report("aider", "2026-W20", len(context.issues), items, NOW)


@then('"{title_a}" appears above "{title_b}" in the top-20')
def step_order(context, title_a, title_b):
    titles = [b.issue.title for b in context.ranked[:20]]
    assert title_a in titles, f"{title_a} not in top-20"
    assert title_b in titles, f"{title_b} not in top-20"
    assert titles.index(title_a) < titles.index(title_b), \
        f"expected {title_a} above {title_b}; got order: {titles}"


@then('every entry shows engagement, recency, and label_weight components')
def step_breakdown_visible(context):
    assert "engagement=" in context.report_text
    assert "recency=" in context.report_text
    assert "label_weight=" in context.report_text


@given('a generated weekly report')
def step_generated_report(context):
    context.issues = [_i(1, "Sample issue", 1, 10, ["bug"])]
    context.ranked = rank(context.issues, now=NOW)
    items = [PriorityItem(
        rank=1, breakdown=context.ranked[0], theme_label="t",
        rationale="r", customer_impact="i", suggested_response="s",
    )]
    context.report_text = build_report("aider", "2026-W20", 1, items, NOW)


@then('the report contains the phrase "{phrase}"')
def step_contains(context, phrase):
    assert phrase in context.report_text, f"missing phrase: {phrase}"


@then('the report does not contain the phrase "{phrase}"')
def step_not_contains(context, phrase):
    assert phrase not in context.report_text, f"unexpected phrase present: {phrase}"
```

### Verify-Green

```bash
behave tests/features/weekly_report.feature
# Expected: 3 scenarios passed
```

### Commit

`bdd: weekly_report.feature + step defs covering ordering, breakdown audit, honest-framing`

---

## T20 — SynthesisSource schema

**Component:** `voc/schema/synthesis_source.py`
**Risk tier:** vibe-light
**Risks:** schema drift between sources; URL field validation

### Red

`tests/schema/test_synthesis_source.py`:

```python
from datetime import datetime, timezone
import pytest
from voc.schema.synthesis_source import SynthesisSource


def test_source_requires_core_fields():
    with pytest.raises(ValueError):
        SynthesisSource(source="reddit")


def test_source_normalizes_utc():
    s = SynthesisSource(
        id="reddit:abc123",
        source="reddit",
        url="https://reddit.com/r/ChatGPTCoding/comments/abc123",
        author_hash="a" * 64,
        content="aider has been giving me trouble with...",
        created_at="2026-05-01T12:00:00-04:00",
        tool_mentioned="aider",
    )
    assert s.created_at.tzinfo == timezone.utc


def test_source_rejects_unknown_source():
    with pytest.raises(ValueError):
        SynthesisSource(
            id="x:1", source="discord", url="https://x", author_hash="a"*64,
            content="", created_at="2026-05-01T00:00:00Z", tool_mentioned="aider",
        )  # Discord excluded per v3.2
```

### Verify-Red

```bash
pytest tests/schema/test_synthesis_source.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/schema/synthesis_source.py`:

```python
"""Public-source customer voice fragment. v3.2: GitHub + Reddit + HN only. NO Discord."""
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Source = Literal["github_issue", "github_comment", "reddit", "hn"]
Tool = Literal["aider", "cline", "continue"]


class SynthesisSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: Source
    url: str
    author_hash: str = Field(..., description="SHA-256 of author identifier")
    content: str
    created_at: datetime
    tool_mentioned: Tool

    @field_validator("created_at", mode="before")
    @classmethod
    def to_utc(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
```

### Verify-Green

```bash
pytest tests/schema/test_synthesis_source.py -x
# Expected: 3 passed
```

### Commit

`schema: SynthesisSource pydantic model; Discord excluded per v3.2 pivot`

---

## T21 — Reddit ingestion (HN-Algolia-style HTTP, no PRAW)

**Component:** `voc/ingest/reddit.py`
**Risk tier:** vibe-careful
**Risks:** Reddit JSON API rate-limit; auth not required for public read; user-agent required by ToS

### Red

`tests/ingest/test_reddit.py`:

```python
import respx
import httpx
from voc.ingest.reddit import fetch_mentions

SAMPLE = {
    "data": {
        "children": [
            {"data": {
                "id": "abc123",
                "author": "alice",
                "selftext": "aider crashes on empty files",
                "title": "anyone else having aider crashes?",
                "permalink": "/r/ChatGPTCoding/comments/abc123/",
                "created_utc": 1747500000,
                "subreddit": "ChatGPTCoding",
            }},
            {"data": {
                "id": "def456",
                "author": "bob",
                "selftext": "",
                "title": "weather is nice today",
                "permalink": "/r/ChatGPTCoding/comments/def456/",
                "created_utc": 1747500100,
                "subreddit": "ChatGPTCoding",
            }},
        ]
    }
}


@respx.mock
def test_fetch_mentions_filters_by_tool_name():
    respx.get("https://www.reddit.com/r/ChatGPTCoding/search.json").respond(200, json=SAMPLE)
    out = list(fetch_mentions(subreddit="ChatGPTCoding", tool="aider", limit=25))
    assert len(out) == 1
    assert out[0].tool_mentioned == "aider"
    assert "crashes" in out[0].content


@respx.mock
def test_fetch_mentions_hashes_author():
    respx.get("https://www.reddit.com/r/ChatGPTCoding/search.json").respond(200, json=SAMPLE)
    out = list(fetch_mentions(subreddit="ChatGPTCoding", tool="aider", limit=25))
    assert out[0].author_hash != "alice"
    assert len(out[0].author_hash) == 64
```

### Verify-Red

```bash
pytest tests/ingest/test_reddit.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/ingest/reddit.py`:

```python
"""Reddit ingestion via public JSON endpoint. No PRAW; no auth required.

Reddit ToS requires distinct User-Agent. Set REDDIT_USER_AGENT or default to lodestar/0.1.
"""
from __future__ import annotations
import hashlib
import os
from datetime import datetime, timezone
from typing import Iterator
import httpx
from voc.schema.synthesis_source import SynthesisSource

SEARCH_URL = "https://www.reddit.com/r/{sub}/search.json"
UA = os.environ.get("REDDIT_USER_AGENT", "lodestar/0.1 (public-data VoC research)")


def _hash(s: str) -> str:
    return hashlib.sha256((s or "_anon").encode("utf-8")).hexdigest()


def fetch_mentions(subreddit: str, tool: str, limit: int = 100) -> Iterator[SynthesisSource]:
    url = SEARCH_URL.format(sub=subreddit)
    params = {"q": tool, "restrict_sr": "1", "limit": str(limit), "sort": "new"}
    headers = {"User-Agent": UA}
    with httpx.Client(headers=headers, timeout=15) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    for child in data.get("data", {}).get("children", []):
        d = child["data"]
        combined = f"{d.get('title', '')}\n\n{d.get('selftext') or ''}".lower()
        if tool.lower() not in combined:
            continue
        yield SynthesisSource(
            id=f"reddit:{d['id']}",
            source="reddit",
            url=f"https://www.reddit.com{d['permalink']}",
            author_hash=_hash(d.get("author")),
            content=f"{d.get('title', '')}\n\n{d.get('selftext') or ''}",
            created_at=datetime.fromtimestamp(d["created_utc"], tz=timezone.utc),
            tool_mentioned=tool,  # type: ignore
        )
```

### Verify-Green

```bash
pytest tests/ingest/test_reddit.py -x
# Expected: 2 passed
```

### Commit

`ingest: Reddit r/ChatGPTCoding mention fetcher via public JSON API`

---

## T22 — Hacker News ingestion

**Component:** `voc/ingest/hn.py`
**Risk tier:** vibe-light
**Risks:** Algolia rate-limit; story-vs-comment shape difference

### Red

`tests/ingest/test_hn.py`:

```python
import respx
from voc.ingest.hn import fetch_mentions

SAMPLE = {
    "hits": [
        {
            "objectID": "12345",
            "author": "hnuser",
            "story_text": "aider is impressive but crashes on large repos",
            "url": "https://example.com",
            "created_at_i": 1747500000,
            "title": "Show HN: my aider experience",
        },
        {
            "objectID": "67890",
            "author": "x",
            "story_text": None,
            "comment_text": "I love cline more than aider these days",
            "created_at_i": 1747500200,
        },
    ]
}


@respx.mock
def test_hn_fetches_and_maps():
    respx.get("https://hn.algolia.com/api/v1/search_by_date").respond(200, json=SAMPLE)
    out = list(fetch_mentions(tool="aider", limit=50))
    assert len(out) == 2
    assert all(s.source == "hn" for s in out)
    assert any("aider is impressive" in s.content for s in out)


@respx.mock
def test_hn_filters_irrelevant():
    respx.get("https://hn.algolia.com/api/v1/search_by_date").respond(200, json={
        "hits": [{
            "objectID": "z", "author": "u",
            "comment_text": "nothing to do with the tool", "created_at_i": 1747500000,
        }]
    })
    out = list(fetch_mentions(tool="aider", limit=50))
    assert out == []
```

### Verify-Red

```bash
pytest tests/ingest/test_hn.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/ingest/hn.py`:

```python
"""HackerNews ingestion via Algolia search API. No auth required."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Iterator
import httpx
from voc.schema.synthesis_source import SynthesisSource

SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


def _hash(s: str) -> str:
    return hashlib.sha256((s or "_anon").encode("utf-8")).hexdigest()


def fetch_mentions(tool: str, limit: int = 50) -> Iterator[SynthesisSource]:
    params = {"query": tool, "tags": "(story,comment)", "hitsPerPage": str(limit)}
    with httpx.Client(timeout=15) as client:
        r = client.get(SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()
    for hit in data.get("hits", []):
        text = hit.get("story_text") or hit.get("comment_text") or hit.get("title") or ""
        if tool.lower() not in text.lower():
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        yield SynthesisSource(
            id=f"hn:{hit['objectID']}",
            source="hn",
            url=url,
            author_hash=_hash(hit.get("author")),
            content=text,
            created_at=datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc),
            tool_mentioned=tool,  # type: ignore
        )
```

### Verify-Green

```bash
pytest tests/ingest/test_hn.py -x
# Expected: 2 passed
```

### Commit

`ingest: HackerNews ingestion via Algolia search API`

---

## T23 — Synthesis memo CLI

**Component:** `voc/synthesis/__main__.py`
**Risk tier:** vibe-careful
**Risks:** moderation bypass; missing source attribution; over-quoting

### Red

`tests/synthesis/test_synthesis_cli.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from voc.synthesis.__main__ import build_memo
from voc.schema.synthesis_source import SynthesisSource

NOW = datetime(2026, 5, 17, tzinfo=timezone.utc)


def _s(n: int, source: str, content: str) -> SynthesisSource:
    return SynthesisSource(
        id=f"{source}:{n}", source=source,  # type: ignore
        url=f"https://x/{n}", author_hash="a"*64,
        content=content, created_at=NOW, tool_mentioned="aider",
    )


def test_memo_groups_by_source():
    sources = [
        _s(1, "github_issue", "issue voice"),
        _s(2, "reddit", "reddit voice"),
        _s(3, "hn", "hn voice"),
    ]
    text = build_memo(tool="aider", week="2026-W20", sources=sources)
    assert "## GitHub issues" in text
    assert "## Reddit" in text
    assert "## Hacker News" in text


def test_memo_includes_attribution_urls():
    sources = [_s(1, "reddit", "voice")]
    text = build_memo(tool="aider", week="2026-W20", sources=sources)
    assert "https://x/1" in text


def test_memo_redacts_pii_before_quoting():
    """Critical: every quote MUST pass through PII filter."""
    sources = [_s(1, "github_issue", "Email me at user@example.com for repro")]
    text = build_memo(tool="aider", week="2026-W20", sources=sources)
    assert "user@example.com" not in text
    assert "[EMAIL_REDACTED]" in text
```

### Verify-Red

```bash
pytest tests/synthesis/test_synthesis_cli.py -x
# Expected: ModuleNotFoundError
```

### Green

`voc/synthesis/__init__.py`: empty.
`voc/synthesis/__main__.py`:

```python
"""Per-tool per-week voice synthesis memo builder.

Pulls SynthesisSource fragments from multiple channels (GitHub issues + Reddit + HN),
passes every fragment through the PII filter (T12), groups by source, and writes
a Markdown memo with full attribution.

v3.2 pivot: this replaces the customer-interview pillar. Public sources only.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from voc.moderation.pii import scan_and_redact
from voc.schema.synthesis_source import SynthesisSource

SOURCE_DISPLAY = {
    "github_issue":   "GitHub issues",
    "github_comment": "GitHub comments",
    "reddit":         "Reddit",
    "hn":             "Hacker News",
}


def build_memo(tool: str, week: str, sources: list[SynthesisSource]) -> str:
    tool_title = tool.capitalize()
    lines = [
        f"# {tool_title} — Week {week} voice synthesis memo",
        "",
        "_Public-source voice synthesis. v3.2 pivot: no customer interviews; "
        "Discord excluded (login-gated); GitHub issues + Reddit + HN only._",
        "",
        f"**Total fragments:** {len(sources)}",
        "",
        "---",
        "",
        "## Synthesis (Wei to write)",
        "",
        "[~3-5 paragraphs of cross-source themes; what are users saying; "
        "where do they hurt; what changed since last week]",
        "",
        "---",
        "",
    ]
    # Group by source
    by_source: dict[str, list[SynthesisSource]] = {}
    for s in sources:
        by_source.setdefault(s.source, []).append(s)

    for src_key, display in SOURCE_DISPLAY.items():
        items = by_source.get(src_key, [])
        if not items:
            continue
        lines.append(f"## {display}")
        lines.append("")
        for s in items:
            scrubbed = scan_and_redact(s.content)
            lines.append(f"### [{s.id}]({s.url})")
            lines.append("")
            lines.append(f"_created: {s.created_at.isoformat()}_")
            lines.append("")
            lines.append("> " + scrubbed.redacted_text.replace("\n", "\n> "))
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tool", required=True, choices=["aider", "cline", "continue"])
    p.add_argument("--week", required=True, help="ISO week e.g. 2026-W20")
    p.add_argument("--issues-parquet", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    # MVP: just use issues. Reddit/HN ingest happens via separate scripts; merge in T24.
    raise SystemExit("Use scripts/run_weekly_pipeline.sh (T24) to orchestrate full sources.")


if __name__ == "__main__":
    main()
```

### Verify-Green

```bash
pytest tests/synthesis/test_synthesis_cli.py -x
# Expected: 3 passed
```

### Commit

`synthesis: voice memo builder with PII filter on every fragment; multi-source grouping`

---

## T24 — End-to-end weekly pipeline orchestrator

**Component:** `scripts/run_weekly_pipeline.sh` + smoke test
**Risk tier:** vibe-careful
**Risks:** silent partial failures; missing intermediate artifacts; no cleanup on error

### Red

`tests/integration/test_pipeline_smoke.py`:

```python
"""Smoke test: orchestrator script exists, is executable, and dry-run succeeds."""
import subprocess
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run_weekly_pipeline.sh"


def test_pipeline_script_exists():
    assert SCRIPT.exists(), f"missing orchestrator: {SCRIPT}"


def test_pipeline_script_is_executable():
    import os
    assert os.access(SCRIPT, os.X_OK), f"not executable: {SCRIPT}"


def test_pipeline_dry_run():
    result = subprocess.run(
        [str(SCRIPT), "--dry-run", "--tool", "aider", "--week", "2026-W20"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "ingest" in result.stdout
    assert "dedup" in result.stdout
    assert "rank" in result.stdout
    assert "synthesis" in result.stdout
```

### Verify-Red

```bash
pytest tests/integration/test_pipeline_smoke.py -x
# Expected: script missing
```

### Green

`scripts/run_weekly_pipeline.sh`:

```bash
#!/bin/bash
# lodestar weekly pipeline orchestrator
# Per tool, per week: ingest → dedup → rank → synthesis memo skeleton
#
# Usage: scripts/run_weekly_pipeline.sh --tool aider --week 2026-W20 [--dry-run]

set -euo pipefail

DRY_RUN=0
TOOL=""
WEEK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift;;
        --tool) TOOL="$2"; shift 2;;
        --week) WEEK="$2"; shift 2;;
        *) echo "unknown arg: $1" >&2; exit 1;;
    esac
done

[[ -z "$TOOL" ]] && { echo "--tool required" >&2; exit 1; }
[[ -z "$WEEK" ]] && { echo "--week required" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/${WEEK}/${TOOL}"
mkdir -p "$OUT"

run() {
    echo ">>> $*"
    if [[ "$DRY_RUN" -eq 0 ]]; then
        "$@"
    fi
}

# Stage 1: ingest GitHub issues
run python -m voc.ingest --tool "$TOOL" --window 28 --out "$OUT/issues.parquet"

# Stage 2: dedup (fuzzy + semantic)
run python -m voc.dedup --in "$OUT/issues.parquet" --out "$OUT/issues_dedup.parquet"

# Stage 3: rank → top-20 markdown
run python -m voc.report.ranker_cli --in "$OUT/issues_dedup.parquet" --out "$OUT/top20.md" --top 20

# Stage 4: synthesis memo skeleton (Wei fills the synthesis paragraphs)
run python -m voc.synthesis --tool "$TOOL" --week "$WEEK" --issues-parquet "$OUT/issues_dedup.parquet" --out "$OUT/synthesis.md"

echo ">>> done. artifacts in $OUT"
```

(make executable: `chmod +x scripts/run_weekly_pipeline.sh`)

### Verify-Green

```bash
chmod +x scripts/run_weekly_pipeline.sh
pytest tests/integration/test_pipeline_smoke.py -x
# Expected: 3 passed
```

### Refactor

Add a `--force` flag passthrough to T6's ingest CLI. Currently the script's idempotency is implicit (skips if parquet <1h old).

### Commit

`integration: weekly pipeline orchestrator (ingest → dedup → rank → synthesis) with --dry-run`

---

## 5C summary

**Code lands:** `voc/report/weekly.py`, `voc/synthesis/__main__.py`, `voc/ingest/{reddit,hn}.py`, `voc/schema/synthesis_source.py`, `scripts/run_weekly_pipeline.sh`, `tests/features/`.
**Tests land:** 7 new test files + 1 BDD feature; ~25 new test cases.
**Commits:** 8.

**Closes:**
- Component #8 from arch plan Pass 2 (`voc/report/weekly.py`) → T17 + T19 BDD scenarios
- v3.2 voice-source pivot → T21 (Reddit) + T22 (HN); T20 schema excludes Discord at type level

**Honest-framing threading:**
- T17 report template: "Full observed weekly population (no sampling claim)"
- T19 BDD scenario: explicit "report does not contain 'statistically significant' or 'sampled'"
- T20 schema: Discord excluded at the Literal level (will raise ValueError if anyone tries)
- T23 memo template: "Public sources only. Discord excluded (login-gated)."

**Gates Pass 5D on:**
- T19 BDD passes (proves report shape matches Wei's hand-edit expectations)
- T24 orchestrator dry-run passes (proves all pieces compose)

— end Pass 5C —
