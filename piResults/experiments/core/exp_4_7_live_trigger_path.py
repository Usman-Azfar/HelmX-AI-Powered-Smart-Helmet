"""Checklist 4.7 -- safe live trigger-path test: live sensor loop -> scorer ->
TriggerPolicy -> LocalAlarm, WITHOUT a destructive physical impact test.

Per the checklist's own allowance ("Replay injection is acceptable if
physical triggering would be unsafe"): a REAL live MPU6050 feeds a few
seconds of real baseline samples into the exact deploy/crash_monitor.py
WindowScorer/TriggerPolicy objects (proving the live sensor -> scorer path
works end to end), then a real recorded DaRUS crash session's raw samples
(gyro converted to deg/s, accel gravity-inclusive -- exactly what a live
MPU6050 would hand read_sensor(), same convention as exp_c_replay_validation.py)
are injected through those SAME objects to safely exercise the trigger path
without a physical impact. On the first confirmed trigger, the REAL LocalAlarm
fires a genuine GPIO18 pulse (gpiozero), confirming the alarm actuation path
in this live context. Finally, a few more seconds of real live sensor samples
confirm the path resumes normally after injection.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_4_7_live_trigger_path.py
"""
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, units

PREFERRED_SESSION_SUBSTR = "Iso_312"  # a DaRUS crash session A5 found reliably detected at the 0.6s floor


def main():
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("w4_7_trigger_path")

    cfg = common.load_config()
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])

    print("Connecting to real MPU6050...")
    sensor = cm.connect_sensor(cfg, logger)
    print("Connected.")

    # --- Stage 1: real live baseline through the real scorer/policy ---
    print("\nStage 1: 3s of real live sensor samples through the real WindowScorer/TriggerPolicy...")
    baseline_windows = []
    period = 1.0 / cfg["sensor"]["sample_rate_hz"]
    t_end = time.monotonic() + 3.0
    while time.monotonic() < t_end:
        sample = cm.read_sensor(sensor, logger)
        if sample is not None:
            scorer.append(sample)
            result = scorer.try_score()
            if result is not None:
                is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
                baseline_windows.append({"crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                                          "is_anomaly": is_anomaly, "triggered": triggered})
        time.sleep(period)
    print(f"  {len(baseline_windows)} real live windows scored, "
          f"{sum(w['is_anomaly'] for w in baseline_windows)} anomalous, "
          f"{sum(w['triggered'] for w in baseline_windows)} triggered (expected: 0 anomalous/triggered, quiet desk).")

    # --- Stage 2: inject a real recorded crash session through the SAME scorer/policy ---
    print("\nStage 2: loading a real recorded DaRUS crash session for safe replay injection...")
    raw_sessions = io_loaders.load_all_sessions()
    candidates = [s for s in raw_sessions if "darus" in s.source.lower() and "crash" in s.session_id.lower()]
    chosen = next((s for s in candidates if PREFERRED_SESSION_SUBSTR in s.session_id), candidates[0])
    print(f"  Injecting session: {chosen.session_id} ({chosen.source}, label={chosen.label}, {len(chosen.df)} rows)")

    df = units.gyro_to_deg_per_s(chosen.df, chosen.gyro_in_deg_per_s)
    injected_windows = []
    trigger_window_index = None
    alarm_fired = False
    alarm = None
    for i, row in enumerate(df.itertuples()):
        scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
        result = scorer.try_score()
        if result is None:
            continue
        is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
        injected_windows.append({
            "window_index": i, "crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
            "is_anomaly": is_anomaly, "triggered": triggered,
        })
        if triggered and not alarm_fired:
            trigger_window_index = i
            print(f"  TRIGGERED at injected sample index {i} "
                  f"(crash_prob={result['crash_prob']:.4f}, recon_error={result['recon_error']:.4f}) "
                  f"-- firing real LocalAlarm (GPIO{cfg['alarm']['gpio_pin']})...")
            alarm = cm.LocalAlarm(cfg["alarm"]["gpio_pin"], logger)
            alarm.start()
            time.sleep(0.5)
            alarm.stop()
            alarm_fired = True

    n_anomalous = sum(w["is_anomaly"] for w in injected_windows)
    n_triggered = sum(w["triggered"] for w in injected_windows)
    print(f"  Injection complete: {len(injected_windows)} windows scored, {n_anomalous} anomalous, "
          f"{n_triggered} trigger event(s).")

    # --- Stage 3: back to real live sensor, confirm the path resumes normally ---
    print("\nStage 3: 3s more of real live sensor samples, confirming the path resumes after injection...")
    scorer.clear()  # same call main() makes after handle_suspected_crash()'s countdown
    resume_windows = []
    t_end = time.monotonic() + 3.0
    resume_errors = 0
    while time.monotonic() < t_end:
        sample = cm.read_sensor(sensor, logger)
        if sample is None:
            resume_errors += 1
        else:
            scorer.append(sample)
            result = scorer.try_score()
            if result is not None:
                is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
                resume_windows.append({"crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                                        "is_anomaly": is_anomaly, "triggered": triggered})
        time.sleep(period)
    print(f"  {len(resume_windows)} windows scored after resume, {resume_errors} sensor read errors.")

    report = {
        "device": common.device_info(),
        "context": (
            "Checklist 4.7 -- live sensor loop -> scorer -> TriggerPolicy -> LocalAlarm, with the "
            "crash-inducing portion done via safe replay injection (a real recorded DaRUS crash "
            "session) rather than a physical impact, per the checklist's own allowance for this item."
        ),
        "injected_session_id": chosen.session_id,
        "injected_session_source": chosen.source,
        "injected_session_label": chosen.label,
        "stage1_live_baseline": {
            "n_windows": len(baseline_windows),
            "n_anomalous": sum(w["is_anomaly"] for w in baseline_windows),
            "n_triggered": sum(w["triggered"] for w in baseline_windows),
            "windows": baseline_windows,
        },
        "stage2_injected_crash_replay": {
            "n_windows": len(injected_windows),
            "n_anomalous": n_anomalous,
            "n_triggered": n_triggered,
            "trigger_window_index": trigger_window_index,
            "alarm_fired_real_gpio": alarm_fired,
            "gpio_pin": cfg["alarm"]["gpio_pin"],
            "windows": injected_windows,
        },
        "stage3_live_resume": {
            "n_windows": len(resume_windows),
            "n_sensor_read_errors": resume_errors,
            "n_anomalous": sum(w["is_anomaly"] for w in resume_windows),
            "windows": resume_windows,
        },
    }
    common.save_json(report, "4_7_live_trigger_path")


if __name__ == "__main__":
    main()
