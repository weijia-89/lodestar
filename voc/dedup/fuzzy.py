"""Fuzzy title dedup via rapidfuzz token_set_ratio + union-find clustering.

Deterministic given fixed input order. No randomness.

Performance: O(n²) upper-triangle sweep = n*(n-1)/2 comparisons. At v0 scale
(post-smoke Aider revised to 66 issues per 4-week window per Pass 4.5 findings
2026-05-17), this is ~2,145 comparisons, well under 100ms. TODO: switch to
LSH (datasketch.MinHashLSH) when n > 5000.
"""
from collections.abc import Sequence

from rapidfuzz import fuzz

from voc.dedup._union_find import find, union
from voc.schema.issue import Issue


def cluster_by_title(issues: Sequence[Issue], threshold: int = 85) -> list[int]:
    """Return list[cluster_id] aligned with issues. Cluster ids = smallest-index in cluster.

    Titles are lowercased before scoring (case-insensitive match). Morphological
    variants ("crashes" vs "crash") are NOT collapsed; that would require stemming,
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
                union(parent, i, j)
    return [find(parent, i) for i in range(n)]
