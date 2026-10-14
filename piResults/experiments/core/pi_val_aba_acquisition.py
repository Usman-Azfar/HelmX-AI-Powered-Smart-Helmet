"""HelmX_FINAL_Pi_ABA_Acquisition_Test.txt -- one condition of the A1(polling)
-> B(FIFO) -> A2(polling) matched acquisition-method comparison.

Purpose: isolate whether switching ONLY the acquisition method (deployed
polling vs. the FIFO/decimated path from Section E2/E3) changes the
reconstruction-error distribution or confirmed-trigger behavior, holding
model, thresholds, preprocessing, and physical conditions constant. This is
the explicit follow-up the E2/E3/E4/H2 round's own writeup called for
(acquisition_compare/acquisition_comparison.txt: "would need a same-duration
polling rerun under identical conditions to isolate acquisition method from
coincidence").

Both modes share the identical CrashModel / CausalGravityFilter /
WindowScorer / SampleStreamGuard / TriggerPolicy classes from
deploy/crash_monitor.py -- only the sample-acquisition mechanism differs:

- polling: one on-demand I2C read of ACCEL_XOUT_H then GYRO_XOUT_H per
  sample tick, sleep-paced to the deployed 50Hz period (mirrors
  crash_monitor.main()'s real loop and gap-handling exactly, including the
  gravity-filter reset on a long gap).
- fifo: the same hardware-FIFO-buffered, software-decimated acquisition as
  pi_val_e2_fifo_acquisition.py.

DISCLOSED METHODOLOGY NOTE -- FIFO sample timestamps: the host never
receives a true per-hardware-sample timestamp under FIFO/buffered
acquisition (a whole batch is drained at once). Each decimated (~50Hz) fed
sample within a drain batch is assigned an ESTIMATED timestamp by evenly
interpolating across the wall-clock interval since the previous drain
(anchored at each drain's *start* time, since that's closest to when the
batch's samples actually finished accumulating in the FIFO). This is a
necessary, disclosed approximation -- not a hidden assumption -- needed to
feed the same SampleStreamGuard timing-gap/V_T/C_D machinery used for the
polling path, for a fair matched comparison at the model's actual decision
rate rather than the raw native FIFO push rate.

Run on the Pi, one condition per invocation, in order:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_aba_acquisition.py --mode polling --label A1_polling --duration-min 20
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_aba_acquisition.py --mode fifo     --label B_fifo     --duration-min 20
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_aba_acquisition.py --mode polling --label A2_polling --duration-min 20
"""
import argparse
import csv
import json
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
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

REG_SMPLRT_DIV = 0x19
REG_FIFO_EN = 0x23
REG_USER_CTRL = 0x6A
REG_FIFO_COUNT_H = 0x72
REG_FIFO_R_W = 0x74
SMPLRT_DIV_VALUE = 159
FIFO_EN_GYRO_ACCEL = 0x78
BYTES_PER_SAMPLE = 12
MAX_BLOCK_READ = 24
CALIBRATION_S = 2.0
POLL_INTERVAL_S_FIFO = 0.03
TARGET_HZ = 50

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


def register_dump(bus, address):
    raw = {name: bus.read_byte_data(address, reg) for name, reg in REGISTERS.items()}
    return {"raw_hex": {name: hex(v) for name, v in raw.items()}, "who_am_i": hex(raw["WHO_AM_I"])}


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
        freq = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").read_text().strip()
    except OSError:
        freq = None
    return {"services": state, "cpu_governor": gov, "cpu_frequency_khz": freq}


def to_physical(ax_r, ay_r, az_r, gx_r, gy_r, gz_r):
    return (ax_r / ACCEL_SENS_LSB_PER_G * G_TO_MS2, ay_r / ACCEL_SENS_LSB_PER_G * G_TO_MS2,
            az_r / ACCEL_SENS_LSB_PER_G * G_TO_MS2, gx_r / GYRO_SENS_LSB_PER_DEG_S,
            gy_r / GYRO_SENS_LSB_PER_DEG_S, gz_r / GYRO_SENS_LSB_PER_DEG_S)


