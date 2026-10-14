"""HelmX_FInal_Pi_REqwuirements.md Section D1 -- raw inter-sample interval
characterization under one named software-load condition. Reads raw registers
back-to-back (same smbus2 approach as pi_val_c1_stationary_noise.py) for
--duration-min minutes and reports the full D1 metric set using the SAME
30ms/10ms thresholds as deploy/config.yaml: sensor.timing_guard (not an
adaptive 3x-mean heuristic), so these numbers are directly comparable to the
deployed guard's own behavior.

Run once per condition, with --condition labeling the output file:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_d1_timing_loads.py \\
        --duration-min 12 --condition reduced_background
"""
import argparse
import csv
import json
import struct
import sys
import time
from pathlib import Path

import numpy as np
import smbus2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-min", type=float, default=12.0)
    parser.add_argument("--condition", required=True,
                         help="e.g. minimal_background, normal_helmx_workload, heavier_interactive_workload")
    args = parser.parse_args()

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    max_dt_s = cfg["sensor"]["timing_guard"]["max_dt_s"]
    min_dt_s = cfg["sensor"]["timing_guard"]["min_dt_s"]
    bus = smbus2.SMBus(1)

    print(f"Condition '{args.condition}': raw back-to-back reads for {args.duration_min} min "
          f"(max_dt_s={max_dt_s}, min_dt_s={min_dt_s}, matching deployed guard thresholds)...")

    dt_list = []
    t_list = []
    errors = []
    exceptions = []
    read_count = 0
    last_t = None
    deadline = time.monotonic() + args.duration_min * 60.0

    while time.monotonic() < deadline:
        now = time.monotonic()
        try:
            bus.read_i2c_block_data(address, ACCEL_XOUT_H, 6)
            bus.read_i2c_block_data(address, GYRO_XOUT_H, 6)
        except OSError as e:
            errors.append({"t": time.time(), "error": str(e)})
            continue
        except Exception as e:
            exceptions.append({"t": time.time(), "error": str(e)})
            continue
        read_count += 1
        if last_t is not None:
            dt_list.append(now - last_t)
            t_list.append(now)
        last_t = now

    dt_ms = np.asarray(dt_list, dtype=np.float64) * 1000.0
    achieved_hz = read_count / (args.duration_min * 60.0)
    gap_mask = dt_ms > (max_dt_s * 1000.0)
    fast_mask = dt_ms < (min_dt_s * 1000.0)
    period_ms = (1.0 / cfg["sensor"]["sample_rate_hz"]) * 1000.0
    dropped_equiv = int(sum(round(d / period_ms) - 1 for d in dt_ms[gap_mask])) if gap_mask.any() else 0

    report = {
        "device": common.device_info(),
        "condition": args.condition,
        "duration_requested_min": args.duration_min,
        "total_samples": read_count,
        "achieved_sample_rate_hz": achieved_hz,
        "mean_dt_ms": float(dt_ms.mean()) if len(dt_ms) else None,
        "p50_dt_ms": float(np.percentile(dt_ms, 50)) if len(dt_ms) else None,
        "p95_dt_ms": float(np.percentile(dt_ms, 95)) if len(dt_ms) else None,
        "p99_dt_ms": float(np.percentile(dt_ms, 99)) if len(dt_ms) else None,
        "p99_9_dt_ms": float(np.percentile(dt_ms, 99.9)) if len(dt_ms) >= 1000 else None,
        "max_dt_ms": float(dt_ms.max()) if len(dt_ms) else None,
        "gap_threshold_ms": max_dt_s * 1000.0,
        "gap_count_gt_threshold": int(gap_mask.sum()),
        "gaps_per_min": float(gap_mask.sum() / args.duration_min),
        "too_fast_threshold_ms": min_dt_s * 1000.0,
        "too_fast_count": int(fast_mask.sum()),
        "too_fast_per_min": float(fast_mask.sum() / args.duration_min),
        "estimated_dropped_equivalent_samples": dropped_equiv,
        "dropped_equivalent_per_min": float(dropped_equiv / args.duration_min),
        "i2c_failures": len(errors),
        "reconnects": 0,
        "exceptions": len(exceptions),
        "errors_sample": errors[:20],
    }

    print("\n=== Summary ===")
    print(f"n={read_count} achieved_hz={achieved_hz:.2f} mean_dt={report['mean_dt_ms']:.2f}ms "
          f"p99={report['p99_dt_ms']:.2f}ms max={report['max_dt_ms']:.2f}ms "
          f"gaps={report['gap_count_gt_threshold']} too_fast={report['too_fast_count']} "
          f"i2c_failures={len(errors)}")

    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "timing_loads"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.condition}_summary.json").write_text(json.dumps(report, indent=2))
    with open(out_dir / f"{args.condition}_dt.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_monotonic", "dt_ms"])
        for t, dt in zip(t_list, dt_ms):
            w.writerow([t, dt])

    print(f"Wrote {out_dir / (args.condition + '_summary.json')} and _dt.csv")


if __name__ == "__main__":
    main()
