#!/bin/bash
# HelmX_FInal_Pi_REqwuirements.md Section D1 -- 3 conditions, 12 min each.
set -uo pipefail
ROOT="/home/helmx/Crash Detection/Crash-Detection"
VENV_PY="$ROOT/.pi_research_venv/bin/python"
SCRIPT="$ROOT/deploy/pi_research_suite/pi_val_d1_timing_loads.py"
OUT="$ROOT/piResults/results/final-validation/timing_loads"
REDUCED_SERVICES="helmx-ble.service mosquitto.service rhasspy.service helmx_assistant.service wayvnc.service wayvnc-control.service"
DURATION="${1:-12}"

echo "[$(date)] Condition 1: minimal_background -- stopping services"
for svc in $REDUCED_SERVICES; do sudo systemctl stop "$svc"; done
sleep 5
"$VENV_PY" "$SCRIPT" --duration-min "$DURATION" --condition minimal_background 2>&1 | tee "$OUT/run_minimal_background.log"

echo "[$(date)] Condition 2: normal_helmx_workload -- restarting services"
for svc in $REDUCED_SERVICES; do sudo systemctl start "$svc"; done
sleep 8
"$VENV_PY" "$SCRIPT" --duration-min "$DURATION" --condition normal_helmx_workload 2>&1 | tee "$OUT/run_normal_helmx_workload.log"

echo "[$(date)] Condition 3: heavier_interactive_workload -- launching stress-ng --cpu 4"
stress-ng --cpu 4 --timeout "$((${DURATION%.*} * 60 + 30))s" > "$OUT/stress_ng_condition3.log" 2>&1 &
STRESS_PID=$!
sleep 3
"$VENV_PY" "$SCRIPT" --duration-min "$DURATION" --condition heavier_interactive_workload 2>&1 | tee "$OUT/run_heavier_interactive_workload.log"
kill "$STRESS_PID" 2>/dev/null

echo "D1_ALL_CONDITIONS_COMPLETE"
