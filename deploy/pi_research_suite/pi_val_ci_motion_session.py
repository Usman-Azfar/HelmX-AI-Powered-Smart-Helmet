"""HelmX_FInal_Pi_REqwuirements.md Sections C2 (per-axis clipping) + I
(benign-motion stress test) -- combined live guided session, since both ask
for nearly the same scenario list. Runs the REAL deployed pipeline (raw
register reads -> CausalGravityFilter -> WindowScorer -> TriggerPolicy,
exact classes from deploy/crash_monitor.py) at the deployed 50Hz pace,
continuously, for the whole session.

Phase boundaries are marked via a file (default /tmp/helmx_motion_marker.txt)
-- an operator (coordinating live with the person moving the helmet)
writes a new phase label to this file at each transition; this script polls
it every sample and logs a phase-boundary event with an exact monotonic
timestamp, matching the file-signal pattern deploy/crash_monitor.py already
uses for cancellation (CancellationListener). Writing "STOP_SESSION" ends the
capture.

CHECKPOINTED: unlike the first attempt at this (lost entirely to an
unplanned mid-session reboot -- nothing was persisted until the very end),
this version writes each phase's stats to its own file THE MOMENT that phase
ends (as soon as the marker changes to the next phase), and flushes raw
samples to CSV in append mode continuously. A crash/reboot mid-session now
only loses the phase in progress, not everything before it.

Run on the Pi (leave running for the whole session):
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_ci_motion_session.py
"""
import csv
import json
import logging
import struct
import sys
import time
from pathlib import Path

import numpy as np
import smbus2

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common
import crash_monitor as cm

ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
ACCEL_SENS_LSB_PER_G = 16384.0
GYRO_SENS_LSB_PER_DEG_S = 131.0
G_TO_MS2 = 9.80665
MARKER_FILE = "/tmp/helmx_motion_marker.txt"
MAX_SESSION_MIN = 40.0
OUT_C2 = None
OUT_I = None
RAW_CSV_FIELDS = ["t_monotonic", "phase", "ax_raw", "ay_raw", "az_raw", "gx_raw", "gy_raw", "gz_raw",
                   "ax_ms2", "ay_ms2", "az_ms2", "gx_dps", "gy_dps", "gz_dps"]


def axis_clip_stats(vals, raw_limit=32767):
    vals = np.asarray(vals)
    return {
        "min_raw": int(vals.min()), "max_raw": int(vals.max()),
        "count_near_neg32768": int((vals <= -32760).sum()),
        "count_near_32767": int((vals >= 32760).sum()),
        "pct_within_99pct_fullscale": float(100.0 * (np.abs(vals) >= 0.99 * raw_limit).sum() / len(vals)),
        "pct_within_95pct_fullscale": float(100.0 * (np.abs(vals) >= 0.95 * raw_limit).sum() / len(vals)),
        "pct_within_90pct_fullscale": float(100.0 * (np.abs(vals) >= 0.90 * raw_limit).sum() / len(vals)),
    }


def finalize_phase(phase_name, ph_samples, ph_windows):
    """Computes C2+I stats for one completed phase and writes it to disk
    IMMEDIATELY -- called the instant the marker changes, not at session end."""
    if not ph_samples:
        report = {"phase": phase_name, "n_samples": 0, "note": "no samples captured in this phase"}
    else:
        clipping = {axis: axis_clip_stats([s[f"{axis}_raw"] for s in ph_samples])
                    for axis in ("ax", "ay", "az", "gx", "gy", "gz")}
        crash_probs = [w["crash_prob"] for w in ph_windows]
        recon_errors = [w["recon_error"] for w in ph_windows]
        report = {
            "phase": phase_name, "n_samples": len(ph_samples),
            "duration_s": ph_samples[-1]["t_monotonic"] - ph_samples[0]["t_monotonic"],
            "n_windows_scored": len(ph_windows),
            "clipping_per_axis_raw_int16": clipping,
            "max_classifier_score": max(crash_probs) if crash_probs else None,
            "max_reconstruction_error": max(recon_errors) if recon_errors else None,
            "n_classifier_threshold_crossings": sum(w["classifier_crossed"] for w in ph_windows),
            "n_recon_threshold_crossings": sum(w["recon_crossed"] for w in ph_windows),
            "n_or_positive_windows": sum(w["or_positive"] for w in ph_windows),
            "n_confirmed_triggers": sum(w["confirmed_triggered"] for w in ph_windows),
            "accel_magnitude_ms2_max": float(max(
                (s["ax_ms2"] ** 2 + s["ay_ms2"] ** 2 + s["az_ms2"] ** 2) ** 0.5 for s in ph_samples)),
            "gyro_magnitude_dps_max": float(max(
                (s["gx_dps"] ** 2 + s["gy_dps"] ** 2 + s["gz_dps"] ** 2) ** 0.5 for s in ph_samples)),
        }
    safe_name = phase_name.replace("/", "_")
    for out_dir in (OUT_C2, OUT_I):
        (out_dir / f"phase_{safe_name}.json").write_text(json.dumps(report, indent=2))
    print(f"  >> CHECKPOINTED phase '{phase_name}': {report.get('n_samples', 0)} samples, "
          f"{report.get('n_windows_scored', 0)} windows -> phase_{safe_name}.json")
    return report


