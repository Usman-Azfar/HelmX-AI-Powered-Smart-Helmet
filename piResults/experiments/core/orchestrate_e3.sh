#!/bin/bash
# HelmX_FInal_Pi_REqwuirements.md Section E3 -- scheduling-enhanced acquisition
# condition: the same FIFO acquisition method as E2 (pi_val_e2_fifo_acquisition.py),
# but run under SCHED_FIFO real-time scheduling (chrt) pinned to one CPU core
# (taskset), to help separate "acquisition method" from "userspace scheduling
# policy" as the two contributing factors to timing jitter.
#
# chrt -f requires elevated privilege on this system (rtprio ulimit is 0 for
# the normal user) -- runs via passwordless sudo, output file ownership fixed
# back to the normal user afterward since sudo would otherwise leave it
# root-owned.
#
# Usage: orchestrate_e3.sh <duration_min>
set -uo pipefail

DURATION_MIN="${1:-20}"
CHRT_PRIORITY=10
CPU_CORE=3

ROOT="/home/helmx/Crash Detection/Crash-Detection"
OUT="$ROOT/piResults/results/final-validation/acquisition_compare"
VENV_PY="$ROOT/.pi_research_venv/bin/python"
LABEL="e3_sched_enhanced"

cd "$ROOT"
echo "[$(date)] Starting E3: SCHED_FIFO priority=$CHRT_PRIORITY, CPU affinity=core $CPU_CORE, duration_min=$DURATION_MIN"

sudo chrt -f "$CHRT_PRIORITY" taskset -c "$CPU_CORE" "$VENV_PY" \
  deploy/pi_research_suite/pi_val_e2_fifo_acquisition.py \
  --duration-min "$DURATION_MIN" --label "$LABEL" \
  --sched-fifo-note "sudo chrt -f $CHRT_PRIORITY taskset -c $CPU_CORE (SCHED_FIFO rt priority $CHRT_PRIORITY, pinned to CPU core $CPU_CORE)"

sudo chown "$(id -u)":"$(id -g)" "$OUT/${LABEL}.json" 2>/dev/null
echo "[$(date)] E3 done."
