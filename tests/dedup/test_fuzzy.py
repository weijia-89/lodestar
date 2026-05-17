"""T7: Fuzzy title dedup via rapidfuzz token_set_ratio + union-find."""
from voc.dedup.fuzzy import cluster_by_title


def test_fuzzy_clusters_near_duplicate_titles(make_issue):
    """Realistic dup-shape: lexically overlapping with order variation + case difference.

    The impl lowercases and uses token_set_ratio (order-invariant). Morphological
    variants like 'crashes' vs 'crash' are out of scope for v0 (would need stemming);
    use pairs that share content tokens to test the actual dedup capability.
    """
    _i = make_issue
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


def test_fuzzy_singleton_when_no_match(make_issue):
    issues = [make_issue(1, "Completely unique title here")]
    clusters = cluster_by_title(issues, threshold=85)
    assert clusters == [0]


def test_fuzzy_deterministic_across_runs(make_issue):
    issues = [make_issue(i, f"t{i % 3}") for i in range(20)]
    c1 = cluster_by_title(issues, threshold=85)
    c2 = cluster_by_title(issues, threshold=85)
    assert c1 == c2
