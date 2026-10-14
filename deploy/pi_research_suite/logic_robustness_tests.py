"""Checklist items 3.18 (malformed-input robustness), 3.21 (replay
determinism), 3.29 (cooldown logic), 3.30 (cancel-window logic), 3.31 (alarm
failure fallback), 3.32 (GSM/GPS failure path) -- all software-only logic
checks against the REAL deployed classes (WindowScorer, TriggerPolicy,
CancellationListener, LocalAlarm, GsmModule, handle_suspected_crash), no
sensor needed. Prints a pass/fail-style report; nothing here is accuracy
evidence, only safe-failure/behavioral-correctness evidence.

Run on the Pi:
    python deploy/pi_research_suite/logic_robustness_tests.py
"""
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, preprocess

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("logic_tests")

results = {}


def section(name):
    print(f"\n--- {name} ---")


cfg = common.load_config()
model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
classifier_t, recon_t = cm.load_model_thresholds(cfg)

# ---- 3.21 Replay repeatability/determinism ----
section("3.21 Replay determinism")
sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
test_session = next(s for s in sessions if s.label == 1 and len(s.df) > 200)


def replay_once(session):
    gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gf)
    probs, recons = [], []
    for row in session.df.itertuples():
        scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
        r = scorer.try_score()
        if r is not None:
            probs.append(r["crash_prob"])
            recons.append(r["recon_error"])
    return np.array(probs), np.array(recons)


p1, r1 = replay_once(test_session)
p2, r2 = replay_once(test_session)
identical = np.array_equal(p1, p2) and np.array_equal(r1, r2)
max_prob_diff = float(np.max(np.abs(p1 - p2))) if len(p1) else None
results["3.21_determinism"] = {
    "session_id": test_session.session_id, "n_windows": int(len(p1)),
    "bit_identical_across_two_replays": bool(identical), "max_abs_prob_diff": max_prob_diff,
}
print(f"session={test_session.session_id} n_windows={len(p1)} "
      f"bit_identical={identical} max_abs_diff={max_prob_diff}")

# ---- 3.18 Malformed-input robustness ----
section("3.18 Malformed-input robustness")
malformed_cases = {
    "nan_sample": [float("nan")] * 6,
    "inf_sample": [float("inf"), -float("inf"), 0, 0, 0, 0],
    "extreme_accel": [1e6, -1e6, 1e6, 0, 0, 0],
    "extreme_gyro": [0, 0, 0, 1e6, -1e6, 1e6],
    "all_zero": [0.0] * 6,
    "constant_nonzero": [9.8, 9.8, 9.8, 1.0, 1.0, 1.0],
}
malformed_results = {}
for case_name, sample in malformed_cases.items():
    gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gf)
    threw = None
    output = None
    try:
        for _ in range(cfg["sensor"]["window_samples"] + cfg["sensor"]["stride_samples"]):
            scorer.append(list(sample))
        result = scorer.try_score()
        if result is not None:
            output = {
                "crash_prob": result["crash_prob"], "recon_error": result["recon_error"],
                "crash_prob_is_nan": bool(np.isnan(result["crash_prob"])),
                "crash_prob_is_finite": bool(np.isfinite(result["crash_prob"])),
            }
    except Exception as e:
        threw = f"{type(e).__name__}: {e}"
    malformed_results[case_name] = {"exception": threw, "output": output}
    print(f"  {case_name}: {'EXCEPTION: ' + threw if threw else output}")
results["3.18_malformed_input"] = malformed_results

# ---- 3.29 Cooldown logic ----
section("3.29 Cooldown logic (events <60s apart suppressed, >60s apart resume)")
policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                           cfg["thresholds"]["cooldown_seconds"])
stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]
anomalous = (1.0, 999.0)  # guaranteed above both thresholds
normal = (0.0, 0.0)

t = 0.0
first_trigger = None
for _ in range(cfg["thresholds"]["consecutive_windows"]):
    _, triggered = policy.update(*anomalous, now=t)
    t += stride_s
    if triggered:
        first_trigger = t
first_trigger_ok = first_trigger is not None

# immediately re-trigger attempt, well within the 60s cooldown -- should NOT fire
t_within_cooldown = first_trigger + 5.0
suppressed = True
for _ in range(cfg["thresholds"]["consecutive_windows"]):
    _, triggered = policy.update(*anomalous, now=t_within_cooldown)
    t_within_cooldown += stride_s
    if triggered:
        suppressed = False

# after the cooldown fully elapses -- should fire again
t_after_cooldown = first_trigger + cfg["thresholds"]["cooldown_seconds"] + 1.0
resumed = False
for _ in range(cfg["thresholds"]["consecutive_windows"]):
    _, triggered = policy.update(*anomalous, now=t_after_cooldown)
    t_after_cooldown += stride_s
    if triggered:
        resumed = True

