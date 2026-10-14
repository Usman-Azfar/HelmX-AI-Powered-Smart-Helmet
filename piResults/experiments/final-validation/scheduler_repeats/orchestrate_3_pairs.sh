#!/bin/bash
# Runs 3 matched loaded/reduced pairs (F1's "at least 3" ask), 20 min each = 6
# runs, ~120 min total. Reduced-condition service stop list matches the
# established convention from piResults/PI_TEST_PROTOCOL_PROGRESS.md exactly.
set -uo pipefail

DURATION_MIN="${1:-20}"
ROOT="/home/helmx/Crash Detection/Crash-Detection"
OUT="$ROOT/piResults/results/final-validation/scheduler_repeats"
REDUCED_SERVICES="helmx-ble.service mosquitto.service rhasspy.service helmx_assistant.service wayvnc.service wayvnc-control.service rpi-connect.service rpi-connect-wayvnc.service"

stop_services() {
  for svc in $REDUCED_SERVICES; do sudo systemctl stop "$svc" 2>&1 | tee -a "$OUT/service_transitions.log"; done
}
start_services() {
  for svc in $REDUCED_SERVICES; do sudo systemctl start "$svc" 2>&1 | tee -a "$OUT/service_transitions.log"; done
}

for PAIR in 1 2 3; do
  echo "===== PAIR $PAIR: loaded condition =====" | tee -a "$OUT/orchestrate.log"
  bash "$OUT/run_pair.sh" loaded "$PAIR" "$DURATION_MIN" 2>&1 | tee -a "$OUT/orchestrate.log"

  echo "===== PAIR $PAIR: stopping services for reduced condition =====" | tee -a "$OUT/orchestrate.log"
  stop_services
  sleep 5

  echo "===== PAIR $PAIR: reduced condition =====" | tee -a "$OUT/orchestrate.log"
  bash "$OUT/run_pair.sh" reduced "$PAIR" "$DURATION_MIN" 2>&1 | tee -a "$OUT/orchestrate.log"

  echo "===== PAIR $PAIR: restarting services =====" | tee -a "$OUT/orchestrate.log"
  start_services
  sleep 5
done

echo "ALL_PAIRS_COMPLETE" | tee -a "$OUT/orchestrate.log"
