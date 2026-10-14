import tempfile

import numpy as np
import tensorflow as tf

from . import config


def _representative_dataset(X_seq, X_aux, n=200):
    n = min(n, len(X_seq))
    idx = np.random.default_rng(config.RANDOM_SEED).choice(len(X_seq), n, replace=False)

    def gen():
        for i in idx:
            yield [X_seq[i:i + 1].astype(np.float32), X_aux[i:i + 1].astype(np.float32)]
    return gen


def export_tflite(model, out_path, quantize="float16", X_seq=None, X_aux=None):
    """quantize: 'float16' (no representative data needed) or 'int8' (needs a
    representative sample of normalized training windows).

    Converts via a SavedModel export rather than TFLiteConverter.from_keras_model:
    the direct Keras-model path crashes the MLIR converter on this TF/Keras 3
    build (BatchNormalization emits a Cast the converter can't type-infer)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        model.export(tmp_dir)
        converter = tf.lite.TFLiteConverter.from_saved_model(tmp_dir)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        if quantize == "float16":
            converter.target_spec.supported_types = [tf.float16]
        elif quantize == "int8":
            if X_seq is None or X_aux is None:
                raise ValueError("int8 quantization needs X_seq/X_aux for the representative dataset")
            converter.representative_dataset = _representative_dataset(X_seq, X_aux)
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        else:
            raise ValueError(f"unknown quantize mode: {quantize}")

        tflite_model = converter.convert()

    out_path = str(out_path)
    with open(out_path, "wb") as f:
        f.write(tflite_model)
    return out_path


def benchmark_tflite(tflite_path, X_seq, X_aux, n_runs=100):
    """Uses the signature-runner API (keyed by the 'seq'/'aux' input names
    from src/model.py) so this matches exactly what deploy/crash_monitor.py
    does on the Pi."""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    runner = interpreter.get_signature_runner()

    import time
    n_runs = min(n_runs, len(X_seq))
    times = []
    for i in range(n_runs):
        seq = X_seq[i:i + 1].astype(np.float32)
        aux = X_aux[i:i + 1].astype(np.float32)
        start = time.perf_counter()
        runner(seq=seq, aux=aux)
        times.append(time.perf_counter() - start)

    times = np.array(times)
    return {
        "mean_ms": float(times.mean() * 1000),
        "p95_ms": float(np.percentile(times, 95) * 1000),
        "n_runs": n_runs,
    }
