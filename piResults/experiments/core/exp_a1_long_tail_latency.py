"""Checklist item 3.5 -- CPU jitter / latency-tail characterization.

Motivated directly by 3.2 (repeated A1) surfacing a 286.8ms single-inference
outlier -- a much larger sample gives real statistical power on how often
large outliers actually occur, rather than relying on 5x1000=5000 samples.

Run on the Pi:
    python deploy/pi_research_suite/exp_a1_long_tail_latency.py --n 50000
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

import common


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=50000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    cfg = common.load_config()
    model_path = common.ROOT / cfg["model_path"]
    rng = np.random.default_rng(args.seed)

    interpreter = tflite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    runner = interpreter.get_signature_runner()
    dummy_seq = np.zeros((1, 60, 6), dtype=np.float32)
    dummy_aux = np.zeros((1, 7), dtype=np.float32)
    runner(seq=dummy_seq, aux=dummy_aux)

    print(f"Running {args.n} inferences, recording every latency...")
    times_ms = np.empty(args.n, dtype=np.float64)
    for i in range(args.n):
        seq = rng.normal(0, 1, size=(1, 60, 6)).astype(np.float32)
        aux = rng.normal(0, 1, size=(1, 7)).astype(np.float32)
        t0 = time.perf_counter()
        runner(seq=seq, aux=aux)
        times_ms[i] = (time.perf_counter() - t0) * 1000.0

    thresholds_ms = [2, 5, 10, 25, 50, 100, 300]
    stride_budget_ms = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"] * 1000.0
    event_counts = {f">{t}ms": int((times_ms > t).sum()) for t in thresholds_ms}

    report = {
        "device": common.device_info(),
        "n": args.n,
        "mean_ms": float(times_ms.mean()),
        "median_ms": float(np.median(times_ms)),
        "p95_ms": float(np.percentile(times_ms, 95)),
        "p99_ms": float(np.percentile(times_ms, 99)),
        "p99_9_ms": float(np.percentile(times_ms, 99.9)) if args.n >= 1000 else None,
        "max_ms": float(times_ms.max()),
        "std_ms": float(times_ms.std()),
        "stride_budget_ms": stride_budget_ms,
        "event_counts_exceeding_threshold": event_counts,
        "event_rates_exceeding_threshold": {k: v / args.n for k, v in event_counts.items()},
        "empirical_deadline_miss_rate_gt_300ms": event_counts[">300ms"] / args.n,
    }
    print("\n=== Summary ===")
    for k, v in report.items():
        if k not in ("device",):
            print(f"  {k}: {v}")
    common.save_json(report, "a1_long_tail_latency")


if __name__ == "__main__":
    main()
