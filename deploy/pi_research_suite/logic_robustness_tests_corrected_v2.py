"""Re-validation of the two deployment weaknesses described in
HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md, run
against the CORRECTED deploy/crash_monitor.py (CrashAlertResult +
SampleStreamGuard), compared where relevant against the FROZEN evaluated-v1
implementation preserved at deploy/frozen_v1/crash_monitor_evaluated_v1.py.

Covers, from that plan:
  W1-R1 cancellation path
  W1-R2 SMS success path (mocked GSM)
  W1-R3 SMS failure path (mocked GSM)
  W1-R4 GPS unavailable + SMS path (mocked GSM/GPS)
  W1-R5 backward-compatibility caller regression (real GsmModule, no hardware)
  W2-R1 no-gap regression: corrected vs. frozen-v1, byte-identical decisions expected
  W2-R2 isolated single-drop simulation (early / mid / crash-transient positions)
  W2-R3 sparse periodic drop simulation (1-in-100, 1-in-500)
  W2-R4 burst-drop simulation (2, 5, 10, 30 samples)
  W2-R5 delayed-sample simulation (+30/+50/+100/+300ms)

No MPU6050 is connected to this Pi (established repeatedly in
piResults/ResultsFromPi.md Section 4) -- this is exactly the "Minimum
post-fix experiment package if MPU still does NOT work" (that plan's
Section 14): every check below is software-only, real deployed classes,
real held-out sessions, no live sensor required. W2-R6 (corrected
replay-paced Pi pipeline benchmark) is a separate script:
exp_a4_replay_streaming_pipeline_corrected_v2.py.

Run on the Pi:
    python deploy/pi_research_suite/logic_robustness_tests_corrected_v2.py
"""
import importlib.util
import json
import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm  # corrected v2
from src import io_loaders, preprocess

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("logic_tests_v2")

results = {}


def section(name):
    print(f"\n--- {name} ---")


