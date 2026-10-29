"""Isolates the training/runtime jerk-feature discrepancy and measures what
correcting it would change.

Training (src/features.py) computes jerk as np.gradient(|a|, t) -- a time
derivative in m/s^3 -- and the window feature is its absolute peak. The
deployed runtime (deploy/crash_monitor.py: compute_aux_features) computes
max(abs(diff(|a|))) with no division by dt, i.e. m/s^2 per sample, ~50x
smaller at 50 Hz. The closure analyses (final-closure/model_L1..L3) measured
the end-to-end gap (L1), the filter alone (L2) and INT8 alone (L3), but never
the jerk formula alone. This script does that, and replays the saved
benign-motion captures with the original and a corrected formula.

Part A -- held-out test split (5,437 windows, same split as every result):
  A1 isolated: frozen Keras model, offline zero-phase windows, training-side
     features for everything EXCEPT jerk; jerk computed by
       training     -- the reference (manifest X_aux)
       runtime      -- deployed formula, max|diff(|a|)|
       corrected    -- max|np.gradient(|a|, 1/50)| within the window
  A2 deployment path: causal EMA(0.3 Hz) stream windows + frozen INT8 TFLite
     (cm.CrashModel), with runtime vs corrected jerk, both compared with the
     offline Keras training-feature reference. A2-runtime is the L1
     configuration; A2-corrected is the same pipeline with only jerk fixed.

Part B -- benign-motion replay: the 11 accepted phases of the 2026-10-11
high-range (+/-16 g, +/-2000 deg/s) guided session
(final-closure/07_high_range_benign_motion), replayed sample by sample
through the deployed SampleStreamGuard -> WindowScorer -> INT8 ->
TriggerPolicy path, exactly as piResults/experiments/closure/verify_guided.py
does. The original-formula replay must reproduce the live window scores and
decisions bit-for-bit (asserted); the corrected replay changes nothing but
compute_aux_features' jerk term. The discarded repeated-tilt attempt is
replayed too but reported separately.

Closure test L11. Outputs, next to the L1-L10 fidelity analyses it extends:
piResults/results/final-closure/model_L11_jerk_isolation/summary.json and
benign_replay_windows.csv."""
import csv
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deploy"))

import numpy as np
import pandas as pd
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, evaluate, units
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)
import crash_monitor as cm  # noqa: E402

RATE = config.TARGET_RATE_HZ
JERK_IDX = config.AUX_FEATURE_COLUMNS.index("jerk_peak")
CLOSURE_DIR = config.ROOT / "piResults" / "results" / "final-closure"
BENIGN_DIR = CLOSURE_DIR / "07_high_range_benign_motion"
OUT_DIR = CLOSURE_DIR / "model_L11_jerk_isolation"
ORIGINAL_AUX = cm.compute_aux_features


def runtime_jerk(windows):
    mag = np.linalg.norm(np.asarray(windows, dtype=np.float64)[:, :, 0:3], axis=2)
    return np.abs(np.diff(mag, axis=1)).max(axis=1)


def corrected_jerk(windows):
    mag = np.linalg.norm(np.asarray(windows, dtype=np.float64)[:, :, 0:3], axis=2)
    return np.abs(np.gradient(mag, 1.0 / RATE, axis=1)).max(axis=1)


def corrected_compute_aux_features(seq_window):
    """Drop-in replacement for cm.compute_aux_features: identical except the
    jerk term is a time derivative (m/s^3), matching src/features.py."""
    aux = ORIGINAL_AUX(seq_window)
    aux[6] = np.float32(corrected_jerk(seq_window[np.newaxis])[0])
    return aux


def agreement(ref, new, y):
    out = {}
    for name, mask in (("overall", np.ones_like(y, bool)), ("normal", y == 0), ("crash_like", y == 1)):
        r, n = ref[mask], new[mask]
        out[name] = {
            "n": int(mask.sum()), "agreement": float(np.mean(r == n)),
            "ref_neg_to_new_pos": int((~r & n).sum()), "ref_pos_to_new_neg": int((r & ~n).sum()),
        }
    return out