def configure_fifo(bus, address):
    bus.write_byte_data(address, REG_SMPLRT_DIV, SMPLRT_DIV_VALUE)
    bus.write_byte_data(address, REG_USER_CTRL, 0x04)
    time.sleep(0.01)
    bus.write_byte_data(address, REG_USER_CTRL, 0x40)
    bus.write_byte_data(address, REG_FIFO_EN, FIFO_EN_GYRO_ACCEL)


def restore_baseline_registers(bus, address):
    bus.write_byte_data(address, REG_FIFO_EN, 0x00)
    bus.write_byte_data(address, REG_USER_CTRL, 0x00)
    bus.write_byte_data(address, REG_SMPLRT_DIV, 0x00)


def read_fifo_count(bus, address):
    hi, lo = bus.read_i2c_block_data(address, REG_FIFO_COUNT_H, 2)
    return (hi << 8) | lo


def drain_fifo_bytes(bus, address, n_bytes):
    raw = bytearray()
    offset = 0
    while offset < n_bytes:
        chunk = min(MAX_BLOCK_READ, n_bytes - offset)
        raw += bytes(bus.read_i2c_block_data(address, REG_FIFO_R_W, chunk))
        offset += chunk
    return raw


def calibrate_native_rate(bus, address, duration_s):
    t0 = time.monotonic()
    deadline = t0 + duration_s
    n_samples = 0
    max_fc = 0
    while time.monotonic() < deadline:
        fc = read_fifo_count(bus, address)
        max_fc = max(max_fc, fc)
        if fc >= BYTES_PER_SAMPLE:
            nbytes = (fc // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
            drain_fifo_bytes(bus, address, nbytes)
            n_samples += nbytes // BYTES_PER_SAMPLE
        time.sleep(POLL_INTERVAL_S_FIFO)
    elapsed = time.monotonic() - t0
    return (n_samples / elapsed if elapsed > 0 else 0.0), max_fc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", required=True, choices=["polling", "fifo"])
    p.add_argument("--label", required=True, help="e.g. A1_polling, B_fifo, A2_polling")
    p.add_argument("--duration-min", type=float, default=20.0)
    args = p.parse_args()

    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "final_aba_acquisition_test" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    sample_rate_hz = cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / sample_rate_hz
    window_samples = cfg["sensor"]["window_samples"]
    stride_samples = cfg["sensor"]["stride_samples"]
    bus = smbus2.SMBus(1)

    reg_report = register_dump(bus, address)
    svc_report = service_state()

    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], sample_rate_hz)
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])
    import logging
    logger = logging.getLogger(f"aba_{args.label}")
    logger.setLevel(logging.ERROR)
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)

    raw_rows = []       # every raw (fed-rate) sample
    window_rows = []    # every scored window
    resource_rows = []  # periodic system metrics
    i2c_failures = 0
    exceptions = 0
    trigger_records = []

    proc = psutil.Process()
    proc.cpu_percent(interval=None)

    def process_sample(t_now, sample_idx, ax_r, ay_r, az_r, gx_r, gy_r, gz_r):
        nonlocal exceptions
        ax, ay, az, gx, gy, gz = to_physical(ax_r, ay_r, az_r, gx_r, gy_r, gz_r)
        gap_detected, dt = guard.observe(t_now)
        if gap_detected:
            scorer.clear()
            guard.record_window_invalidated()
            if dt is not None and dt >= guard.long_gap_reset_s:
                gravity_filter.reset()
        raw_rows.append({
            "sample_idx": sample_idx, "t_monotonic": t_now, "dt_ms": (dt * 1000.0) if dt is not None else "",
            "acquisition_mode": args.mode,
            "ax_raw": ax_r, "ay_raw": ay_r, "az_raw": az_r, "gx_raw": gx_r, "gy_raw": gy_r, "gz_raw": gz_r,
            "ax_ms2": ax, "ay_ms2": ay, "az_ms2": az, "gx_dps": gx, "gy_dps": gy, "gz_dps": gz,
        })
        try:
            scorer.append([ax, ay, az, gx, gy, gz])
            result = scorer.try_score()
        except Exception:
            exceptions += 1
            return
        if result is not None:
            guard.record_window_scored()
            try:
                is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
            except Exception:
                exceptions += 1
                return
            classifier_crossed = result["crash_prob"] > classifier_t
            recon_crossed = result["recon_error"] > recon_t
            row = {
                "window_idx": len(window_rows), "t_monotonic": t_now,
                "crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                "classifier_crossed": classifier_crossed, "recon_crossed": recon_crossed,
                "or_positive": is_anomaly, "anomaly_streak": policy.anomaly_streak,
                "confirmed_triggered": triggered,
                "windowing_ms": result["windowing_ms"], "inference_ms": result["inference_ms"],
                "total_ms": result["total_ms"], "acquisition_mode": args.mode,
            }
            window_rows.append(row)
            if triggered:
                trigger_records.append(row)

    print(f"[{args.label}] mode={args.mode} duration_min={args.duration_min} starting...", flush=True)
    start = time.monotonic()
    deadline = start + args.duration_min * 60.0
    next_resource_sample = time.monotonic()
    fifo_meta = None

    if args.mode == "polling":
        next_tick = time.monotonic()
        sample_idx = 0
        while time.monotonic() < deadline:
            next_tick += period_s
            try:
                ax_r, ay_r, az_r = struct.unpack(">hhh", bytes(bus.read_i2c_block_data(address, ACCEL_XOUT_H, 6)))
                gx_r, gy_r, gz_r = struct.unpack(">hhh", bytes(bus.read_i2c_block_data(address, GYRO_XOUT_H, 6)))
            except OSError:
                i2c_failures += 1
                sleep_for = next_tick - time.monotonic()
                if sleep_for > 0:
                    time.sleep(sleep_for)
                continue
            now = time.monotonic()
            process_sample(now, sample_idx, ax_r, ay_r, az_r, gx_r, gy_r, gz_r)
            sample_idx += 1

            now2 = time.monotonic()
            if now2 >= next_resource_sample:
                s = common.sample_process_resources(proc)
                s["t_elapsed_s"] = now2 - start
                resource_rows.append(s)
                next_resource_sample = now2 + 1.0

            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                next_tick = time.monotonic()

    else:  # fifo
        configure_fifo(bus, address)
        time.sleep(0.05)
        native_hz, max_fc_calib = calibrate_native_rate(bus, address, CALIBRATION_S)
        decimation_n = max(1, round(native_hz / TARGET_HZ))
        fifo_meta = {"measured_native_hz": native_hz, "decimation_n": decimation_n,
                     "max_fifo_bytes_seen_during_calibration": max_fc_calib}
        print(f"[{args.label}] FIFO calibration: native_hz={native_hz:.1f} decimation_n={decimation_n}", flush=True)

        sample_idx = 0
        decim_counter = 0
        last_drain_anchor_t = time.monotonic()
        n_fifo_overflow_suspected = 0
        while time.monotonic() < deadline:
            try:
                fifo_count = read_fifo_count(bus, address)
            except OSError:
                i2c_failures += 1
                time.sleep(POLL_INTERVAL_S_FIFO)
                continue
            if fifo_count >= BYTES_PER_SAMPLE:
                if fifo_count > 1000:
                    n_fifo_overflow_suspected += 1
                n_bytes = (fifo_count // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
                drain_start_t = time.monotonic()
                try:
                    raw_bytes = drain_fifo_bytes(bus, address, n_bytes)
                except OSError:
                    i2c_failures += 1
                    continue
                n_native = len(raw_bytes) // BYTES_PER_SAMPLE
                span = max(drain_start_t - last_drain_anchor_t, 1e-6)
                for i in range(n_native):
                    # Actual FIFO packet order on the MPU6050/6500 family is accel then gyro. Keeping the
                    # accel bytes in their proper slots avoids falsely interpreting gravity as gyroscope
                    # motion, which was the cause of the earlier FIFO sanity failure.
                    ax_r, ay_r, az_r, gx_r, gy_r, gz_r = struct.unpack(
                        ">hhhhhh", raw_bytes[i * BYTES_PER_SAMPLE:(i + 1) * BYTES_PER_SAMPLE])
                    decim_counter += 1
                    if decim_counter < decimation_n:
                        continue
                    decim_counter = 0
                    frac = (i + 1) / n_native
                    est_t = last_drain_anchor_t + frac * span
                    process_sample(est_t, sample_idx, ax_r, ay_r, az_r, gx_r, gy_r, gz_r)
                    sample_idx += 1
                last_drain_anchor_t = drain_start_t

            now2 = time.monotonic()
            if now2 >= next_resource_sample:
                s = common.sample_process_resources(proc)
                s["t_elapsed_s"] = now2 - start
                resource_rows.append(s)
                next_resource_sample = now2 + 1.0

            time.sleep(POLL_INTERVAL_S_FIFO)

        restore_baseline_registers(bus, address)
        fifo_meta["n_fifo_overflow_suspected"] = n_fifo_overflow_suspected

    actual_duration_s = time.monotonic() - start
    print(f"[{args.label}] done: {len(raw_rows)} samples, {len(window_rows)} windows, "
          f"{len(trigger_records)} triggers, i2c_failures={i2c_failures}, exceptions={exceptions}", flush=True)

    # --- raw_sensor.csv ---
    with open(out_dir / "raw_sensor.csv", "w", newline="") as f:
        if raw_rows:
            w = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()))
            w.writeheader()
            w.writerows(raw_rows)

    # --- window_scores.csv ---
    with open(out_dir / "window_scores.csv", "w", newline="") as f:
        if window_rows:
            w = csv.DictWriter(f, fieldnames=list(window_rows[0].keys()))
            w.writeheader()
            w.writerows(window_rows)

    # --- system_metrics.csv ---
    with open(out_dir / "system_metrics.csv", "w", newline="") as f:
        if resource_rows:
            w = csv.DictWriter(f, fieldnames=list(resource_rows[0].keys()))
            w.writeheader()
            w.writerows(resource_rows)

    # --- timing/stream/latency metrics ---
    dt_ms_arr = np.asarray([r["dt_ms"] for r in raw_rows if r["dt_ms"] != ""], dtype=np.float64)
    guard_snap = guard.snapshot()
    nominal_decision_positions = max(0, (len(raw_rows) - window_samples) // stride_samples + 1) if raw_rows else 0
    v_t = (guard_snap["windows_scored"] / (guard_snap["windows_scored"] + guard_snap["windows_invalidated"])
           if (guard_snap["windows_scored"] + guard_snap["windows_invalidated"]) else None)
    c_d = (guard_snap["windows_scored"] / nominal_decision_positions) if nominal_decision_positions else None
    lat_total = np.asarray([w["total_ms"] for w in window_rows], dtype=np.float64) if window_rows else np.asarray([])

    timing_row = {
        "label": args.label, "acquisition_mode": args.mode,
        "duration_s": actual_duration_s, "n_raw_samples": len(raw_rows),
        "achieved_sample_rate_hz": (len(raw_rows) / actual_duration_s) if actual_duration_s else None,
        "nominal_decision_positions": nominal_decision_positions,
        "scored_windows": guard_snap["windows_scored"], "invalidated_windows": guard_snap["windows_invalidated"],
        "never_formed_or_suppressed_positions": max(0, nominal_decision_positions - guard_snap["windows_scored"]),
        "V_T": v_t, "C_D": c_d,
        "timing_gaps": guard_snap["timing_gaps"], "gaps_per_min": guard_snap["timing_gaps"] / (actual_duration_s / 60.0) if actual_duration_s else None,
        "dt_lt_10ms_count": guard_snap["duplicate_or_too_fast_samples"],
        "too_fast_per_min": guard_snap["duplicate_or_too_fast_samples"] / (actual_duration_s / 60.0) if actual_duration_s else None,
        "dropped_equivalent_samples": guard_snap["suspected_dropped_samples"],
        "dropped_equivalent_per_min": guard_snap["suspected_dropped_samples"] / (actual_duration_s / 60.0) if actual_duration_s else None,
        "dt_mean_ms": float(dt_ms_arr.mean()) if len(dt_ms_arr) else None,
        "dt_p50_ms": float(np.percentile(dt_ms_arr, 50)) if len(dt_ms_arr) else None,
        "dt_p95_ms": float(np.percentile(dt_ms_arr, 95)) if len(dt_ms_arr) else None,
        "dt_p99_ms": float(np.percentile(dt_ms_arr, 99)) if len(dt_ms_arr) else None,
        "dt_p999_ms": float(np.percentile(dt_ms_arr, 99.9)) if len(dt_ms_arr) else None,
        "dt_max_ms": float(dt_ms_arr.max()) if len(dt_ms_arr) else None,
        "i2c_failures": i2c_failures, "reconnects": 0, "exceptions": exceptions,
        "latency_mean_ms": float(lat_total.mean()) if len(lat_total) else None,
        "latency_p50_ms": float(np.percentile(lat_total, 50)) if len(lat_total) else None,
        "latency_p95_ms": float(np.percentile(lat_total, 95)) if len(lat_total) else None,
        "latency_p99_ms": float(np.percentile(lat_total, 99)) if len(lat_total) else None,
        "latency_p999_ms": float(np.percentile(lat_total, 99.9)) if len(lat_total) else None,
        "latency_max_ms": float(lat_total.max()) if len(lat_total) else None,
        "latency_count_gt_20ms": int((lat_total > 20).sum()) if len(lat_total) else 0,
        "latency_count_gt_50ms": int((lat_total > 50).sum()) if len(lat_total) else 0,
        "latency_count_gt_100ms": int((lat_total > 100).sum()) if len(lat_total) else 0,
        "latency_count_gt_300ms": int((lat_total > 300).sum()) if len(lat_total) else 0,
    }
    with open(out_dir / "timing.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(timing_row.keys()))
        w.writeheader()
        w.writerow(timing_row)

    # --- model-score / trigger / physical summaries ---
    crash_probs = np.asarray([w["crash_prob"] for w in window_rows], dtype=np.float64) if window_rows else np.asarray([])
    recon_errors = np.asarray([w["recon_error"] for w in window_rows], dtype=np.float64) if window_rows else np.asarray([])
    theta_r = recon_t
    bands = {
        "r_lt_8": int((recon_errors < 8).sum()),
        "8_le_r_lt_9": int(((recon_errors >= 8) & (recon_errors < 9)).sum()),
        "9_le_r_lt_10": int(((recon_errors >= 9) & (recon_errors < 10)).sum()),
        "10_le_r_lt_theta_r": int(((recon_errors >= 10) & (recon_errors < theta_r)).sum()),
        "theta_r_le_r_lt_11.5": int(((recon_errors >= theta_r) & (recon_errors < 11.5)).sum()),
        "11.5_le_r_lt_12.5": int(((recon_errors >= 11.5) & (recon_errors < 12.5)).sum()),
        "r_ge_12.5": int((recon_errors >= 12.5).sum()),
    } if len(recon_errors) else {}

    classifier_only = sum(1 for w in window_rows if w["classifier_crossed"] and not w["recon_crossed"])
    recon_only = sum(1 for w in window_rows if w["recon_crossed"] and not w["classifier_crossed"])
    both_pos = sum(1 for w in window_rows if w["classifier_crossed"] and w["recon_crossed"])
    neither_pos = sum(1 for w in window_rows if not w["classifier_crossed"] and not w["recon_crossed"])
    or_positive_seq = [1 if w["or_positive"] else 0 for w in window_rows]
    longest_run, cur_run = 0, 0
    n_2seq, n_3seq = 0, 0
    for v in or_positive_seq:
        cur_run = cur_run + 1 if v else 0
        longest_run = max(longest_run, cur_run)
        if cur_run == 2:
            n_2seq += 1
        if cur_run == 3:
            n_3seq += 1

    def axis_stats(vals):
        arr = np.asarray(vals, dtype=np.float64)
        if len(arr) == 0:
            return {}
        return {"min": float(arr.min()), "max": float(arr.max()), "mean": float(arr.mean()),
                "std": float(arr.std()), "rms": float(np.sqrt(np.mean(arr ** 2))), "abs_max": float(np.abs(arr).max())}

    physical = {}
    if raw_rows:
        for axis in ("ax_ms2", "ay_ms2", "az_ms2", "gx_dps", "gy_dps", "gz_dps"):
            physical[axis] = axis_stats([r[axis] for r in raw_rows])
        accel_mag = np.sqrt(np.asarray([r["ax_ms2"] for r in raw_rows]) ** 2 +
                             np.asarray([r["ay_ms2"] for r in raw_rows]) ** 2 +
                             np.asarray([r["az_ms2"] for r in raw_rows]) ** 2)
        gyro_mag = np.sqrt(np.asarray([r["gx_dps"] for r in raw_rows]) ** 2 +
                            np.asarray([r["gy_dps"] for r in raw_rows]) ** 2 +
                            np.asarray([r["gz_dps"] for r in raw_rows]) ** 2)
        physical["accel_magnitude_ms2"] = {"mean": float(accel_mag.mean()), "std": float(accel_mag.std()), "max": float(accel_mag.max())}
        physical["gyro_magnitude_dps"] = {"mean": float(gyro_mag.mean()), "std": float(gyro_mag.std()), "max": float(gyro_mag.max())}

    throttle = common.read_throttled() if hasattr(common, "read_throttled") else None

    summary = {
        "label": args.label, "acquisition_mode": args.mode,
        "context": "HelmX_FINAL_Pi_ABA_Acquisition_Test.txt condition run",
        "metadata": {
            "date": time.strftime("%Y-%m-%d"), "start_epoch": time.time() - actual_duration_s,
            "duration_s": actual_duration_s, "device": common.device_info(),
            "register_dump": reg_report, "service_state": svc_report, "fifo_meta": fifo_meta,
        },
        "model_score_analysis": {
            "classifier_prob": {
                "min": float(crash_probs.min()) if len(crash_probs) else None,
                "mean": float(crash_probs.mean()) if len(crash_probs) else None,
                "median": float(np.median(crash_probs)) if len(crash_probs) else None,
                "p95": float(np.percentile(crash_probs, 95)) if len(crash_probs) else None,
                "p99": float(np.percentile(crash_probs, 99)) if len(crash_probs) else None,
                "max": float(crash_probs.max()) if len(crash_probs) else None,
                "n_above_threshold": classifier_only + both_pos,
                "threshold": classifier_t,
            },
            "reconstruction_error": {
                "min": float(recon_errors.min()) if len(recon_errors) else None,
                "mean": float(recon_errors.mean()) if len(recon_errors) else None,
                "median": float(np.median(recon_errors)) if len(recon_errors) else None,
                "p90": float(np.percentile(recon_errors, 90)) if len(recon_errors) else None,
                "p95": float(np.percentile(recon_errors, 95)) if len(recon_errors) else None,
                "p99": float(np.percentile(recon_errors, 99)) if len(recon_errors) else None,
                "p999": float(np.percentile(recon_errors, 99.9)) if len(recon_errors) else None,
                "max": float(recon_errors.max()) if len(recon_errors) else None,
                "n_above_threshold": recon_only + both_pos,
                "threshold": theta_r,
                "bands_around_threshold": bands,
            },
        },
        "trigger_analysis": {
            "classifier_only_positive_windows": classifier_only, "reconstruction_only_positive_windows": recon_only,
            "both_positive_windows": both_pos, "neither_positive_windows": neither_pos,
            "total_or_positive_windows": classifier_only + recon_only + both_pos,
            "longest_consecutive_or_positive_run": longest_run,
            "n_2window_sequences": n_2seq, "n_3window_confirmed_triggers": n_3seq,
            "total_confirmed_triggers": len(trigger_records),
            "trigger_events": trigger_records,
        },
        "physical_sensor_summary": physical,
        "system_state": {
            "resources_summary": {
                "process_cpu_percent": common.summarize_series(resource_rows, "process_cpu_percent"),
                "process_rss_mb": common.summarize_series(resource_rows, "process_rss_mb"),
                "system_cpu_percent": common.summarize_series(resource_rows, "system_cpu_percent"),
                "temperature_c": common.summarize_series(resource_rows, "temperature_c"),
            },
            "throttling_status": throttle,
        },
        "timing_and_latency": timing_row,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=common._json_default))

    txt = [
        f"HelmX ABA Acquisition Test -- Condition {args.label} ({args.mode})",
        "=" * 70,
        f"Duration: {actual_duration_s:.1f}s ({actual_duration_s/60:.2f} min), "
        f"{len(raw_rows)} samples, {len(window_rows)} windows scored, achieved "
        f"{timing_row['achieved_sample_rate_hz']:.2f}Hz" if raw_rows else "No samples captured.",
        "",
        f"V_T={v_t}, C_D={c_d}, timing_gaps={guard_snap['timing_gaps']}, i2c_failures={i2c_failures}, exceptions={exceptions}",
        f"dt p50/p99/max (ms): {timing_row['dt_p50_ms']}/{timing_row['dt_p99_ms']}/{timing_row['dt_max_ms']}",
        f"processing latency p50/p99/max (ms): {timing_row['latency_p50_ms']}/{timing_row['latency_p99_ms']}/{timing_row['latency_max_ms']}",
        "",
        f"Classifier prob: max={summary['model_score_analysis']['classifier_prob']['max']}, "
        f"n_above_threshold={summary['model_score_analysis']['classifier_prob']['n_above_threshold']}",
        f"Reconstruction error: median={summary['model_score_analysis']['reconstruction_error']['median']}, "
        f"p99={summary['model_score_analysis']['reconstruction_error']['p99']}, "
        f"max={summary['model_score_analysis']['reconstruction_error']['max']}, "
        f"n_above_threshold={summary['model_score_analysis']['reconstruction_error']['n_above_threshold']}",
        f"Bands around threshold ({theta_r:.4f}): {json.dumps(bands)}",
        "",
        f"Trigger analysis: classifier_only={classifier_only}, recon_only={recon_only}, both={both_pos}, "
        f"neither={neither_pos}, total_or_positive={classifier_only+recon_only+both_pos}, "
        f"longest_run={longest_run}, confirmed_triggers={len(trigger_records)}",
    ]
    if trigger_records:
        txt.append("Trigger events:")
        for t in trigger_records:
            txt.append(f"  window {t['window_idx']} t={t['t_monotonic']:.1f}s crash_prob={t['crash_prob']:.4f} recon_error={t['recon_error']:.4f}")
    (out_dir / "summary.txt").write_text("\n".join(txt) + "\n")

    print(f"[{args.label}] Wrote outputs to {out_dir}")


if __name__ == "__main__":
    main()
