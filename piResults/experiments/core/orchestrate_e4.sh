#!/bin/bash
# HelmX_FInal_Pi_REqwuirements.md Section E4 -- deployment-realistic
# no-IDE/no-desktop stress reduction. Stops every non-essential HelmX-adjacent
# service (same established list as F1/E1's "reduced" condition) and runs the
# deployed polling pipeline (exp_w2_live3_soak.py, the same base F1/G1/E1
# reused) for --duration-min minutes.
#
# DISCLOSED LIMITATION: the doc also asks for VS Code and the interactive
# coding agent to be closed. That part is not done here -- this script is
# launched BY that same agent, which must keep running to orchestrate and
# later analyze the run, so "interactive_agent_present" stays yes for this
# condition, same confound F1 already disclosed for its own runs. Every
# other non-essential background service IS stopped.
#
# Usage: orchestrate_e4.sh <duration_min>
set -uo pipefail

DURATION_MIN="${1:-20}"
REDUCED_SERVICES="helmx-ble.service mosquitto.service rhasspy.service helmx_assistant.service wayvnc.service wayvnc-control.service rpi-connect.service rpi-connect-wayvnc.service"

ROOT="/home/helmx/Crash Detection/Crash-Detection"
OUT="$ROOT/piResults/results/final-validation/runtime_optional"
VENV_PY="$ROOT/.pi_research_venv/bin/python"

mkdir -p "$OUT"
cd "$ROOT"

stop_services() {
  for svc in $REDUCED_SERVICES; do sudo systemctl stop "$svc" 2>&1 | tee -a "$OUT/e4_service_transitions.log"; done
}
start_services() {
  for svc in $REDUCED_SERVICES; do sudo systemctl start "$svc" 2>&1 | tee -a "$OUT/e4_service_transitions.log"; done
}

echo "[$(date)] E4: stopping non-essential services for deployment-reduced-interactive condition" | tee -a "$OUT/e4_orchestrate.log"
stop_services

echo "[$(date)] E4: running exp_w2_live3_soak.py for $DURATION_MIN min" | tee -a "$OUT/e4_orchestrate.log"
"$VENV_PY" deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min "$DURATION_MIN" \
  2>&1 | tee "$OUT/e4_deployment_reduced_interactive_stdout.log"

echo "[$(date)] E4: restarting services" | tee -a "$OUT/e4_orchestrate.log"
start_services

# exp_w2_live3_soak.py always writes to piResults/results/generated/w2_live3_soak.json --
# copy it into the E4 output dir under a distinguishing name before any other
# script overwrites that shared filename.
cp "$ROOT/piResults/results/generated/w2_live3_soak.json" "$OUT/e4_deployment_reduced_interactive.json"
echo "[$(date)] E4 done. Report copied to $OUT/e4_deployment_reduced_interactive.json" | tee -a "$OUT/e4_orchestrate.log"
