"""Checklist items 3.22 (FP16 vs INT8 event-level agreement), 3.23 (threshold-
margin analysis), 3.24 (reconstruction-error quantization comparison), 3.25
(OR-rule branch contribution), 3.26 (detailed causal-filter comparison
extended beyond Experiment C's binary agreement number). One script since
they all reuse the same test-split load + the same Keras/FP16/INT8 model
predictions (computed once, reused five ways) and Experiment C's offline-vs-
causal window pairs.

Run on the Pi (needs full requirements.txt -- tensorflow):
    python deploy/pi_research_suite/exp_extended_ablation_batch.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
import crash_monitor as cm
from src import io_loaders, preprocess, manifest, normalize, units
from src import model as model_lib  # noqa: F401


def tflite_predict_all(path, X_seq, X_aux):
    interp = tflite.Interpreter(model_path=str(path))
    interp.allocate_tensors()
    runner = interp.get_signature_runner()
    probs, recons = [], []
    for i in range(len(X_seq)):
        out = runner(seq=X_seq[i:i + 1], aux=X_aux[i:i + 1])
        probs.append(float(out["crash_prob"][0, 0]))
        recons.append(float(out["recon_error"][0, 0]))
    return np.array(probs), np.array(recons)


def main():
    cfg = common.load_config()
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    consecutive_windows = cfg["thresholds"]["consecutive_windows"]
    cooldown_seconds = cfg["thresholds"]["cooldown_seconds"]
    stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]

    print("Loading sessions, building test split (offline canonicalized)...")
    raw_sessions = io_loaders.load_all_sessions()
    split_of = manifest.assign_splits(raw_sessions)
    canon_sessions = preprocess.canonicalize_all(raw_sessions)
    ds = manifest.build_dataset(canon_sessions, split_of, "test")
    normalizer = normalize.Normalizer.load(ROOT / "models" / "normalizer.npz")
    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    X_seq, X_aux = X_seq.astype(np.float32), X_aux.astype(np.float32)
    print(f"Test split: {len(ds.y)} windows across {len(set(ds.session_id.tolist()))} sessions.")

    keras_model = tf.keras.models.load_model(ROOT / "models" / "helmx_crash_model.keras")
    keras_out = keras_model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    keras_probs = keras_out["crash_prob"].ravel()
    keras_recons = keras_out["recon_error"].ravel()

    print("Running FP16 + INT8 TFLite over the same windows...")
    fp16_probs, fp16_recons = tflite_predict_all(ROOT / "models/helmx_crash_model_fp16.tflite", X_seq, X_aux)
    int8_probs, int8_recons = tflite_predict_all(ROOT / "models/helmx_crash_model_int8.tflite", X_seq, X_aux)

    report = {"device": common.device_info(), "n_test_windows": int(len(ds.y))}

    # ---- 3.23 Threshold-margin analysis (INT8, the deployed model) ----
    margins = [0.001, 0.005, 0.01, 0.05]
    dist_to_threshold = np.abs(int8_probs - classifier_t)
    margin_counts = {f"within_{m}": int((dist_to_threshold <= m).sum()) for m in margins}
    report["3.23_threshold_margin_analysis"] = {
        "classifier_threshold": classifier_t,
        "counts": margin_counts,
        "fraction_of_test_set": {k: v / len(ds.y) for k, v in margin_counts.items()},
        "note": "How many held-out windows land within epsilon of the deployed decision boundary "
                "-- explains why INT8 quantization drift (Experiment D) rarely flips the real "
                "deployed decision: most windows sit far from the boundary either way.",
    }

    # ---- 3.24 Reconstruction-error quantization comparison ----
    def recon_stats(name, recons, ref_recons):
        decisions = recons > recon_t
        ref_decisions = ref_recons > recon_t
        return {
            "mean_abs_diff_vs_keras": float(np.mean(np.abs(recons - ref_recons))),
            "max_abs_diff_vs_keras": float(np.max(np.abs(recons - ref_recons))),
            "threshold_crossing_agreement_vs_keras": float(np.mean(decisions == ref_decisions)),
        }
    report["3.24_reconstruction_error_quantization"] = {
        "recon_threshold": recon_t,
        "fp16": recon_stats("fp16", fp16_recons, keras_recons),
        "int8": recon_stats("int8", int8_recons, keras_recons),
    }

    # ---- 3.25 OR-rule branch contribution (INT8, deployed thresholds) ----
    clf_positive = int8_probs > classifier_t
    recon_positive = int8_recons > recon_t
    classifier_only = int(np.sum(clf_positive & ~recon_positive))
    recon_only = int(np.sum(~clf_positive & recon_positive))
    both = int(np.sum(clf_positive & recon_positive))
    neither = int(np.sum(~clf_positive & ~recon_positive))
    report["3.25_or_rule_branch_contribution_window_level"] = {
        "classifier_only_positive": classifier_only, "reconstruction_only_positive": recon_only,
        "both_positive": both, "neither": neither,
        "total": int(len(ds.y)),
    }

    # Event-level: which branch's signal was actually present on the window that caused each
    # session's real TriggerPolicy to fire (per session, using INT8 -- the deployed model).
    session_ids = ds.session_id
    event_branch = []
    for sid in sorted(set(session_ids.tolist())):
        idx = np.where(session_ids == sid)[0]
        policy = cm.TriggerPolicy(classifier_t, recon_t, consecutive_windows, cooldown_seconds)
        fired_by = None
        for k, i in enumerate(idx):
            is_anomaly, triggered = policy.update(float(int8_probs[i]), float(int8_recons[i]), now=k * stride_s)
            if triggered:
                c = bool(clf_positive[i]); r = bool(recon_positive[i])
                fired_by = "both" if (c and r) else ("classifier_only" if c else ("reconstruction_only" if r else "neither(!)"))
                break
        event_branch.append({"session_id": sid, "label": int(ds.y[idx[0]]) if len(idx) else None,
                              "event_fired": fired_by is not None, "fired_by_branch": fired_by})
    report["3.25_or_rule_branch_contribution_event_level"] = event_branch

    # ---- 3.26 Detailed causal-filter comparison (extends Experiment C) ----
    print("Re-running the offline-vs-causal-filter comparison (Experiment C) with richer stats...")
    canonical_by_id = {s.session_id: s for s in canon_sessions}
    raw_test = [s for s in raw_sessions if split_of.get(s.session_id) == "test"]
    model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])

    all_offline_probs, all_rt_probs = [], []
    all_offline_recons, all_rt_recons = [], []
    all_sources, all_labels = [], []
    for s in raw_test:
        canon = canonical_by_id[s.session_id]
        sess_ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
        if len(sess_ds.y) == 0:
            continue
        off_p, off_r = [], []
        for i in range(len(sess_ds.y)):
            p, r = model.predict(sess_ds.X_seq[i], sess_ds.X_aux[i])
            off_p.append(p); off_r.append(r)

        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
        gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
        scorer = cm.WindowScorer(cfg, model, gf)
        rt_p, rt_r = [], []
        for row in df.itertuples():
            scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
            res = scorer.try_score()
            if res is not None:
                rt_p.append(res["crash_prob"]); rt_r.append(res["recon_error"])

        n = min(len(off_p), len(rt_p))
        if n == 0:
            continue
        all_offline_probs.extend(off_p[:n]); all_rt_probs.extend(rt_p[:n])
        all_offline_recons.extend(off_r[:n]); all_rt_recons.extend(rt_r[:n])
        all_sources.extend([s.source] * n)
        all_labels.extend([s.label] * n)

    off_p_arr, rt_p_arr = np.array(all_offline_probs), np.array(all_rt_probs)
    off_r_arr, rt_r_arr = np.array(all_offline_recons), np.array(all_rt_recons)
    labels_arr = np.array(all_labels)
    sources_arr = np.array(all_sources)
    prob_diff = off_p_arr - rt_p_arr
    recon_diff = off_r_arr - rt_r_arr

    def per_group_stats(mask, name):
        if mask.sum() == 0:
            return None
        return {
            "n": int(mask.sum()),
            "mean_abs_prob_diff": float(np.mean(np.abs(prob_diff[mask]))),
            "mean_abs_recon_diff": float(np.mean(np.abs(recon_diff[mask]))),
        }

    report["3.26_detailed_causal_filter_comparison"] = {
        "n_windows": int(len(off_p_arr)),
        "prob_correlation_offline_vs_realtime": float(np.corrcoef(off_p_arr, rt_p_arr)[0, 1]),
        "recon_correlation_offline_vs_realtime": float(np.corrcoef(off_r_arr, rt_r_arr)[0, 1]),
        "prob_diff_distribution": {
            "mean": float(np.mean(prob_diff)), "std": float(np.std(prob_diff)),
            "max_abs": float(np.max(np.abs(prob_diff))), "p95_abs": float(np.percentile(np.abs(prob_diff), 95)),
        },
        "recon_diff_distribution": {
            "mean": float(np.mean(recon_diff)), "std": float(np.std(recon_diff)),
            "max_abs": float(np.max(np.abs(recon_diff))), "p95_abs": float(np.percentile(np.abs(recon_diff), 95)),
        },
        "by_source": {src: per_group_stats(sources_arr == src, src) for src in sorted(set(all_sources))},
        "by_class": {
            "normal(label=0)": per_group_stats(labels_arr == 0, "normal"),
            "crash_like(label=1)": per_group_stats(labels_arr == 1, "crash_like"),
        },
    }

    # ---- 3.22 FP16 vs INT8 event-level agreement (using the offline-canonicalized test split) ----
    def event_fired_sessions(probs, recons):
        fired = {}
        for sid in sorted(set(session_ids.tolist())):
            idx = np.where(session_ids == sid)[0]
            policy = cm.TriggerPolicy(classifier_t, recon_t, consecutive_windows, cooldown_seconds)
            f = False
            trigger_k = None
            for k, i in enumerate(idx):
                _, triggered = policy.update(float(probs[i]), float(recons[i]), now=k * stride_s)
                if triggered:
                    f = True
                    trigger_k = k
                    break
            fired[sid] = {"fired": f, "trigger_window_idx": trigger_k}
        return fired

    fp16_events = event_fired_sessions(fp16_probs, fp16_recons)
    int8_events = event_fired_sessions(int8_probs, int8_recons)
    agree = sum(1 for sid in fp16_events if fp16_events[sid]["fired"] == int8_events[sid]["fired"])
    missed_by_int8_only = [sid for sid in fp16_events if fp16_events[sid]["fired"] and not int8_events[sid]["fired"]]
    extra_by_int8_only = [sid for sid in fp16_events if not fp16_events[sid]["fired"] and int8_events[sid]["fired"]]
    report["3.22_fp16_vs_int8_event_level_agreement"] = {
        "n_sessions": len(fp16_events),
        "agreement": agree / len(fp16_events),
        "sessions_fp16_fired_int8_missed": missed_by_int8_only,
        "sessions_int8_fired_fp16_missed": extra_by_int8_only,
        "fp16_events": fp16_events, "int8_events": int8_events,
    }

    print("\n=== Summary (full detail in JSON) ===")
    summary = {k: v for k, v in report.items() if k not in ("3.25_or_rule_branch_contribution_event_level",)}
    print(json.dumps(summary, indent=2)[:6000])
    common.save_json(report, "extended_ablation_batch")


if __name__ == "__main__":
    main()
