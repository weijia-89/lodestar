"""Semantic dedup via cosine similarity on TF-IDF vectors + union-find clustering.

Deterministic given fixed input order.

Performance: cosine_similarity returns a dense n-by-n matrix. At v0 scale
(n<=66 per Pass 4.5 post-smoke estimate), memory is ~0.2 MB. Ceiling is
~3000 issues (~72 MB float64) before we'd need to switch to a sparse /
blocked similarity computation.
"""
from collections.abc import Sequence

from sklearn.metrics.pairwise import cosine_similarity

from voc.dedup._union_find import find, union
from voc.dedup.tfidf import vectorize
from voc.schema.issue import Issue


def cluster_semantic(issues: Sequence[Issue], similarity_threshold: float = 0.5) -> list[int]:
    """Return list[cluster_id] aligned with issues. Cluster ids = smallest-index in cluster."""
    n = len(issues)
    if n == 0:
        return []
    matrix, _ = vectorize(issues)
    if matrix.shape[1] == 0:  # all empty after stop-word filtering
        return list(range(n))
    sim = cosine_similarity(matrix)
    parent = list(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= similarity_threshold:
                union(parent, i, j)
    return [find(parent, i) for i in range(n)]
