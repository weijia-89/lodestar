"""Threshold-boundary + default-value tests for dedup.

Authored to kill mutmut survivors flagged by the 2026-05-17 mutation run.
These are coverage gaps in the original red-green: tests always passed
explicit threshold args, so mutating the default value or flipping >= to >
went undetected. Each test below kills a specific mutant family.
"""
import inspect

import pytest

from voc.dedup.fuzzy import cluster_by_title
from voc.dedup.semantic import cluster_semantic
from voc.dedup.tfidf import vectorize


def test_fuzzy_default_threshold_is_85():
    """Kills voc.dedup.fuzzy.x_cluster_by_title__mutmut_1 (default 85 -> 86).

    Introspect the function signature directly. Threshold defaults aren't
    just style; they're part of the public API contract.
    """
    sig = inspect.signature(cluster_by_title)
    assert sig.parameters["threshold"].default == 85


def test_fuzzy_uses_gte_not_gt_at_threshold(make_issue):
    """Kills voc.dedup.fuzzy.x_cluster_by_title__mutmut_20 (>= -> >).

    At exactly the threshold value, the pair must cluster (>=, not strict >).
    """
    # Construct two issues with token_set_ratio = 100 (identical lowercased
    # title). At threshold 100, '>=' clusters, '>' does not.
    a = make_issue(1, "Aider crashes on empty file")
    b = make_issue(2, "AIDER CRASHES ON EMPTY FILE")  # case-only diff -> ratio=100
    clusters = cluster_by_title([a, b], threshold=100)
    assert clusters[0] == clusters[1], (
        "boundary case failed: ratio=100 at threshold=100 must cluster"
    )


def test_semantic_default_threshold_is_0_5():
    """Kills voc.dedup.semantic.x_cluster_semantic__mutmut_1 (default 0.5 -> 1.5).

    Introspect the function signature directly.
    """
    sig = inspect.signature(cluster_semantic)
    assert sig.parameters["similarity_threshold"].default == 0.5


def test_semantic_uses_gte_not_gt_at_threshold(make_issue):
    """Kills voc.dedup.semantic.x_cluster_semantic__mutmut_24 (>= -> >).

    Two identical issues have cosine similarity exactly 1.0. At
    similarity_threshold=1.0, '>=' clusters; '>' does not.
    """
    a = make_issue(1, "identical title here", "identical body here")
    b = make_issue(2, "identical title here", "identical body here")
    clusters = cluster_semantic([a, b], similarity_threshold=1.0)
    assert clusters[0] == clusters[1], (
        "boundary case failed: identical pair (sim=1.0) at threshold=1.0 must cluster"
    )


def test_tfidf_tiny_corpus_boundary_at_5(make_issue):
    """Kills voc.dedup.tfidf.x_vectorize__mutmut_8 (< 5 -> <= 5) and
    _9 (< 5 -> < 6).

    The fallback applies max_df=1.0 only at n<5. At n=5 the production
    config (max_df=0.95) fires; with a degenerate corpus where every term
    appears in 5/5 docs (100% > 95% cap), sklearn raises ValueError
    'After pruning, no terms remain'. Under either mutation, n=5 would
    incorrectly use the fallback and NOT raise.
    """
    issues = [make_issue(i, "crash bug here", "stack trace details") for i in range(5)]
    with pytest.raises(ValueError, match="no terms remain"):
        vectorize(issues)


def test_tfidf_tiny_corpus_fallback_at_4(make_issue):
    """Complement: n=4 hits the fallback (n<5), so the same degenerate corpus
    succeeds and 'crash' appears in the vocab.
    """
    issues = [make_issue(i, "crash bug here", "stack trace details") for i in range(4)]
    _, vocab = vectorize(issues)
    assert "crash" in vocab, "n=4 fallback to max_df=1.0 not firing"
