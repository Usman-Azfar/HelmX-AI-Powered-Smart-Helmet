"""Checklist 4.5 + Deployment-Weaknesses-plan W2-LIVE-3 -- >=1 hour live
corrected soak test. Same live pipeline as exp_w2_live2_pipeline.py (real
MPU6050 -> SampleStreamGuard -> causal gravity filter -> windowing -> aux
features -> INT8 inference -> TriggerPolicy), run continuously for
--duration-min minutes (default 75, comfortably over the plan's >=1h ask),
with periodic checkpointing every 5 minutes so a long run's data isn't lost
if interrupted, plus an explicit RSS-drift/leak check over the full run.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min 75
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


def _leak_check(rss_series):
    if len(rss_series) < 4:
        return {"slope_mb_per_min": None, "verdict": "not enough samples"}
    t = np.arange(len(rss_series), dtype=np.float64)
    rss = np.asarray(rss_series, dtype=np.float64)
    slope_per_min = np.polyfit(t, rss, 1)[0] * 60.0
    q = max(1, len(rss) // 4)
    verdict = ("possible leak (RSS climbing)" if slope_per_min > 0.5
               else "stable plateau" if abs(slope_per_min) <= 0.5
               else "RSS decreasing (unusual, but not a leak)")
    return {
        "slope_mb_per_min": float(slope_per_min),
        "first_quarter_mean_mb": float(rss[:q].mean()),
        "last_quarter_mean_mb": float(rss[-q:].mean()),
        "verdict": verdict,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration-min", type=float, default=75.0)
    p.add_argument("--checkpoint-every-min", type=float, default=5.0)
    args = p.parse_args()

    cfg = common.load_config()
    sample_rate = cfg["sensor"]["sample_rate_hz"]
    period_s = 1.0 / sample_rate
    stride_budget_ms = (cfg["sensor"]["stride_samples"] / sample_rate) * 1000.0
    classifier_t, recon_t = cm.load_model_thresholds(cfg)

    logger = logging.getLogger("w2_live3_soak")
    logger.setLevel(logging.WARNING)

    model = cm.CrashModel(cm.ROOT / cfg["model_path"], cm.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], sample_rate)
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)

    print(f"Connecting to real MPU6050 for a {args.duration_min}-minute soak...")
    n_reconnects = 0
    sensor = cm.connect_sensor(cfg, logger)
    print("Connected. Soak running -- this will take a while.")

    proc = psutil.Process()
    proc.cpu_percent(interval=None)

    duration_s = args.duration_min * 60.0
    start = time.monotonic()
    deadline = start + duration_s
    checkpoint_every_s = args.checkpoint_every_min * 60.0
    next_checkpoint = start + checkpoint_every_s

    n_input_samples = 0
    n_windows = 0
    n_triggers = 0
    n_sensor_read_failures = 0
    exceptions = []
    window_latencies_ms = []
    trigger_events = []
    resource_samples = []
    next_tick = time.monotonic()
    next_resource_sample = time.monotonic()
    max_temp_seen = None

    while time.monotonic() < deadline:
        next_tick += period_s
        sample = cm.read_sensor(sensor, logger)
        if sample is None:
            n_sensor_read_failures += 1
            sensor = cm.connect_sensor(cfg, logger)
            n_reconnects += 1
            continue

        now = time.monotonic()
        gap_detected, dt = guard.observe(now)
        if gap_detected:
            scorer.clear()
            guard.record_window_invalidated()
            if dt is not None and dt >= guard.long_gap_reset_s:
                gravity_filter.reset()

        try:
            preprocess_ms = scorer.append(sample)
            n_input_samples += 1
        except Exception as e:
            exceptions.append({"t_elapsed_s": now - start, "error": str(e)})
            preprocess_ms = 0.0

        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()

        try:
            result = scorer.try_score()
        except Exception as e:
            exceptions.append({"t_elapsed_s": time.monotonic() - start, "error": str(e)})
            result = None

        if result is not None:
            n_windows += 1
            guard.record_window_scored()
            total_ms = preprocess_ms + result["windowing_ms"] + result["inference_ms"]
            window_latencies_ms.append(total_ms)
            try:
                is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
                if triggered:
                    n_triggers += 1
                    trigger_events.append({
                        "t_elapsed_s": time.monotonic() - start,
                        "crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                    })
            except Exception as e:
                exceptions.append({"t_elapsed_s": time.monotonic() - start, "error": str(e)})

        now2 = time.monotonic()
        if now2 >= next_resource_sample:
            temp = common.read_temp_c()
            if temp is not None:
                max_temp_seen = temp if max_temp_seen is None else max(max_temp_seen, temp)
            res_sample = {
                "t_elapsed_s": now2 - start,
                "process_cpu_percent": proc.cpu_percent(interval=None),
                "process_rss_mb": proc.memory_info().rss / (1024 * 1024),
                "system_cpu_percent": psutil.cpu_percent(interval=None),
                "system_ram_used_mb": (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024 * 1024),
                "swap_used_mb": psutil.swap_memory().used / (1024 * 1024),
                "temperature_c": temp,
                "cpu_freq_mhz": read_cpu_freq_mhz(),
                "load_avg_1min": os.getloadavg()[0],
            }
            resource_samples.append(res_sample)
            next_resource_sample = now2 + 1.0

        if now2 >= next_checkpoint:
            elapsed_min = (now2 - start) / 60.0
            print(f"[checkpoint {elapsed_min:.1f} min] samples={n_input_samples} windows={n_windows} "
                  f"triggers={n_triggers} reconnects={n_reconnects} exceptions={len(exceptions)} "
                  f"max_temp={max_temp_seen}")
            next_checkpoint = now2 + checkpoint_every_s

    throttled = common.read_throttled()
    lat = np.asarray(window_latencies_ms, dtype=np.float64)
    rss_series = [s["process_rss_mb"] for s in resource_samples]

    report = {
        "device": common.device_info(),
        "context": (
            "Checklist 4.5 / W2-LIVE-3 -- >=1h live corrected soak against a REAL, physically "
            "connected MPU6050, using the exact deploy/crash_monitor.py classes (corrected-v2, with "
            "SampleStreamGuard). Runs the exact same pipeline in-process (not via subprocess restart "
            "supervision) -- 'process restarts' below reflects sensor reconnects "
            "(cm.connect_sensor retries), not a killed/relaunched OS process."
        ),
        "config": {
            "requested_duration_min": args.duration_min,
            "actual_duration_min": (time.monotonic() - start) / 60.0,
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
        "exceptions_sample": exceptions[:50],
        "per_window_latency_ms": common.percentile_stats(window_latencies_ms),
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
        "memory_leak_check": _leak_check(rss_series),
        "max_temperature_c": max_temp_seen,
        "throttling_status": throttled,
        "thermal_throttling_occurred": bool(throttled and (
            throttled["currently_throttled"] or throttled["throttling_occurred"]
            or throttled["arm_freq_capped_now"] or throttled["arm_freq_capped_occurred"]
        )) if throttled else None,
        "raw_resource_samples": resource_samples,
    }
    print("\n=== Summary ===")
    print(json.dumps({k: v for k, v in report.items() if k != "raw_resource_samples"}, indent=2)[:4000])
    common.save_json(report, "w2_live3_soak")


if __name__ == "__main__":
    main()
