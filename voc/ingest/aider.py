"""Aider-specific issue ingestion."""
from voc.ingest._mapper import map_raw
from voc.schema.issue import Issue

REPO = "Aider-AI/aider"
TOOL = "aider"


def to_issue(raw: dict) -> Issue:
    return map_raw(raw, tool=TOOL, repo=REPO)
