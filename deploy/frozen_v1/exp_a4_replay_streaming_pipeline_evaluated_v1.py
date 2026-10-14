"""Checklist item 3.1 -- full replay-paced software-pipeline benchmark
(HelmX_Paper1_FINAL_Pi_Data_Collection_Checklist.md).

Measures the complete deployed software path WITHOUT physical I2C acquisition
(no MPU6050 wired -- see pin_connections.md): recorded raw IMU samples -> unit
conversion (already applied by canonicalize_all) -> causal gravity filtering
(CausalGravityFilter, the real deployed class) -> rolling buffer -> 60x6
window formation -> 7 aux-feature extraction -> INT8 inference -> threshold
logic -> TriggerPolicy, run at the REAL deployed cadence (50Hz input, one
decision every stride_seconds=300ms), unlike Experiment C which replayed as
fast as the CPU allowed. Real recorded sessions are looped back-to-back
(state carries across session boundaries -- irrelevant for a pure
timing/throughput benchmark) until the requested duration is reached.

Concurrently samples process/system resources every 1s: process CPU%, system
CPU%, process RSS, system RAM used/available, swap, CPU temperature,
throttling status, CPU frequency, load average.

Run on the Pi:
    python deploy/pi_research_suite/exp_a4_replay_streaming_pipeline.py --duration-min 15
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, preprocess


def read_cpu_freq_mhz():
    try:
        out = subprocess.run(["vcgencmd", "measure_clock", "arm"], capture_output=True, text=True, timeout=2)
        if "=" in out.stdout:
            return int(out.stdout.strip().split("=")[1]) / 1e6
    except Exception:
        pass
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration-min", type=float, default=15.0)
    args = p.parse_args()

    cfg = common.load_config()
    stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / cfg["sensor"]["sample_rate_hz"]
    classifier_t, recon_t = cm.load_model_thresholds(cfg)

    print("Loading + canonicalizing all sessions for replay...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    print(f"{len(sessions)} sessions loaded, looping back-to-back at real 50Hz cadence.")

    model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])

    proc = psutil.Process()
    proc.cpu_percent(interval=None)

    duration_s = args.duration_min * 60.0
    start = time.monotonic()
    deadline = start + duration_s

    n_input_samples = 0
    n_windows = 0
    n_triggers = 0
    exceptions = []
    window_latencies_ms = []
    resource_samples = []
    next_tick = time.monotonic()
    next_resource_sample = time.monotonic()

    session_idx = 0
    row_iter = iter(sessions[session_idx].df.itertuples())

    while time.monotonic() < deadline:
        try:
            row = next(row_iter)
        except StopIteration:
            session_idx = (session_idx + 1) % len(sessions)
            row_iter = iter(sessions[session_idx].df.itertuples())
            row = next(row_iter)

        next_tick += period_s
        try:
            preprocess_ms = scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
            n_input_samples += 1
        except Exception as e:
            exceptions.append(str(e))
            preprocess_ms = 0.0

        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()

        try:
            result = scorer.try_score()
        except Exception as e:
            exceptions.append(str(e))
            result = None

        if result is not None:
            n_windows += 1
            total_ms = preprocess_ms + result["windowing_ms"] + result["inference_ms"]
            window_latencies_ms.append(total_ms)
            try:
                _, triggered = policy.update(result["crash_prob"], result["recon_error"])
                if triggered:
                    n_triggers += 1
            except Exception as e:
                exceptions.append(str(e))

        now = time.monotonic()
        if now >= next_resource_sample:
            sample = {
                "t_elapsed_s": now - start,
                "process_cpu_percent": proc.cpu_percent(interval=None),
                "process_rss_mb": proc.memory_info().rss / (1024 * 1024),
                "system_cpu_percent": psutil.cpu_percent(interval=None),
                "system_ram_used_mb": (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024 * 1024),
                "system_ram_available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "swap_used_mb": psutil.swap_memory().used / (1024 * 1024),
                "temperature_c": common.read_temp_c(),
                "cpu_freq_mhz": read_cpu_freq_mhz(),
                "load_avg_1min": __import__("os").getloadavg()[0],
            }
            resource_samples.append(sample)
            next_resource_sample = now + 1.0

    throttled = common.read_throttled()
    lat = np.asarray(window_latencies_ms, dtype=np.float64)
    stride_budget_ms = stride_s * 1000.0

    report = {
        "device": common.device_info(),
        "config": {
            "requested_duration_min": args.duration_min,
            "sample_rate_hz": cfg["sensor"]["sample_rate_hz"],
            "window_samples": cfg["sensor"]["window_samples"],
            "stride_samples": cfg["sensor"]["stride_samples"],
            "stride_budget_ms": stride_budget_ms,
        },
        "n_input_samples": n_input_samples,
        "n_windows_generated": n_windows,
        "n_triggers": n_triggers,
        "n_exceptions": len(exceptions),
        "exceptions_sample": exceptions[:20],
        "per_window_latency_ms": common.percentile_stats(window_latencies_ms),
        "deadline_miss_count_gt_stride_budget": int((lat > stride_budget_ms).sum()) if len(lat) else 0,
        "deadline_miss_rate": float((lat > stride_budget_ms).mean()) if len(lat) else None,
        "windows_per_sec_achieved": n_windows / (time.monotonic() - start),
        "resources": {
            "process_cpu_percent": common.summarize_series(resource_samples, "process_cpu_percent"),
            "system_cpu_percent": common.summarize_series(resource_samples, "system_cpu_percent"),
            "process_rss_mb": common.summarize_series(resource_samples, "process_rss_mb"),
            "system_ram_used_mb": common.summarize_series(resource_samples, "system_ram_used_mb"),
            "swap_used_mb": common.summarize_series(resource_samples, "swap_used_mb"),
            "temperature_c": common.summarize_series(resource_samples, "temperature_c"),
            "cpu_freq_mhz": common.summarize_series(resource_samples, "cpu_freq_mhz"),
            "n_resource_samples": len(resource_samples),
        },
        "throttling_status": throttled,
        "thermal_throttling_occurred": bool(throttled and (
            throttled["currently_throttled"] or throttled["throttling_occurred"]
            or throttled["arm_freq_capped_now"] or throttled["arm_freq_capped_occurred"]
        )) if throttled else None,
        "raw_resource_samples": resource_samples,
    }
    print("\n=== Summary ===")
    print(json.dumps({k: v for k, v in report.items() if k != "raw_resource_samples"}, indent=2))
    common.save_json(report, "a4_replay_streaming_pipeline")


if __name__ == "__main__":
    main()
