"""Experiment D -- quantization verification (PI_RESEARCH_GUIDE.md Section D).

Compares Keras (float32), FP16 TFLite, and INT8 TFLite (the one actually
deployed) on the SAME held-out test-split windows, loaded the normal offline
way (preprocess.canonicalize_all + manifest.build_dataset -- this experiment
is about the model artifact, not the streaming pipeline, so offline
canonicalization is the right preprocessing here, unlike Experiment C).

Answers: does quantization materially change predictions? Not "which is
fastest" (Experiment A1 already covers INT8 timing on-device).

Run on the Pi (needs full requirements.txt -- tensorflow):
    python deploy/pi_research_suite/exp_d_quantization_comparison.py
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common
from src import io_loaders, preprocess, manifest, normalize
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)


def main():
    cfg = common.load_config()

    print("Loading + canonicalizing sessions, building test split...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)
    ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Test split: {len(ds.y)} windows ({int((ds.y == 1).sum())} crash-like, "
          f"{int((ds.y == 0).sum())} normal)")

    normalizer = normalize.Normalizer.load(ROOT / "models" / "normalizer.npz")
    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    X_seq = X_seq.astype(np.float32)
    X_aux = X_aux.astype(np.float32)

    with open(ROOT / "models" / "thresholds.json") as f:
        thresholds = json.load(f)
    deployed_threshold = thresholds["classifier_prob_balanced"]

    print("Loading Keras model + predicting (float32 reference)...")
    keras_model = tf.keras.models.load_model(ROOT / "models" / "helmx_crash_model.keras")
    t0 = time.perf_counter()
    keras_out = keras_model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    keras_predict_time_s = time.perf_counter() - t0
    keras_probs = keras_out["crash_prob"].ravel()

    results = {
        "device": common.device_info(),
        "n_test_windows": int(len(X_seq)),
        "keras": {
            "size_bytes": os.path.getsize(ROOT / "models" / "helmx_crash_model.keras"),
            "total_predict_time_s_batched": keras_predict_time_s,
        },
    }

    for name, relpath in [("fp16", "models/helmx_crash_model_fp16.tflite"),
                           ("int8", "models/helmx_crash_model_int8.tflite")]:
        path = ROOT / relpath
        print(f"\nRunning {name} ({path})...")
        interpreter = tflite.Interpreter(model_path=str(path))
        interpreter.allocate_tensors()
        runner = interpreter.get_signature_runner()
        times_ms, probs = [], []
        for i in range(len(X_seq)):
            t0 = time.perf_counter()
            out = runner(seq=X_seq[i:i + 1], aux=X_aux[i:i + 1])
            times_ms.append((time.perf_counter() - t0) * 1000)
            probs.append(float(out["crash_prob"][0, 0]))
        probs = np.array(probs)
        stats = common.percentile_stats(times_ms)
        results[name] = {
            "size_bytes": os.path.getsize(path),
            **stats,
            "mean_abs_diff_vs_keras": float(np.mean(np.abs(probs - keras_probs))),
            "classification_agreement_vs_keras_at_0.5": float(np.mean((probs >= 0.5) == (keras_probs >= 0.5))),
            "classification_agreement_vs_keras_at_deployed_threshold": float(
                np.mean((probs >= deployed_threshold) == (keras_probs >= deployed_threshold))
            ),
        }
        print(f"  size={results[name]['size_bytes']} bytes  median={stats['median_ms']:.3f}ms "
              f"p95={stats['p95_ms']:.3f}ms  mean_abs_diff_vs_keras={results[name]['mean_abs_diff_vs_keras']:.6f}  "
              f"agreement@0.5={results[name]['classification_agreement_vs_keras_at_0.5']:.4f}  "
              f"agreement@deployed_t={results[name]['classification_agreement_vs_keras_at_deployed_threshold']:.4f}")

    results["deployed_threshold_used"] = deployed_threshold
    print("\n=== Summary ===")
    print(json.dumps(results, indent=2))
    common.save_json(results, "d_quantization_comparison")


if __name__ == "__main__":
    main()
