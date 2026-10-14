"""ExperimentsToPerform.txt item 2: real measurements on the actual target
edge device -- inference latency, CPU usage, RAM usage, model load time,
power/battery impact if measurable, and behavior when a second always-on
workload (standing in for the drowsiness-detection module) runs concurrently.

This CANNOT be run from the development machine that produced the rest of
this repo's structured result JSON files -- there is no Raspberry Pi (or other
target edge device) attached to that environment. Copy this file, `deploy/`,
`models/helmx_crash_model_int8.tflite`, and `models/normalizer.npz` to the
actual device, then:

    pip install -r deploy/requirements.txt   # now includes psutil
    python deploy/benchmark_device.py [--runs 500] [--concurrent-workers 1]

It writes `piResults/results/generated/pi_benchmark.json` in the same schema style as this repo's
other results files. Uses only synthetic (random-but-realistically-scaled)
sensor windows -- no real MPU6050 needed to benchmark model/CPU/RAM behavior,
so this also runs standalone on a Pi with no sensor wired up yet.

Deliberately standalone (no `import src...`), matching deploy/crash_monitor.py's
existing convention of not depending on the full training-side package -- only
tflite-runtime + numpy + psutil + pyyaml are required on the device."""
import argparse
import json
import multiprocessing
import os
import time
from pathlib import Path

import numpy as np
import yaml

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

try:
    import psutil