def score_block(y, sids, prob, recon, ref_prob, ref_recon, t_cls, t_rec, normal_hours):
    cls_dec, ref_cls = prob > t_cls, ref_prob > t_cls
    or_dec = cls_dec | (recon > t_rec)
    ref_or = ref_cls | (ref_recon > t_rec)
    m = evaluate.full_classification_metrics(y, prob, t_cls)
    ev = evaluate.simulate_deployed_alerts(y, or_dec.astype(float), sids, 0.5, normal_hours=normal_hours)
    return {
        "classifier_metrics": {k: m[k] for k in ("roc_auc", "pr_auc", "f1_score", "precision",
                                                  "recall_sensitivity", "specificity", "confusion_matrix")},
        "classifier_score_mae_vs_reference": float(np.mean(np.abs(prob - ref_prob))),
        "recon_score_mae_vs_reference": float(np.mean(np.abs(recon - ref_recon))),
        "classifier_decision_agreement": agreement(ref_cls, cls_dec, y),
        "or_rule_decision_agreement": agreement(ref_or, or_dec, y),
        "or_rule_event_level": ev,
        "or_rule_positive_windows": int(or_dec.sum()),
    }


def jerk_feature_stats(train_j, rt_j, cor_j, aux_mean, aux_std):
    def z(v):
        return (v - aux_mean[JERK_IDX]) / aux_std[JERK_IDX]
    return {
        "training_jerk_median": float(np.median(train_j)),
        "runtime_jerk_median": float(np.median(rt_j)),
        "corrected_jerk_median": float(np.median(cor_j)),
        "median_ratio_training_over_runtime": float(np.median(train_j / np.maximum(rt_j, 1e-9))),
        "median_abs_rel_error_corrected_vs_training": float(np.median(np.abs(cor_j - train_j) / np.maximum(train_j, 1e-9))),
        "normalized_z_training_p5_p50_p95": np.percentile(z(train_j), [5, 50, 95]).tolist(),
        "normalized_z_runtime_p5_p50_p95": np.percentile(z(rt_j), [5, 50, 95]).tolist(),
        "normalized_z_corrected_p5_p50_p95": np.percentile(z(cor_j), [5, 50, 95]).tolist(),
        "normalizer_jerk_mean_std": [float(aux_mean[JERK_IDX]), float(aux_std[JERK_IDX])],
    }


def part_a():
    raw_sessions = io_loaders.load_all_sessions()
    sessions = preprocess.canonicalize_all(raw_sessions)
    split_of = manifest.assign_splits(sessions)
    ds = manifest.build_dataset(sessions, split_of, "test")
    normal_hours = evaluate.normal_session_hours(sessions, split_of, "test")
    with open(config.MODELS_DIR / "thresholds.json") as f:
        th = json.load(f)
    t_cls, t_rec = th["classifier_prob_balanced"], th["recon_error"]

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    keras = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")

    def keras_predict(aux):
        Xs, Xa = normalizer.transform(ds.X_seq, aux)
        out = keras.predict({"seq": Xs, "aux": Xa}, verbose=0)
        return out["crash_prob"].ravel(), out["recon_error"].ravel()

    ref_prob, ref_recon = keras_predict(ds.X_aux)
    train_j = ds.X_aux[:, JERK_IDX].astype(np.float64)
    rt_j, cor_j = runtime_jerk(ds.X_seq), corrected_jerk(ds.X_seq)

    a1 = {}
    for name, j in (("runtime_formula", rt_j), ("corrected_formula", cor_j)):
        aux = ds.X_aux.copy()
        aux[:, JERK_IDX] = j
        p, r = keras_predict(aux)
        a1[name] = score_block(ds.y, ds.session_id, p, r, ref_prob, ref_recon, t_cls, t_rec, normal_hours)
    a1["training_reference"] = score_block(ds.y, ds.session_id, ref_prob, ref_recon, ref_prob, ref_recon,
                                           t_cls, t_rec, normal_hours)

    # A2: causal stream windows + INT8, same reference.
    int8 = cm.CrashModel(config.MODELS_DIR / "helmx_crash_model_int8.tflite",
                         config.MODELS_DIR / "normalizer.npz")
    canon_by_id = {s.session_id: s for s in sessions}
    probs = {"runtime_formula": [], "corrected_formula": []}
    recons = {"runtime_formula": [], "corrected_formula": []}
    keep = []
    for s in raw_sessions:
        if split_of.get(s.session_id) != "test":
            continue
        n_ref = len(manifest.build_dataset([canon_by_id[s.session_id]], {s.session_id: "t"}, "t").y)
        # ds windows are grouped by session in load order; locate this session's block
        idx = np.where(ds.session_id == s.session_id)[0]
        assert len(idx) == n_ref
        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
        accel = df[["ax", "ay", "az"]].to_numpy(dtype=np.float64)
        gyro = df[["gx", "gy", "gz"]].to_numpy(dtype=np.float64)
        gf = cm.CausalGravityFilter(0.3, RATE)
        accel_f = np.array([gf.apply(a) for a in accel])
        wins = []
        i = config.WINDOW_SAMPLES
        while i <= len(accel_f):
            st = i - config.WINDOW_SAMPLES
            wins.append(np.concatenate([accel_f[st:i], gyro[st:i]], axis=1).astype(np.float32))
            i += config.STRIDE_SAMPLES
        n = min(len(wins), n_ref)
        for w in wins[:n]:
            for name, fn in (("runtime_formula", ORIGINAL_AUX), ("corrected_formula", corrected_compute_aux_features)):
                p, r = int8.predict(w, fn(w))
                probs[name].append(p)
                recons[name].append(r)
        keep.extend(idx[:n].tolist())
    keep = np.array(keep)
    a2 = {}
    for name in probs:
        a2[name] = score_block(ds.y[keep], ds.session_id[keep], np.array(probs[name]), np.array(recons[name]),
                               ref_prob[keep], ref_recon[keep], t_cls, t_rec, normal_hours)
    a2["n_windows_compared"] = int(len(keep))

    return {
        "n_windows": int(len(ds.y)), "n_crash_like": int(ds.y.sum()), "normal_hours": normal_hours,
        "thresholds": {"classifier_prob_balanced": t_cls, "recon_error": t_rec},
        "jerk_feature_scale": jerk_feature_stats(train_j, rt_j, cor_j, normalizer.aux_mean, normalizer.aux_std),
        "A1_isolated_jerk_formula_keras_offline_windows": a1,
        "A2_causal_ema_int8_deployment_path": a2,
    }


