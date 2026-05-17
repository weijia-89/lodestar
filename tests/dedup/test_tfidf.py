"""T9 Red: Deterministic TF-IDF vectorizer."""
from datetime import datetime, timezone

import numpy as np

from voc.dedup.tfidf import vectorize
from voc.schema.issue import Issue


def _i(n: int, title: str, body: str = "") -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body=body, url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a" * 64,
        comments_count=0, reactions_count=0,
    )


def test_vectorize_deterministic_across_runs():
    # Use varied real-feeling text so default token_pattern (≥2 chars) keeps
    # the index suffix and we don't collapse to a degenerate vocabulary.
    topics = ["crash bug", "performance issue", "feature request", "documentation fix"]
    issues = [_i(i, f"{topics[i % 4]} number {i:02d}", f"detailed body about {topics[i % 4]}") for i in range(20)]
    m1, vocab1 = vectorize(issues)
    m2, vocab2 = vectorize(issues)
    assert np.array_equal(m1.toarray(), m2.toarray())
    assert vocab1 == vocab2


def test_vectorize_uses_title_plus_body():
    issues = [
        _i(1, "crash on empty file", "stack trace included"),
        _i(2, "crash", ""),
    ]
    m, vocab = vectorize(issues)
    stack_idx = vocab["stack"]
    assert m[0, stack_idx] > 0
    assert m[1, stack_idx] == 0


def test_vectorize_empty_corpus_returns_empty_matrix():
    m, vocab = vectorize([])
    assert m.shape == (0, 0)
    assert vocab == {}
