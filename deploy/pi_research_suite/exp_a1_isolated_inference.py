"""Experiment A1 -- isolated crash-model inference benchmark.

Runs the DEPLOYED INT8 TFLite model alone (not Keras -- that's what the real
system actually runs): 100 warm-up inferences, 1,000 measured inferences,
repeated 5 times, reporting mean/median/p95/p99/max/std latency and
throughput, plus model load/init time measured separately.

Fixed-shape (60, 6) seq + (7,) aux tensors are used with random-but-
plausible values (matching deploy/benchmark_device.py's existing
`synthetic_window` convention) -- inference latency for a fixed-shape
tensor op doesn't depend on the data's values, only its shape/dtype, so this
is standard practice and doesn't need real sensor data (Experiment C is
where real/replayed data matters, for prediction-correctness, not timing).

Run on the Pi:
    python deploy/pi_research_suite/exp_a1_isolated_inference.py
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

import common


def build_interpreter(model_path):
    t0 = time.perf_counter()
    interpreter = tflite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    runner = interpreter.get_signature_runner()
    dummy_seq = np.zeros((1, 60, 6), dtype=np.float32)
    dummy_aux = np.zeros((1, 7), dtype=np.float32)
    runner(seq=dummy_seq, aux=dummy_aux)  # first call pays any lazy runtime init
    load_time_ms = (time.perf_counter() - t0) * 1000.0
    return runner, load_time_ms


def synthetic_window(rng):
    seq = rng.normal(0, 1, size=(1, 60, 6)).astype(np.float32)
    aux = rng.normal(0, 1, size=(1, 7)).astype(np.float32)
    return seq, aux


def run_pass(runner, n_warmup, n_measured, rng):
    for _ in range(n_warmup):
        seq, aux = synthetic_window(rng)
        runner(seq=seq, aux=aux)

    times_ms = []
    for _ in range(n_measured):
        seq, aux = synthetic_window(rng)
        t0 = time.perf_counter()
        runner(seq=seq, aux=aux)
        times_ms.append((time.perf_counter() - t0) * 1000.0)

    stats = common.percentile_stats(times_ms)
    stats["throughput_windows_per_sec"] = 1000.0 / stats["mean_ms"] if stats["mean_ms"] else None
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="path to .tflite model (default: deployed INT8)")
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--measured", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = common.load_config()
    model_path = Path(args.model) if args.model else (common.ROOT / cfg["model_path"])
    rng = np.random.default_rng(args.seed)

    print(f"Loading model: {model_path}")
    runner, load_time_ms = build_interpreter(model_path)
    print(f"Model load time: {load_time_ms:.2f} ms")

    repeat_results = []
    for i in range(args.repeats):
        print(f"\n--- Pass {i + 1}/{args.repeats}: {args.warmup} warmup + {args.measured} measured ---")
        stats = run_pass(runner, args.warmup, args.measured, rng)
        print(f"  mean={stats['mean_ms']:.3f}ms median={stats['median_ms']:.3f}ms "
              f"p95={stats['p95_ms']:.3f}ms p99={stats['p99_ms']:.3f}ms max={stats['max_ms']:.3f}ms")
        repeat_results.append(stats)

    # Pool the "headline" numbers across repeats (mean of means, worst-case max, etc.)
    # rather than just reporting the last pass -- the point of repeating 5x is to
    # check run-to-run consistency, not to throw 4 of the 5 passes away.
    medians = [r["median_ms"] for r in repeat_results]
    p95s = [r["p95_ms"] for r in repeat_results]
    p99s = [r["p99_ms"] for r in repeat_results]
    maxes = [r["max_ms"] for r in repeat_results]

    report = {
        "device": common.device_info(),
        "model": {
            "path": str(model_path),
            "format": model_path.suffix.lstrip(".").lower(),
            "size_bytes": model_path.stat().st_size if model_path.exists() else None,
            "load_time_ms": load_time_ms,
        },
        "config": {"warmup": args.warmup, "measured": args.measured, "repeats": args.repeats},
        "repeats": repeat_results,
        "across_repeats": {
            "median_ms_mean": float(np.mean(medians)), "median_ms_std": float(np.std(medians)),
            "p95_ms_mean": float(np.mean(p95s)), "p95_ms_std": float(np.std(p95s)),
            "p99_ms_mean": float(np.mean(p99s)), "p99_ms_std": float(np.std(p99s)),
            "max_ms_worst": float(np.max(maxes)),
        },
        "stride_seconds": cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"],
        "note": (
            "The deployed stride is stride_seconds above -- compare median/p95/p99 latency "
            "against it directly: even a p99 a few ms wide leaves enormous headroom against a "
            "~300ms budget between windows."
        ),
    }
    print("\n=== Summary across repeats ===")
    print(f"median: {report['across_repeats']['median_ms_mean']:.3f} +/- {report['across_repeats']['median_ms_std']:.3f} ms")
    print(f"p95:    {report['across_repeats']['p95_ms_mean']:.3f} +/- {report['across_repeats']['p95_ms_std']:.3f} ms")
    print(f"p99:    {report['across_repeats']['p99_ms_mean']:.3f} +/- {report['across_repeats']['p99_ms_std']:.3f} ms")
    print(f"worst max seen: {report['across_repeats']['max_ms_worst']:.3f} ms")
    print(f"stride budget:  {report['stride_seconds'] * 1000:.1f} ms")

    common.save_json(report, "a1_isolated_inference")


if __name__ == "__main__":
    main()
