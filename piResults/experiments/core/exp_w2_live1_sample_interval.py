"""Checklist 4.2 + Deployment-Weaknesses-plan W2-LIVE-1 -- live raw MPU6050
sample-interval characterization.

Timestamps every real MPU6050 read (mpu6050-raspberrypi, address from
deploy/config.yaml) for --duration-min minutes, back-to-back as fast as the
I2C bus allows (no artificial pacing -- this measures the sensor/library's
own achievable rate and jitter, not the deployed 50Hz-paced loop; the paced
in-pipeline behavior is covered separately by W2-LIVE-2). Records raw accel/
gyro values for a plausibility check, every read's wall-clock interval, and
any read-time exceptions (I2C errors).

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_w2_live1_sample_interval.py --duration-min 12
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import common

try:
    from mpu6050 import mpu6050
except ImportError:
    mpu6050 = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-min", type=float, default=12.0)
    args = parser.parse_args()

    if mpu6050 is None:
        print("mpu6050 package not installed -- pip install mpu6050-raspberrypi")
        sys.exit(1)

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    sensor = mpu6050(address)
    print(f"Connected to MPU6050 at {hex(address)}. Sampling back-to-back for {args.duration_min} min...")

    intervals_s = []
    errors = []
    samples = []
    last_t = None
    deadline = time.monotonic() + args.duration_min * 60.0
    read_count = 0

    while time.monotonic() < deadline:
        now = time.monotonic()
        try:
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
        except OSError as e:
            errors.append({"t": time.time(), "error": str(e)})
            continue
        read_count += 1
        if last_t is not None:
            intervals_s.append(now - last_t)
        last_t = now
        if read_count <= 2000:  # keep the raw sample list bounded; stats use all reads
            samples.append({
                "t": time.time(),
                "ax": accel["x"], "ay": accel["y"], "az": accel["z"],
                "gx": gyro["x"], "gy": gyro["y"], "gz": gyro["z"],
            })

    intervals_ms = np.asarray(intervals_s, dtype=np.float64) * 1000.0
    achieved_hz = read_count / (args.duration_min * 60.0)

    # A "gap" here is any interval that's a clear multiple of the mean interval --
    # conservative, descriptive characterization (not the deployed guard's
    # threshold, which W2-LIVE-1 exists specifically to help calibrate).
    mean_interval_ms = float(intervals_ms.mean()) if len(intervals_ms) else None
    gap_threshold_ms = mean_interval_ms * 3 if mean_interval_ms else None
    gaps = intervals_ms[intervals_ms > gap_threshold_ms] if gap_threshold_ms else np.array([])

    accel_mag = np.array([
        (s["ax"] ** 2 + s["ay"] ** 2 + s["az"] ** 2) ** 0.5 for s in samples
    ])
    gyro_mag = np.array([
        (s["gx"] ** 2 + s["gy"] ** 2 + s["gz"] ** 2) ** 0.5 for s in samples
    ])

    report = {
        "device": common.device_info(),
        "i2c_address": hex(address),
        "requested_duration_min": args.duration_min,
        "actual_duration_s": args.duration_min * 60.0,
        "total_reads": read_count,
        "achieved_hz": achieved_hz,
        "i2c_read_failures": len(errors),
        "errors": errors[:50],
        "interval_stats_ms": {
            "n": len(intervals_ms),
            "mean_ms": mean_interval_ms,
            "p50_ms": float(np.percentile(intervals_ms, 50)) if len(intervals_ms) else None,
            "p95_ms": float(np.percentile(intervals_ms, 95)) if len(intervals_ms) else None,
            "p99_ms": float(np.percentile(intervals_ms, 99)) if len(intervals_ms) else None,
            "max_ms": float(intervals_ms.max()) if len(intervals_ms) else None,
            "min_ms": float(intervals_ms.min()) if len(intervals_ms) else None,
            "std_ms": float(intervals_ms.std()) if len(intervals_ms) else None,
        },
        "gap_threshold_ms_3x_mean": gap_threshold_ms,
        "num_gaps_over_3x_mean": int(len(gaps)),
        "estimated_dropped_samples_over_3x_mean": int(sum(round(g / mean_interval_ms) - 1 for g in gaps)) if mean_interval_ms else None,
        "plausibility": {
            "accel_magnitude_mean": float(accel_mag.mean()) if len(accel_mag) else None,
            "accel_magnitude_std": float(accel_mag.std()) if len(accel_mag) else None,
            "accel_magnitude_min": float(accel_mag.min()) if len(accel_mag) else None,
            "accel_magnitude_max": float(accel_mag.max()) if len(accel_mag) else None,
            "gyro_magnitude_mean": float(gyro_mag.mean()) if len(gyro_mag) else None,
            "gyro_magnitude_max": float(gyro_mag.max()) if len(gyro_mag) else None,
            "note": "expect accel_magnitude near 9.81 (stationary, gravity only); first 2000 reads sampled for this stat",
        },
        "raw_samples_capped_2000": samples,
    }

    print("\n=== Summary ===")
    print(f"Total reads: {read_count}  Achieved Hz: {achieved_hz:.2f}  I2C failures: {len(errors)}")
    print(f"Interval mean={mean_interval_ms:.2f}ms p50={report['interval_stats_ms']['p50_ms']:.2f}ms "
          f"p95={report['interval_stats_ms']['p95_ms']:.2f}ms p99={report['interval_stats_ms']['p99_ms']:.2f}ms "
          f"max={report['interval_stats_ms']['max_ms']:.2f}ms")
    print(f"Gaps (>3x mean): {len(gaps)}  Est. dropped samples: {report['estimated_dropped_samples_over_3x_mean']}")
    print(f"Accel magnitude: mean={report['plausibility']['accel_magnitude_mean']:.3f} "
          f"(expect ~9.81 if stationary)")

    common.save_json(report, "w2_live1_sample_interval")


if __name__ == "__main__":
    main()
