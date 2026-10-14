"""Exports the trained Keras model to TFLite (float16 + int8) and benchmarks
inference latency, using a sample of normalized validation windows for the
int8 representative dataset."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, export
from src import model as model_lib  # noqa: F401 (registers the custom reconstruction loss for load_model)


def main():
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)
    val_ds = manifest.build_dataset(sessions, split_of, "val")

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    X_seq, X_aux = normalizer.transform(val_ds.X_seq, val_ds.X_aux)

    keras_path = config.MODELS_DIR / "helmx_crash_model.keras"
    model = tf.keras.models.load_model(keras_path)

    fp16_path = config.MODELS_DIR / "helmx_crash_model_fp16.tflite"
    export.export_tflite(model, fp16_path, quantize="float16")

    int8_path = config.MODELS_DIR / "helmx_crash_model_int8.tflite"
    export.export_tflite(model, int8_path, quantize="int8", X_seq=X_seq, X_aux=X_aux)

    report = {"keras": {"size_bytes": keras_path.stat().st_size, "benchmark_this_machine": None}}
    for name, path in [("fp16", fp16_path), ("int8", int8_path)]:
        report[name] = {
            "size_bytes": path.stat().st_size,
            "benchmark_this_machine": export.benchmark_tflite(path, X_seq, X_aux),
        }

    print(json.dumps(report, indent=2))
    config.METRICS_DIR.mkdir(exist_ok=True, parents=True)
    with open(config.METRICS_DIR / "export_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
