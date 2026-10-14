"""HelmX_FInal_Pi_REqwuirements.md sections K, L, M1, M2, N1, N2, O -- all
replay-based analyses on frozen test/val-split data, no live sensor needed.
Loads models/data once and runs every section in one pass to avoid repeated
TF model loads.

Run on the Pi (or any dev machine with the full training-side package):
    .pi_research_venv/bin/python deploy/pi_research_suite/exp_final_replay_analysis.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from scipy.signal import butter, lfilter, freqz

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
from src import io_loaders, preprocess, manifest, normalize, units, config as src_config
from src import model as model_lib  # noqa: F401 (registers custom layers/losses for load_model)

OUT_DIR = ROOT / "piResults" / "results" / "final-validation"


def tflite_predict_all(path, X_seq, X_aux, preserve_all_tensors=False):
    if preserve_all_tensors:
        interpreter = tf.lite.Interpreter(model_path=str(path), experimental_preserve_all_tensors=True)
    else:
        interpreter = tflite.Interpreter(model_path=str(path))
    interpreter.allocate_tensors()
    runner = interpreter.get_signature_runner()
    probs, recons = [], []
    for i in range(len(X_seq)):
        out = runner(seq=X_seq[i:i + 1], aux=X_aux[i:i + 1])
        probs.append(float(out["crash_prob"][0, 0]))
        recons.append(float(out["recon_error"][0, 0]))
    return np.array(probs), np.array(recons), interpreter


def section_k_int8_outlier(ds, X_seq, X_aux, keras_probs, keras_recons, int8_probs, int8_recons,
                            fp16_probs, fp16_recons, classifier_t, recon_t):
    print("\n=== Section K: INT8 reconstruction-outlier diagnostic ===")
    diffs = np.abs(int8_recons - keras_recons)
    idx = int(np.argmax(diffs))
    print(f"Outlier window index (test-split order): {idx}, |diff|={diffs[idx]:.4f}")
    print(f"Session: {ds.session_id[idx]}, weak label: {int(ds.y[idx])}")

    int8_path = ROOT / "models/helmx_crash_model_int8.tflite"
    interpreter = tf.lite.Interpreter(model_path=str(int8_path), experimental_preserve_all_tensors=True)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    seq_name_to_idx = {d["name"]: d["index"] for d in input_details}
    for d in input_details:
        if "seq" in d["name"]:
            interpreter.set_tensor(d["index"], X_seq[idx:idx + 1])
        elif "aux" in d["name"]:
            interpreter.set_tensor(d["index"], X_aux[idx:idx + 1])
    interpreter.invoke()

    tensor_trace = []
    for det in interpreter.get_tensor_details():
        try:
            t = interpreter.get_tensor(det["index"])
        except ValueError:
            continue
        quant = det.get("quantization_parameters", {})
        entry = {
            "name": det["name"], "index": det["index"], "dtype": str(det["dtype"]),
            "shape": list(t.shape) if hasattr(t, "shape") else None,
            "quant_scales": [float(s) for s in quant.get("scales", [])][:5],
            "quant_zero_points": [int(z) for z in quant.get("zero_points", [])][:5],
        }
        if t.size > 0 and np.issubdtype(t.dtype, np.number):
            entry["min"] = float(t.min())
            entry["max"] = float(t.max())
            entry["mean"] = float(t.mean())
            if t.dtype == np.int8:
                entry["count_at_int8_min_-128"] = int((t == -128).sum())
                entry["count_at_int8_max_127"] = int((t == 127).sum())
        tensor_trace.append(entry)

    seq_win = X_seq[idx]
    aux_win = X_aux[idx]
    summary = {
        "outlier_window_index_test_split": idx,
        "session_id": str(ds.session_id[idx]),
        "weak_label": int(ds.y[idx]),
        "reference_outputs": {
            "keras": {"classifier_prob": float(keras_probs[idx]), "recon_error": float(keras_recons[idx])},
            "fp16_tflite": {"classifier_prob": float(fp16_probs[idx]), "recon_error": float(fp16_recons[idx])},
            "int8_tflite": {"classifier_prob": float(int8_probs[idx]), "recon_error": float(int8_recons[idx])},
        },
        "operational_decisions": {
            name: {
                "classifier_threshold_crossed": bool(p > classifier_t),
                "recon_threshold_crossed": bool(r > recon_t),
                "or_rule_positive": bool(p > classifier_t or r > recon_t),
            }
            for name, (p, r) in {
                "keras": (keras_probs[idx], keras_recons[idx]),
                "fp16": (fp16_probs[idx], fp16_recons[idx]),
                "int8": (int8_probs[idx], int8_recons[idx]),
            }.items()
        },
        "input_characterization": {
            "seq_normalized_min": float(seq_win.min()), "seq_normalized_max": float(seq_win.max()),
            "per_channel_min": [float(x) for x in seq_win.min(axis=0)],
            "per_channel_max": [float(x) for x in seq_win.max(axis=0)],
            "aux_normalized_values": [float(x) for x in aux_win],
        },
        "quantization_characterization": {
            "input_details": [
                {"name": d["name"], "dtype": str(d["dtype"]),
                 "scale": float(d["quantization_parameters"]["scales"][0]) if len(d["quantization_parameters"]["scales"]) else None,
                 "zero_point": int(d["quantization_parameters"]["zero_points"][0]) if len(d["quantization_parameters"]["zero_points"]) else None}
                for d in input_details
            ],
            "output_details": [
                {"name": d["name"], "dtype": str(d["dtype"]),
                 "scale": float(d["quantization_parameters"]["scales"][0]) if len(d["quantization_parameters"]["scales"]) else None,
                 "zero_point": int(d["quantization_parameters"]["zero_points"][0]) if len(d["quantization_parameters"]["zero_points"]) else None}
                for d in output_details
            ],
        },
        "first_layer_note": (
            "See int8_outlier_tensors.json for the full per-tensor trace (preserve_all_tensors). "
            "No cause is asserted here beyond what the tensor min/max/saturation-count data directly "
            "shows -- do not guess the mechanism if the trace doesn't clearly localize it."
        ),
    }

    OUT_DIR.joinpath("int8_outlier", "int8_outlier_summary.json").write_text(json.dumps(summary, indent=2))
    OUT_DIR.joinpath("int8_outlier", "int8_outlier_tensors.json").write_text(json.dumps(tensor_trace, indent=2))
    np.savez(OUT_DIR / "int8_outlier" / "int8_outlier_tensors.npz",
              seq_normalized=seq_win, aux_normalized=aux_win)
    print(f"Wrote {OUT_DIR / 'int8_outlier'}")
    return summary


def section_l_representative_audit(sessions_canonical, split_of):
    print("\n=== Section L: INT8 representative-dataset audit ===")
    val_ds = manifest.build_dataset(sessions_canonical, split_of, "val")
    normalizer = normalize.Normalizer.load(ROOT / "models" / "normalizer.npz")
    X_seq_val, X_aux_val = normalizer.transform(val_ds.X_seq, val_ds.X_aux)

    n = min(200, len(X_seq_val))
    idx = np.random.default_rng(src_config.RANDOM_SEED).choice(len(X_seq_val), n, replace=False)

    def summarize(mask_idx, label):
        sids = val_ds.session_id[mask_idx]
        labels = val_ds.y[mask_idx]
        sources = [sid.split("_")[0] if "_" in sid else sid for sid in sids]
        seq = X_seq_val[mask_idx]
        return {
            "label": label, "n": int(len(mask_idx)),
            "n_normal": int((labels == 0).sum()), "n_crash_like": int((labels == 1).sum()),
            "unique_sessions": int(len(set(sids.tolist()))),
            "session_composition": {sid: int((sids == sid).sum()) for sid in sorted(set(sids.tolist()))},
            "per_channel_normalized_min": [float(x) for x in seq.min(axis=(0, 1))],
            "per_channel_normalized_max": [float(x) for x in seq.max(axis=(0, 1))],
        }

    rep_summary = summarize(idx, "representative_200_seed42")
    full_val_summary = summarize(np.arange(len(X_seq_val)), "full_validation_set")

    rep_min = np.array(rep_summary["per_channel_normalized_min"])
    rep_max = np.array(rep_summary["per_channel_normalized_max"])
    full_min = np.array(full_val_summary["per_channel_normalized_min"])
    full_max = np.array(full_val_summary["per_channel_normalized_max"])
    coverage_note = {
        "representative_set_narrower_than_full_val_on_channels": [
            i for i in range(len(rep_min)) if rep_min[i] > full_min[i] or rep_max[i] < full_max[i]
        ],
    }

    out = {
        "seed": src_config.RANDOM_SEED, "requested_n": 200,
        "selected_indices": [int(i) for i in idx],
        "representative_set": rep_summary,
        "full_validation_set": full_val_summary,
        "coverage_note": coverage_note,
    }
    OUT_DIR.joinpath("int8_calibration", "representative_dataset_notes.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT_DIR / 'int8_calibration' / 'representative_dataset_notes.json'}")
    return out


def _windows_from_filtered_stream(accel_filtered, gyro_deg_s, window_samples, stride_samples):
    """Slides window_samples/stride_samples over an already highpass-filtered
    accel stream (Nx3) + raw gyro deg/s stream (Nx3), matching WindowScorer's
    windowing, and computes aux features per window -- WITHOUT going through
    CausalGravityFilter again (the filtering already happened)."""
    n = len(accel_filtered)
    windows, auxs = [], []
    i = window_samples
    while i <= n:
        start = i - window_samples
        seq = np.concatenate([accel_filtered[start:i], gyro_deg_s[start:i]], axis=1).astype(np.float32)
        windows.append(seq)
        auxs.append(cm.compute_aux_features(seq))
        i += stride_samples
    return windows, auxs


def _predict_windows(model, normalizer_seq_mean, normalizer_seq_std, normalizer_aux_mean, normalizer_aux_std,
                      cm_model, windows, auxs):
    probs, recons = [], []
    for w, a in zip(windows, auxs):
        p, r = cm_model.predict(w, a)
        probs.append(p)
        recons.append(r)
    return np.array(probs), np.array(recons)


def _causal_butterworth_highpass(accel_gravity_inclusive, cutoff_hz, rate_hz, order=2):
    nyq = rate_hz / 2.0
    b, a = butter(order, cutoff_hz / nyq, btype="highpass")
    return lfilter(b, a, accel_gravity_inclusive, axis=0), (b, a)


def sections_m_ema_and_butterworth(test_raw_sessions, canonical_by_id, cm_model, cfg):
    print("\n=== Sections M1/M2: EMA cutoff sensitivity + causal Butterworth comparison ===")
    stride_s = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]
    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    consecutive_windows = cfg["thresholds"]["consecutive_windows"]
    cooldown_seconds = cfg["thresholds"]["cooldown_seconds"]
    window_samples = cfg["sensor"]["window_samples"]
    stride_samples = cfg["sensor"]["stride_samples"]
    rate_hz = cfg["sensor"]["sample_rate_hz"]

    def any_trigger(probs, recons):
        policy = cm.TriggerPolicy(classifier_t, recon_t, consecutive_windows, cooldown_seconds)
        fired = False
        for k, (p, r) in enumerate(zip(probs, recons)):
            _, triggered = policy.update(p, r, now=k * stride_s)
            fired = fired or triggered
        return fired

    ema_cutoffs = [0.1, 0.2, 0.3, 0.4, 0.5]
    m1_rows = []
    m2_filter_response = {}

    for s in test_raw_sessions:
        canon = canonical_by_id[s.session_id]
        ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
        if len(ds.y) == 0:
            continue
        offline_probs, offline_recons = [], []
        for i in range(len(ds.y)):
            p, r = cm_model.predict(ds.X_seq[i], ds.X_aux[i])
            offline_probs.append(p)
            offline_recons.append(r)
        offline_probs = np.array(offline_probs)
        offline_recons = np.array(offline_recons)
        offline_fired = any_trigger(offline_probs, offline_recons)

        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
        accel_raw = df[["ax", "ay", "az"]].to_numpy(dtype=np.float64)
        gyro_deg_s = df[["gx", "gy", "gz"]].to_numpy(dtype=np.float64)

        for cutoff in ema_cutoffs:
            gf = cm.CausalGravityFilter(cutoff, rate_hz)
            accel_filtered = np.array([gf.apply(a) for a in accel_raw])
            windows, auxs = _windows_from_filtered_stream(accel_filtered, gyro_deg_s, window_samples, stride_samples)
            if not windows:
                continue
            probs, recons = [], []
            for w, a in zip(windows, auxs):
                p, r = cm_model.predict(w, a)
                probs.append(p)
                recons.append(r)
            probs, recons = np.array(probs), np.array(recons)
            n = min(len(offline_probs), len(probs))
            if n == 0:
                continue
            off_p, off_r = offline_probs[:n], offline_recons[:n]
            rt_p, rt_r = probs[:n], recons[:n]
            off_dec = (off_p > classifier_t) | (off_r > recon_t)
            rt_dec = (rt_p > classifier_t) | (rt_r > recon_t)
            rt_fired = any_trigger(probs, recons)
            m1_rows.append({
                "session_id": s.session_id, "label": s.label, "cutoff_hz": cutoff,
                "n_windows": n,
                "classifier_mae": float(np.mean(np.abs(off_p - rt_p))),
                "recon_mae": float(np.mean(np.abs(off_r - rt_r))),
                "classifier_corr": float(np.corrcoef(off_p, rt_p)[0, 1]) if n > 1 else None,
                "recon_corr": float(np.corrcoef(off_r, rt_r)[0, 1]) if n > 1 else None,
                "n_decision_flips": int((off_dec != rt_dec).sum()),
                "event_trigger_agreement": bool(offline_fired == rt_fired),
                "offline_event_fired": bool(offline_fired), "cutoff_event_fired": bool(rt_fired),
            })

        # M2: causal 2nd-order Butterworth at the deployed 0.3Hz corner
        accel_bw, (b, a) = _causal_butterworth_highpass(accel_raw, 0.3, rate_hz, order=2)
        windows, auxs = _windows_from_filtered_stream(accel_bw, gyro_deg_s, window_samples, stride_samples)
        if windows:
            probs, recons = [], []
            for w, aux in zip(windows, auxs):
                p, r = cm_model.predict(w, aux)
                probs.append(p)
                recons.append(r)
            probs, recons = np.array(probs), np.array(recons)
            n = min(len(offline_probs), len(probs))
            off_p, off_r = offline_probs[:n], offline_recons[:n]
            rt_p, rt_r = probs[:n], recons[:n]
            off_dec = (off_p > classifier_t) | (off_r > recon_t)
            rt_dec = (rt_p > classifier_t) | (rt_r > recon_t)
            rt_fired = any_trigger(probs, recons)
            m1_rows.append({
                "session_id": s.session_id, "label": s.label, "cutoff_hz": "causal_butterworth_0.3",
                "n_windows": n,
                "classifier_mae": float(np.mean(np.abs(off_p - rt_p))),
                "recon_mae": float(np.mean(np.abs(off_r - rt_r))),
                "classifier_corr": float(np.corrcoef(off_p, rt_p)[0, 1]) if n > 1 else None,
                "recon_corr": float(np.corrcoef(off_r, rt_r)[0, 1]) if n > 1 else None,
                "n_decision_flips": int((off_dec != rt_dec).sum()),
                "event_trigger_agreement": bool(offline_fired == rt_fired),
                "offline_event_fired": bool(offline_fired), "cutoff_event_fired": bool(rt_fired),
            })

    # Frequency response of all three filter families at the deployed 0.3Hz corner.
    rate = cfg["sensor"]["sample_rate_hz"]
    w, h_bw = freqz(*butter(2, 0.3 / (rate / 2), btype="highpass"), worN=512, fs=rate)
    ema_alpha_tau = 1.0 / (2 * np.pi * 0.3)
    ema_alpha = float(np.exp(-1.0 / (ema_alpha_tau * rate)))
    # EMA lowpass gravity-estimate transfer function: G(z) = (1-alpha) / (1 - alpha*z^-1); highpass = 1 - G(z)
    b_lp, a_lp = [1 - ema_alpha], [1, -ema_alpha]
    _, h_lp = freqz(b_lp, a_lp, worN=512, fs=rate)
    h_ema_hp = 1 - h_lp
    m2_filter_response = {
        "freq_hz": w.tolist(),
        "causal_butterworth_2nd_order_0.3hz_mag_db": (20 * np.log10(np.abs(h_bw) + 1e-12)).tolist(),
        "causal_butterworth_2nd_order_0.3hz_phase_deg": np.angle(h_bw, deg=True).tolist(),
        "deployed_causal_ema_0.3hz_mag_db": (20 * np.log10(np.abs(h_ema_hp) + 1e-12)).tolist(),
        "deployed_causal_ema_0.3hz_phase_deg": np.angle(h_ema_hp, deg=True).tolist(),
        "note": (
            "Offline reference is zero-phase (filtfilt) -- has no meaningful causal phase-delay curve "
            "to plot alongside these two causal filters; it's the amplitude-accurate ground truth both "
            "causal filters are compared against via MAE/correlation/decision-flip counts above instead."
        ),
    }

    import csv
    with open(OUT_DIR / "ema_sensitivity" / "ema_sensitivity.csv", "w", newline="") as f:
        w_csv = csv.DictWriter(f, fieldnames=list(m1_rows[0].keys()))
        w_csv.writeheader()
        w_csv.writerows(m1_rows)
    OUT_DIR.joinpath("filter_identity", "filter_comparison.json").write_text(json.dumps(m2_filter_response, indent=2))
    print(f"Wrote {OUT_DIR / 'ema_sensitivity' / 'ema_sensitivity.csv'} ({len(m1_rows)} rows)")
    print(f"Wrote {OUT_DIR / 'filter_identity' / 'filter_comparison.json'}")
    return m1_rows, m2_filter_response


def sections_n_class_stratified(test_raw_sessions, canonical_by_id, cm_model, cfg,
                                 ds_full, keras_probs, keras_recons, int8_probs, int8_recons,
                                 classifier_t, recon_t):
    print("\n=== Sections N1/N2: class-stratified deployment fidelity ===")

    # N1: causal (deployed EMA @0.3Hz) vs offline (zero-phase Butterworth), per-window, class-stratified.
    all_offline_dec, all_rt_dec, all_labels, all_sids = [], [], [], []
    rate_hz = cfg["sensor"]["sample_rate_hz"]
    window_samples = cfg["sensor"]["window_samples"]
    stride_samples = cfg["sensor"]["stride_samples"]
    stride_s = stride_samples / rate_hz
    consecutive_windows = cfg["thresholds"]["consecutive_windows"]
    cooldown_seconds = cfg["thresholds"]["cooldown_seconds"]

    def any_trigger(probs, recons):
        policy = cm.TriggerPolicy(classifier_t, recon_t, consecutive_windows, cooldown_seconds)
        fired_at = None
        for k, (p, r) in enumerate(zip(probs, recons)):
            _, triggered = policy.update(p, r, now=k * stride_s)
            if triggered and fired_at is None:
                fired_at = k
        return fired_at

    session_flip_notes = []
    for s in test_raw_sessions:
        canon = canonical_by_id[s.session_id]
        ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
        if len(ds.y) == 0:
            continue
        offline_probs, offline_recons = [], []
        for i in range(len(ds.y)):
            p, r = cm_model.predict(ds.X_seq[i], ds.X_aux[i])
            offline_probs.append(p)
            offline_recons.append(r)
        offline_probs, offline_recons = np.array(offline_probs), np.array(offline_recons)

        gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], rate_hz)
        scorer = cm.WindowScorer(cfg, cm_model, gravity_filter)
        df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
        rt_probs, rt_recons = [], []
        for row in df.itertuples():
            scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
            result = scorer.try_score()
            if result is not None:
                rt_probs.append(result["crash_prob"])
                rt_recons.append(result["recon_error"])
        rt_probs, rt_recons = np.array(rt_probs), np.array(rt_recons)

        n = min(len(offline_probs), len(rt_probs))
        if n == 0:
            continue
        labels = ds.y[:n]
        off_dec = (offline_probs[:n] > classifier_t) | (offline_recons[:n] > recon_t)
        rt_dec = (rt_probs[:n] > classifier_t) | (rt_recons[:n] > recon_t)
        all_offline_dec.append(off_dec); all_rt_dec.append(rt_dec)
        all_labels.append(labels); all_sids.extend([s.session_id] * n)

        flips = np.where(off_dec != rt_dec)[0]
        if len(flips):
            off_trig = any_trigger(offline_probs[:n], offline_recons[:n])
            rt_trig = any_trigger(rt_probs[:n], rt_recons[:n])
            session_flip_notes.append({
                "session_id": s.session_id, "n_flipped_windows": int(len(flips)),
                "flipped_window_indices": [int(x) for x in flips],
                "offline_event_trigger_window": off_trig, "causal_event_trigger_window": rt_trig,
                "event_trigger_changed_by_flip": bool((off_trig is not None) != (rt_trig is not None)),
            })

    offline_dec = np.concatenate(all_offline_dec)
    rt_dec = np.concatenate(all_rt_dec)
    labels = np.concatenate(all_labels)

    def confusion_table(ref_dec, trans_dec, mask, name):
        r, t = ref_dec[mask], trans_dec[mask]
        return {
            "group": name, "n": int(mask.sum()),
            "ref_neg_to_trans_neg": int(((~r) & (~t)).sum()),
            "ref_neg_to_trans_pos": int(((~r) & t).sum()),
            "ref_pos_to_trans_neg": int((r & (~t)).sum()),
            "ref_pos_to_trans_pos": int((r & t).sum()),
            "agreement_rate": float((r == t).mean()) if mask.sum() else None,
        }

    n1_report = {
        "method": "reference=offline zero-phase Butterworth decision, transformed=causal EMA(0.3Hz) decision, both via the deployed INT8 model + thresholds, per-window, index-aligned per session.",
        "normal_windows": confusion_table(offline_dec, rt_dec, labels == 0, "normal (label=0)"),
        "crash_like_windows": confusion_table(offline_dec, rt_dec, labels == 1, "crash_like (label=1)"),
        "overall": confusion_table(offline_dec, rt_dec, np.ones(len(labels), dtype=bool), "all"),
        "sessions_with_flips_and_event_trigger_check": session_flip_notes,
    }

    # N2: INT8 vs Keras (reference), class-stratified, on the SAME test-split ds used for K/L.
    keras_dec = (keras_probs > classifier_t)
    int8_dec = (int8_probs > classifier_t)
    labels_full = ds_full.y
    n2_report = {
        "method": "reference=Keras float32 classifier decision at the deployed threshold, transformed=INT8 TFLite classifier decision, same threshold, per-window on the full test split.",
        "normal_windows": confusion_table(keras_dec, int8_dec, labels_full == 0, "normal (label=0)"),
        "crash_like_windows": confusion_table(keras_dec, int8_dec, labels_full == 1, "crash_like (label=1)"),
        "overall": confusion_table(keras_dec, int8_dec, np.ones(len(labels_full), dtype=bool), "all"),
    }
    # Reconstruction-threshold and OR-rule stratified agreement too, per doc's ask.
    keras_or = (keras_probs > classifier_t) | (keras_recons > recon_t)
    int8_or = (int8_probs > classifier_t) | (int8_recons > recon_t)
    n2_report["or_rule_normal_windows"] = confusion_table(keras_or, int8_or, labels_full == 0, "normal (OR rule)")
    n2_report["or_rule_crash_like_windows"] = confusion_table(keras_or, int8_or, labels_full == 1, "crash_like (OR rule)")

    OUT_DIR.joinpath("class_fidelity", "class_stratified_fidelity_N1_causal_vs_offline.json").write_text(json.dumps(n1_report, indent=2))
    OUT_DIR.joinpath("class_fidelity", "class_stratified_fidelity_N2_int8_vs_keras.json").write_text(json.dumps(n2_report, indent=2))
    print(f"Wrote {OUT_DIR / 'class_fidelity'}")
    return n1_report, n2_report


def section_o_frozen_context():
    print("\n=== Section O: frozen detector operating-point context ===")
    with open(ROOT / "results" / "test_metrics.json") as f:
        test_metrics = json.load(f)
    with open(ROOT / "results" / "hybrid_ablation.json") as f:
        hybrid = json.load(f)

    balanced = test_metrics.get("classifier_only_balanced", {})
    or_tuned = hybrid.get("hybrid_or_tuned", {})
    branch = None
    extended_path = ROOT / "piResults" / "results" / "foundational" / "current" / "extended_ablation_batch.json"
    if extended_path.exists():
        with open(extended_path) as f:
            ext = json.load(f)
        branch = ext.get("3.25_or_rule_branch_contribution_window_level")

    out = {
        "source_files": ["results/test_metrics.json", "results/hybrid_ablation.json",
                          "piResults/results/foundational/current/extended_ablation_batch.json"],
        "classifier_only_balanced": balanced,
        "hybrid_or_tuned": or_tuned,
        "or_rule_branch_attribution_window_level": branch,
        "doc_cited_values_to_verify": {
            "or_precision": 0.906, "or_recall": 0.203, "or_f1": 0.331,
            "classifier_only": 19, "reconstruction_only": 1, "both": 14, "neither": 5403,
        },
    }
    OUT_DIR.joinpath("frozen_detector", "frozen_detector_context.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT_DIR / 'frozen_detector' / 'frozen_detector_context.json'}")
    return out


def main():
    cfg = common.load_config()
    classifier_t, recon_t = cm.load_model_thresholds(cfg)

    print("Loading + canonicalizing sessions, building test/val splits...")
    raw_sessions = io_loaders.load_all_sessions()
    canonical_sessions = preprocess.canonicalize_all(raw_sessions)
    canonical_by_id = {s.session_id: s for s in canonical_sessions}
    split_of = manifest.assign_splits(raw_sessions)
    test_raw = [s for s in raw_sessions if split_of.get(s.session_id) == "test"]
    ds = manifest.build_dataset(canonical_sessions, split_of, "test")
    print(f"Test split: {len(ds.y)} windows ({int((ds.y == 1).sum())} crash-like, {int((ds.y == 0).sum())} normal)")

    normalizer = normalize.Normalizer.load(ROOT / "models" / "normalizer.npz")
    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    X_seq, X_aux = X_seq.astype(np.float32), X_aux.astype(np.float32)

    print("Loading Keras model, predicting reference...")
    keras_model = tf.keras.models.load_model(ROOT / "models" / "helmx_crash_model.keras")
    keras_out = keras_model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    keras_probs = keras_out["crash_prob"].ravel()
    keras_recons = keras_out["recon_error"].ravel()

    print("Running FP16 TFLite over test split...")
    fp16_probs, fp16_recons, _ = tflite_predict_all(ROOT / "models/helmx_crash_model_fp16.tflite", X_seq, X_aux)
    print("Running INT8 TFLite over test split...")
    int8_probs, int8_recons, _ = tflite_predict_all(ROOT / "models/helmx_crash_model_int8.tflite", X_seq, X_aux)

    section_k_int8_outlier(ds, X_seq, X_aux, keras_probs, keras_recons, int8_probs, int8_recons,
                            fp16_probs, fp16_recons, classifier_t, recon_t)
    section_l_representative_audit(canonical_sessions, split_of)

    cm_model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
    sections_m_ema_and_butterworth(test_raw, canonical_by_id, cm_model, cfg)
    sections_n_class_stratified(test_raw, canonical_by_id, cm_model, cfg, ds,
                                 keras_probs, keras_recons, int8_probs, int8_recons, classifier_t, recon_t)
    section_o_frozen_context()

    print("\n=== All replay-based sections (K, L, M1, M2, N1, N2, O) complete. ===")


if __name__ == "__main__":
    main()
