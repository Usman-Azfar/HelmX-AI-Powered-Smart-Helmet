"""Checklist 4.4 + Deployment-Weaknesses-plan W2-LIVE-2 -- live corrected
end-to-end pipeline: physical MPU6050 -> SampleStreamGuard -> causal
gravity filter -> windowing -> aux features -> INT8 inference -> TriggerPolicy,
using the REAL classes from deploy/crash_monitor.py (the corrected-v2
version, with SampleStreamGuard), driven by a REAL live sensor at the real
50Hz-paced cadence -- not a replay. This is exp_a4_replay_streaming_pipeline_
corrected_v2.py's protocol with the recorded-session row iterator swapped for
a real blocking MPU6050 read.

A confirmed trigger is logged (streak/crash_prob/recon_error) but
handle_suspected_crash() is NOT invoked -- this experiment measures pipeline
timing/resource cost, not the alarm/SMS path (already covered by
logic_robustness_tests_corrected_v2.py and, for the live GPIO path, by the
separate 4.7 live trigger-path test).

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_w2_live2_pipeline.py --duration-min 12
"""
import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import common
import crash_monitor as cm


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
    p.add_argument("--duration-min", type=float, default=12.0)
    args = p.parse_args()

    cfg = common.load_config()
    sample_rate = cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / sample_rate
    stride_budget_ms = (cfg["sensor"]["stride_samples"] / sample_rate) * 1000.0
    classifier_t, recon_t = cm.load_model_thresholds(cfg)

    logger = logging.getLogger("w2_live2")
    logger.setLevel(logging.WARNING)  # keep console clean; this script reports via JSON, not per-window logs

    model = cm.CrashModel(cm.ROOT / cfg["model_path"], cm.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], sample_rate)
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)

    print("Connecting to real MPU6050...")
    sensor = cm.connect_sensor(cfg, logger)
    print("Connected. Running live pipeline...")

    proc = psutil.Process()
    proc.cpu_percent(interval=None)

    duration_s = args.duration_min * 60.0
    start = time.monotonic()
    deadline = start + duration_s

    n_input_samples = 0
    n_windows = 0
    n_triggers = 0
    n_sensor_read_failures = 0
    n_reconnects = 0
    exceptions = []
    window_latencies_ms = []
    guard_overhead_ms = []
    trigger_events = []
    resource_samples = []
    next_tick = time.monotonic()
    next_resource_sample = time.monotonic()

    while time.monotonic() < deadline:
        next_tick += period_s
        sample = cm.read_sensor(sensor, logger)
        if sample is None:
            n_sensor_read_failures += 1
            sensor = cm.connect_sensor(cfg, logger)
            n_reconnects += 1
            continue

        now = time.monotonic()
        t_guard0 = time.perf_counter()
        gap_detected, dt = guard.observe(now)
        if gap_detected:
            scorer.clear()
            guard.record_window_invalidated()
            if dt is not None and dt >= guard.long_gap_reset_s:
                gravity_filter.reset()
        guard_ms = (time.perf_counter() - t_guard0) * 1000.0
        guard_overhead_ms.append(guard_ms)

        try:
            preprocess_ms = scorer.append(sample)
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
            guard.record_window_scored()
            total_ms = guard_ms + preprocess_ms + result["windowing_ms"] + result["inference_ms"]
            window_latencies_ms.append(total_ms)
            try:
                is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
                if triggered:
                    n_triggers += 1
                    trigger_events.append({
                        "t_elapsed_s": time.monotonic() - start,
                        "crash_prob": result["crash_prob"],
                        "recon_error": result["recon_error"],
                    })
            except Exception as e:
                exceptions.append(str(e))

        now2 = time.monotonic()
        if now2 >= next_resource_sample:
            res_sample = {
                "t_elapsed_s": now2 - start,
                "process_cpu_percent": proc.cpu_percent(interval=None),
                "process_rss_mb": proc.memory_info().rss / (1024 * 1024),
                "system_cpu_percent": psutil.cpu_percent(interval=None),
                "system_ram_used_mb": (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024 * 1024),
                "swap_used_mb": psutil.swap_memory().used / (1024 * 1024),
                "temperature_c": common.read_temp_c(),
                "cpu_freq_mhz": read_cpu_freq_mhz(),
                "load_avg_1min": os.getloadavg()[0],
            }
            resource_samples.append(res_sample)
            next_resource_sample = now2 + 1.0

    throttled = common.read_throttled()
    lat = np.asarray(window_latencies_ms, dtype=np.float64)

    report = {
        "device": common.device_info(),
        "context": (
            "Checklist 4.4 / W2-LIVE-2 -- live corrected end-to-end pipeline against a REAL, "
            "physically connected MPU6050 (address " + hex(cfg['sensor']['i2c_address']) + "), "
            "using the exact deploy/crash_monitor.py classes (corrected-v2, with SampleStreamGuard). "
            "Sensor sat stationary/gently handled on the desk during this run -- see the separate "
            "4.6 physical-movement smoke test for labeled movement phases."
        ),
        "config": {
            "requested_duration_min": args.duration_min,
            "sample_rate_hz": sample_rate,
            "window_samples": cfg["sensor"]["window_samples"],
            "stride_samples": cfg["sensor"]["stride_samples"],
            "stride_budget_ms": stride_budget_ms,
            "timing_guard": cfg["sensor"].get("timing_guard"),
        },
        "n_input_samples": n_input_samples,
        "n_windows_generated": n_windows,
        "n_triggers": n_triggers,
        "trigger_events": trigger_events,
        "n_sensor_read_failures": n_sensor_read_failures,
        "n_reconnects": n_reconnects,
        "n_exceptions": len(exceptions),
        "exceptions_sample": exceptions[:20],
        "per_window_latency_ms": common.percentile_stats(window_latencies_ms),
        "guard_observe_overhead_ms": common.percentile_stats(guard_overhead_ms),
        "deadline_miss_count_gt_stride_budget": int((lat > stride_budget_ms).sum()) if len(lat) else 0,
        "deadline_miss_rate": float((lat > stride_budget_ms).mean()) if len(lat) else None,
        "windows_per_sec_achieved": n_windows / (time.monotonic() - start),
        "stream_guard_telemetry": guard.snapshot(),
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
    common.save_json(report, "w2_live2_pipeline")


if __name__ == "__main__":
    main()
