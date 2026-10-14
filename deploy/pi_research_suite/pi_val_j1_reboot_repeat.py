"""HelmX_FInal_Pi_REqwuirements.md Section J1 -- reboot/reassembly repeatability
("boot 2" side). Boot 1's equivalent data already exists from the same-day
earlier campaign (register dump in mpu_config/, stationary + gentle_rotation
phases in benign_motion/), all captured before the unplanned reboot that
happened mid motion-session -- so this script only captures the "boot 2"
(post-reboot) side: a fresh register dump, then a short marker-driven
live-pipeline capture repeating the same two scenarios (stationary, then
gentle rotation) for direct comparison against boot 1's phase_1_stationary.json
and phase_2_gentle_rotation.json.

Writes ONLY to reboot_repeatability/ -- never touches mpu_config/ or
benign_motion/'s existing boot-1 files.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_j1_reboot_repeat.py
"""
import json
import subprocess
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
MAX_SESSION_MIN = 10.0

REGISTERS = {
    "SMPLRT_DIV": 0x19, "CONFIG": 0x1A, "GYRO_CONFIG": 0x1B, "ACCEL_CONFIG": 0x1C,
    "FIFO_EN": 0x23, "INT_ENABLE": 0x38, "INT_STATUS": 0x3A,
    "PWR_MGMT_1": 0x6B, "PWR_MGMT_2": 0x6C, "WHO_AM_I": 0x75, "USER_CTRL": 0x6A,
}
SERVICE_LIST = [
    "helmx-ble.service", "mosquitto.service", "rhasspy.service", "helmx_assistant.service",
    "wayvnc.service", "wayvnc-control.service", "rpi-connect.service", "rpi-connect-wayvnc.service",
    "bluetooth.service",
]


def register_dump(out_dir):
    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    bus = smbus2.SMBus(1)
    raw = {name: bus.read_byte_data(address, reg) for name, reg in REGISTERS.items()}
    report = {
        "device": common.device_info(), "i2c_address": hex(address),
        "raw_hex": {name: hex(v) for name, v in raw.items()},
        "who_am_i": hex(raw["WHO_AM_I"]), "who_am_i_expected_0x68": raw["WHO_AM_I"] == 0x68,
    }
    (out_dir / "boot2_register_dump.json").write_text(json.dumps(report, indent=2))
    print(f"Boot 2 register dump: WHO_AM_I={report['who_am_i']}")
    return report


def service_state():
    state = {}
    for svc in SERVICE_LIST:
        try:
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=3)
            state[svc] = r.stdout.strip()
        except Exception as e:
            state[svc] = f"unknown ({e})"
    try:
        gov = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read_text().strip()
    except OSError:
        gov = None
    return {"services": state, "cpu_governor": gov}


def axis_clip_stats(vals, raw_limit=32767):
    vals = np.asarray(vals)
    return {
        "min_raw": int(vals.min()), "max_raw": int(vals.max()),
        "count_near_neg32768": int((vals <= -32760).sum()), "count_near_32767": int((vals >= 32760).sum()),
    }


def finalize_phase(out_dir, phase_name, ph_samples, ph_windows):
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
            "gyro_magnitude_dps_mean": float(np.mean([
                (s["gx_dps"] ** 2 + s["gy_dps"] ** 2 + s["gz_dps"] ** 2) ** 0.5 for s in ph_samples])),
        }
    (out_dir / f"boot2_{phase_name}.json").write_text(json.dumps(report, indent=2))
    print(f"  >> CHECKPOINTED '{phase_name}': {report.get('n_samples', 0)} samples -> boot2_{phase_name}.json")
    return report


def main():
    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "reboot_repeatability"
    out_dir.mkdir(parents=True, exist_ok=True)

    reg_report = register_dump(out_dir)
    svc_report = service_state()
    (out_dir / "boot2_service_state.json").write_text(json.dumps(svc_report, indent=2))

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    rate_hz = cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / rate_hz
    bus = smbus2.SMBus(1)

    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], rate_hz)
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])

    Path(MARKER_FILE).write_text("waiting_for_phase_1")
    print(f"Marker file: {MARKER_FILE} -- write a new phase label to advance, 'STOP_SESSION' to end.")
    print("Boot-2 repeat capture running. Waiting for phase markers (stationary, then gentle_rotation)...",
          flush=True)

    all_phase_reports = {}
    phase_samples, phase_windows = [], []
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
                    all_phase_reports[current_phase] = finalize_phase(out_dir, current_phase, phase_samples, phase_windows)
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
        all_phase_reports[current_phase] = finalize_phase(out_dir, current_phase, phase_samples, phase_windows)

    (out_dir / "boot2_combined.json").write_text(json.dumps({
        "device": common.device_info(), "i2c_errors_total": n_i2c_errors,
        "per_phase": all_phase_reports, "register_dump": reg_report, "service_state": svc_report,
    }, indent=2))
    print(f"\nBoot-2 session ended. {len(all_phase_reports)} phases. i2c_errors={n_i2c_errors}")


if __name__ == "__main__":
    main()
