#!/bin/bash
# Experiment 1 orchestration: runs the real deployed detector pipeline for
# DURATION_MIN minutes while simultaneously collecting perf process-level,
# perf system-level, and perf sched-trace data. Used once for the LOADED
# condition and once for the REDUCED condition (services stopped first).
#
# Usage: run_condition.sh <condition_name: loaded|reduced> <duration_min>
set -uo pipefail

COND="$1"
DURATION_MIN="${2:-20}"
DURATION_S=$(python3 -c "print(int(float(\"$DURATION_MIN\")*60))")
SCHED_S=600   # 10-minute scheduler trace, within the longer detector run

ROOT="/home/helmx/Crash Detection/Crash-Detection"
RAW="$ROOT/piResults/newPiResults_raw"
VENV_PY="$ROOT/.pi_research_venv/bin/python"

cd "$ROOT"
echo "[$(date)] Starting condition=$COND duration_min=$DURATION_MIN"

# 1. Launch the real live detector pipeline in the background.
"$VENV_PY" deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min "$DURATION_MIN" \
  > "$RAW/detector_${COND}_stdout.log" 2>&1 &
DETECTOR_PID=$!
echo "Detector PID: $DETECTOR_PID"
echo "$DETECTOR_PID" > "$RAW/detector_${COND}.pid"

# Give it a moment to actually connect to the sensor and start its loop.
sleep 5
if ! kill -0 "$DETECTOR_PID" 2>/dev/null; then
  echo "ERROR: detector process died immediately, aborting condition $COND" | tee "$RAW/ERROR_${COND}.txt"
  exit 1
fi

# /proc snapshot before
cat "/proc/$DETECTOR_PID/status" > "$RAW/proc_status_${COND}_before.txt" 2>&1
cat "/proc/$DETECTOR_PID/sched" > "$RAW/proc_sched_${COND}_before.txt" 2>&1

# 2. perf stat process-level, for the full detector run duration.
sudo perf stat -p "$DETECTOR_PID" \
  -e task-clock,context-switches,cpu-migrations,page-faults,cycles,instructions \
  -o "$RAW/perf_${COND}_process.txt" \
  sleep "$DURATION_S" &
PERF_PROC_PID=$!

# 3. perf stat system-level, matched duration.
sudo perf stat -a \
  -e task-clock,context-switches,cpu-migrations,page-faults \
  -o "$RAW/perf_${COND}_system.txt" \
  sleep "$DURATION_S" &
PERF_SYS_PID=$!

# 4. perf sched trace, shorter (10 min), started now so it lands well inside the run.
sudo perf sched record -a -o "$RAW/perf_${COND}_sched.data" -- sleep "$SCHED_S" &
PERF_SCHED_PID=$!

echo "Launched perf process ($PERF_PROC_PID), perf system ($PERF_SYS_PID), perf sched ($PERF_SCHED_PID)"

# Wait for the scheduler trace to finish first, then post-process it immediately.
wait "$PERF_SCHED_PID"
sudo perf sched latency -i "$RAW/perf_${COND}_sched.data" > "$RAW/sched_${COND}_latency.txt" 2>&1
sudo perf sched timehist -i "$RAW/perf_${COND}_sched.data" > "$RAW/sched_${COND}_timehist.txt" 2>&1
sudo chown "$(id -u)":"$(id -g)" "$RAW/perf_${COND}_sched.data" 2>/dev/null
echo "[$(date)] sched trace done for $COND"

# Wait for perf stat process/system stat runs to finish.
wait "$PERF_PROC_PID"
wait "$PERF_SYS_PID"
echo "[$(date)] perf stat done for $COND"

# Wait for the detector itself to finish (should already be close to done).
wait "$DETECTOR_PID"
echo "[$(date)] detector done for $COND"

# /proc snapshot after (best-effort; process may have exited)
cat "/proc/$DETECTOR_PID/status" > "$RAW/proc_status_${COND}_after.txt" 2>&1 || echo "process exited before after-snapshot" > "$RAW/proc_status_${COND}_after.txt"

# Move the detector's JSON report out of the shared piResults/results/generated/ path
# (exp_w2_live3_soak.py always writes to the same w2_live3_soak.json filename)
# so the two conditions don't clobber each other.
cp "$ROOT/piResults/results/generated/w2_live3_soak.json" "$RAW/detector_${COND}.json"

echo "[$(date)] Condition $COND complete."