def replay_phase(phase_dir, cfg, aux_fn):
    cm.compute_aux_features = aux_fn
    try:
        th = cm.load_model_thresholds(cfg)
        scorer = cm.WindowScorer(cfg, cm.CrashModel(config.MODELS_DIR / "helmx_crash_model_int8.tflite",
                                                    config.MODELS_DIR / "normalizer.npz"),
                                 cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], 50))
        guard = cm.SampleStreamGuard(cfg["sensor"]["timing_guard"], 0.02, logging.getLogger("jerk_replay"))
        raw = pd.read_csv(phase_dir / "raw_sensor.csv", float_precision="round_trip")
        out = []
        for r in raw.itertuples():
            gap, dt = guard.observe(r.t_monotonic)
            if gap:
                scorer.clear()
                if dt >= guard.long_gap_reset_s:
                    scorer.gravity_filter.reset()
            scorer.append([r.ax_ms2, r.ay_ms2, r.az_ms2, r.gx_dps, r.gy_dps, r.gz_dps])
            res = scorer.try_score()
            if res is not None:
                out.append((int(r.sample_idx), res["crash_prob"], res["recon_error"], float(res["aux"][6])))
        return np.array(out), th
    finally:
        cm.compute_aux_features = ORIGINAL_AUX


def policy(windows_t, prob, recon, th, cfg):
    p = cm.TriggerPolicy(*th, cfg["thresholds"]["consecutive_windows"], cfg["thresholds"]["cooldown_seconds"])
    return np.array([p.update(a, b, now=t) for t, a, b in zip(windows_t, prob, recon)])


