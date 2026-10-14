#!/usr/bin/env bash
# Run as helmx from a text console or plain SSH, never from the desktop/IDE.
set -euo pipefail
cd '/home/helmx/Crash Detection'
sudo -v
helmx_session_dir="Crash-Detection/piResults/results/final-closure/headless_console_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$helmx_session_dir"
helmx_system_units=()
helmx_user_units=()
for unit in lightdm.service wayvnc.service; do
    if systemctl is-active --quiet "$unit"; then
        helmx_system_units+=("$unit")
    fi
done
for unit in rpi-connect.service rpi-connect-wayvnc.service; do
    if systemctl --user is-active --quiet "$unit"; then
        helmx_user_units+=("$unit")
    fi
done
printf '%s\n' "${helmx_system_units[@]}" > "$helmx_session_dir/system_services_before.txt"
printf '%s\n' "${helmx_user_units[@]}" > "$helmx_session_dir/user_services_before.txt"
restore_services() {
    helmx_exit_status=$?
    trap - EXIT
    set +e
    helmx_restore_failed=0
    for unit in "${helmx_system_units[@]}"; do
        sudo systemctl start "$unit" || helmx_restore_failed=1
    done
    for unit in "${helmx_user_units[@]}"; do
        systemctl --user start "$unit" || helmx_restore_failed=1
    done
    printf 'Session exit status: %s\n' "$helmx_exit_status" > "$helmx_session_dir/session_status.txt"
    if (( helmx_restore_failed )); then
        echo "Service restoration failed; inspect saved service lists in $helmx_session_dir."
        (( helmx_exit_status != 0 )) || helmx_exit_status=1
    else
        echo 'Previously active desktop/remote services restored. Return to the chat for results review.'
    fi
    printf 'Restoration failed: %s\n' "$helmx_restore_failed" >> "$helmx_session_dir/session_status.txt"
    exit "$helmx_exit_status"
}
trap restore_services EXIT
for unit in "${helmx_user_units[@]}"; do
    systemctl --user stop "$unit"
done
for unit in "${helmx_system_units[@]}"; do
    sudo systemctl stop "$unit"
done
echo 'Starting two 20-minute recordings. Keep the helmet untouched and the desktop/IDE closed.'
sudo Crash-Detection/.pi_research_venv/bin/python -u Crash-Detection/piResults/results/final-closure/scripts/headless_batch.py 2>&1 | tee "$helmx_session_dir/batch.log"
