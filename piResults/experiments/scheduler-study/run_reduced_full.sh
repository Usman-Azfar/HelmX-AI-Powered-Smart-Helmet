#!/bin/bash
# Stops the same background-service set as the precedent reduced-load run
# (piResults/mpu6050Results.md), snapshots the resulting service state,
# runs Condition B (reduced) via run_condition.sh, then restarts everything.
set -uo pipefail
RAW="/home/helmx/Crash Detection/Crash-Detection/piResults/newPiResults_raw"
SERVICES="helmx-ble mosquitto rhasspy helmx_assistant wayvnc wayvnc-control rpi-connect rpi-connect-wayvnc"

echo "[$(date)] Stopping reduced-background service set: $SERVICES"
for s in $SERVICES; do
  sudo systemctl stop "$s.service" 2>&1
done
sleep 3

{
  echo "=== Reduced-condition active services snapshot, $(date) ==="
  systemctl list-units --type=service --state=running 2>&1
  echo ""
  echo "=== relevant service status after stop ==="
  for s in bluetooth $SERVICES; do
    echo "--- $s.service ---"
    systemctl is-active "$s.service" 2>&1
    systemctl is-enabled "$s.service" 2>&1
  done
  echo ""
  echo "Stopped set: $SERVICES"
  echo "Left running (base daemon, not part of prior reduced set either): bluetooth.service"
} > "$RAW/03_services_reduced.txt"

echo "[$(date)] Running Condition B (reduced) for 20 min..."
bash "$RAW/run_condition.sh" reduced 20 > "$RAW/orchestrator_reduced.log" 2>&1

echo "[$(date)] Condition B done. Restarting stopped services..."
for s in $SERVICES; do
  sudo systemctl start "$s.service" 2>&1
done
sleep 3
{
  echo "=== Services restarted, verification, $(date) ==="
  for s in bluetooth $SERVICES; do
    echo "--- $s.service ---"
    systemctl is-active "$s.service" 2>&1
  done
} > "$RAW/04_services_restarted_verification.txt"

echo "[$(date)] ALL_DONE_REDUCED_AND_RESTARTED"
