"""Experiment C -- replay validation on real hardware (PI_RESEARCH_GUIDE.md
Section C, "the most important experiment").

deploy/crash_monitor.py uses a CAUSAL gravity-removal approximation
(CausalGravityFilter, an EMA) in real time; the offline training/evaluation
pipeline (src/units.py: remove_gravity) uses a zero-phase Butterworth filter.
Documented as a deliberate tradeoff, never before verified to agree in
practice. This script isolates JUST that difference: the SAME deployed INT8
TFLite model + SAME thresholds are used for both paths (no quantization
confound -- that's Experiment D's job), only the filter differs.

For each held-out TEST session:
  - "offline" predictions: canonicalize the session the normal way
    (preprocess.canonicalize_all -> zero-phase filter), window it with
    manifest.build_dataset, run each window through CrashModel.predict.
  - "real-time" predictions: feed the RAW per-sample stream (gyro converted
    to deg/s, accel still gravity-inclusive -- exactly what a live MPU6050
    would hand read_sensor()) through the REAL WindowScorer (causal filter),
    one sample at a time.
  - Window i (offline, stride-indexed) and the i-th successful
    WindowScorer.try_score() call cover the identical raw sample range, so
    they're compared index-for-index.

Run on the Pi (needs the full requirements.txt -- tensorflow -- not just
deploy/requirements.txt, since it reuses src/):
    python deploy/pi_research_suite/exp_c_replay_validation.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, preprocess, manifest, units


def any_trigger(probs, recons, classifier_t, recon_t, consecutive_windows, cooldown_seconds, stride_s):
    policy = cm.TriggerPolicy(classifier_t, recon_t, consecutive_windows, cooldown_seconds)
    fired = False
    for k, (p, r) in enumerate(zip(probs, recons)):
        _, triggered = policy.update(p, r, now=k * stride_s)
        fired = fired or triggered
    return fired


def main():
    cfg = common.load_config()
    stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    consecutive_windows = cfg["thresholds"]["consecutive_windows"]
    cooldown_seconds = cfg["thresholds"]["cooldown_seconds"]

    print("Loading sessions...")
    raw_sessions = io_loaders.load_all_sessions()
    split_of = manifest.assign_splits(raw_sessions)
    test_raw = [s for s in raw_sessions if split_of.get(s.session_id) == "test"]
    canonical_by_id = {s.session_id: s for s in preprocess.canonicalize_all(raw_sessions)}
    print(f"{len(raw_sessions)} total sessions, {len(test_raw)} in the test split.")

    model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])

    session_reports = []
    all_prob_diffs, all_recon_diffs = [], []
    window_agree_count, window_total = 0, 0
    event_agree_count = 0

    for s in test_raw:
        canon = canonical_by_id[s.session_id]
        ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
        if len(ds.y) == 0:
            continue

        offline_probs, offline_recons = [], []
        for i in range(len(ds.y)):
            p, r = model.predict(ds.X_seq[i], ds.X_aux[i])
            offline_probs.append(p)
            offline_recons.append(r)

        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)  # gyro->deg/s only; accel keeps gravity
        gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
        scorer = cm.WindowScorer(cfg, model, gravity_filter)
        rt_probs, rt_recons = [], []
        for row in df.itertuples():
            scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
            result = scorer.try_score()
            if result is not None:
                rt_probs.append(result["crash_prob"])
                rt_recons.append(result["recon_error"])

        n = min(len(offline_probs), len(rt_probs))
        if n == 0:
            continue
        offline_probs_a = np.array(offline_probs[:n])
        offline_recons_a = np.array(offline_recons[:n])
        rt_probs_a = np.array(rt_probs[:n])
        rt_recons_a = np.array(rt_recons[:n])

        prob_diff = np.abs(offline_probs_a - rt_probs_a)
        recon_diff = np.abs(offline_recons_a - rt_recons_a)
        all_prob_diffs.extend(prob_diff.tolist())
        all_recon_diffs.extend(recon_diff.tolist())

        offline_decision = (offline_probs_a > classifier_t) | (offline_recons_a > recon_t)
        rt_decision = (rt_probs_a > classifier_t) | (rt_recons_a > recon_t)
        window_agree_count += int((offline_decision == rt_decision).sum())
        window_total += n

        offline_fired = any_trigger(offline_probs_a, offline_recons_a, classifier_t, recon_t,
                                     consecutive_windows, cooldown_seconds, stride_s)
        rt_fired = any_trigger(rt_probs_a, rt_recons_a, classifier_t, recon_t,
                                consecutive_windows, cooldown_seconds, stride_s)
        event_agree = offline_fired == rt_fired
        event_agree_count += int(event_agree)

        session_reports.append({
            "session_id": s.session_id, "source": s.source, "label": s.label,
            "n_windows_offline": len(offline_probs), "n_windows_realtime": len(rt_probs),
            "n_windows_compared": n,
            "mean_abs_prob_diff": float(prob_diff.mean()),
            "mean_abs_recon_diff": float(recon_diff.mean()),
            "window_decision_agreement": float((offline_decision == rt_decision).mean()),
            "offline_event_fired": bool(offline_fired), "realtime_event_fired": bool(rt_fired),
            "event_agreement": bool(event_agree),
        })
        print(f"  {s.session_id} ({s.source}, label={s.label}): {n} windows, "
              f"window_agree={session_reports[-1]['window_decision_agreement']:.3f}, "
              f"event_agree={event_agree}")

    report = {
        "device": common.device_info(),
        "method": (
            "Same deployed INT8 TFLite model + same thresholds used for BOTH the offline "
            "(zero-phase Butterworth, canonicalize_all) and real-time (causal EMA, "
            "CausalGravityFilter via the real WindowScorer) paths -- isolates ONLY the filter "
            "difference, no quantization confound (see Experiment D)."
        ),
        "sessions": len(session_reports),
        "windows_compared": window_total,
        "window_decision_agreement": (window_agree_count / window_total) if window_total else None,
        "event_decision_agreement": (event_agree_count / len(session_reports)) if session_reports else None,
        "mean_abs_crash_prob_diff": float(np.mean(all_prob_diffs)) if all_prob_diffs else None,
        "mean_abs_recon_error_diff": float(np.mean(all_recon_diffs)) if all_recon_diffs else None,
        "per_session": session_reports,
    }
    print("\n=== Summary ===")
    print(json.dumps({k: v for k, v in report.items() if k != "per_session"}, indent=2))
    common.save_json(report, "c_replay_validation")


if __name__ == "__main__":
    main()
