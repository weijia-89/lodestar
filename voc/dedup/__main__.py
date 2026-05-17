"""Dedup CLI: appends cluster_id_fuzzy + cluster_id_semantic columns to issue parquet.

Usage:
    python -m voc.dedup --in aider.parquet --out aider_dedup.parquet \
        --fuzzy-threshold 85 --semantic-threshold 0.5

Hidden invariant (revisit when ranker exists): cluster ids are the smallest
input-index in each cluster, so they are stable IFF the input parquet is in a
stable order. Ingest currently sorts issues by id before writing, so this
holds for the canonical pipeline. Re-shuffling input would produce the same
partition with relabeled cluster ids.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from voc.dedup.fuzzy import cluster_by_title
from voc.dedup.semantic import cluster_semantic
from voc.ingest.parquet_io import read_issues


def run_dedup(
    input: Path,
    output: Path,
    fuzzy_threshold: int = 85,
    semantic_threshold: float = 0.5,
) -> int:
    issues = list(read_issues(input))
    fuzzy_clusters = cluster_by_title(issues, threshold=fuzzy_threshold)
    semantic_clusters = cluster_semantic(issues, similarity_threshold=semantic_threshold)
    table = pq.read_table(input)
    table = table.append_column("cluster_id_fuzzy", pa.array(fuzzy_clusters, type=pa.int64()))
    table = table.append_column("cluster_id_semantic", pa.array(semantic_clusters, type=pa.int64()))
    pq.write_table(table, output, compression="zstd")
    return len(issues)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input", type=Path, required=True)
    p.add_argument("--out", dest="output", type=Path, required=True)
    p.add_argument("--fuzzy-threshold", type=int, default=85)
    p.add_argument("--semantic-threshold", type=float, default=0.5)
    args = p.parse_args()
    n = run_dedup(args.input, args.output, args.fuzzy_threshold, args.semantic_threshold)
    print(f"deduped {n} issues; cluster_id_fuzzy + cluster_id_semantic added → {args.output}")


if __name__ == "__main__":
    main()
