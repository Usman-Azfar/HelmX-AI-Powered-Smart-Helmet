"""Reviewer request (model-agnostic concern): apply the SAME offline
validation protocol used for the deployed HelmX model to a second, simpler
detector, so the paper's validation methodology is shown not to depend on the
particular hybrid network being validated.

This is an OFFLINE study only -- no new Raspberry Pi hardware campaign. It
reuses, unchanged, the frozen pipeline pieces the HelmX results were produced
with:

- session-level stratified split (src/manifest.py: assign_splits, seed 42);
- 60-sample / 15-stride windowing and canonical units (src/preprocess.py);
- validation-only threshold calibration (src/evaluate.py:
  choose_threshold_by_f1 / choose_threshold_by_recall, as scripts/train.py);
- window metrics, recall at 95% specificity, and the deployed event rule
  (3 consecutive windows + 60 s cooldown, real non-overlapping exposure
  hours) via src/evaluate.py and scripts/experiment_common.py;
- the three frozen external sets (STRIDE false-alarm data, scooter, SimRa)
  through their existing standalone loaders, no retraining, no recalibration;
- the unseen-DaRUS protocol (retrain without DaRUS, test on all 39 sessions);
- the causal-filter sensitivity replay (Section M1/M2 of
  deploy/pi_research_suite/exp_final_replay_analysis.py): causal EMA cutoffs
  0.1-0.5 Hz and a causal 2nd-order Butterworth at 0.3 Hz vs. the offline
  zero-phase reference, using the deployed CausalGravityFilter itself.

Simpler detectors evaluated (all use only window statistics, no neural net):

- accel_peak_rule: one threshold on peak |a| (gravity removed) -- the classic
  fixed-threshold fall/crash rule.
- gyro_peak_rule: one threshold on peak |omega|.
- logreg_7feat: standardized logistic regression on the 7 window statistics
  (accel/gyro magnitude mean, std, peak; peak jerk), trained on the train
  split only, class-balanced, C=1.0 fixed (no tuning on test).

Baseline features are computed by ONE function (window_features) for both the
offline and the causal-replay paths, using the deployed jerk definition
(deploy/crash_monitor.py: compute_aux_features). This deliberately avoids the
training/runtime jerk-scale mismatch already documented for HelmX in the
closure analyses (model_L1/L2/L3), so the baseline has no such skew.

IMPORTANT caveat, disclosed rather than hidden: for fall/near-fall (and the
scooter crash) sessions, window labels are assigned by the top-30% peak
|a| heuristic (src/manifest.py: _windows_for_session). accel_peak_rule's
score is that same quantity, so its window metrics on those sessions are
partly circular. Metrics are therefore also reported stratified by label
source; DaRUS windows carry genuine per-timestep ground truth and are free
of this circularity.

HelmX numbers in the same tables are recomputed here with the frozen Keras
model and models/thresholds.json, and cross-checked against the archived
JSONs (reproduction_check) so both detectors are scored by identical code.
HelmX unseen-DaRUS numbers are quoted from the archived
results/external-validation/unseen_crash_experiment.json (that experiment
retrains the network; not repeated here).

Outputs: results/experiments/baseline_simple_detector.json and
results/experiments/baseline_filter_sensitivity.csv."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deploy"))

import numpy as np
import tensorflow as tf
from scipy.signal import butter, lfilter
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src import config, io_loaders, preprocess, manifest, normalize, evaluate, units
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)
from experiment_common import evaluate_variant  # noqa: E402
from extended_false_alarm_evaluation import load_extended_normal_sessions  # noqa: E402
from external_test_scooter_dataset import load_external_scooter_sessions  # noqa: E402
from external_test_simra_dataset import load_external_simra_sessions  # noqa: E402
import crash_monitor as cm  # noqa: E402

FEATURE_NAMES = [
    "accel_mag_mean", "accel_mag_std", "accel_mag_peak",
    "gyro_mag_mean", "gyro_mag_std", "gyro_mag_peak",
    "jerk_peak_per_sample",
]
EMA_CUTOFFS = [0.1, 0.2, 0.3, 0.4, 0.5]
CONSECUTIVE_WINDOWS = 3
COOLDOWN_SECONDS = 60.0


def window_features(X_seq):
    """(N, 60, 6) canonical windows -> (N, 7), vectorized equivalent of
    deploy/crash_monitor.py: compute_aux_features."""
    X_seq = np.asarray(X_seq, dtype=np.float64)
    accel_mag = np.linalg.norm(X_seq[:, :, 0:3], axis=2)
    gyro_mag = np.linalg.norm(X_seq[:, :, 3:6], axis=2)
    jerk = np.abs(np.diff(accel_mag, axis=1)).max(axis=1)
    return np.column_stack([
        accel_mag.mean(1), accel_mag.std(1), accel_mag.max(1),
        gyro_mag.mean(1), gyro_mag.std(1), gyro_mag.max(1),
        jerk,
    ])


class Baselines:
    """Fits the three simple detectors on train, calibrates thresholds on
    val, then scores any windows."""

    def __init__(self, train_ds, val_ds):
        f_train = window_features(train_ds.X_seq)
        self.logreg = make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=2000, C=1.0),
        ).fit(f_train, train_ds.y)
        val_scores = self.score(val_ds.X_seq)
        self.thresholds = {}
        for name, s in val_scores.items():
            self.thresholds[name] = {
                "balanced": evaluate.choose_threshold_by_f1(val_ds.y, s),
                "high_recall": evaluate.choose_threshold_by_recall(val_ds.y, s, target_recall=0.90),
            }
        self.n_train_windows = int(len(train_ds.y))
        self.n_val_windows = int(len(val_ds.y))

    def score(self, X_seq):
        f = window_features(X_seq)
        return self.score_features(f)

    def score_features(self, f):
        return {
            "accel_peak_rule": f[:, 2],
            "gyro_peak_rule": f[:, 5],
            "logreg_7feat": self.logreg.predict_proba(f)[:, 1],
        }

    def describe(self):
        lr = self.logreg.named_steps["logisticregression"]
        return {
            "logreg_coefficients_standardized": dict(zip(FEATURE_NAMES, lr.coef_.ravel().tolist())),
            "logreg_intercept": float(lr.intercept_[0]),
            "thresholds_from_validation": self.thresholds,
            "n_train_windows": self.n_train_windows,
            "n_val_windows": self.n_val_windows,
        }


class HelmX:
    def __init__(self):
        self.normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
        self.model = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")
        with open(config.MODELS_DIR / "thresholds.json") as f:
            self.t = json.load(f)

    def predict(self, ds):
        X_seq, X_aux = self.normalizer.transform(ds.X_seq, ds.X_aux)
        out = self.model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
        return out["crash_prob"].ravel(), out["recon_error"].ravel()


def score_all(ds, helmx, baselines):
    """-> {detector_name: (scores, threshold)} for one dataset. The HelmX
    deployed OR rule is wrapped as a {0,1} score with threshold 0.5, exactly
    as the external-test scripts do."""
    prob, recon = helmx.predict(ds)
    t = helmx.t
    or_rule = ((prob > t["classifier_prob_balanced"]) | (recon > t["recon_error"])).astype(float)
    signals = {
        "helmx_classifier": (prob, t["classifier_prob_balanced"]),
        "helmx_deployed_or_rule": (or_rule, 0.5),
    }
    for name, s in baselines.score(ds.X_seq).items():
        signals[name] = (s, baselines.thresholds[name]["balanced"])
    return signals


def protocol_block(ds, signals, normal_hours):
    window, event = {}, {}
    for name, (scores, thresh) in signals.items():
        m = evaluate.full_classification_metrics(ds.y, scores, thresh)
        m.update({k: v for k, v in evaluate_variant(ds.y, scores, ds.session_id, thresh).items()
                  if k.startswith("recall_at") or k.startswith("specificity_achieved")})
        window[name] = m
        event[name] = evaluate.simulate_deployed_alerts(
            ds.y, scores, ds.session_id, thresh,
            consecutive=CONSECUTIVE_WINDOWS, cooldown_seconds=COOLDOWN_SECONDS,
            normal_hours=normal_hours if normal_hours and normal_hours > 0 else None,
        )
    return {"window_level": window, "event_level_deployed_rule": event}


def stratified_by_label_source(ds, signals, sessions):
    """Window metrics restricted to (a) DaRUS windows (true per-timestep
    labels) and (b) peak-heuristic-labeled fall/near-fall windows together
    with all normal-source windows."""
    frame_labeled = {s.session_id for s in sessions if s.frame_labels is not None}
    is_frame = np.array([sid in frame_labeled for sid in ds.session_id])
    out = {}
    for stratum, mask in {
        "darus_frame_labeled_only": is_frame,
        "excluding_darus": ~is_frame,
    }.items():
        if mask.sum() == 0 or len(set(ds.y[mask])) < 2:
            continue
        out[stratum] = {
            "n_windows": int(mask.sum()), "n_positive": int(ds.y[mask].sum()),
            "detectors": {
                name: {k: v for k, v in evaluate.full_classification_metrics(ds.y[mask], s[mask], t).items()
                       if k in ("roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity",
                                "specificity", "confusion_matrix")}
                for name, (s, t) in signals.items()
            },
        }
    out["note"] = (
        "Fall/near-fall positives are the top-30% peak-|a| windows of each session, so "
        "accel_peak_rule is partly scored against its own feature outside DaRUS; the DaRUS "
        "stratum uses genuine per-timestep impact labels."
    )
    out["sources_in_split"] = sorted(set(ds.source.tolist()))
    return out


def bootstrap_vs_helmx(ds, signals):
    base_s, base_t = signals["helmx_classifier"]
    return {
        name: evaluate.bootstrap_metric_difference(ds.y, base_s, base_t, s, t)
        for name, (s, t) in signals.items() if name not in ("helmx_classifier",)
    }


def external_set(name, sessions, helmx, baselines, distances_km=None):
    sessions = preprocess.canonicalize_all(sessions)
    label_of = {s.session_id: s.label for s in sessions}
    split_of = {s.session_id: "external" for s in sessions}
    ds = manifest.build_dataset(sessions, split_of, "external")
    secs = evaluate.session_durations_seconds(sessions)
    normal_hours = sum(v for sid, v in secs.items() if label_of[sid] == 0) / 3600.0
    signals = score_all(ds, helmx, baselines)
    block = protocol_block(ds, signals, normal_hours)
    if distances_km is not None:
        km = sum(d for d in distances_km.values() if d is not None)
        for ev in block["event_level_deployed_rule"].values():
            ev["false_alerts_per_km"] = ev["total_false_alert_events"] / km if km > 0 else None
        block["total_distance_km"] = km
    block.update({
        "dataset": name, "n_sessions": len(sessions),
        "n_positive_sessions": sum(label_of.values()), "n_windows": int(len(ds.y)),
        "n_positive_windows": int(ds.y.sum()), "normal_hours": normal_hours,
    })
    return block


def unseen_darus(all_sessions):
    non_darus = [s for s in all_sessions if s.source != "darus"]
    darus = [s for s in all_sessions if s.source == "darus"]
    split_of = manifest.assign_splits(non_darus)
    tr = manifest.build_dataset(non_darus, split_of, "train")
    va = manifest.build_dataset(non_darus, split_of, "val")
    b = Baselines(tr, va)
    d_split = {s.session_id: "unseen" for s in darus}
    ds = manifest.build_dataset(darus, d_split, "unseen")
    normal_hours = evaluate.normal_session_hours(darus, d_split, "unseen")
    signals = {n: (s, b.thresholds[n]["balanced"]) for n, s in b.score(ds.X_seq).items()}
    block = protocol_block(ds, signals, normal_hours)

    archived_path = config.EXTERNAL_VALIDATION_DIR / "unseen_crash_experiment.json"
    with open(archived_path) as f:
        arch = json.load(f)
    block["helmx_archived_for_comparison"] = {
        "source": str(archived_path.relative_to(config.ROOT)),
        "classifier_only": {k: arch["classifier_only"].get(k) for k in
                            ("roc_auc", "pr_auc", "f1_score", "recall_sensitivity", "specificity")},
        "reconstruction_only_mean": {k: arch["reconstruction_only_mean"].get(k) for k in
                                     ("roc_auc", "pr_auc", "f1_score", "recall_sensitivity", "specificity")},
        "deployed_alert_simulation": arch.get("deployed_alert_simulation"),
    }
    block["baseline_fit"] = b.describe()
    block.update({"n_darus_sessions": len(darus), "n_windows": int(len(ds.y)),
                  "n_positive_windows": int(ds.y.sum())})
    return block


def _windows_from_stream(accel, gyro):
    n = len(accel)
    out = []
    i = config.WINDOW_SAMPLES
    while i <= n:
        s = i - config.WINDOW_SAMPLES
        out.append(np.concatenate([accel[s:i], gyro[s:i]], axis=1))
        i += config.STRIDE_SAMPLES
    return np.stack(out) if out else np.empty((0, config.WINDOW_SAMPLES, 6))


def _event_fired(decisions, stride_s):
    """Same confirmation logic as deploy/crash_monitor.py: TriggerPolicy,
    driven with replayed timestamps."""
    streak, cooldown_until, fired = 0, 0.0, False
    for k, d in enumerate(decisions):
        now = k * stride_s
        streak = streak + 1 if d else 0
        if streak >= CONSECUTIVE_WINDOWS and now >= cooldown_until:
            fired, streak, cooldown_until = True, 0, now + COOLDOWN_SECONDS
    return fired


def filter_sensitivity(raw_sessions, canonical_by_id, split_of, baselines):
    """Section M1/M2 protocol for the baselines: causal-filter replay of each
    test session vs. the offline zero-phase reference windows."""
    rate = config.TARGET_RATE_HZ
    stride_s = config.STRIDE_SAMPLES / rate
    rows = []
    for s in raw_sessions:
        if split_of.get(s.session_id) != "test":
            continue
        canon = canonical_by_id[s.session_id]
        ref_ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
        if len(ref_ds.y) == 0:
            continue
        ref_scores = baselines.score(ref_ds.X_seq)

        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
        accel_raw = df[["ax", "ay", "az"]].to_numpy(dtype=np.float64)
        gyro = df[["gx", "gy", "gz"]].to_numpy(dtype=np.float64)

        variants = {}
        for c in EMA_CUTOFFS:
            gf = cm.CausalGravityFilter(c, rate)
            variants[c] = np.array([gf.apply(a) for a in accel_raw])
        b, a = butter(2, 0.3 / (rate / 2.0), btype="highpass")
        variants["causal_butterworth_0.3"] = lfilter(b, a, accel_raw, axis=0)

        for cutoff, accel_f in variants.items():
            win = _windows_from_stream(accel_f, gyro)
            if len(win) == 0:
                continue
            rt_scores = baselines.score(win)
            n = min(len(ref_ds.y), len(win))
            for name in ref_scores:
                t = baselines.thresholds[name]["balanced"]
                off, rt = ref_scores[name][:n], rt_scores[name][:n]
                off_dec, rt_dec = off >= t, rt >= t
                off_fired, rt_fired = _event_fired(off_dec, stride_s), _event_fired(rt_dec, stride_s)
                with np.errstate(invalid="ignore", divide="ignore"):
                    corr = float(np.corrcoef(off, rt)[0, 1]) if n > 1 else float("nan")
                rows.append({
                    "detector": name, "session_id": s.session_id, "label": s.label,
                    "cutoff_hz": cutoff, "n_windows": n,
                    "score_mae": float(np.mean(np.abs(off - rt))),
                    "score_mae_relative_to_threshold": float(np.mean(np.abs(off - rt)) / t) if t else None,
                    "score_corr": corr,
                    "n_decision_flips": int((off_dec != rt_dec).sum()),
                    "event_trigger_agreement": bool(off_fired == rt_fired),
                    "offline_event_fired": bool(off_fired), "cutoff_event_fired": bool(rt_fired),
                })
    return rows


def summarize_filter_rows(rows):
    out = {}
    for det in sorted({r["detector"] for r in rows}):
        out[det] = {}
        for c in EMA_CUTOFFS + ["causal_butterworth_0.3"]:
            sel = [r for r in rows if r["detector"] == det and r["cutoff_hz"] == c]
            if not sel:
                continue
            corrs = [r["score_corr"] for r in sel if r["score_corr"] == r["score_corr"]]
            out[det][str(c)] = {
                "n_sessions": len(sel),
                "n_windows": sum(r["n_windows"] for r in sel),
                "mean_session_score_mae": float(np.mean([r["score_mae"] for r in sel])),
                "mean_session_score_mae_relative_to_threshold": float(np.mean(
                    [r["score_mae_relative_to_threshold"] for r in sel])),
                "mean_session_score_corr": float(np.mean(corrs)) if corrs else None,
                "total_decision_flips": sum(r["n_decision_flips"] for r in sel),
                "sessions_event_agreement": sum(r["event_trigger_agreement"] for r in sel),
                "sessions_offline_fired": sum(r["offline_event_fired"] for r in sel),
                "sessions_causal_fired": sum(r["cutoff_event_fired"] for r in sel),
                "disagreeing_sessions": [
                    {"session_id": r["session_id"], "label": r["label"],
                     "offline_fired": r["offline_event_fired"], "causal_fired": r["cutoff_event_fired"]}
                    for r in sel if not r["event_trigger_agreement"]
                ],
            }
    return out


def reproduction_check(test_block, ext_blocks):
    """Recomputed HelmX numbers vs. the archived result JSONs."""
    checks = []

    def add(label, archived, recomputed):
        ok = archived is not None and recomputed is not None and abs(archived - recomputed) < 1e-6
        checks.append({"metric": label, "archived": archived, "recomputed": recomputed, "match": bool(ok)})

    with open(config.METRICS_DIR / "test_metrics.json") as f:
        tm = json.load(f)
    add("test classifier_only_balanced f1", tm["classifier_only_balanced"]["f1"],
        test_block["window_level"]["helmx_classifier"]["f1_score"])
    add("test classifier_only_balanced roc_auc", tm["classifier_only_balanced"]["roc_auc"],
        test_block["window_level"]["helmx_classifier"]["roc_auc"])
    add("test deployed false_alerts_per_hour (classifier balanced)",
        tm["deployed_alert_simulation"]["classifier_only_balanced"]["false_alerts_per_hour"],
        test_block["event_level_deployed_rule"]["helmx_classifier"]["false_alerts_per_hour"])
    for key, fname in (("scooter", "external_test_scooter_dataset.json"),
                       ("simra", "external_test_simra_dataset.json")):
        with open(config.EXTERNAL_VALIDATION_DIR / fname) as f:
            arch = json.load(f)
        add(f"{key} model_a_classifier roc_auc", arch["window_level_metrics"]["model_a_classifier"]["roc_auc"],
            ext_blocks[key]["window_level"]["helmx_classifier"]["roc_auc"])
        add(f"{key} OR-rule event session_recall",
            arch["event_level_deployed_alert_simulation"]["hybrid_or_fusion_deployed_rule"]["session_recall"],
            ext_blocks[key]["event_level_deployed_rule"]["helmx_deployed_or_rule"]["session_recall"])
    with open(config.EXTERNAL_VALIDATION_DIR / "extended_false_alarm_evaluation.json") as f:
        arch = json.load(f)
    add("stride classifier false alert events",
        arch["deployed_alert_simulation_new_data_only"]["total_false_alert_events"],
        ext_blocks["stride"]["event_level_deployed_rule"]["helmx_classifier"]["total_false_alert_events"])
    return checks


def main():
    print("Loading + canonicalizing sessions...")
    raw_sessions = io_loaders.load_all_sessions()
    sessions = preprocess.canonicalize_all(raw_sessions)
    canonical_by_id = {s.session_id: s for s in sessions}
    split_of = manifest.assign_splits(sessions)
    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"train/val/test windows: {len(train_ds.y)}/{len(val_ds.y)}/{len(test_ds.y)}")

    baselines = Baselines(train_ds, val_ds)
    helmx = HelmX()

    print("Held-out test split...")
    normal_hours = evaluate.normal_session_hours(sessions, split_of, "test")
    signals = score_all(test_ds, helmx, baselines)
    test_block = protocol_block(test_ds, signals, normal_hours)
    test_block["high_recall_operating_point"] = {
        name: evaluate.simulate_deployed_alerts(
            test_ds.y, s, test_ds.session_id, baselines.thresholds[name]["high_recall"],
            normal_hours=normal_hours)
        for name, s in baselines.score(test_ds.X_seq).items()
    }
    test_block["stratified_by_label_source"] = stratified_by_label_source(test_ds, signals, sessions)
    test_block["paired_bootstrap_f1_vs_helmx_classifier"] = bootstrap_vs_helmx(test_ds, signals)
    test_block.update({"n_windows": int(len(test_ds.y)), "n_positive_windows": int(test_ds.y.sum()),
                       "normal_hours": normal_hours})

    print("External sets...")
    stride_sessions, stride_km = load_extended_normal_sessions()
    ext = {
        "stride": external_set("STRIDE extended normal road (false-alarm only)", stride_sessions,
                               helmx, baselines, distances_km=stride_km),
        "scooter": external_set("Scooter riding + overturn/collision", load_external_scooter_sessions(),
                                helmx, baselines),
        "simra": external_set("SimRa bicycle near-miss", load_external_simra_sessions(), helmx, baselines),
    }

    print("Unseen-DaRUS protocol (baselines retrained without DaRUS)...")
    unseen = unseen_darus(sessions)

    print("Causal-filter sensitivity replay...")
    rows = filter_sensitivity(raw_sessions, canonical_by_id, split_of, baselines)
    config.EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = config.EXPERIMENTS_DIR / "baseline_filter_sensitivity.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    report = {
        "description": (
            "Offline application of the HelmX validation protocol to three simpler, non-neural "
            "detectors (single-threshold accel-peak and gyro-peak rules; 7-feature logistic "
            "regression). Same split, windowing, validation-only threshold calibration, deployed "
            "event rule (3 windows + 60 s cooldown), frozen external sets, unseen-DaRUS retrain, "
            "and causal-filter replay. No Raspberry Pi hardware runs."
        ),
        "detectors": {
            "accel_peak_rule": "score = peak |a| (m/s^2, gravity removed) in the 1.2 s window",
            "gyro_peak_rule": "score = peak |omega| (deg/s) in the 1.2 s window",
            "logreg_7feat": "StandardScaler + LogisticRegression(C=1, class_weight=balanced) on "
                            + ", ".join(FEATURE_NAMES),
            "helmx_classifier": "frozen HelmX classifier head, classifier_prob_balanced threshold",
            "helmx_deployed_or_rule": "frozen HelmX classifier OR reconstruction rule (deployed)",
        },
        "label_circularity_caveat": (
            "Outside DaRUS, positive windows are chosen by the top-30% peak-|a| heuristic, which is "
            "accel_peak_rule's own score; see held_out_test.stratified_by_label_source."
        ),
        "baseline_fit": baselines.describe(),
        "held_out_test": test_block,
        "external": ext,
        "unseen_darus": unseen,
        "filter_sensitivity_summary": summarize_filter_rows(rows),
        "filter_sensitivity_csv": str(csv_path.relative_to(config.ROOT)),
    }
    report["reproduction_check"] = reproduction_check(test_block, ext)
    path = evaluate.save_metrics(report, "baseline_simple_detector")
    print(f"Saved {path} and {csv_path}")
    for c in report["reproduction_check"]:
        print(("OK  " if c["match"] else "DIFF"), c["metric"], c["archived"], c["recomputed"])


if __name__ == "__main__":
    main()
