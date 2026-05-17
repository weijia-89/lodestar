"""Continue-specific issue ingestion.

Module name is continue_ because 'continue' is a Python keyword.
"""
from voc.ingest._mapper import map_raw
from voc.schema.issue import Issue

REPO = "continuedev/continue"
TOOL = "continue"


def to_issue(raw: dict) -> Issue:
    return map_raw(raw, tool=TOOL, repo=REPO)
