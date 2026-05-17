"""Fuzzy title dedup via rapidfuzz token_set_ratio + union-find clustering.

Deterministic given fixed input order. No randomness.

Performance: O(n²) sweep. At v0 scale (≤162 issues per tool/week per Pass 4.5,
revised to 66 for Aider after 2026-05-17 smoke), this is ~26k comparisons,
well under 1s. TODO: switch to LSH (datasketch.MinHashLSH) when n > 5000.
"""
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
    """Return list[cluster_id] aligned with issues. Cluster ids = smallest-index in cluster.

    Titles are lowercased before scoring (case-insensitive match). Morphological
    variants ("crashes" vs "crash") are NOT collapsed — that would require stemming,
    out of scope for v0. Lexically-overlapping near-duplicates with shared content
    words are caught (token_set_ratio is order-invariant).
    """
    n = len(issues)
    parent = list(range(n))
    titles = [i.title.lower() for i in issues]
    for i in range(n):
        for j in range(i + 1, n):
            score = fuzz.token_set_ratio(titles[i], titles[j])
            if score >= threshold:
                _union(parent, i, j)
    return [_find(parent, i) for i in range(n)]
