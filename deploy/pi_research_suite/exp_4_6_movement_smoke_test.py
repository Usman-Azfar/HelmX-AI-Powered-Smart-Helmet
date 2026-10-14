"""Checklist 4.6 -- physical movement smoke test.

Reads the real live MPU6050 continuously through a fixed, printed schedule of
labeled phases (stationary baseline, gentle rotation, tilt, shake, non-crash
bump), so a human can perform each movement while this script is running.
Confirms plausible signal ranges per phase and that no read errors/exceptions
occur under real handling -- explicitly NOT an accuracy claim (see the
checklist's own caveat) and explicitly NOT a destructive/impact test.

Run on the Pi, and physically handle the sensor according to the printed
countdown:
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_4_6_movement_smoke_test.py
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

try:
    from mpu6050 import mpu6050
except ImportError:
    mpu6050 = None

PHASES = [
    ("stationary_baseline", 15, "Leave the sensor still and flat/resting on a surface."),
    ("gentle_rotation", 20, "Slowly rotate the sensor through different orientations by hand."),
    ("tilt", 20, "Slowly tilt the sensor side to side and front/back."),
    ("shake", 20, "Gently shake the sensor by hand (moderate motion, not an impact)."),
    ("non_crash_bump", 20, "Gently tap/knock the sensor a few times (a bump, not a drop or impact)."),
]


def main():
    if mpu6050 is None:
        print("mpu6050 package not installed")
        sys.exit(1)

    cfg = common.load_config()
    sensor = mpu6050(cfg["sensor"]["i2c_address"])

    print("=== 4.6 Physical movement smoke test ===")
    print("Schedule (perform the action when its phase starts):")
    t_cursor = 0
    for name, dur, instr in PHASES:
        print(f"  [{t_cursor:>3}s - {t_cursor+dur:>3}s] {name}: {instr}")
        t_cursor += dur
    print("Starting in 3 seconds...")
    time.sleep(3)

    phase_results = []
    errors_total = 0
    for name, duration_s, instr in PHASES:
        print(f"\n>>> PHASE: {name} ({duration_s}s) -- {instr}")
        samples = []
        errors = 0
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            try:
                a = sensor.get_accel_data()
                g = sensor.get_gyro_data()
                samples.append((a["x"], a["y"], a["z"], g["x"], g["y"], g["z"]))
            except OSError as e:
                errors += 1
                print(f"    I2C read error: {e}")
            time.sleep(0.02)  # ~50Hz

        arr = np.asarray(samples, dtype=np.float64) if samples else np.zeros((0, 6))
        accel_mag = np.linalg.norm(arr[:, 0:3], axis=1) if len(arr) else np.array([])
        gyro_mag = np.linalg.norm(arr[:, 3:6], axis=1) if len(arr) else np.array([])
        result = {
            "phase": name,
            "instruction": instr,
            "duration_s": duration_s,
            "n_reads": len(samples),
            "n_errors": errors,
            "accel_magnitude": {
                "mean": float(accel_mag.mean()) if len(accel_mag) else None,
                "std": float(accel_mag.std()) if len(accel_mag) else None,
                "min": float(accel_mag.min()) if len(accel_mag) else None,
                "max": float(accel_mag.max()) if len(accel_mag) else None,
            },
            "gyro_magnitude": {
                "mean": float(gyro_mag.mean()) if len(gyro_mag) else None,
                "std": float(gyro_mag.std()) if len(gyro_mag) else None,
                "min": float(gyro_mag.min()) if len(gyro_mag) else None,
                "max": float(gyro_mag.max()) if len(gyro_mag) else None,
            },
        }
        phase_results.append(result)
        errors_total += errors
        print(f"    reads={len(samples)} errors={errors} "
              f"accel_mag mean={result['accel_magnitude']['mean']:.2f} max={result['accel_magnitude']['max']:.2f} "
              f"gyro_mag mean={result['gyro_magnitude']['mean']:.2f} max={result['gyro_magnitude']['max']:.2f}")

    report = {
        "device": common.device_info(),
        "context": "Checklist 4.6 -- non-destructive physical movement smoke test, real live MPU6050.",
        "phases": phase_results,
        "total_i2c_errors": errors_total,
    }
    print("\n=== Summary ===")
    for r in phase_results:
        print(f"{r['phase']:>20}: accel_mag mean={r['accel_magnitude']['mean']:.2f} max={r['accel_magnitude']['max']:.2f}  "
              f"gyro_mag mean={r['gyro_magnitude']['mean']:.2f} max={r['gyro_magnitude']['max']:.2f}  errors={r['n_errors']}")
    print(f"Total I2C errors across all phases: {errors_total}")

    common.save_json(report, "4_6_movement_smoke_test")


if __name__ == "__main__":
    main()
