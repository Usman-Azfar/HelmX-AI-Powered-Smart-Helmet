#!/bin/bash
# HelmX_FInal_Pi_REqwuirements.md Section F1 -- one matched loaded/reduced pair.
# Adapted from piResults/newPiResults_raw/run_condition.sh (Round 9's single-pair
# harness) to write into final_pi_results/scheduler_repeats/ with a pair number in
# every filename, so N pairs don't clobber each other.
#
# Usage: run_pair.sh <condition: loaded|reduced> <pair_num> <duration_min>
set -uo pipefail

COND="$1"
PAIR="$2"
DURATION_MIN="${3:-20}"
DURATION_S=$(python3 -c "print(int(float(\"$DURATION_MIN\")*60))")
SCHED_S=$(python3 -c "print(min(600, int(float(\"$DURATION_MIN\")*60) - 30))")

ROOT="/home/helmx/Crash Detection/Crash-Detection"
OUT="$ROOT/piResults/results/final-validation/scheduler_repeats"
VENV_PY="$ROOT/.pi_research_venv/bin/python"

cd "$ROOT"
echo "[$(date)] Starting pair=$PAIR condition=$COND duration_min=$DURATION_MIN"

"$VENV_PY" deploy/pi_research_suite/exp_w2_live3_soak_raw_dt.py --duration-min "$DURATION_MIN" \
  --raw-dt-csv-out "$OUT/run${PAIR}_${COND}_dt.csv" \
  > "$OUT/run${PAIR}_${COND}_stdout.log" 2>&1 &
DETECTOR_PID=$!
echo "Detector PID: $DETECTOR_PID"

sleep 5
if ! kill -0 "$DETECTOR_PID" 2>/dev/null; then
  echo "ERROR: detector process died immediately, aborting pair $PAIR condition $COND" | tee "$OUT/ERROR_run${PAIR}_${COND}.txt"
  exit 1
fi

sudo perf stat -p "$DETECTOR_PID" \
  -e task-clock,context-switches,cpu-migrations,page-faults,cycles,instructions \
  -o "$OUT/run${PAIR}_${COND}_perf_process.txt" \
  sleep "$DURATION_S" &
PERF_PROC_PID=$!

sudo perf stat -a \
  -e task-clock,context-switches,cpu-migrations,page-faults \
  -o "$OUT/run${PAIR}_${COND}_perf_system.txt" \
  sleep "$DURATION_S" &
PERF_SYS_PID=$!

sudo perf sched record -a -o "$OUT/run${PAIR}_${COND}_sched.data" -- sleep "$SCHED_S" &
PERF_SCHED_PID=$!

echo "Launched perf process ($PERF_PROC_PID), perf system ($PERF_SYS_PID), perf sched ($PERF_SCHED_PID)"

wait "$PERF_SCHED_PID"
sudo perf sched latency -i "$OUT/run${PAIR}_${COND}_sched.data" > "$OUT/run${PAIR}_${COND}_sched_latency.txt" 2>&1
sudo chown "$(id -u)":"$(id -g)" "$OUT/run${PAIR}_${COND}_sched.data" 2>/dev/null
echo "[$(date)] sched trace done for pair=$PAIR $COND"

wait "$PERF_PROC_PID"
wait "$PERF_SYS_PID"
echo "[$(date)] perf stat done for pair=$PAIR $COND"

wait "$DETECTOR_PID"
echo "[$(date)] detector done for pair=$PAIR $COND"

cp "$ROOT/piResults/results/generated/w2_live3_soak.json" "$OUT/run${PAIR}_${COND}_detector.json"
# Remove the large raw sched.data now that latency has been extracted (matches
# the .gitignore precedent set for the Round 9 perf .data/timehist dumps --
# several hundred MB each, not meant to be committed).
rm -f "$OUT/run${PAIR}_${COND}_sched.data"

echo "[$(date)] Pair $PAIR condition $COND complete."
