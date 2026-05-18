"""Tests for voc.analytics.themes — TF-IDF + MiniBatchKMeans theme clustering.

Contract:
- `cluster_themes(df, *, n_themes=5, min_df=2, random_state=0)` returns a
  dict of theme_id -> ThemeLabel with fields theme_id, top_terms, issue_ids.
- Input df has id, title, body columns. The function concatenates title + body
  per row to form the document corpus.
- Empty input, single-issue input, or min_df larger than corpus size all
  return an empty dict (graceful degrade; no exception).
- n_themes larger than population is clamped to population.
- Determinism: same input + same random_state -> same output.
"""
from __future__ import annotations

import pandas as pd

from voc.analytics.themes import ThemeLabel, cluster_themes


def _df(items: list[tuple[str, str]]) -> pd.DataFrame:
    """Build an issue-shaped DataFrame from (title, body) pairs."""
    return pd.DataFrame(
        [
            {"id": f"i{idx}", "title": title, "body": body}
            for idx, (title, body) in enumerate(items)
        ]
    )


def test_happy_path_returns_n_themes_with_terms_and_members():
    df = _df(
        [
            ("crash on save", "python crash trace on save"),
            ("crash on open", "python crashes when opening files"),
            ("crash on quit", "segfault crash when quitting"),
            ("slow performance", "feature feels very slow"),
            ("slow with large files", "performance is slow on big inputs"),
            ("performance regression", "slow after recent update"),
            ("docs typo in readme", "documentation typo here"),
            ("missing docs page", "no documentation found for flag"),
            ("documentation outdated", "docs are old and incorrect"),
            ("readme docs typo", "documentation has a typo"),
        ]
    )
    themes = cluster_themes(df, n_themes=3, random_state=0)

    assert len(themes) == 3
    for theme in themes.values():
        assert isinstance(theme, ThemeLabel)
        assert len(theme.issue_ids) >= 1
        assert len(theme.top_terms) > 0
        # Every issue id must appear in some cluster's membership.
    all_members = [iid for t in themes.values() for iid in t.issue_ids]
    assert sorted(all_members) == sorted(df["id"].tolist())


def test_empty_input_returns_empty_dict():
    df = pd.DataFrame(columns=["id", "title", "body"])
    assert cluster_themes(df, n_themes=3, random_state=0) == {}


def test_single_issue_returns_empty_dict():
    df = _df([("crash on save", "trace")])
    assert cluster_themes(df, n_themes=3, random_state=0) == {}


def test_n_themes_clamps_to_population():
    """n_themes larger than the number of input docs is clamped to len(df).

    Uses shared vocab across the 3 docs so the default min_df=2 keeps
    a non-empty vocabulary; the assertion under test is the clamp, not
    the min_df edge case (which has its own test).
    """
    df = _df(
        [
            ("crash on save", "python crash"),
            ("crash on quit", "python crash"),
            ("crash on open", "python crash"),
        ]
    )
    themes = cluster_themes(df, n_themes=10, random_state=0)
    # At most one theme per issue; clamped down from n_themes=10.
    assert 0 < len(themes) <= 3


def test_min_df_above_corpus_returns_empty():
    """When min_df exceeds vocabulary doc-frequency, return empty dict."""
    df = _df(
        [
            ("alpha", "one"),
            ("beta", "two"),
            ("gamma", "three"),
        ]
    )
    # Every term is unique (appears in 1 doc); min_df=5 means no term qualifies.
    assert cluster_themes(df, n_themes=2, min_df=5, random_state=0) == {}


def test_deterministic_across_runs():
    """Same input + same random_state -> structurally identical output."""
    df = _df(
        [
            ("crash on save", "python crash"),
            ("crash on quit", "python segfault"),
            ("crash on open", "python crash on file open"),
            ("slow performance", "slow"),
            ("slow load", "feels slow on start"),
            ("performance bad", "slow and laggy"),
            ("docs typo", "documentation typo"),
            ("docs outdated", "documentation old"),
        ]
    )
    a = cluster_themes(df, n_themes=3, random_state=0)
    b = cluster_themes(df, n_themes=3, random_state=0)

    def _shape(themes: dict[int, ThemeLabel]) -> set[tuple[tuple[str, ...], tuple[str, ...]]]:
        return {
            (tuple(t.top_terms), tuple(sorted(t.issue_ids)))
            for t in themes.values()
        }

    assert _shape(a) == _shape(b)
