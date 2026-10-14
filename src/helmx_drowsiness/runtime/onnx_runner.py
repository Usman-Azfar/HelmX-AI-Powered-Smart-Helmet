"""Strict ONNX Runtime adapter for edge-portable temporal inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray


class OnnxTemporalRunner:
    def __init__(self, model_path: str | Path, *, threads: int = 2) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"ONNX model not found: {path}")
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(
            str(path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        names = {item.name for item in self.session.get_inputs()}
        if names != {"frames", "physiology", "quality"}:
            raise ValueError(f"unexpected ONNX inputs: {sorted(names)}")

    def predict(
        self,
        frames: NDArray[np.float32],
        physiology: NDArray[np.float32],
        quality: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        inputs = {
            "frames": np.ascontiguousarray(frames, dtype=np.float32),
            "physiology": np.ascontiguousarray(physiology, dtype=np.float32),
            "quality": np.ascontiguousarray(quality, dtype=np.float32),
        }
        logits = np.asarray(self.session.run(["logits"], inputs)[0], dtype=np.float64)
        shifted = logits - logits.max(axis=-1, keepdims=True)
        exponent = np.exp(shifted)
        result = (exponent / exponent.sum(axis=-1, keepdims=True)).astype(np.float32)
        return np.asarray(result, dtype=np.float32)
