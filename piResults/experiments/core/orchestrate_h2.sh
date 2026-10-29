#!/bin/bash
# HelmX_FInal_Pi_REqwuirements.md Section H2 -- optional 3-hour soak.
# Reuses exp_w2_live3_soak.py exactly as H1's preserved 90-min soak did
# (Round 8/9) -- it already reports every field H2 asks for (sample count,
# scored windows, timing gaps, dropped/too-fast events, V_T/C_D-equivalent
# stream-guard telemetry, p50/p95/p99/max dt and processing latency,
# deadline misses, I2C failures, reconnects, exceptions, CPU/RSS/temp
# stats incl. p95/max and drift-over-time via 5-min checkpoints, throttle
# state, trigger count) -- so this is orchestration only, no new script.
#
# NOT RUN AUTOMATICALLY. Prepared and ready; launch only when explicitly
# told to (the user asked for this to happen last, on their go-ahead --
# it ties up the sensor for 3 hours, exclusively, per the doc's own
# single-I2C-device constraint already established this campaign).
#
# Usage: orchestrate_h2.sh   (duration is fixed at 180 min per the doc)
set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${HELMX_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
OUT="$ROOT/piResults/results/final-validation/long_soak"
VENV_PY="${HELMX_PYTHON:-$ROOT/.pi_research_venv/bin/python}"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Python executable not found: $VENV_PY" >&2
  echo "Set HELMX_PYTHON or create .pi_research_venv in the repository root." >&2
  exit 2
fi

mkdir -p "$OUT"
cd "$ROOT"

echo "[$(date)] H2: starting 3-hour soak" | tee -a "$OUT/h2_orchestrate.log"
"$VENV_PY" deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min 180 --checkpoint-every-min 5 \
  2>&1 | tee "$OUT/h2_long_soak_stdout.log"

cp "$ROOT/piResults/results/generated/w2_live3_soak.json" "$OUT/long_soak_summary.json"
echo "[$(date)] H2 done. Report copied to $OUT/long_soak_summary.json" | tee -a "$OUT/h2_orchestrate.log"
