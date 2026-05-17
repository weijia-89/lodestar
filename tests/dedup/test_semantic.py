"""T10 Red: Semantic dedup clustering via cosine similarity + union-find."""
from datetime import datetime, timezone

from voc.dedup.semantic import cluster_semantic
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


def test_semantic_groups_issues_with_overlapping_bodies():
    """Semantic dedup catches issues whose titles differ but bodies overlap.

    This is the value-add over fuzzy title dedup: fuzzy only sees titles, but
    real duplicate GitHub issues often have divergent titles + similar bodies.
    """
    body_overlap = (
        "When I run aider on a large repository the agent loop "
        "hangs after the first edit and never returns control to me. "
        "I have to kill the process. Reproduces every time on macOS."
    )
    issues = [
        _i(1, "Crash on large repo", body_overlap),
        _i(2, "Aider hangs after first edit", body_overlap + " Also seeing it on Linux."),
        _i(3, "Add Rust language support", "Would like first-class Rust support in aider."),
        _i(4, "Documentation typo in README", "The install section has a broken link to pypi."),
    ]
    clusters = cluster_semantic(issues, similarity_threshold=0.5)
    assert clusters[0] == clusters[1], "shared-body dupes should cluster"
    assert clusters[2] != clusters[0]
    assert clusters[3] != clusters[0]
    assert clusters[2] != clusters[3]


def test_semantic_deterministic():
    topics = ["crash bug", "performance issue", "feature request", "documentation fix"]
    issues = [_i(i, f"{topics[i % 4]} number {i:02d}", f"detailed body about {topics[i % 4]}") for i in range(20)]
    c1 = cluster_semantic(issues, similarity_threshold=0.5)
    c2 = cluster_semantic(issues, similarity_threshold=0.5)
    assert c1 == c2


def test_semantic_singleton_when_no_match():
    issues = [_i(1, "completely unique terminology zxqwrt")]
    clusters = cluster_semantic(issues, similarity_threshold=0.5)
    assert clusters == [0]


def test_semantic_empty_corpus():
    assert cluster_semantic([], similarity_threshold=0.5) == []