def main():
    global OUT_C2, OUT_I
    OUT_C2 = common.ROOT / "piResults" / "results" / "final-validation" / "clipping"
    OUT_I = common.ROOT / "piResults" / "results" / "final-validation" / "benign_motion"
    OUT_C2.mkdir(parents=True, exist_ok=True)
    OUT_I.mkdir(parents=True, exist_ok=True)
    raw_csv_path = OUT_C2 / "motion_session_raw.csv"
    raw_csv_file = open(raw_csv_path, "w", newline="")
    raw_csv_writer = csv.DictWriter(raw_csv_file, fieldnames=RAW_CSV_FIELDS)
    raw_csv_writer.writeheader()

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    rate_hz = cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / rate_hz
    bus = smbus2.SMBus(1)

    logger = logging.getLogger("ci_motion_session")
    logger.setLevel(logging.ERROR)
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], rate_hz)
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])

    Path(MARKER_FILE).write_text("waiting_for_phase_1")
    print(f"Marker file: {MARKER_FILE} -- write a new phase label to advance, 'STOP_SESSION' to end.")
    print("Capture running (checkpointed per-phase). Waiting for phase markers...", flush=True)

    all_phase_reports = {}
    phase_samples = []
    phase_windows = []
    current_phase = "waiting_for_phase_1"
    start = time.monotonic()
    deadline = start + MAX_SESSION_MIN * 60.0
    next_tick = time.monotonic()
    next_marker_check = time.monotonic()
    n_i2c_errors = 0

    while time.monotonic() < deadline:
        next_tick += period_s

        now_check = time.monotonic()
        if now_check >= next_marker_check:
            try:
                marker = Path(MARKER_FILE).read_text().strip()
            except OSError:
                marker = current_phase
            next_marker_check = now_check + 0.1
            if marker != current_phase:
                if current_phase != "waiting_for_phase_1":
                    all_phase_reports[current_phase] = finalize_phase(current_phase, phase_samples, phase_windows)
                phase_samples, phase_windows = [], []
                current_phase = marker
                print(f"[{time.monotonic() - start:7.2f}s] Phase -> {current_phase}", flush=True)
            if current_phase == "STOP_SESSION":
                break

        try:
            ax_r, ay_r, az_r = struct.unpack(">hhh", bytes(bus.read_i2c_block_data(address, ACCEL_XOUT_H, 6)))
            gx_r, gy_r, gz_r = struct.unpack(">hhh", bytes(bus.read_i2c_block_data(address, GYRO_XOUT_H, 6)))
        except OSError:
            n_i2c_errors += 1
            continue

        t = time.monotonic()
        ax_g, ay_g, az_g = ax_r / ACCEL_SENS_LSB_PER_G, ay_r / ACCEL_SENS_LSB_PER_G, az_r / ACCEL_SENS_LSB_PER_G
        gx_d, gy_d, gz_d = gx_r / GYRO_SENS_LSB_PER_DEG_S, gy_r / GYRO_SENS_LSB_PER_DEG_S, gz_r / GYRO_SENS_LSB_PER_DEG_S
        row = {
            "t_monotonic": t, "phase": current_phase,
            "ax_raw": ax_r, "ay_raw": ay_r, "az_raw": az_r, "gx_raw": gx_r, "gy_raw": gy_r, "gz_raw": gz_r,
            "ax_ms2": ax_g * G_TO_MS2, "ay_ms2": ay_g * G_TO_MS2, "az_ms2": az_g * G_TO_MS2,
            "gx_dps": gx_d, "gy_dps": gy_d, "gz_dps": gz_d,
        }
        phase_samples.append(row)
        raw_csv_writer.writerow(row)
        raw_csv_file.flush()  # durable immediately -- this is the whole point of this rewrite

        scorer.append([row["ax_ms2"], row["ay_ms2"], row["az_ms2"], gx_d, gy_d, gz_d])
        result = scorer.try_score()
        if result is not None:
            is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
            phase_windows.append({
                "t_monotonic": t, "crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                "classifier_crossed": result["crash_prob"] > classifier_t,
                "recon_crossed": result["recon_error"] > recon_t,
                "or_positive": is_anomaly, "confirmed_triggered": triggered,
            })

        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()

    if current_phase not in ("STOP_SESSION", "waiting_for_phase_1") and current_phase not in all_phase_reports:
        all_phase_reports[current_phase] = finalize_phase(current_phase, phase_samples, phase_windows)
    raw_csv_file.close()

    combined = {
        "device": common.device_info(),
        "context": "Combined C2 (per-axis clipping) + I (benign-motion stress test), live guided session, checkpointed per-phase.",
        "accel_full_scale_g": 2.0, "gyro_full_scale_dps": 250.0,
        "i2c_errors_total": n_i2c_errors,
        "per_phase": all_phase_reports,
        "important_caveats": [
            "These do not reproduce motorcycle vibration.", "These do not reproduce crashes.",
            "Report only benign-handling behavior, per the doc's own explicit instruction.",
        ],
    }
    (OUT_C2 / "clipping_and_benign_motion_session.json").write_text(json.dumps(combined, indent=2))
    (OUT_I / "clipping_and_benign_motion_session.json").write_text(json.dumps(combined, indent=2))
    print(f"\nSession ended. {len(all_phase_reports)} phases checkpointed. i2c_errors={n_i2c_errors}")
    print(f"Combined report written to {OUT_C2} and {OUT_I}")


if __name__ == "__main__":
    main()
