# Ranker design — lodestar v0 (T18-T24)

**Status:** Spec authored 2026-05-17 evening; supersedes the placeholder ranker entry in `docs/superpowers/plans/2026-05-17-architecture.md` Component #6.

**Goal:** Take a deduplicated parquet of `Issue` rows for one tool's weekly window. Produce a ranked top-N candidate pool. Surface every component of the score so a human reviewer can audit, override, and write rationale on the top 5.

**Anti-goal:** Do not classify severity. Do not claim statistical inference. Do not collapse the score into a single opaque number without per-component breakout.

## Module layout

```
voc/rank/
├── __init__.py        Public API: rank, RankConfig, ScoreBreakdown
├── signals.py         Pure functions: recency_score, engagement_score, label_score
├── score.py           RankConfig dataclass + score_issue (composes signals)
├── ranker.py          rank() and top_n() over Sequence[Issue]
└── __main__.py        CLI: read parquet, rank, write parquet with score columns

tests/rank/
├── __init__.py
├── conftest.py        Shared make_issue + make_now fixtures
├── test_signals.py    Per-signal property tests
├── test_score.py      Composite scoring + RankConfig
├── test_ranker.py     Top-N, ties, determinism, empty input
├── test_invariants.py Shuffle-invariance, monotonicity
└── test_cli.py        Parquet round-trip
```

## Scoring formula

```
score(issue, now, cfg) = w_r * recency(issue, now, cfg)
                      + w_e * engagement(issue, cfg)
                      + w_l * label(issue, cfg)
```

Defaults: `w_r=0.4, w_e=0.4, w_l=0.2`. All in [0, 1] before weighting; composite is in [0, 1].

### recency_score

Exponential decay over `updated_at` (not `created_at`, since active discussion signals current pain):

```
age_days = (now - issue.updated_at).days
recency = 2 ** (-age_days / half_life_days)
```

Default `half_life_days=14` (a 2-week-old issue scores half a fresh one; a 4-week-old issue scores a quarter).

Choice rationale: `2 ** (-t/T)` rather than `exp(-t/T)` so the half-life parameter is directly interpretable; reviewers can reason about "what does 14 mean" without converting.

### engagement_score

`comments_count` weighted 1x; `reactions_count` weighted 3x (reactions cost a deliberate click and cannot be off-topic). Normalized by a tool-relative ceiling so noisy tools don't dominate cross-tool views:

```
raw = comments_count + 3 * reactions_count
engagement = log1p(raw) / log1p(cfg.engagement_ceiling)
```

Clamped to [0, 1]. Default `engagement_ceiling=100`.

`log1p` rather than linear because engagement is heavy-tailed (one mega-thread should not dominate). `log1p(0) == 0` is a useful boundary.

### label_score

Sum of weights for labels present on the issue, divided by the maximum-possible sum (assuming a single most-valuable label):

```
matched = sum(cfg.label_weights.get(label.lower(), 0) for label in issue.labels)
label = min(matched / cfg.label_max, 1.0)
```

Default `label_weights = {"bug": 0.5, "crash": 1.0, "regression": 1.0, "p0": 1.0, "p1": 0.7, "breaking": 0.8, "data-loss": 1.0}`.

Default `label_max=1.0` so a single P0/crash/regression saturates the label component.

## Per-tool vs cross-tool ranking

Default: per-tool. Cross-tool ranking conflates Aider (~13 issues/week) with Continue (~94/week) on raw counts. The CLI exposes `--mode tool|global`; `global` ranks across all tools after per-tool normalization.

## API contract

