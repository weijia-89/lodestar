"""T3 Red: Aider issue mapper."""
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
