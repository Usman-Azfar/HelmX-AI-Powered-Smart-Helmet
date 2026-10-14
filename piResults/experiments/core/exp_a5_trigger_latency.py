"""Experiment A5 -- trigger-to-local-alarm latency (PI_RESEARCH_GUIDE.md
Section A5).

Replays real crash-like sessions (from the full loaded dataset -- the guide
doesn't restrict this to the test split, since it's testing the TriggerPolicy
confirmation rule's timing, not generalization) through the REAL
WindowScorer + TriggerPolicy, using SYNTHETIC timestamps spaced
stride_seconds apart (matching the real deployed cadence) rather than
waiting through real wall-clock time. Measures, in that synthetic timeline,
how long from the first anomalous window to TriggerPolicy actually firing --
this is the real "3 consecutive windows" confirmation-rule latency, not
inference compute time (which A1 already showed is ~0.5ms, negligible next
to the 300ms stride).

On the first real trigger, also calls the REAL LocalAlarm.start()/stop() (a
genuine GPIO18 pulse via gpiozero -- confirms the alarm path fires without
error on real hardware), and separately reports the wall-clock time that
took (informational only -- GPIO toggling is near-instant, this isn't the
number the guide's schema wants).

Per the guide: the GSM/SMS/30s cancellation countdown is deliberately kept
OUT of this measurement -- that's a separate, fixed, known 30s
(countdown_seconds) added on top only if the countdown's own cancellation
window later expires uncancelled.

Run on the Pi:
    python deploy/pi_research_suite/exp_a5_trigger_latency.py
"""
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, preprocess, manifest

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("a5")


def replay_session(session, model, cfg, classifier_t, recon_t, stride_s):
    ds = manifest.build_dataset([session], {session.session_id: "test"}, "test")
    if len(ds.y) == 0:
        return None

    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])
    first_abnormal_idx = None
    for i in range(len(ds.y)):
        crash_prob, recon_error = model.predict(ds.X_seq[i], ds.X_aux[i])
        now = i * stride_s
        is_anomaly, triggered = policy.update(crash_prob, recon_error, now=now)
        if is_anomaly and first_abnormal_idx is None:
            first_abnormal_idx = i
        if triggered:
            trigger_idx = i
            synthetic_latency_s = (trigger_idx - first_abnormal_idx) * stride_s
            return {
                "session_id": session.session_id, "source": session.source,
                "n_windows": int(len(ds.y)),
                "first_abnormal_window_idx": int(first_abnormal_idx),
                "trigger_window_idx": int(trigger_idx),
                "synthetic_latency_s": synthetic_latency_s,
                "detected": True,
            }
    return {
        "session_id": session.session_id, "source": session.source,
        "n_windows": int(len(ds.y)),
        "first_abnormal_window_idx": first_abnormal_idx,
        "trigger_window_idx": None,
        "synthetic_latency_s": None,
        "detected": False,
    }


def main():
    cfg = common.load_config()
    stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])

    print("Loading + canonicalizing sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    crash_sessions = [s for s in sessions if s.label == 1]
    print(f"{len(crash_sessions)} crash-like sessions to replay.")

    per_session = []
    for s in crash_sessions:
        result = replay_session(s, model, cfg, classifier_t, recon_t, stride_s)
        if result is None:
            continue
        per_session.append(result)
        status = f"latency={result['synthetic_latency_s']:.2f}s" if result["detected"] else "NOT DETECTED"
        print(f"  {s.session_id} ({s.source}): {result['n_windows']} windows -> {status}")

    detected = [r for r in per_session if r["detected"]]
    latencies = [r["synthetic_latency_s"] for r in detected]

    # Real GPIO alarm smoke test: fire it once for real, on the first detected event.
    gpio_test = None
    if detected:
        alarm = cm.LocalAlarm(cfg["alarm"]["gpio_pin"], logger)
        t0 = time.perf_counter()
        try:
            alarm.start()
            time.sleep(0.5)
            alarm.stop()
            gpio_wall_s = time.perf_counter() - t0
            gpio_test = {
                "gpio_pin": cfg["alarm"]["gpio_pin"],
                "ran_without_error": True,
                "used_real_gpio_device": alarm.device is not None,
                "wall_clock_s": gpio_wall_s,
                "note": "GPIO toggled successfully -- this timing is near-instant electrical "
                        "switching, not a measurement the guide's schema asks for; whether an "
                        "actual buzzer/vibration motor is physically wired to this pin to audibly "
                        "confirm is a separate hardware question (see pin_connections.md).",
            }
        except Exception as e:
            gpio_test = {"gpio_pin": cfg["alarm"]["gpio_pin"], "ran_without_error": False, "error": str(e)}

    report = {
        "device": common.device_info(),
        "n_sessions_replayed": len(per_session),
        "n_events_detected": len(detected),
        "n_events_missed": len(per_session) - len(detected),
        "detection_rate": len(detected) / len(per_session) if per_session else None,
        "mean_trigger_latency_s": float(np.mean(latencies)) if latencies else None,
        "median_trigger_latency_s": float(np.median(latencies)) if latencies else None,
        "p95_trigger_latency_s": float(np.percentile(latencies, 95)) if latencies else None,
        "min_s": float(np.min(latencies)) if latencies else None,
        "max_s": float(np.max(latencies)) if latencies else None,
        "stride_seconds": stride_s,
        "consecutive_windows_required": cfg["thresholds"]["consecutive_windows"],
        "gpio_alarm_smoke_test": gpio_test,
        "per_session": per_session,
    }
    print("\n=== Summary ===")
    print(json.dumps({k: v for k, v in report.items() if k != "per_session"}, indent=2))
    common.save_json(report, "a5_trigger_latency")


if __name__ == "__main__":
    main()
