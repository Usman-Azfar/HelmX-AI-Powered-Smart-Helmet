#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${HELMX_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SERVICE_USER="${HELMX_USER:-${SUDO_USER:-$(id -un)}}"
PYTHON_BIN="${HELMX_PYTHON:-$ROOT/.pi_research_venv/bin/python}"
TEMPLATE="$SCRIPT_DIR/helmx-crash-monitor.service"
TARGET="/etc/systemd/system/helmx-crash-monitor.service"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  echo "Set HELMX_PYTHON to the deployment environment's Python executable." >&2
  exit 2
fi

escape_sed() { printf '%s' "$1" | sed 's/[&|]/\\&/g'; }

sed \
  -e "s|__HELMX_USER__|$(escape_sed "$SERVICE_USER")|g" \
  -e "s|__HELMX_ROOT__|$(escape_sed "$ROOT")|g" \
  -e "s|__HELMX_PYTHON__|$(escape_sed "$PYTHON_BIN")|g" \
  "$TEMPLATE" | sudo tee "$TARGET" >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable --now helmx-crash-monitor.service
echo "Installed and started $TARGET for user $SERVICE_USER"