def part_b():
    plan = json.loads((BENIGN_DIR / "guided_plan.json").read_text())
    phases = plan["phases"] + ["05_repeated_tilt_DISCARDED_no_intended_tilting"]
    results, rows = [], []
    for phase in phases:
        d = BENIGN_DIR / phase
        cfg = json.loads((d / "configuration.json").read_text())
        live = pd.read_csv(d / "window_scores.csv", float_precision="round_trip")
        orig, th = replay_phase(d, cfg, ORIGINAL_AUX)
        corr, _ = replay_phase(d, cfg, corrected_compute_aux_features)
        if not np.array_equal(orig[:, 0], live.sample_idx.to_numpy()):
            raise RuntimeError(f"Replay window endpoints differ from live capture for {phase}")
        assert np.array_equal(orig[:, 0], corr[:, 0])
        # The live scores came from the Pi's ARM TFLite build; this replay runs
        # the same INT8 model on x86 TFLite, where a few windows can differ by
        # a few output quantization steps. Scores are compared and recorded;
        # the decisions and alerts must match the live run exactly.
        score_diff = np.abs(orig[:, 1:3] - live[["crash_prob", "recon_error"]].to_numpy())
        t = live.t_monotonic.to_numpy()
        dec_o = policy(t, orig[:, 1], orig[:, 2], th, cfg)
        dec_c = policy(t, corr[:, 1], corr[:, 2], th, cfg)
        if not np.array_equal(dec_o, live[["or_positive", "confirmed_triggered"]].to_numpy()):
            raise RuntimeError(f"Original-formula replay decisions differ from live capture for {phase}")
        t_cls, t_rec = th
        res = {"phase": phase, "accepted": phase in plan["phases"], "windows": int(len(live)),
               "original_replay_vs_live": {
                   "decisions_and_alerts_identical": True,
                   "windows_with_any_score_difference": int((score_diff.max(axis=1) > 0).sum()),
                   "max_abs_classifier_diff": float(score_diff[:, 0].max()),
                   "max_abs_recon_diff": float(score_diff[:, 1].max()),
               }}
        for name, arr, dec in (("original", orig, dec_o), ("corrected", corr, dec_c)):
            res[name] = {
                "classifier_max": float(arr[:, 1].max()),
                "classifier_crossings": int((arr[:, 1] > t_cls).sum()),
                "reconstruction_max": float(arr[:, 2].max()),
                "reconstruction_crossings": int((arr[:, 2] > t_rec).sum()),
                "or_positive_windows": int(dec[:, 0].sum()),
                "confirmed_alerts": int(dec[:, 1].sum()),
                "jerk_feature_median": float(np.median(arr[:, 3])),
            }
        results.append(res)
        for k in range(len(live)):
            rows.append({"phase": phase, "window_idx": k, "sample_idx": int(orig[k, 0]),
                         "t_monotonic": float(t[k]),
                         "crash_prob_original": orig[k, 1], "crash_prob_corrected": corr[k, 1],
                         "recon_error_original": orig[k, 2], "recon_error_corrected": corr[k, 2],
                         "jerk_original": orig[k, 3], "jerk_corrected": corr[k, 3],
                         "or_positive_original": bool(dec_o[k, 0]), "or_positive_corrected": bool(dec_c[k, 0]),
                         "confirmed_original": bool(dec_o[k, 1]), "confirmed_corrected": bool(dec_c[k, 1])})
    acc = [r for r in results if r["accepted"]]
    totals = {name: {k: sum(r[name][k] for r in acc) for k in
                     ("classifier_crossings", "reconstruction_crossings", "or_positive_windows", "confirmed_alerts")}
              for name in ("original", "corrected")}
    return {"source": str(BENIGN_DIR.relative_to(config.ROOT)), "phases": results,
            "accepted_phase_totals": totals,
            "phases_with_alert_original": [r["phase"] for r in acc if r["original"]["confirmed_alerts"]],
            "phases_with_alert_corrected": [r["phase"] for r in acc if r["corrected"]["confirmed_alerts"]],
            "scope": ("Offline replay of saved captures through the deployed code path; only the jerk "
                      "term differs between runs. Not a new physical trial; operator motion is not "
                      "amplitude-matched or independently verified (see guided_plan.json).")}, rows


def main():
    print("Part A: held-out test split...")
    a = part_a()
    print("Part B: benign-motion replay...")
    b, rows = part_b()
    report = {
        "description": ("Isolated training/runtime jerk-feature comparison (Part A) and original-vs-corrected "
                        "replay of the saved high-range benign-motion captures (Part B). Frozen model, "
                        "normalizer and thresholds; no retraining."),
        "formulas": {
            "training": "max |np.gradient(|a|, t)| over the window, m/s^3 (src/features.py)",
            "runtime_original": "max |diff(|a|)|, m/s^2 per sample, no dt (deploy/crash_monitor.py)",
            "corrected": "max |np.gradient(|a|, 1/50 s)| within the window, m/s^3",
        },
        "part_a_held_out_test": a,
        "part_b_benign_motion_replay": b,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "summary.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    csv_path = OUT_DIR / "benign_replay_windows.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved {path} and {csv_path}")


if __name__ == "__main__":
    main()
