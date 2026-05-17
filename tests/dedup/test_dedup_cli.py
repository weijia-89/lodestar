"""T8: Fuzzy dedup CLI appends cluster_id_fuzzy column."""
from pathlib import Path

import pyarrow.parquet as pq

from voc.dedup.__main__ import run_dedup
from voc.ingest.parquet_io import write_issues


def test_dedup_cli_adds_cluster_column(tmp_path: Path, make_issue):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        make_issue(1, "Aider crashes on empty file"),
        make_issue(2, "crash: aider crashes on empty file"),  # lexical dup
        make_issue(3, "Memory leak in long-running sessions"),  # not a dup
    ]
    write_issues(issues, src)
    n = run_dedup(input=src, output=dst, fuzzy_threshold=85)
    assert n == 3
    table = pq.read_table(dst)
    assert "cluster_id_fuzzy" in table.column_names
    clusters = table["cluster_id_fuzzy"].to_pylist()
    assert clusters[0] == clusters[1]
    assert clusters[2] != clusters[0]