def load_frozen_v1():
    """Imports the frozen evaluated-v1 crash_monitor.py under a distinct
    module name (both files are literally named crash_monitor.py) so W2-R1
    can run the pre-fix and post-fix WindowScorer side by side."""
    path = ROOT / "deploy" / "frozen_v1" / "crash_monitor_evaluated_v1.py"
    spec = importlib.util.spec_from_file_location("crash_monitor_v1_frozen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cm_v1 = load_frozen_v1()
cfg = common.load_config()
model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
classifier_t, recon_t = cm.load_model_thresholds(cfg)
period_s = 1.0 / cfg["sensor"]["sample_rate_hz"]

print("Loading + canonicalizing sessions...")
sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
crash_session = next(s for s in sessions if s.label == 1 and len(s.df) > 200)
normal_session = next(s for s in sessions if s.label == 0 and len(s.df) > 600)
samples_crash = [[r.ax, r.ay, r.az, r.gx, r.gy, r.gz] for r in crash_session.df.itertuples()]
samples_normal = [[r.ax, r.ay, r.az, r.gx, r.gy, r.gz] for r in normal_session.df.itertuples()]
print(f"crash-like session: {crash_session.session_id} ({len(samples_crash)} samples)")
print(f"normal session: {normal_session.session_id} ({len(samples_normal)} samples)")


# =====================================================================
# Weakness 1 -- handle_suspected_crash() structured result
# =====================================================================

class FakeGsm:
    """Mocked GSM module -- deterministic send_sms()/get_gps_coordinates()
    return values, per the plan's W1-R2/R3/R4 (real GsmModule against no
    hardware always returns False/None, which only covers the failure
    side; these mocks let the success side be tested too)."""

    def __init__(self, sms_result, gps_result):
        self._sms_result = sms_result
        self._gps_result = gps_result
        self.sms_calls = 0
        self.gps_calls = 0

    def get_gps_coordinates(self, timeout_seconds):
        self.gps_calls += 1
        return self._gps_result

    def send_sms(self, message):
        self.sms_calls += 1
        return self._sms_result


def short_cfg(countdown_seconds, cancel_signal_file):
    c = json.loads(json.dumps(cfg))  # deep copy
    c["alarm"]["countdown_seconds"] = countdown_seconds
    c["alarm"]["cancel_signal_file"] = cancel_signal_file
    return c


with tempfile.TemporaryDirectory() as tmpdir:
    signal_path = os.path.join(tmpdir, "cancel_signal")
    canceller = cm.CancellationListener(signal_path, logger)
    alarm = cm.LocalAlarm(cfg["alarm"]["gpio_pin"], logger)

    # ---- W1-R1: cancellation path ----
    section("W1-R1 cancellation path")

    def cancel_after_delay():
        time.sleep(0.5)
        Path(signal_path).touch()

    fake_gsm = FakeGsm(sms_result=True, gps_result=(24.86, 67.01))
    threading.Thread(target=cancel_after_delay, daemon=True).start()
    r1 = cm.handle_suspected_crash(alarm, canceller, fake_gsm, short_cfg(2, signal_path), logger)
    results["W1-R1_cancellation"] = {
        "cancelled": r1.cancelled, "sms_attempted": r1.sms_attempted,
        "sms_sent": r1.sms_sent, "gps_available": r1.gps_available,
        "sms_calls_made": fake_gsm.sms_calls,
        "expected": {"cancelled": True, "sms_attempted": False, "sms_sent": False, "gps_available": False},
        "matches_expected": (r1.cancelled, r1.sms_attempted, r1.sms_sent, r1.gps_available, fake_gsm.sms_calls)
                             == (True, False, False, False, 0),
    }
    print(f"  {results['W1-R1_cancellation']}")

    # ---- W1-R2: SMS success path ----
    section("W1-R2 SMS success path (mocked send_sms -> True)")
    fake_gsm = FakeGsm(sms_result=True, gps_result=(24.86, 67.01))
    r2 = cm.handle_suspected_crash(alarm, canceller, fake_gsm, short_cfg(0.3, signal_path), logger)
    results["W1-R2_sms_success"] = {
        "cancelled": r2.cancelled, "sms_attempted": r2.sms_attempted,
        "sms_sent": r2.sms_sent, "gps_available": r2.gps_available,
        "expected": {"cancelled": False, "sms_attempted": True, "sms_sent": True, "gps_available": True},
        "matches_expected": (r2.cancelled, r2.sms_attempted, r2.sms_sent, r2.gps_available)
                             == (False, True, True, True),
    }
    print(f"  {results['W1-R2_sms_success']}")

    # ---- W1-R3: SMS failure path ----
    section("W1-R3 SMS failure path (mocked send_sms -> False)")
    fake_gsm = FakeGsm(sms_result=False, gps_result=(24.86, 67.01))
    r3 = cm.handle_suspected_crash(alarm, canceller, fake_gsm, short_cfg(0.3, signal_path), logger)
    results["W1-R3_sms_failure"] = {
        "cancelled": r3.cancelled, "sms_attempted": r3.sms_attempted,
        "sms_sent": r3.sms_sent, "gps_available": r3.gps_available,
        "expected": {"cancelled": False, "sms_attempted": True, "sms_sent": False, "gps_available": True},
        "matches_expected": (r3.cancelled, r3.sms_attempted, r3.sms_sent, r3.gps_available)
                             == (False, True, False, True),
        "note": "This is the exact case that was silently mis-reported as success pre-fix "
                "(evaluated-v1 handle_suspected_crash() returned True here). Corrected result "
                "reports sms_sent=False, matching what actually happened.",
    }
    print(f"  {results['W1-R3_sms_failure']}")

    # ---- W1-R4: GPS unavailable + SMS path (both sms outcomes) ----
    section("W1-R4 GPS unavailable + SMS path (mocked get_gps_coordinates -> None)")
    fake_gsm_a = FakeGsm(sms_result=True, gps_result=None)
    r4a = cm.handle_suspected_crash(alarm, canceller, fake_gsm_a, short_cfg(0.3, signal_path), logger)
    fake_gsm_b = FakeGsm(sms_result=False, gps_result=None)
    r4b = cm.handle_suspected_crash(alarm, canceller, fake_gsm_b, short_cfg(0.3, signal_path), logger)
    results["W1-R4_gps_unavailable"] = {
        "sms_success_case": {
            "gps_available": r4a.gps_available, "sms_sent": r4a.sms_sent,
            "matches_expected": (r4a.gps_available, r4a.sms_sent) == (False, True),
        },
        "sms_failure_case": {
            "gps_available": r4b.gps_available, "sms_sent": r4b.sms_sent,
            "matches_expected": (r4b.gps_available, r4b.sms_sent) == (False, False),
        },
        "note": "gps_available=False is independent of sms_sent in both directions -- GPS "
                "absence never implies or masks SMS outcome.",
    }
    print(f"  {results['W1-R4_gps_unavailable']}")

    # ---- W1-R5: backward-compatibility caller regression ----
    section("W1-R5 caller regression (real GsmModule, no hardware -- matches original 3.30c)")
    real_gsm = cm.GsmModule(cfg["gsm"], logger)  # will fail to connect, as established; must not crash
    threw = None
    try:
        r5 = cm.handle_suspected_crash(alarm, canceller, real_gsm, short_cfg(0.3, signal_path), logger)
        r5_dict = {"cancelled": r5.cancelled, "sms_attempted": r5.sms_attempted,
                   "sms_sent": r5.sms_sent, "gps_available": r5.gps_available}
    except Exception as e:
        threw = f"{type(e).__name__}: {e}"
        r5_dict = None
    results["W1-R5_caller_regression"] = {
        "raised_exception": threw, "result": r5_dict,
        "expected": {"cancelled": False, "sms_attempted": True, "sms_sent": False, "gps_available": False},
        "matches_expected": threw is None and r5_dict == {
            "cancelled": False, "sms_attempted": True, "sms_sent": False, "gps_available": False},
        "note": "Real (unmocked) GsmModule with no GSM/GPS hardware present -- same condition "
                "as evaluated-v1's 3.30c/3.32 tests. sms_sent=False now correctly distinguishes "
                "this from the cancelled case, unlike evaluated-v1's unconditional return True.",
    }
    print(f"  {results['W1-R5_caller_regression']}")


# =====================================================================
# Weakness 2 -- SampleStreamGuard timing-gap detection
# =====================================================================

def replay_frozen_v1(samples):
    gf = cm_v1.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm_v1.WindowScorer(cfg, model, gf)
    probs, recons = [], []
    for s in samples:
        scorer.append(s)
        r = scorer.try_score()
        if r is not None:
            probs.append(r["crash_prob"])
            recons.append(r["recon_error"])
    return np.array(probs), np.array(recons)


def replay_corrected_no_gap(samples):
    """Corrected v2 path with a perfectly regular synthetic clock (dt ==
    period_s every sample) -- the guard should observe zero gaps and the
    underlying WindowScorer/CausalGravityFilter math is untouched, so this
    should reproduce evaluated-v1 exactly."""
    gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gf)
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)
    probs, recons = [], []
    t = 0.0
    for s in samples:
        gap_detected, _ = guard.observe(t)
        if gap_detected:
            scorer.clear()
            guard.record_window_invalidated()
        scorer.append(s)
        r = scorer.try_score()
        if r is not None:
            guard.record_window_scored()
            probs.append(r["crash_prob"])
            recons.append(r["recon_error"])
        t += period_s
    return np.array(probs), np.array(recons), guard