except ImportError:
    psutil = None

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None):
    path = path or (Path(__file__).parent / "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _busy_worker(stop_flag):
    """Pegs one CPU core until `stop_flag.value` is set -- a crude but honest
    stand-in for 'another always-on inference workload' (e.g. the drowsiness-
    detection module) running concurrently on the same device, since we don't
    have that module's actual code to run for real."""
    while not stop_flag.value:
        _ = sum(i * i for i in range(1000))


class ConcurrentLoad:
    """Context manager: spawns `n_workers` busy-loop processes on __enter__,
    stops them on __exit__. No-op if n_workers <= 0."""

    def __init__(self, n_workers):
        self.n_workers = n_workers
        self.stop_flag = multiprocessing.Value("b", False)
        self.procs = []

    def __enter__(self):
        for _ in range(self.n_workers):
            p = multiprocessing.Process(target=_busy_worker, args=(self.stop_flag,))
            p.start()
            self.procs.append(p)
        if self.procs:
            time.sleep(0.5)  # let the workers actually ramp up before measuring
        return self

    def __exit__(self, *exc):
        self.stop_flag.value = True
        for p in self.procs:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()


def read_power_now_microwatts():
    """Best-effort power draw from sysfs (present on some Pi HATs/UPS add-ons
    that expose a fuel gauge; NOT present on a plain Pi 4 with no such HAT).
    Returns None (never a fabricated number) if nothing usable is found."""
    base = Path("/sys/class/power_supply")
    if not base.exists():
        return None
    for supply in base.iterdir():
        power_path = supply / "power_now"
        if power_path.exists():
            try:
                return int(power_path.read_text().strip())  # microwatts
            except (OSError, ValueError):
                continue
        voltage_path, current_path = supply / "voltage_now", supply / "current_now"
        if voltage_path.exists() and current_path.exists():
            try:
                v_uV = int(voltage_path.read_text().strip())
                i_uA = int(current_path.read_text().strip())
                return v_uV * i_uA / 1e6  # -> microwatts
            except (OSError, ValueError):
                continue
    return None


def build_interpreter(model_path):
    t0 = time.perf_counter()
    interpreter = tflite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    runner = interpreter.get_signature_runner()
    # First call includes any lazy init the runtime does -- count it as part
    # of "load time", since that's what the deployed process actually pays
    # before it can serve its first real prediction.
    dummy_seq = np.zeros((1, 60, 6), dtype=np.float32)
    dummy_aux = np.zeros((1, 7), dtype=np.float32)
    runner(seq=dummy_seq, aux=dummy_aux)
    load_time_s = time.perf_counter() - t0
    return runner, load_time_s


def synthetic_window(rng):
    """A random-but-plausible normalized (60, 6) window + (7,) aux features --
    values don't need to be physically meaningful, only the right shape/dtype,
    since this benchmarks compute/resource cost, not detection accuracy."""
    seq = rng.normal(0, 1, size=(1, 60, 6)).astype(np.float32)
    aux = rng.normal(0, 1, size=(1, 7)).astype(np.float32)
    return seq, aux


def benchmark_latency(runner, n_runs, rng):
    times = []
    for _ in range(n_runs):
        seq, aux = synthetic_window(rng)
        start = time.perf_counter()
        runner(seq=seq, aux=aux)
        times.append(time.perf_counter() - start)
    times = np.array(times) * 1000.0  # ms
    return {
        "n_runs": n_runs,
        "mean_ms": float(times.mean()),
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
        "p99_ms": float(np.percentile(times, 99)),
        "max_ms": float(times.max()),
        "throughput_windows_per_sec": float(1000.0 / times.mean()),
    }


def benchmark_resources(runner, n_runs, rng, sample_interval_s=0.05):
    """Runs inference for ~the same duration as benchmark_latency while
    sampling this process's CPU% and RSS memory in the background."""
    if psutil is None:
        return {"error": "psutil not installed -- pip install psutil"}

    proc = psutil.Process(os.getpid())
    proc.cpu_percent(interval=None)  # prime the internal counter

    cpu_samples, rss_samples = [], []
    next_sample = time.perf_counter()
    for _ in range(n_runs):
        seq, aux = synthetic_window(rng)
        runner(seq=seq, aux=aux)
        now = time.perf_counter()
        if now >= next_sample:
            cpu_samples.append(proc.cpu_percent(interval=None))
            rss_samples.append(proc.memory_info().rss)
            next_sample = now + sample_interval_s

    cpu_samples = [c for c in cpu_samples if c is not None]
    return {
        "cpu_percent_mean": float(np.mean(cpu_samples)) if cpu_samples else None,
        "cpu_percent_max": float(np.max(cpu_samples)) if cpu_samples else None,
        "rss_mb_mean": float(np.mean(rss_samples) / (1024 * 1024)) if rss_samples else None,
        "rss_mb_max": float(np.max(rss_samples) / (1024 * 1024)) if rss_samples else None,
        "n_samples": len(cpu_samples),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=500, help="inferences per measurement pass")
    parser.add_argument("--concurrent-workers", type=int, default=1,
                         help="busy-loop worker processes to run concurrently for the 'concurrent' pass (0 to skip that pass)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = load_config()
    model_path = ROOT / cfg["model_path"]
    rng = np.random.default_rng(args.seed)

    print(f"Loading model: {model_path}")
    runner, load_time_s = build_interpreter(model_path)
    print(f"Model load time: {load_time_s * 1000:.1f} ms")

    print(f"Benchmarking latency ({args.runs} runs, no contention)...")
    latency_solo = benchmark_latency(runner, args.runs, rng)
    print(f"  mean={latency_solo['mean_ms']:.3f}ms p95={latency_solo['p95_ms']:.3f}ms")

    print(f"Benchmarking CPU/RAM ({args.runs} runs, no contention)...")
    resources_solo = benchmark_resources(runner, args.runs, rng)

    report = {
        "device_info": {
            "platform": os.uname().sysname + " " + os.uname().machine if hasattr(os, "uname") else "unknown",
            "cpu_count": os.cpu_count(),
        },
        "model_path": str(model_path),
        "model_load_time_ms": load_time_s * 1000.0,
        "power_now_microwatts": read_power_now_microwatts(),
        "power_note": (
            "None means no sysfs power-supply fuel-gauge was found on this device "
            "(expected on a plain Pi 4 with no UPS/power-monitoring HAT) -- this is "
            "reported honestly as unavailable, not estimated."
        ),
        "solo": {
            "latency": latency_solo,
            "resources": resources_solo,
        },
    }

    if args.concurrent_workers > 0:
        print(f"Benchmarking latency + CPU/RAM under {args.concurrent_workers} concurrent "
              "busy-loop worker(s) (standing in for the drowsiness-detection module)...")
        with ConcurrentLoad(args.concurrent_workers):
            latency_concurrent = benchmark_latency(runner, args.runs, rng)
            resources_concurrent = benchmark_resources(runner, args.runs, rng)
        print(f"  mean={latency_concurrent['mean_ms']:.3f}ms p95={latency_concurrent['p95_ms']:.3f}ms "
              f"(vs {latency_solo['mean_ms']:.3f}ms solo)")
        report["concurrent"] = {
            "n_busy_workers": args.concurrent_workers,
            "note": (
                "Busy-loop worker processes simulate CPU contention from another "
                "always-on workload (e.g. drowsiness detection); this is a proxy, "
                "not the actual drowsiness-detection module's real CPU profile."
            ),
            "latency": latency_concurrent,
            "resources": resources_concurrent,
        }

    results_dir = ROOT / "piResults" / "results" / "generated"
    results_dir.mkdir(exist_ok=True, parents=True)
    out_path = results_dir / "pi_benchmark.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nWrote {out_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
