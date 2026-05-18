"""T2 Red: GitHub Issues HTTP client with pagination + 429 retry."""
from datetime import UTC, datetime

import httpx
import respx

from voc.ingest.github_client import GitHubIssuesClient


@respx.mock
def test_fetch_issues_since_paginates_until_empty():
    base = "https://api.github.com/repos/Aider-AI/aider/issues"
    page1 = [{"number": i, "title": f"i{i}", "state": "open"} for i in range(1, 101)]
    page2 = [{"number": i, "title": f"i{i}", "state": "open"} for i in range(101, 150)]
    respx.get(base, params={"page": "1", "per_page": "100", "state": "all",
                            "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=page1)
    respx.get(base, params={"page": "2", "per_page": "100", "state": "all",
                            "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=page2)
    respx.get(base, params={"page": "3", "per_page": "100", "state": "all",
                            "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=[])

    client = GitHubIssuesClient(token=None)
    since = datetime(2026, 4, 19, tzinfo=UTC)
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
    since = datetime(2026, 4, 19, tzinfo=UTC)
    out = list(client.fetch_issues_since("Aider-AI/aider", since))
    assert len(out) == 1
    assert route.call_count == 3


@respx.mock
def test_fetch_issues_skips_pull_requests():
    """GitHub Issues API returns PRs too; we filter them out."""
    base = "https://api.github.com/repos/Aider-AI/aider/issues"
    respx.get(base, params={"page": "1", "per_page": "100", "state": "all",
                            "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=[
        {"number": 1, "title": "real issue", "state": "open"},
        {"number": 2, "title": "this is a PR", "state": "open",
         "pull_request": {"url": "..."}},
    ])
    respx.get(base, params={"page": "2", "per_page": "100", "state": "all",
                            "since": "2026-04-19T00:00:00+00:00"}).respond(200, json=[])
    client = GitHubIssuesClient(token=None)
    since = datetime(2026, 4, 19, tzinfo=UTC)
    out = list(client.fetch_issues_since("Aider-AI/aider", since))
    assert len(out) == 1
    assert out[0]["number"] == 1