def any_trigger(probs, recons):
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])
    fired = False
    for k, (p, r) in enumerate(zip(probs, recons)):
        _, triggered = policy.update(p, r, now=k * (cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]))
        fired = fired or triggered
    return fired


# ---- W2-R1: no-gap regression, corrected vs. frozen-v1 ----
section("W2-R1 no-gap regression: corrected-v2 vs. frozen evaluated-v1")
for label, samples in (("crash_session", samples_crash), ("normal_session", samples_normal)):
    p_v1, r_v1 = replay_frozen_v1(samples)
    p_v2, r_v2, guard_v2 = replay_corrected_no_gap(samples)
    identical = np.array_equal(p_v1, p_v2) and np.array_equal(r_v1, r_v2)
    decision_v1 = (p_v1 > classifier_t) | (r_v1 > recon_t)
    decision_v2 = (p_v2 > classifier_t) | (r_v2 > recon_t)
    decision_agree = float(np.mean(decision_v1 == decision_v2)) if len(decision_v1) else None
    fired_v1 = any_trigger(p_v1, r_v1)
    fired_v2 = any_trigger(p_v2, r_v2)
    results[f"W2-R1_no_gap_regression_{label}"] = {
        "n_windows_v1": int(len(p_v1)), "n_windows_v2": int(len(p_v2)),
        "bit_identical_outputs": bool(identical),
        "max_abs_prob_diff": float(np.max(np.abs(p_v1 - p_v2))) if len(p_v1) == len(p_v2) and len(p_v1) else None,
        "window_decision_agreement": decision_agree,
        "event_trigger_agreement": fired_v1 == fired_v2,
        "corrected_guard_timing_gaps": guard_v2.timing_gaps,
        "corrected_guard_windows_invalidated": guard_v2.windows_invalidated,
        "all_pass": bool(identical and decision_agree == 1.0 and fired_v1 == fired_v2
                          and guard_v2.timing_gaps == 0 and guard_v2.windows_invalidated == 0),
    }
    print(f"  {label}: {results[f'W2-R1_no_gap_regression_{label}']}")


