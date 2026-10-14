"""HelmX_FInal_Pi_REqwuirements.md Section J1 -- extra boot-cycle capture.

Section J's official requirement (register dump + service state + a couple
of motion phases per boot) was already satisfied by boot1/boot2
(reboot_repeatability/). This is a *third*, additional boot-cycle capture,
run because the Pi rebooted again (2026-09-20, ~12:58) partway through the
optional E2/E3/E4/H2/R campaign -- captured for due diligence before
resuming that campaign, not because J was reopened.

Non-interactive: captures register dump, service state, and one stationary
phase only (no marker file, no requirement for a human to move the helmet --
that's what distinguishes this from pi_val_j1_reboot_repeat.py's boot2 script).

Writes to reboot_repeatability/boot3_*.json -- never touches boot1/boot2 files.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_boot3_documentation.py
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
STATIONARY_DURATION_S = 60.0

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
    (out_dir / "boot3_register_dump.json").write_text(json.dumps(report, indent=2))
    print(f"Boot 3 register dump: WHO_AM_I={report['who_am_i']}")
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
    try:
        boot_time = subprocess.run(["uptime", "-s"], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception:
        boot_time = None
    return {"services": state, "cpu_governor": gov, "system_boot_time": boot_time}


def axis_clip_stats(vals):
    vals = np.asarray(vals)
    return {
        "min_raw": int(vals.min()), "max_raw": int(vals.max()),
        "count_near_neg32768": int((vals <= -32760).sum()), "count_near_32767": int((vals >= 32760).sum()),
    }


def main():
    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "reboot_repeatability"
    out_dir.mkdir(parents=True, exist_ok=True)

    reg_report = register_dump(out_dir)
    svc_report = service_state()
    (out_dir / "boot3_service_state.json").write_text(json.dumps(svc_report, indent=2))

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

    print(f"Boot-3 stationary capture running for {STATIONARY_DURATION_S:.0f}s -- leave the sensor still.",
          flush=True)

    samples, windows = [], []
    start = time.monotonic()
    deadline = start + STATIONARY_DURATION_S
    next_tick = time.monotonic()
    n_i2c_errors = 0

    while time.monotonic() < deadline:
        next_tick += period_s
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
            "t_monotonic": t,
            "ax_raw": ax_r, "ay_raw": ay_r, "az_raw": az_r, "gx_raw": gx_r, "gy_raw": gy_r, "gz_raw": gz_r,
            "ax_ms2": ax_g * G_TO_MS2, "ay_ms2": ay_g * G_TO_MS2, "az_ms2": az_g * G_TO_MS2,
            "gx_dps": gx_d, "gy_dps": gy_d, "gz_dps": gz_d,
        }
        samples.append(row)

        scorer.append([row["ax_ms2"], row["ay_ms2"], row["az_ms2"], gx_d, gy_d, gz_d])
        result = scorer.try_score()
        if result is not None:
            is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
            windows.append({
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

    if samples:
        dts = np.diff([s["t_monotonic"] for s in samples])
        clipping = {axis: axis_clip_stats([s[f"{axis}_raw"] for s in samples])
                    for axis in ("ax", "ay", "az", "gx", "gy", "gz")}
        accel_mag = [(s["ax_ms2"] ** 2 + s["ay_ms2"] ** 2 + s["az_ms2"] ** 2) ** 0.5 for s in samples]
        gyro_mag = [(s["gx_dps"] ** 2 + s["gy_dps"] ** 2 + s["gz_dps"] ** 2) ** 0.5 for s in samples]
        crash_probs = [w["crash_prob"] for w in windows]
        recon_errors = [w["recon_error"] for w in windows]
        report = {
            "phase": "stationary", "n_samples": len(samples),
            "duration_s": samples[-1]["t_monotonic"] - samples[0]["t_monotonic"],
            "i2c_errors": n_i2c_errors,
            "dt_stats_ms": {"p50": float(np.percentile(dts, 50) * 1000),
                             "p95": float(np.percentile(dts, 95) * 1000),
                             "p99": float(np.percentile(dts, 99) * 1000),
                             "max": float(dts.max() * 1000)},
            "n_windows_scored": len(windows),
            "clipping_per_axis_raw_int16": clipping,
            "accel_magnitude_ms2_mean": float(np.mean(accel_mag)),
            "accel_magnitude_ms2_max": float(max(accel_mag)),
            "gyro_magnitude_dps_mean": float(np.mean(gyro_mag)),
            "gyro_magnitude_dps_max": float(max(gyro_mag)),
            "max_classifier_score": max(crash_probs) if crash_probs else None,
            "max_reconstruction_error": max(recon_errors) if recon_errors else None,
            "n_classifier_threshold_crossings": sum(w["classifier_crossed"] for w in windows),
            "n_recon_threshold_crossings": sum(w["recon_crossed"] for w in windows),
            "n_or_positive_windows": sum(w["or_positive"] for w in windows),
            "n_confirmed_triggers": sum(w["confirmed_triggered"] for w in windows),
        }
    else:
        report = {"phase": "stationary", "n_samples": 0, "i2c_errors": n_i2c_errors, "note": "no samples captured"}

    (out_dir / "boot3_stationary.json").write_text(json.dumps(report, indent=2))
    (out_dir / "boot3_combined.json").write_text(json.dumps({
        "device": common.device_info(), "register_dump": reg_report, "service_state": svc_report,
        "stationary": report,
    }, indent=2))
    print(f"\nBoot-3 documentation complete. i2c_errors={n_i2c_errors}, "
          f"max_classifier_score={report.get('max_classifier_score')}, "
          f"max_reconstruction_error={report.get('max_reconstruction_error')}, "
          f"confirmed_triggers={report.get('n_confirmed_triggers')}")


if __name__ == "__main__":
    main()
