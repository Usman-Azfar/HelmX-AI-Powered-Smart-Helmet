"""HelmX_FInal_Pi_REqwuirements.md Section C1 -- mounted stationary noise test.

Reads RAW int16 registers directly via smbus2 (not the mpu6050 library's
already-converted get_accel_data()/get_gyro_data(), so both raw and converted
values are available and the conversion factor is explicit and auditable),
back-to-back for --duration-min minutes with the helmet stationary. Full
per-axis stats (no sample cap -- 10 min @ ~50 reads/s is ~30k samples, trivial
to hold in memory).

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_c1_stationary_noise.py --duration-min 10
"""
import argparse
import csv
import struct
import sys
import time
from pathlib import Path

import numpy as np
import smbus2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

ACCEL_XOUT_H = 0x3B  # accel: 6 bytes from here, gyro: 6 bytes from 0x43
GYRO_XOUT_H = 0x43
ACCEL_SENS_LSB_PER_G = 16384.0    # FS_SEL=0 / AFS_SEL=0, confirmed by B1 register dump on this device
GYRO_SENS_LSB_PER_DEG_S = 131.0   # FS_SEL=0, confirmed by B1 register dump on this device
G_TO_MS2 = 9.80665


def read_raw_block(bus, address, reg, n_bytes=6):
    data = bus.read_i2c_block_data(address, reg, n_bytes)
    return struct.unpack(">hhh", bytes(data))


