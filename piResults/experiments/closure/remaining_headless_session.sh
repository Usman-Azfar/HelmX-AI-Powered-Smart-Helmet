#!/usr/bin/env bash
# Full runs require a local console and IDE exit. Smoke may explicitly retain IDE.
set -euo pipefail
helmx_wrapper_path="$(realpath "$0")"
cd '/home/helmx/Crash Detection'
if (( EUID != 0 )); then
    exec sudo bash "$helmx_wrapper_path" --operator-user "$(id -un)" "$@"
fi
helmx_operator_user=''
helmx_smoke=0
helmx_keep_ide=0
while (( $# )); do
    case "$1" in
        --operator-user)
            [[ $# -ge 2 ]] || exit 2
            helmx_operator_user="$2"
            shift 2 ;;
        --smoke-test) helmx_smoke=1; shift ;;
        --keep-ide) helmx_keep_ide=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
if [[ -z "$helmx_operator_user" || "$helmx_operator_user" == root ]]; then
    echo 'Run this wrapper as helmx; it invokes sudo itself.' >&2
    exit 1
fi
if (( helmx_keep_ide && ! helmx_smoke )); then
    echo '--keep-ide is only allowed with --smoke-test.' >&2
    exit 2
fi
helmx_flags=()
if (( helmx_smoke )); then
    helmx_flags+=(--smoke-test)
    echo 'D4 then K1 smoke: 60 seconds per condition, four recordings plus verification.'
else
    echo 'D4 then K1: six pairs each, ten minutes per condition; about four hours plus review overhead.'
    echo 'Both studies require a successful smoke test of the current Python sources.'
fi
if (( helmx_keep_ide )); then
    helmx_flags+=(--keep-ide)
    echo 'IDE/desktop retained. Other configured remote services will stop and restart. Smoke evidence only.'
else
    echo 'Keep the IDE closed until both studies finish.'
fi
echo 'Keep the helmet untouched throughout the recordings.'
for helmx_study in D4 K1; do
    Crash-Detection/.pi_research_venv/bin/python -u Crash-Detection/piResults/results/final-closure/scripts/randomized_studies.py run --study "$helmx_study" --operator-user "$helmx_operator_user" "${helmx_flags[@]}"
done
echo 'Both studies finished and services restored. Review the evidence before treating any requirement as complete.'