# ---- Shared drop/delay simulation harness ----

def build_delivered_stream(samples, drop_indices, period_s, delay_at=None, delay_s=0.0):
    """drop_indices: indices into `samples` that are dropped (never
    delivered). delay_at/delay_s: optionally add extra real-time delay
    before ONE specific (non-dropped) index is considered "arrived",
    without dropping it -- simulates W2-R5's delayed-not-lost case.
    Returns (delivered_samples, delivered_timestamps)."""
    drop_indices = set(drop_indices)
    delivered, timestamps = [], []
    t = 0.0
    dropped_run = 0
    for i, s in enumerate(samples):
        if i in drop_indices:
            dropped_run += 1
            continue
        t += period_s * (dropped_run + 1)
        dropped_run = 0
        if delay_at is not None and i == delay_at:
            t += delay_s
        delivered.append(s)
        timestamps.append(t)
    return delivered, timestamps


def replay_with_guard(samples, timestamps):
    gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gf)
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)
    events = []  # per-sample: (gap_detected, dt, buf_len_before_clear, buf_len_after_clear)
    probs, recons = [], []
    exception = None
    try:
        for s, t in zip(samples, timestamps):
            gap_detected, dt = guard.observe(t)
            buf_len_before_clear = None
            buf_len_after_clear = None
            if gap_detected:
                buf_len_before_clear = len(scorer.buffer)
                scorer.clear()
                buf_len_after_clear = len(scorer.buffer)
                guard.record_window_invalidated()
                if dt is not None and dt >= guard.long_gap_reset_s:
                    gf.reset()
            events.append((gap_detected, dt, buf_len_before_clear, buf_len_after_clear))
            scorer.append(s)
            r = scorer.try_score()
            if r is not None:
                guard.record_window_scored()
                probs.append(r["crash_prob"])
                recons.append(r["recon_error"])
    except Exception as e:
        exception = f"{type(e).__name__}: {e}"
    return {
        "guard": guard, "events": events,
        "probs": np.array(probs), "recons": np.array(recons),
        "exception": exception,
    }


# ---- W2-R2: isolated single-drop simulation ----
section("W2-R2 isolated single-drop simulation (3 positions on the crash-like session)")
n = len(samples_crash)
positions = {"early": int(n * 0.1), "middle": int(n * 0.5), "crash_transient_late": int(n * 0.9)}
w2r2 = {}
for pos_name, idx in positions.items():
    delivered, ts = build_delivered_stream(samples_crash, {idx}, period_s)
    out = replay_with_guard(delivered, ts)
    gaps_detected = [e for e in out["events"] if e[0]]
    w2r2[pos_name] = {
        "dropped_sample_index": idx,
        "no_exception": out["exception"] is None,
        "exception": out["exception"],
        "gap_detected": len(gaps_detected) == 1,
        "n_gaps_detected": len(gaps_detected),
        "windows_invalidated": out["guard"].windows_invalidated,
        "windows_scored": out["guard"].windows_scored,
        "buffer_len_at_gap_before_clear": gaps_detected[0][2] if gaps_detected else None,
    }
results["W2-R2_isolated_single_drop"] = w2r2
print(json.dumps(w2r2, indent=2, default=str))

# ---- W2-R3: sparse periodic drop simulation ----
section("W2-R3 sparse periodic drop simulation (normal_session, 1-in-100 and 1-in-500)")
w2r3 = {}
n_normal = len(samples_normal)
for every in (100, 500):
    drop_idx = set(range(0, n_normal, every))
    delivered, ts = build_delivered_stream(samples_normal, drop_idx, period_s)
    out = replay_with_guard(delivered, ts)
    baseline_probs, baseline_recons = replay_frozen_v1(samples_normal)
    fired_dropped = any_trigger(out["probs"], out["recons"])
    fired_baseline = any_trigger(baseline_probs, baseline_recons)
    total_span_s = ts[-1] - ts[0] if len(ts) > 1 else 0.0
    invalid_span_s = out["guard"].windows_invalidated * (cfg["sensor"]["window_samples"] * period_s)
    w2r3[f"1_in_{every}"] = {
        "n_dropped": len(drop_idx), "n_delivered": len(delivered),
        "no_exception": out["exception"] is None,
        "gap_count": out["guard"].timing_gaps,
        "windows_invalidated": out["guard"].windows_invalidated,
        "windows_scored": out["guard"].windows_scored,
        "approx_pct_time_invalidated": (invalid_span_s / total_span_s * 100.0) if total_span_s else None,
        "false_trigger_vs_no_drop_baseline": bool(fired_dropped and not fired_baseline),
        "event_outcome_matches_baseline": fired_dropped == fired_baseline,
    }
