"""Parquet round-trip for Issue model. Closes A8 (dtype-drift) assumption tax."""
from pathlib import Path
from typing import Iterable, Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from voc.schema.issue import Issue


# Explicit schema for empty-corpus case. Field order matches Issue.model_dump output.
_EMPTY_SCHEMA = pa.schema([
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


def write_issues(issues: Iterable[Issue], path: Path) -> None:
    """Serialize issues to parquet (zstd-compressed). Empty-corpus → explicit schema."""
    rows = [i.model_dump(mode="json") for i in issues]
    if not rows:
        table = pa.Table.from_pylist([], schema=_EMPTY_SCHEMA)
    else:
        table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression="zstd")


def read_issues(path: Path) -> Iterator[Issue]:
    """Deserialize parquet rows back to Issue instances."""
    table = pq.read_table(path)
    for row in table.to_pylist():
        yield Issue.model_validate(row)