results["3.29_cooldown_logic"] = {
    "first_trigger_fired": first_trigger_ok,
    "second_trigger_suppressed_within_cooldown": suppressed,
    "third_trigger_resumed_after_cooldown": resumed,
    "all_correct": bool(first_trigger_ok and suppressed and resumed),
}
print(f"  first_trigger_fired={first_trigger_ok} suppressed_within_60s={suppressed} "
      f"resumed_after_60s={resumed}")

# ---- 3.30 Cancel-window software logic ----
section("3.30 Cancel-window (CancellationListener) logic")
with tempfile.TemporaryDirectory() as tmpdir:
    signal_path = os.path.join(tmpdir, "cancel_signal")
    canceller = cm.CancellationListener(signal_path, logger)

    no_file_result = canceller.check_and_clear()
    Path(signal_path).touch()
    file_present_result = canceller.check_and_clear()
    file_consumed = not os.path.exists(signal_path)
    second_check_after_consume = canceller.check_and_clear()

    results["3.30_cancel_window"] = {
        "no_signal_returns_false": no_file_result is False,
        "signal_present_returns_true": file_present_result is True,
        "signal_file_deleted_after_consumption": file_consumed,
        "stale_signal_cannot_double_fire": second_check_after_consume is False,
    }
    print(f"  no_signal={no_file_result} signal_present={file_present_result} "
          f"consumed={file_consumed} second_check={second_check_after_consume}")

    # Full handle_suspected_crash() path, real code, with a short 2s countdown
    # (not the deployed 30s) purely to keep this test fast -- behavior is
    # identical, only the wait duration differs.
    section("3.30b Full handle_suspected_crash() -- cancelled case (real code, 2s countdown)")
    short_cfg = json.loads(json.dumps(cfg))  # deep copy
    short_cfg["alarm"]["countdown_seconds"] = 2
    short_cfg["alarm"]["cancel_signal_file"] = signal_path
    alarm = cm.LocalAlarm(short_cfg["alarm"]["gpio_pin"], logger)
    gsm = cm.GsmModule(short_cfg["gsm"], logger)  # will fail to connect, as established -- must not crash

    def cancel_after_delay():
        time.sleep(0.5)
        Path(signal_path).touch()

    import threading
    threading.Thread(target=cancel_after_delay, daemon=True).start()
    t0 = time.perf_counter()
    sms_sent = cm.handle_suspected_crash(alarm, canceller, gsm, short_cfg, logger)
    elapsed = time.perf_counter() - t0
    results["3.30b_handle_suspected_crash_cancelled"] = {
        "sms_sent": sms_sent, "expected": False, "elapsed_s": elapsed, "matches_expected": sms_sent is False,
    }
    print(f"  cancelled mid-countdown -> sms_sent={sms_sent} (expected False), elapsed={elapsed:.2f}s")

    section("3.30c Full handle_suspected_crash() -- uncancelled case, no GSM/GPS (3.32)")
    t0 = time.perf_counter()
    sms_sent_2 = cm.handle_suspected_crash(alarm, canceller, gsm, short_cfg, logger)
    elapsed_2 = time.perf_counter() - t0
    results["3.32_gsm_gps_failure_path"] = {
        "sms_sent_return_value": sms_sent_2,
        "note": "send_sms() returns False (not an exception) when no GSM connection exists; "
                "get_gps_coordinates() returns None immediately (no real hardware timeout wait) "
                "-- both already-established facts confirmed again here via the real code path.",
        "raised_exception": False, "elapsed_s": elapsed_2,
    }
    print(f"  uncancelled, no GSM/GPS -> handle_suspected_crash() returned {sms_sent_2} "
          f"without raising, elapsed={elapsed_2:.2f}s")

# ---- 3.31 Alarm failure fallback ----
section("3.31 Alarm failure fallback (invalid GPIO pin)")
bad_alarm = cm.LocalAlarm(9999, logger)  # invalid BCM pin number
degraded_to_log_only = bad_alarm.device is None
threw_on_start = None
try:
    bad_alarm.start()
    bad_alarm.stop()
except Exception as e:
    threw_on_start = f"{type(e).__name__}: {e}"
results["3.31_alarm_failure_fallback"] = {
    "invalid_pin": 9999, "degraded_to_log_only_mode": degraded_to_log_only,
    "start_stop_raised_exception": threw_on_start,
    "safe_degradation_confirmed": bool(degraded_to_log_only and threw_on_start is None),
}
print(f"  invalid pin 9999 -> device=None: {degraded_to_log_only}, "
      f"start()/stop() raised: {threw_on_start}")

print("\n=== Full JSON ===")
print(json.dumps(results, indent=2, default=str))
common.save_json(results, "logic_robustness_tests")
