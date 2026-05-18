#!/usr/bin/env python3
"""Form-check pre-score scaffold for lodestar.

Per form-check Section 5: this does NOT auto-score. It STRUCTURES the entry
Wei (or Cascade in adversarial-review mode) writes. The discipline is human
judgment per component; this just lays out the JSON shape.

Usage:
  scripts/form_check_score.py \\
    --tier vibe-careful \\
    --code-read 90 --test-verif 89 --hallucination 94 \\
    --bug-class 86 --adversarial 90 --reversibility 95 \\
    --doc-accuracy 90 --blast-radius 85 --threat-model 82 \\
    --subject "Pass 5A+B+C plan"

Writes to ~/Projects/career-help/applications/.recovery/calibration.jsonl
unless --dry-run.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Component weights from form-check Section 5
WEIGHTS = {
    "code_read": 0.15,
    "test_verif": 0.20,
    "hallucination": 0.15,
    "bug_class": 0.12,
    "adversarial": 0.10,
    "reversibility": 0.08,
    "doc_accuracy": 0.08,
    "blast_radius": 0.07,
    "threat_model": 0.05,
}

# Tier-floor + minima per form-check Section 5
TIERS = {
    "vibe-safe": {
        "floor": 80,
        "minima": {"test_verif": 70, "hallucination": 70},
    },
    "vibe-careful": {
        "floor": 90,
        "minima": {"test_verif": 80, "hallucination": 85, "adversarial": 70},
    },
    "vibe-dangerous": {
        "floor": 95,
        "minima": {
            "test_verif": 90,
            "hallucination": 90,
            "adversarial": 85,
            "reversibility": 90,
        },
    },
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tier", required=True, choices=list(TIERS))
    p.add_argument("--subject", required=True)
    p.add_argument("--code-read", type=int, required=True)
    p.add_argument("--test-verif", type=int, required=True)
    p.add_argument("--hallucination", type=int, required=True)
    p.add_argument("--bug-class", type=int, required=True)
    p.add_argument("--adversarial", type=int, required=True)
    p.add_argument("--reversibility", type=int, required=True)
    p.add_argument("--doc-accuracy", type=int, required=True)
    p.add_argument("--blast-radius", type=int, required=True)
    p.add_argument("--threat-model", type=int, required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    components = {
        "code_read": args.code_read,
        "test_verif": args.test_verif,
        "hallucination": args.hallucination,
        "bug_class": args.bug_class,
        "adversarial": args.adversarial,
        "reversibility": args.reversibility,
        "doc_accuracy": args.doc_accuracy,
        "blast_radius": args.blast_radius,
        "threat_model": args.threat_model,
    }
    headline = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    headline = min(99.0, round(headline, 1))  # cap per form-check

    tier_def = TIERS[args.tier]
    minima_passed = all(components[k] >= v for k, v in tier_def["minima"].items())
    floor_passed = headline >= tier_def["floor"]
    verdict = "PASS" if (minima_passed and floor_passed) else "FAIL"

    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "skill": "form-check",
        "event": "pre_score",
        "subject": args.subject,
        "tier": args.tier,
        "tier_floor": tier_def["floor"],
        "headline_score": headline,
        "components": components,
        "minima_passed": minima_passed,
        "floor_passed": floor_passed,
        "verdict": verdict,
        "notes": (
            "Uncalibrated per form-check Section 5 honest-precision "
            "warning until N>=50 entries in calibration.jsonl."
        ),
    }

    if args.dry_run:
        print(json.dumps(entry))
        return 0

    log_path = (
        Path.home() / "Projects" / "career-help" / "applications" / ".recovery" / "calibration.jsonl"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"appended to {log_path}: verdict={verdict} headline={headline}", file=sys.stderr)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
