"""Deterministic TF-IDF vectorization for Issue title+body. Closes F3.

TfidfVectorizer is deterministic by construction (no random_state). Determinism
comes from sorted vocabulary, which sklearn does by default. Config is pinned;
do not change without a regression test.
"""
from typing import Sequence

import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

from voc.schema.issue import Issue

TFIDF_CONFIG = {
    "lowercase": True,
    "stop_words": "english",
    "ngram_range": (1, 2),
    "min_df": 1,
    "max_df": 0.95,
    "norm": "l2",
    "sublinear_tf": True,
}


def vectorize(issues: Sequence[Issue]) -> tuple[sp.csr_matrix, dict[str, int]]:
    """Return (tfidf_matrix, vocabulary). Empty corpus → empty matrix + empty vocab.

    For tiny corpora (n<5), max_df=0.95 collapses below min_df=1 and sklearn
    raises. Fall back to max_df=1.0 (no doc-frequency cap) in that case;
    the cap exists to drop pseudo-stopwords which only matters at scale.
    """
    if not issues:
        return sp.csr_matrix((0, 0)), {}
    corpus = [f"{i.title}\n{i.body}" for i in issues]
    config = dict(TFIDF_CONFIG)
    if len(issues) < 5:
        config["max_df"] = 1.0
    vec = TfidfVectorizer(**config)
    matrix = vec.fit_transform(corpus)
    return matrix, vec.vocabulary_
