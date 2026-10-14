"""Computes the complete metrics suite (classification, reconstruction,
threshold distribution, detection latency, inference footprint) on the
train and test splits and saves results/metrics/full_metrics.json -- the source
data for performance.md."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, evaluate
from src import model as model_lib  # noqa: F401 (registers the custom reconstruction loss for load_model)


def split_report(name, sessions, split_of, model, normalizer, thresholds):
    ds = manifest.build_dataset(sessions, split_of, name)
    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()
    recon_error = preds["recon_error"].ravel()
    reconstruction = preds["reconstruction"]
    recon_error_peak = evaluate.peak_reconstruction_error(X_seq, reconstruction)

    # Real (non-overlapping) exposure time, not n_windows * window_seconds --
    # see src/evaluate.py: normal_session_hours (changesToMake2.txt item 2).
    normal_hours = evaluate.normal_session_hours(sessions, split_of, name)

    report = {
        "n_windows": int(len(ds.y)),
        "n_normal": int((ds.y == 0).sum()),
        "n_crash_like": int((ds.y == 1).sum()),
        "n_sessions": int(len(set(ds.session_id.tolist()))),
        "normal_exposure_hours": normal_hours,
        "classification_metrics": {
            "balanced_operating_point": evaluate.full_classification_metrics(
                ds.y, crash_prob, thresholds["classifier_prob_balanced"], normal_hours
            ),
            "high_recall_operating_point": evaluate.full_classification_metrics(
                ds.y, crash_prob, thresholds["classifier_prob_high_recall"], normal_hours
            ),
        },
        # Compared against the normalized X_seq (what the model was actually
        # trained to reconstruct), not ds.X_seq's raw physical units -- those
        # are on wildly different scales per source (e.g. DaRUS crash-impact
        # accel is in the hundreds of m/s^2) and would make this meaningless.
        "reconstruction_error_metrics": evaluate.reconstruction_error_metrics(
            X_seq, reconstruction, ds.y
        ),
        "reconstruction_anomaly_score_distribution": evaluate.reconstruction_error_distribution(
            recon_error, ds.y
        ),
        # changesToMake.txt item 2: peak-over-window variant alongside the
        # model's built-in mean-over-window recon_error -- see
        # src/evaluate.py: peak_reconstruction_error.
        "reconstruction_anomaly_score_distribution_peak": evaluate.reconstruction_error_distribution(
            recon_error_peak, ds.y
        ),
    }
    return report


def benchmark_keras(model, X_seq, X_aux, n_runs=200):
    n_runs = min(n_runs, len(X_seq))
    idx = np.random.default_rng(config.RANDOM_SEED).choice(len(X_seq), n_runs, replace=False)
    times = []
    for i in idx:
        seq = X_seq[i:i + 1]
        aux = X_aux[i:i + 1]
        start = time.perf_counter()
        model.predict({"seq": seq, "aux": aux}, verbose=0)
        times.append(time.perf_counter() - start)
    times = np.array(times)
    return {
        "mean_ms": float(times.mean() * 1000),
        "p95_ms": float(np.percentile(times, 95) * 1000),
        "throughput_windows_per_sec": float(1.0 / times.mean()),
        "n_runs": n_runs,
    }


def main():
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    model = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")
    with open(config.MODELS_DIR / "thresholds.json") as f:
        thresholds = json.load(f)

    report = {
        "train": split_report("train", sessions, split_of, model, normalizer, thresholds),
        "test": split_report("test", sessions, split_of, model, normalizer, thresholds),
    }

    for name, threshold_key in [
        ("balanced", "classifier_prob_balanced"),
        ("high_recall", "classifier_prob_high_recall"),
    ]:
        report["test"].setdefault("detection_latency_seconds", {})[name] = evaluate.detection_latency_stats(
            sessions, split_of, "test", model, normalizer, thresholds[threshold_key],
        )

    test_ds = manifest.build_dataset(sessions, split_of, "test")
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    report["inference_benchmark_this_machine"] = {
        "keras_fp32": benchmark_keras(model, X_seq, X_aux),
    }

    with open(config.METRICS_DIR / "export_report.json") as f:
        export_report = json.load(f)
    report["model_footprint"] = {
        name: {"size_kb": round(v["size_bytes"] / 1024, 1)} for name, v in export_report.items()
    }
    for tag, key in [("tflite_fp16", "fp16"), ("tflite_int8", "int8")]:
        bench = dict(export_report[key]["benchmark_this_machine"])
        bench["throughput_windows_per_sec"] = 1000.0 / bench["mean_ms"]
        report["inference_benchmark_this_machine"][tag] = bench

    print(json.dumps(report, indent=2))
    evaluate.save_metrics(report, "full_metrics")


if __name__ == "__main__":
    main()
