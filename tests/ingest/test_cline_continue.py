"""T4 Red: Cline + Continue mappers."""
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
