"""Experiment A2 -- CPU and RAM under sustained operation.

Monitors the REAL crash-monitor loop (deploy/crash_monitor.py), not a
synthetic inference-only loop, for >=10-15 minutes, sampling every 1 second:
process CPU%, total system CPU%, process RSS RAM, total system RAM, swap
usage, and temperature alongside. Reports mean/p95/max CPU, mean/max RAM, and
an explicit memory-leak check (RSS trend across the run).

By default this LAUNCHES deploy/crash_monitor.py itself as a subprocess and
monitors it (needs a real MPU6050 wired up, since crash_monitor.py will try
to connect to one and retry indefinitely if it can't -- if you don't have the
sensor wired yet, run deploy/pi_research_suite/exp_a1_isolated_inference.py's
`--measured` loop for CPU/RAM instead, or point --pid at any long-running
process for a dry run of the monitoring logic itself). Use --pid to attach to
an already-running instance instead of launching a new one.

Run on the Pi:
    python deploy/pi_research_suite/exp_a2_resource_usage.py --duration-min 15
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

try:
    import psutil
except ImportError:
    psutil = None

import common


def _leak_check(rss_series):
    """A stable plateau is what we want; a steady climb (e.g. 105MB -> 106 ->
    108 -> 130...) suggests a leak. Reports the trend as a simple linear-fit
    slope (MB/minute) over the whole run plus a first-quarter vs last-quarter
    comparison, which is more robust to one-off GC-driven jumps than eyeballing
    a raw series."""
    if len(rss_series) < 4:
        return {"slope_mb_per_min": None, "first_quarter_mean_mb": None,
                "last_quarter_mean_mb": None, "verdict": "not enough samples"}
    t = np.arange(len(rss_series), dtype=np.float64)  # ~1 sample/sec
    rss = np.asarray(rss_series, dtype=np.float64)
    slope_per_sec = np.polyfit(t, rss, 1)[0]
    slope_per_min = slope_per_sec * 60.0
    q = max(1, len(rss) // 4)
    first_q, last_q = float(rss[:q].mean()), float(rss[-q:].mean())
    verdict = (
        "possible leak (RSS climbing)" if slope_per_min > 0.5
        else "stable plateau" if abs(slope_per_min) <= 0.5
        else "RSS decreasing (unusual, but not a leak)"
    )
    return {
        "slope_mb_per_min": float(slope_per_min),
        "first_quarter_mean_mb": first_q,
        "last_quarter_mean_mb": last_q,
        "verdict": verdict,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-min", type=float, default=15.0)
    parser.add_argument("--interval-s", type=float, default=1.0)
    parser.add_argument("--pid", type=int, default=None, help="attach to an already-running process instead of launching crash_monitor.py")
    parser.add_argument("--launch", action="store_true", default=True)
    parser.add_argument("--no-launch", dest="launch", action="store_false")
    args = parser.parse_args()

    if psutil is None:
        print("psutil not installed -- pip install psutil (deploy/requirements.txt)")
        sys.exit(1)

    proc_handle = None
    if args.pid is not None:
        target_pid = args.pid
        print(f"Attaching to existing process PID {target_pid}")
    elif args.launch:
        print("Launching deploy/crash_monitor.py as a subprocess to monitor...")
        proc_handle = subprocess.Popen(
            [sys.executable, str(common.DEPLOY_DIR / "crash_monitor.py")],
            cwd=str(common.ROOT),
        )
        target_pid = proc_handle.pid
        time.sleep(2.0)  # let it get past model load / sensor connect before sampling starts
    else:
        print("Neither --pid nor --launch given -- nothing to monitor.")
        sys.exit(1)

    proc = psutil.Process(target_pid)
    proc.cpu_percent(interval=None)  # prime psutil's internal delta counter

    duration_s = args.duration_min * 60.0
    print(f"Sampling every {args.interval_s}s for {args.duration_min} min (PID {target_pid})...")
    samples = []
    deadline = time.monotonic() + duration_s
    try:
        while time.monotonic() < deadline:
            if not proc.is_running():
                print("Monitored process is no longer running -- stopping early.")
                break
            samples.append(common.sample_process_resources(proc))
            time.sleep(args.interval_s)
    except KeyboardInterrupt:
        print("Interrupted -- reporting on samples collected so far.")
    finally:
        if proc_handle is not None:
            proc_handle.terminate()
            try:
                proc_handle.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc_handle.kill()

    rss_series = [s["process_rss_mb"] for s in samples if s.get("process_rss_mb") is not None]
    report = {
        "device": common.device_info(),
        "pid_monitored": target_pid,
        "requested_duration_min": args.duration_min,
        "actual_samples": len(samples),
        "interval_s": args.interval_s,
        "process_cpu_percent": common.summarize_series(samples, "process_cpu_percent"),
        "system_cpu_percent": common.summarize_series(samples, "system_cpu_percent"),
        "process_rss_mb": common.summarize_series(samples, "process_rss_mb"),
        "system_ram_used_mb": common.summarize_series(samples, "system_ram_used_mb"),
        "swap_used_mb": common.summarize_series(samples, "swap_used_mb"),
        "temperature_c": common.summarize_series(samples, "temperature_c"),
        "memory_leak_check": _leak_check(rss_series),
        "raw_samples": samples,
    }
    print("\n=== Summary ===")
    print(f"Process CPU: mean={report['process_cpu_percent']['mean']} p95={report['process_cpu_percent']['p95']} max={report['process_cpu_percent']['max']}")
    print(f"Process RAM: mean={report['process_rss_mb']['mean']:.1f}MB max={report['process_rss_mb']['max']:.1f}MB" if report['process_rss_mb']['mean'] else "Process RAM: n/a")
    print(f"Memory trend: {report['memory_leak_check']['verdict']} ({report['memory_leak_check']['slope_mb_per_min']:.3f} MB/min)" if report['memory_leak_check']['slope_mb_per_min'] is not None else "Memory trend: not enough samples")

    common.save_json(report, "a2_resource_usage")


if __name__ == "__main__":
    main()
