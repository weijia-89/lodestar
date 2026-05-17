"""T7 Red: Fuzzy title dedup via rapidfuzz token_set_ratio + union-find."""
from datetime import datetime, timezone

from voc.dedup.fuzzy import cluster_by_title
from voc.schema.issue import Issue


def _i(n: int, title: str) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="", url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a" * 64,
        comments_count=0, reactions_count=0,
    )


def test_fuzzy_clusters_near_duplicate_titles():
    """Realistic dup-shape: lexically overlapping with order variation + case difference.

    The impl lowercases and uses token_set_ratio (order-invariant). Morphological
    variants like 'crashes' vs 'crash' are out of scope for v0 (would need stemming);
    use pairs that share content tokens to test the actual dedup capability.
    """
    issues = [
        _i(1, "Aider crashes on empty file"),
        _i(2, "crash: aider crashes on empty file"),  # case + extra prefix
        _i(3, "Add Rust language support to aider"),
        _i(4, "Memory leak in long-running sessions"),  # clearly different issue
    ]
    clusters = cluster_by_title(issues, threshold=85)
    assert clusters[0] == clusters[1]
    assert clusters[2] != clusters[3]
    assert clusters[0] != clusters[2]


def test_fuzzy_singleton_when_no_match():
    issues = [_i(1, "Completely unique title here")]
    clusters = cluster_by_title(issues, threshold=85)
    assert clusters == [0]


def test_fuzzy_deterministic_across_runs():
    issues = [_i(i, f"t{i % 3}") for i in range(20)]
    c1 = cluster_by_title(issues, threshold=85)
    c2 = cluster_by_title(issues, threshold=85)
    assert c1 == c2