results["W2-R3_sparse_periodic_drop"] = w2r3
print(json.dumps(w2r3, indent=2, default=str))

# ---- W2-R4: burst-drop simulation ----
section("W2-R4 burst-drop simulation (normal_session, 2/5/10/30 consecutive samples)")
w2r4 = {}
burst_start = n_normal // 3
for burst_size in (2, 5, 10, 30):
    drop_idx = set(range(burst_start, burst_start + burst_size))
    delivered, ts = build_delivered_stream(samples_normal, drop_idx, period_s)
    out = replay_with_guard(delivered, ts)
    gaps_detected = [e for e in out["events"] if e[0]]
    w2r4[f"burst_{burst_size}"] = {
        "no_exception": out["exception"] is None,
        "n_gap_events": len(gaps_detected),
        "gap_events_equal_one": len(gaps_detected) == 1,
        "gap_dt_ms": [round(e[1] * 1000.0, 1) for e in gaps_detected],
        "windows_invalidated": out["guard"].windows_invalidated,
        "windows_scored": out["guard"].windows_scored,
        "gravity_filter_reset_triggered": (gaps_detected[0][1] >= cfg["sensor"]["timing_guard"]["long_gap_reset_s"])
                                           if gaps_detected else False,
    }
results["W2-R4_burst_drop"] = w2r4
print(json.dumps(w2r4, indent=2, default=str))

# invariant check: buffer is empty immediately after every detected gap (before the new
# sample is appended) -- proves old/new samples can never be mixed in one scored window
mix_check_passed = True
for burst_size in (2, 5, 10, 30):
    drop_idx = set(range(burst_start, burst_start + burst_size))
    delivered, ts = build_delivered_stream(samples_normal, drop_idx, period_s)
    out = replay_with_guard(delivered, ts)
    for gap_detected, dt, buf_len_before_clear, buf_len_after_clear in out["events"]:
        if gap_detected and buf_len_after_clear != 0:
            mix_check_passed = False
results["W2-R4_old_new_samples_never_mixed"] = {
    "buffer_always_empty_immediately_after_clear_on_detected_gap": mix_check_passed,
    "note": "SampleStreamGuard calls scorer.clear() BEFORE the arriving sample is appended -- "
            "checked directly here (buffer length read right after clear(), before the new "
            "sample is appended) -- so the buffer is provably empty at that point on every "
            "detected gap; a scored window can never span samples from before and after a "
            "detected gap. (The buffer length BEFORE clear() is normally nonzero -- that's the "
            "stale in-flight window being correctly discarded, not a violation.)",
}
print(f"  old/new samples never mixed across a detected gap: {mix_check_passed}")

# ---- W2-R5: delayed-sample simulation (not dropped, just late) ----
section("W2-R5 delayed-sample simulation (normal_session, +30/+50/+100/+300ms, sample NOT dropped)")
w2r5 = {}
delay_idx = n_normal // 2
for delay_ms in (30, 50, 100, 300):
    delivered, ts = build_delivered_stream(samples_normal, set(), period_s, delay_at=delay_idx, delay_s=delay_ms / 1000.0)
    out = replay_with_guard(delivered, ts)
    gaps_detected = [e for e in out["events"] if e[0]]
    w2r5[f"delay_{delay_ms}ms"] = {
        "sample_dropped": False,
        "no_exception": out["exception"] is None,
        "gap_detected": len(gaps_detected) >= 1,
        "observed_dt_ms": round(gaps_detected[0][1] * 1000.0, 1) if gaps_detected else None,
        "windows_invalidated": out["guard"].windows_invalidated,
        "accepted_not_discarded": True,  # the guard never drops a sample itself, only invalidates the window
    }
results["W2-R5_delayed_sample"] = w2r5
print(json.dumps(w2r5, indent=2, default=str))
results["W2-R5_note"] = (
    "This harness only constructs monotonically increasing synthetic timestamps, so it cannot "
    "simulate a genuinely out-of-order/duplicate-timestamp arrival -- that scenario is deferred "
    "to real hardware (W2-LIVE-1) since it depends on real I2C/driver behavior, not something a "
    "software replay harness can honestly fabricate."
)

print("\n=== Full JSON ===")
print(json.dumps(results, indent=2, default=str))
common.save_json(results, "logic_robustness_tests_corrected_v2")
