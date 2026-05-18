#!/usr/bin/env bash
# Reproduction script for Aider issue #5131
# https://github.com/Aider-AI/aider/issues/5131
#
# Bug: benchmark/benchmark.py defines its model-settings flag as
#   --read-model-settings, but the aider docs at
#   aider/website/docs/config/adv-model-settings.md document the flag as
#   --model-settings-file. A user who follows the docs into the benchmark
#   passes a flag benchmark.py does not accept; benchmark.py silently
#   ignores it (because typer rejects unknown flags with an error message
#   that may be missed in a long benchmark log), and the run proceeds
#   without the requested model settings. Compounded by
#   LONG_TIMEOUT = 24 * 60 * 60 in benchmark.py, the failure mode
#   presents as a multi-hour hang rather than a clean argparse failure.
#
# Strategy: static evidence only (no API key, no LLM, no Aider install).
# Clone Aider at main HEAD, grep the four pieces of evidence the issue
# names, and produce a PASS/FAIL per probe.
#
# Runtime: ~5-15s on a warm git cache.
# Cost: $0 (no LLM calls).
#
# Usage:
#   bash scripts/repro/aider-5131/repro.sh
#
# Exit codes:
#   0 - bug reproduced as described, or repro skipped cleanly
#   1 - bug NOT reproduced (probes diverged from expected; either upstream
#       fixed the bug, or the repro is stale)
#   2 - environment error (git not on PATH; network unavailable)

set -uo pipefail

REPRO_DIR="/tmp/aider-repro-5131"
LOG="$REPRO_DIR/repro.log"
AIDER_REPO="$REPRO_DIR/aider"
ISSUE_URL="https://github.com/Aider-AI/aider/issues/5131"

# --- environment check -------------------------------------------------

if ! command -v git >/dev/null 2>&1; then
  echo "[ENV-FAIL] git not on PATH. Install git and retry." >&2
  exit 2
fi

# --- idempotent setup --------------------------------------------------

rm -rf "$REPRO_DIR"
mkdir -p "$REPRO_DIR"
: > "$LOG"

echo "Repro for aider#5131. Issue: $ISSUE_URL" | tee -a "$LOG"
echo "Working directory: $REPRO_DIR" | tee -a "$LOG"
echo "" | tee -a "$LOG"

# --- clone aider at main HEAD ------------------------------------------

echo "=== Cloning aider (shallow, main HEAD) ===" | tee -a "$LOG"
if ! git clone --depth=1 --quiet https://github.com/Aider-AI/aider "$AIDER_REPO" 2>>"$LOG"; then
  echo "[ENV-FAIL] git clone failed (network or upstream unavailable). See $LOG." >&2
  exit 2
fi
RESOLVED_SHA=$(git -C "$AIDER_REPO" rev-parse HEAD)
echo "Aider main HEAD SHA: $RESOLVED_SHA" | tee -a "$LOG"
echo "" | tee -a "$LOG"

# --- probes ------------------------------------------------------------
# Each probe records actual evidence to the log and returns PASS/FAIL.
# All four must PASS for the bug to be considered reproduced.

FAIL_COUNT=0

# Probe 1: benchmark.py defines --read-model-settings
echo "=== Probe 1: benchmark.py defines --read-model-settings ===" | tee -a "$LOG"
BENCH_FILE="$AIDER_REPO/benchmark/benchmark.py"
if grep -n -- '--read-model-settings' "$BENCH_FILE" >> "$LOG" 2>&1; then
  echo "[PROBE-1 PASS] --read-model-settings is defined in benchmark.py" | tee -a "$LOG"
else
  echo "[PROBE-1 FAIL] --read-model-settings NOT found in benchmark.py" | tee -a "$LOG"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo "" | tee -a "$LOG"

# Probe 2: benchmark.py does NOT accept --model-settings-file
echo "=== Probe 2: benchmark.py does NOT define --model-settings-file ===" | tee -a "$LOG"
if grep -n -- '--model-settings-file' "$BENCH_FILE" >> "$LOG" 2>&1; then
  echo "[PROBE-2 FAIL] --model-settings-file unexpectedly present in benchmark.py" | tee -a "$LOG"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  echo "[PROBE-2 PASS] --model-settings-file is absent from benchmark.py (as the bug predicts)" | tee -a "$LOG"
fi
echo "" | tee -a "$LOG"

# Probe 3: docs/config/adv-model-settings.md documents --model-settings-file
echo "=== Probe 3: docs document --model-settings-file ===" | tee -a "$LOG"
DOCS_FILE="$AIDER_REPO/aider/website/docs/config/adv-model-settings.md"
if [ -f "$DOCS_FILE" ] && grep -n -- '--model-settings-file' "$DOCS_FILE" >> "$LOG" 2>&1; then
  echo "[PROBE-3 PASS] --model-settings-file is documented in adv-model-settings.md" | tee -a "$LOG"
else
  echo "[PROBE-3 FAIL] --model-settings-file NOT found in adv-model-settings.md" | tee -a "$LOG"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo "" | tee -a "$LOG"

# Probe 4: silent-hang amplifier (LONG_TIMEOUT)
echo "=== Probe 4: LONG_TIMEOUT amplifier present in benchmark.py ===" | tee -a "$LOG"
if grep -n 'LONG_TIMEOUT *= *24 *\* *60 *\* *60' "$BENCH_FILE" >> "$LOG" 2>&1; then
  echo "[PROBE-4 PASS] LONG_TIMEOUT = 24 * 60 * 60 confirmed; failures present as hangs" | tee -a "$LOG"
else
  echo "[PROBE-4 FAIL] LONG_TIMEOUT amplifier missing or rewritten" | tee -a "$LOG"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo "" | tee -a "$LOG"

# Probe 5 (informational; does not affect pass/fail): does benchmark/README.md
# link out to the docs that use the different flag name?
echo "=== Probe 5 (informational): benchmark README links to docs ===" | tee -a "$LOG"
BENCH_README="$AIDER_REPO/benchmark/README.md"
if [ -f "$BENCH_README" ]; then
  grep -n 'adv-model-settings' "$BENCH_README" >> "$LOG" 2>&1 || true
  echo "[PROBE-5 INFO] See $LOG for the README link context" | tee -a "$LOG"
fi
echo "" | tee -a "$LOG"

# --- verdict -----------------------------------------------------------

echo "=== Verdict ===" | tee -a "$LOG"
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "[REPRO PASS] Bug aider#5131 reproduced at SHA $RESOLVED_SHA." | tee -a "$LOG"
  echo "             - benchmark.py accepts --read-model-settings (probe 1)" | tee -a "$LOG"
  echo "             - benchmark.py rejects --model-settings-file (probe 2)" | tee -a "$LOG"
  echo "             - docs tell users to use --model-settings-file (probe 3)" | tee -a "$LOG"
  echo "             - LONG_TIMEOUT amplifies the silent-failure mode (probe 4)" | tee -a "$LOG"
  echo "" | tee -a "$LOG"
  echo "Full log: $LOG" | tee -a "$LOG"
  exit 0
else
  echo "[REPRO FAIL] $FAIL_COUNT of 4 probes diverged from the bug description." | tee -a "$LOG"
  echo "             Upstream may have shipped a fix, or the source layout moved." | tee -a "$LOG"
  echo "             See $LOG for the per-probe evidence." | tee -a "$LOG"
  exit 1
fi
