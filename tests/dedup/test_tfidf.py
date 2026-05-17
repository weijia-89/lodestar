"""T9: Deterministic TF-IDF vectorizer."""
import numpy as np

from voc.dedup.tfidf import vectorize


def test_vectorize_deterministic_across_runs(make_issue):
    # Use varied real-feeling text so default token_pattern (≥2 chars) keeps
    # the index suffix and we don't collapse to a degenerate vocabulary.
    topics = ["crash bug", "performance issue", "feature request", "documentation fix"]
    issues = [
        make_issue(i, f"{topics[i % 4]} number {i:02d}", f"detailed body about {topics[i % 4]}")
        for i in range(20)
    ]
    m1, vocab1 = vectorize(issues)
    m2, vocab2 = vectorize(issues)
    assert np.array_equal(m1.toarray(), m2.toarray())
    assert vocab1 == vocab2


def test_vectorize_uses_title_plus_body(make_issue):
    issues = [
        make_issue(1, "crash on empty file", "stack trace included"),
        make_issue(2, "crash", ""),
    ]
    m, vocab = vectorize(issues)
    stack_idx = vocab["stack"]
    assert m[0, stack_idx] > 0
    assert m[1, stack_idx] == 0


def test_vectorize_empty_corpus_returns_empty_matrix():
    m, vocab = vectorize([])
    assert m.shape == (0, 0)
    assert vocab == {}
