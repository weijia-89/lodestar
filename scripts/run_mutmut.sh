#!/usr/bin/env bash
# Run mutmut on voc/dedup/ with 4 parallel workers. Self-contained: cleans
# the prior mutants/ tree, kicks off a fresh run, and writes both progress
# and results to a log file.
#
# Usage:
#     bash scripts/run_mutmut.sh              # foreground
#     bash scripts/run_mutmut.sh --detach     # background, prints PID
#
# Requires: mutmut installed in the project venv. The dedup conftest carries
# a multiprocessing monkey-patch needed for mutmut+Python 3.14 compatibility.
set -euo pipefail
cd "$(dirname "$0")/.."

LOG=/tmp/lodestar_mutmut.log
DETACH=false
for arg in "$@"; do
    case "$arg" in
        --detach) DETACH=true ;;
    esac
done

# Clean any partial state from prior failed runs.
rm -rf mutants .mutmut-cache mutants.db mutmut-stats.db 2>/dev/null || true
: > "$LOG"

run() {
    echo "=== START $(date) ==="
    start=$(date +%s)
    .venv/bin/python -m mutmut run --max-children 4 2>&1
    end=$(date +%s)
    echo "=== RUN_END $(date) ELAPSED=$((end - start))s ==="
    echo "=== RESULTS ==="
    .venv/bin/python -m mutmut results 2>&1
    echo "=== DONE ==="
}

if [[ "$DETACH" == "true" ]]; then
    (run) >> "$LOG" 2>&1 &
    PID=$!
    disown
    echo "spawned PID=$PID log=$LOG"
else
    run | tee "$LOG"
fi