```python
@dataclass(frozen=True)
class RankConfig:
    half_life_days: float = 14.0
    reaction_weight: float = 3.0
    engagement_ceiling: float = 100.0
    label_weights: Mapping[str, float] = field(default_factory=_default_label_weights)
    label_max: float = 1.0
    w_recency: float = 0.4
    w_engagement: float = 0.4
    w_label: float = 0.2

@dataclass(frozen=True)
class ScoreBreakdown:
    issue_id: str
    recency: float
    engagement: float
    label: float
    composite: float

def rank(
    issues: Sequence[Issue],
    now: datetime,
    config: RankConfig = RankConfig(),
) -> list[ScoreBreakdown]:
    """Return ScoreBreakdowns sorted by composite descending, then by issue.id ascending."""

def top_n(
    issues: Sequence[Issue],
    n: int,
    now: datetime,
    config: RankConfig = RankConfig(),
) -> list[tuple[Issue, ScoreBreakdown]]:
    """Top-N convenience. Stable: ties broken by issue.id."""
```

## CLI

```
python -m voc.rank --input <dedup.parquet> --output <ranked.parquet> [--top 20] [--now ISO8601]
```

Adds columns to the parquet: `recency_score`, `engagement_score`, `label_score`, `composite_score`, `rank` (1-indexed). Sorts by rank ascending.

## Adversarial review of this design (form-check S4 falsifier pass)

| # | Claim | Falsifier | Disposition |
|---|---|---|---|
| R1 | Exponential decay on `updated_at` is appropriate | Linear decay or `created_at` would rank differently | Use `updated_at` because re-opened bugs and reactivated discussions signal current pain. Document and make decay configurable. |
| R2 | `reactions * 3` weight is arbitrary | Any value other than 1 is unjustified | Reactions require a deliberate click (cannot be off-topic; cost ~3 seconds vs comments which cost minutes but carry noise). Industry intuition pegs 3-5x. Conservative default; configurable. |
| R3 | Label weights encode my bias | Default weights reflect a v0 author's prior, not Cursor PM judgment | Defaults are documented; CLI accepts a `--labels-json` override path. The defaults are starting points to be calibrated. |
| R4 | The composite IS a stealth severity | `composite_score` will be used as severity by anyone glancing at the report | ScoreBreakdown surfaces every component. Report renderer labels the score as "Candidate priority (not severity)" and lists the components inline. Severity field on the top-5 is human-written, source="human" per the schema carveout. |
| R5 | Determinism under input order | Floating-point summation across permutations may drift; dict iteration order in label_weights | Property tests: shuffle input N times, assert identical ScoreBreakdown sequence. Sort tiebreaker by issue.id locks the output. |
| R6 | Parquet round-trip preserves float64 scores | pyarrow may downcast or precision-clip | Round-trip test in test_cli.py asserts byte-identical scores via parquet. |
| R7 | Empty corpus | Division-by-zero in normalization | Explicit guards: `rank([])` returns `[]`; ceiling=0 guarded. |
| R8 | Per-tool vs global mode | Global ranking with raw scores conflates tools | Default is per-tool. Global mode requires explicit `--mode global` flag and documents the conflation risk in CLI help. |
| R9 | Hardcoded magic numbers | half_life_days=14, ceiling=100, weights — none empirically grounded | All in RankConfig dataclass; CLI accepts overrides; values are sensible defaults documented inline. |
| R10 | log1p normalization may underweight high-engagement outliers | A bug with 200 reactions vs 100 scores nearly the same | That is the intended behavior. Heavy tail compression. Documented. |

## Test taxonomy

- **Unit (signals)** — recency_score, engagement_score, label_score in isolation
- **Property** — monotonicity (older → lower recency), shuffle-invariance, score-bounds
- **Composite (score)** — components combine as documented
- **Ranker** — top_n returns N, ties broken deterministically, empty input, single input
- **CLI** — parquet round-trip preserves scores, adds expected columns
- **Mutation** — after green, run `bash scripts/run_mutmut.sh` extended to `voc/rank/` and target ≥80% kill rate on covered code

## Out of scope for this design (deferred)

- Cross-tool calibration beyond the per-tool default mode
- Per-label calibration based on observed merge-vs-close rates (requires production data)
- Time-decay sensitivity analysis (sweep half_life over [7, 14, 28] days and observe rank changes)
- Embedding-based similarity bonus (related-cluster signal)
