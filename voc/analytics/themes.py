"""TF-IDF theme clustering over the deduped, moderated issue corpus.

Vectorizes (title + body) per issue with sklearn's TfidfVectorizer, clusters
with MiniBatchKMeans, and surfaces top-K terms per cluster by centroid weight.
Returns a dict of theme_id -> ThemeLabel for the report layer.

Descriptive only. No severity assignment, no priority claim, no
statistical-significance claim. Matches the project refusal list in
AGENTS.md.

Determinism: TfidfVectorizer is deterministic by construction (sorted
vocabulary). MiniBatchKMeans is deterministic with `random_state` pinned.

Stop words: sklearn's English default plus a small domain list of terms
that appear across nearly every Aider/Cline/Continue issue and therefore
do not differentiate themes. The list is conservative; expand only with
evidence (e.g. an emitted theme with degenerate top terms).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.cluster import (  # type: ignore[import-untyped]
    MiniBatchKMeans,  # TODO(v0.2): drop when sklearn ships py.typed marker
)
from sklearn.feature_extraction.text import (  # type: ignore[import-untyped]
    ENGLISH_STOP_WORDS,
    TfidfVectorizer,
)

# Domain stop words: appear across most Aider/Cline/Continue issues and
# do not differentiate themes. Keep this list short; expand only when an
# emitted theme has degenerate top-terms (e.g. the same noise term
# dominates multiple clusters).
DOMAIN_STOPWORDS: frozenset[str] = frozenset(
    {"aider", "cline", "continue", "issue", "bug", "error"}
)


@dataclass(frozen=True)
class ThemeLabel:
    """A single theme: its cluster id, top TF-IDF terms, and member issue ids.

    `top_terms` is ordered by centroid weight, descending. `issue_ids` is the
    list of input ids assigned to this cluster (order matches input order
    within the cluster).
    """

    theme_id: int
    top_terms: list[str]
    issue_ids: list[str]


def cluster_themes(
    df: pd.DataFrame,
    *,
    n_themes: int = 5,
    min_df: int = 2,
    top_terms_per_theme: int = 5,
    random_state: int = 0,
) -> dict[int, ThemeLabel]:
    """Cluster issues into themes via TF-IDF + MiniBatchKMeans.

    Args:
        df: DataFrame with id, title, body columns. title + body are
            concatenated to form the document corpus.
        n_themes: target number of clusters. Clamped to len(df).
        min_df: minimum document frequency for a term to enter the
            vocabulary. If no term meets this threshold, returns {}.
        top_terms_per_theme: top-K terms returned per cluster by centroid
            weight.
        random_state: seed for MiniBatchKMeans determinism.

    Returns:
        Dict mapping theme_id -> ThemeLabel. Returns an empty dict when
        the input has fewer than 2 rows or when the vocabulary collapses
        to empty (e.g. min_df too high for the corpus).
    """
    if len(df) < 2:
        return {}

    corpus = [
        f"{row.title}\n{row.body}"  # type: ignore[attr-defined]
        for row in df.itertuples(index=False)
    ]
    issue_ids = [str(row.id) for row in df.itertuples(index=False)]  # type: ignore[attr-defined]

    stop_words = sorted(ENGLISH_STOP_WORDS | DOMAIN_STOPWORDS)

    try:
        vec = TfidfVectorizer(
            lowercase=True,
            stop_words=stop_words,
            ngram_range=(1, 2),
            min_df=min_df,
            norm="l2",
            sublinear_tf=True,
        )
        matrix = vec.fit_transform(corpus)
    except ValueError:
        # Vocabulary collapsed (e.g. min_df > corpus size, or all tokens
        # are stop words). Graceful degrade.
        return {}

    if matrix.shape[1] == 0:
        return {}

    k = min(n_themes, len(df))
    if k < 1:
        return {}

    kmeans = MiniBatchKMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=10,
        batch_size=max(256, len(df)),
    )
    labels = kmeans.fit_predict(matrix)
    feature_names = vec.get_feature_names_out()
    centers = kmeans.cluster_centers_  # shape: (k, n_features)

    themes: dict[int, ThemeLabel] = {}
    for cluster_id in range(k):
        center = centers[cluster_id]
        # Top indices by centroid weight, descending.
        top_idx = center.argsort()[::-1][:top_terms_per_theme]
        top_terms = [
            str(feature_names[i]) for i in top_idx if center[i] > 0
        ]
        members = [
            issue_ids[i]
            for i, lbl in enumerate(labels)
            if int(lbl) == cluster_id
        ]
        themes[cluster_id] = ThemeLabel(
            theme_id=cluster_id,
            top_terms=top_terms,
            issue_ids=members,
        )
    return themes
