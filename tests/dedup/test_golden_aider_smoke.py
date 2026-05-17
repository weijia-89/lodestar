"""Golden-fixture regression test on the live Aider-66 ingest.

Addresses adversarial-review finding F13: synthetic 3-5-issue tests have zero
coverage of real-world title/body distribution (URLs, code fences, unicode,
long bodies). This test runs the full dedup pipeline on a frozen parquet of
the 66 issues ingested 2026-05-17 (28-day window) and asserts cluster counts
fall within ±5% of recorded baselines.

If this fails, the cause is one of:
  1. rapidfuzz, scikit-learn, or pyarrow point-release silently changed behavior
     → investigate, then regenerate baselines + bump the comment below.
  2. We changed our dedup config (thresholds, TFIDF_CONFIG, lowercase, etc.)
     → confirm intended; regenerate baselines.
  3. We regressed. Fix the regression, not the baselines.

Regenerate baselines via:
    python -m voc.ingest --tool aider --window 28 \\
        --out tests/fixtures/aider_smoke_66.parquet --force
    # then re-run /tmp/lodestar_baseline_probe.py (see review session notes)

Library versions when baselines recorded:
    rapidfuzz 3.14.5, scikit-learn 1.8.0, pyarrow 24.0.0, Python 3.14.5
"""
from collections import Counter
from pathlib import Path

import pytest

from voc.dedup.fuzzy import cluster_by_title
from voc.dedup.semantic import cluster_semantic
from voc.ingest.parquet_io import read_issues

FIXTURE = Path(__file__).parent.parent / "fixtures" / "aider_smoke_66.parquet"

# Baselines computed 2026-05-17 against the smoke-ingested parquet.
EXPECTED_ISSUE_COUNT = 66
EXPECTED_FUZZY_CLUSTERS = 50
EXPECTED_SEMANTIC_CLUSTERS = 49
TOLERANCE_PCT = 0.05  # ±5%


@pytest.fixture(scope="module")
def issues():
    if not FIXTURE.exists():
        pytest.skip(f"fixture missing: {FIXTURE}")
    return list(read_issues(FIXTURE))


def _within_tolerance(actual: int, expected: int) -> bool:
    margin = max(1, int(expected * TOLERANCE_PCT))  # min ±1 cluster
    return abs(actual - expected) <= margin


def test_golden_issue_count(issues):
    assert len(issues) == EXPECTED_ISSUE_COUNT, (
        f"Fixture issue count changed (expected {EXPECTED_ISSUE_COUNT}, got {len(issues)}). "
        "Was the fixture re-ingested without updating the baseline?"
    )


def test_golden_fuzzy_cluster_count(issues):
    clusters = cluster_by_title(issues, threshold=85)
    n_clusters = len(set(clusters))
    assert _within_tolerance(n_clusters, EXPECTED_FUZZY_CLUSTERS), (
        f"fuzzy clusters: expected {EXPECTED_FUZZY_CLUSTERS} ±5%, got {n_clusters}. "
        "Check rapidfuzz version or dedup config drift."
    )


def test_golden_semantic_cluster_count(issues):
    clusters = cluster_semantic(issues, similarity_threshold=0.5)
    n_clusters = len(set(clusters))
    assert _within_tolerance(n_clusters, EXPECTED_SEMANTIC_CLUSTERS), (
        f"semantic clusters: expected {EXPECTED_SEMANTIC_CLUSTERS} ±5%, got {n_clusters}. "
        "Check scikit-learn version or TFIDF_CONFIG drift."
    )


def test_golden_fuzzy_catches_known_duplicates(issues):
    """The Aider-66 corpus contains 6 identical 'Uncaught QueryError' reports;
    they must cluster together. This is the most basic dedup contract test."""
    clusters = cluster_by_title(issues, threshold=85)
    sizes = Counter(clusters)
    largest_cluster_size = sizes.most_common(1)[0][1]
    assert largest_cluster_size >= 5, (
        f"largest fuzzy cluster has only {largest_cluster_size} members; "
        "expected ≥5 (the 'Uncaught QueryError in repomap.py' dup-bomb)"
    )