def stats_block(arr, label):
    arr = np.asarray(arr, dtype=np.float64)
    return {
        f"{label}_n": int(len(arr)), f"{label}_mean": float(arr.mean()), f"{label}_std": float(arr.std()),
        f"{label}_rms": float(np.sqrt(np.mean(arr ** 2))), f"{label}_min": float(arr.min()),
        f"{label}_max": float(arr.max()), f"{label}_peak_to_peak": float(arr.max() - arr.min()),
        f"{label}_p50": float(np.percentile(arr, 50)), f"{label}_p95": float(np.percentile(arr, 95)),
        f"{label}_p99": float(np.percentile(arr, 99)), f"{label}_abs_max": float(np.abs(arr).max()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-min", type=float, default=10.0)
    args = parser.parse_args()

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    bus = smbus2.SMBus(1)

    print(f"Connected to MPU6050 at {hex(address)}. Stationary capture for {args.duration_min} min "
          f"(helmet must be placed stationary, no intentional movement)...")

    rows = []
    errors = []
    dt_list = []
    too_fast = 0
    timing_gaps = 0
    last_t = None
    max_dt_s = 0.030  # same threshold convention as deploy/config.yaml: sensor.timing_guard.max_dt_s
    min_dt_s = 0.010

    deadline = time.monotonic() + args.duration_min * 60.0
    temps_raw = []
    while time.monotonic() < deadline:
        now = time.monotonic()
        try:
            ax_r, ay_r, az_r = read_raw_block(bus, address, ACCEL_XOUT_H)
            gx_r, gy_r, gz_r = read_raw_block(bus, address, GYRO_XOUT_H)
            temp_raw = bus.read_i2c_block_data(address, 0x41, 2)
            temp_raw = struct.unpack(">h", bytes(temp_raw))[0]
        except OSError as e:
            errors.append({"t": time.time(), "error": str(e)})
            continue

        if last_t is not None:
            dt = now - last_t
            dt_list.append(dt)
            if dt > max_dt_s:
                timing_gaps += 1
            elif dt < min_dt_s:
                too_fast += 1
        last_t = now

        temps_raw.append(temp_raw)
        rows.append({
            "t": time.time(),
            "ax_raw": ax_r, "ay_raw": ay_r, "az_raw": az_r,
            "gx_raw": gx_r, "gy_raw": gy_r, "gz_raw": gz_r,
            "ax_g": ax_r / ACCEL_SENS_LSB_PER_G, "ay_g": ay_r / ACCEL_SENS_LSB_PER_G, "az_g": az_r / ACCEL_SENS_LSB_PER_G,
            "gx_dps": gx_r / GYRO_SENS_LSB_PER_DEG_S, "gy_dps": gy_r / GYRO_SENS_LSB_PER_DEG_S, "gz_dps": gz_r / GYRO_SENS_LSB_PER_DEG_S,
        })

    ax = np.array([r["ax_g"] for r in rows]) * G_TO_MS2
    ay = np.array([r["ay_g"] for r in rows]) * G_TO_MS2
    az = np.array([r["az_g"] for r in rows]) * G_TO_MS2
    gx = np.array([r["gx_dps"] for r in rows])
    gy = np.array([r["gy_dps"] for r in rows])
    gz = np.array([r["gz_dps"] for r in rows])
    ax_raw = np.array([r["ax_raw"] for r in rows])
    ay_raw = np.array([r["ay_raw"] for r in rows])
    az_raw = np.array([r["az_raw"] for r in rows])
    gx_raw = np.array([r["gx_raw"] for r in rows])
    gy_raw = np.array([r["gy_raw"] for r in rows])
    gz_raw = np.array([r["gz_raw"] for r in rows])

    accel_mag = np.sqrt(ax ** 2 + ay ** 2 + az ** 2)
    gyro_mag = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)
    temp_c = np.array(temps_raw) / 340.0 + 36.53  # MPU6050 datasheet conversion

    dt_ms = np.asarray(dt_list) * 1000.0

    summary = {
        "device": common.device_info(),
        "duration_requested_min": args.duration_min,
        "n_samples": len(rows),
        "i2c_failures": len(errors),
        "errors_sample": errors[:20],
        "timing_gap_count_gt_30ms": timing_gaps,
        "too_fast_count_lt_10ms": too_fast,
        "sample_interval_ms": {
            "mean": float(dt_ms.mean()) if len(dt_ms) else None,
            "p50": float(np.percentile(dt_ms, 50)) if len(dt_ms) else None,
            "p95": float(np.percentile(dt_ms, 95)) if len(dt_ms) else None,
            "p99": float(np.percentile(dt_ms, 99)) if len(dt_ms) else None,
            "max": float(dt_ms.max()) if len(dt_ms) else None,
        },
        "converted_units": {"accel": "m/s^2 (raw/16384 * 9.80665)", "gyro": "deg/s (raw/131.0)"},
        "per_axis_converted": {
            **stats_block(ax, "ax_ms2"), **stats_block(ay, "ay_ms2"), **stats_block(az, "az_ms2"),
            **stats_block(gx, "gx_dps"), **stats_block(gy, "gy_dps"), **stats_block(gz, "gz_dps"),
        },
        "per_axis_raw_int16": {
            **stats_block(ax_raw, "ax_raw"), **stats_block(ay_raw, "ay_raw"), **stats_block(az_raw, "az_raw"),
            **stats_block(gx_raw, "gx_raw"), **stats_block(gy_raw, "gy_raw"), **stats_block(gz_raw, "gz_raw"),
        },
        "accel_magnitude_ms2": {"mean": float(accel_mag.mean()), "std": float(accel_mag.std()),
                                 "note": "expect ~9.81 (stationary, gravity only)"},
        "gyro_magnitude_dps": {"mean": float(gyro_mag.mean()), "std": float(gyro_mag.std())},
        "stationary_die_temperature_c": {"mean": float(temp_c.mean()), "min": float(temp_c.min()), "max": float(temp_c.max())},
    }

    print("\n=== Summary ===")
    print(f"n={len(rows)} samples, {len(errors)} I2C failures, {timing_gaps} gaps>30ms, {too_fast} too-fast<10ms")
    print(f"accel magnitude mean={summary['accel_magnitude_ms2']['mean']:.4f} m/s^2 (expect ~9.81)")
    print(f"gyro magnitude mean={summary['gyro_magnitude_dps']['mean']:.4f} deg/s (expect ~0)")

    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "stationary_noise"
    out_dir.mkdir(parents=True, exist_ok=True)
    import json
    (out_dir / "stationary_noise_summary.json").write_text(json.dumps(summary, indent=2))

    with open(out_dir / "stationary_noise_summary.txt", "w") as f:
        f.write(json.dumps(summary, indent=2))

    with open(out_dir / "stationary_noise_raw.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nWrote {out_dir}")


if __name__ == "__main__":
    main()
