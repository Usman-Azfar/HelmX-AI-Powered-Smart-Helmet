"""Static INT8 quantization with training-only calibration and parity reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from onnxruntime.quantization import (
    CalibrationDataReader,
    CalibrationMethod,
    QuantFormat,
    QuantType,
    quantize_static,
)
from onnxruntime.quantization.shape_inference import quant_pre_process
from torch.utils.data import DataLoader

from helmx_drowsiness.config import ProjectConfig
from helmx_drowsiness.datasets.manifest import read_manifest
from helmx_drowsiness.datasets.sequences import SequenceDataset
from helmx_drowsiness.runtime.onnx_runner import OnnxTemporalRunner
from helmx_drowsiness.training.provenance import sha256_file, write_json

MAXIMUM_PARITY_ERROR = 0.05
MEAN_PARITY_ERROR = 0.01
MINIMUM_ARGMAX_AGREEMENT = 0.99


class SequenceCalibrationReader(CalibrationDataReader):  # type: ignore[misc]
    def __init__(self, dataset: SequenceDataset, *, samples: int) -> None:
        self.iterator = iter(DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0))
        self.remaining = samples

    def get_next(self) -> dict[str, np.ndarray[Any, Any]] | None:
        if self.remaining <= 0:
            return None
        try:
            batch = next(self.iterator)
        except StopIteration:
            return None
        self.remaining -= 1
        return {
            "frames": batch["frames"].numpy().astype(np.float32),
            "physiology": batch["physiology"].numpy().astype(np.float32),
            "quality": batch["quality"].numpy().astype(np.float32),
        }


def quantize_checkpoint_onnx(
    model_path: str | Path,
    output_path: str | Path,
    config: ProjectConfig,
    *,
    calibration_samples: int = 256,
    parity_samples: int = 100,
) -> Path:
    """Create QDQ INT8 weights/activations and measure validation parity."""

    manifest = read_manifest(config.data.manifest)
    root = Path(config.data.manifest).parent
    train = manifest.loc[manifest["split"] == "train"].reset_index(drop=True)
    validation = manifest.loc[manifest["split"] == "validation"].reset_index(drop=True)
    if train.empty or validation.empty:
        raise ValueError("quantization requires non-empty train and validation splits")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    calibration = _stratified_rows(train, calibration_samples)
    parity_frame = _stratified_rows(validation, parity_samples)
    reader = SequenceCalibrationReader(
        SequenceDataset(calibration, root, augment=False), samples=len(calibration)
    )
    preprocessed = destination.with_name(destination.stem + ".preprocessed.onnx")
    preprocessed_data = Path(str(preprocessed) + ".data")
    try:
        quant_pre_process(
            input_model=str(model_path),
            output_model_path=str(preprocessed),
            auto_merge=True,
            skip_symbolic_shape=True,
            save_as_external_data=True,
            all_tensors_to_one_file=True,
            external_data_location=preprocessed_data.name,
        )
        quantize_static(
            str(preprocessed),
            str(destination),
            reader,
            quant_format=QuantFormat.QDQ,
            # U8 activations avoid the severe saturation observed with S8/S8
            # on this MobileNet/causal-TCN graph while retaining signed,
            # per-channel weight quantization for CPU deployment.
            activation_type=QuantType.QUInt8,
            weight_type=QuantType.QInt8,
            calibrate_method=CalibrationMethod.MinMax,
            per_channel=True,
            # MobileNet/TCN convolution activation quantization failed the
            # validation parity gate on the real pilot checkpoint. Restrict
            # post-training quantization to stable projection/classifier ops;
            # convolution INT8 requires quantization-aware retraining.
            op_types_to_quantize=["MatMul", "Gemm"],
        )
    finally:
        preprocessed.unlink(missing_ok=True)
        preprocessed_data.unlink(missing_ok=True)
    parity = _parity(
        Path(model_path),
        destination,
        SequenceDataset(parity_frame, root, augment=False),
        samples=len(parity_frame),
    )
    accepted = _passes_parity(parity)
    write_json(
        destination.with_suffix(".quantization.json"),
        {
            "source_sha256": sha256_file(model_path),
            "quantized_sha256": sha256_file(destination),
            "calibration_samples": len(calibration),
            "calibration_class_counts": _class_counts(calibration),
            "parity_samples": len(parity_frame),
            "parity_class_counts": _class_counts(parity_frame),
            "source_bytes": _onnx_bundle_size(Path(model_path)),
            "quantized_bytes": _onnx_bundle_size(destination),
            "quantized_op_types": ["MatMul", "Gemm"],
            "convolution_quantization": "requires quantization-aware training",
            "parity_gate": {
                "accepted": accepted,
                "maximum_absolute_probability_error": MAXIMUM_PARITY_ERROR,
                "mean_absolute_probability_error": MEAN_PARITY_ERROR,
                "minimum_argmax_agreement": MINIMUM_ARGMAX_AGREEMENT,
            },
            **parity,
        },
    )
    if not accepted:
        destination.unlink(missing_ok=True)
        raise RuntimeError("quantized model failed the validation parity gate")
    return destination


def _stratified_rows(frame: pd.DataFrame, samples: int, *, seed: int = 2026) -> pd.DataFrame:
    """Select deterministic class-balanced rows from an ordered manifest."""

    if samples <= 0:
        raise ValueError("samples must be positive")
    if len(frame) <= samples:
        return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    labels = sorted(frame["label"].unique().tolist())
    base, remainder = divmod(samples, len(labels))
    selected: list[pd.DataFrame] = []
    for index, label in enumerate(labels):
        group = frame.loc[frame["label"] == label]
        target = base + int(index < remainder)
        selected.append(group.sample(n=min(target, len(group)), random_state=seed + index))
    result = pd.concat(selected)
    if len(result) < samples:
        remaining = frame.drop(index=result.index)
        result = pd.concat(
            [result, remaining.sample(n=samples - len(result), random_state=seed)],
        )
    return result.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _class_counts(frame: pd.DataFrame) -> dict[str, int]:
    return {str(label): int(count) for label, count in frame["label"].value_counts().items()}


def _passes_parity(parity: dict[str, float]) -> bool:
    return bool(
        parity["maximum_absolute_probability_error"] <= MAXIMUM_PARITY_ERROR
        and parity["mean_absolute_probability_error"] <= MEAN_PARITY_ERROR
        and parity["argmax_agreement"] >= MINIMUM_ARGMAX_AGREEMENT
    )


def _parity(
    source: Path,
    quantized: Path,
    dataset: SequenceDataset,
    *,
    samples: int,
) -> dict[str, float]:
    float_runner = OnnxTemporalRunner(source)
    int8_runner = OnnxTemporalRunner(quantized)
    differences: list[np.ndarray[Any, Any]] = []
    agreements: list[bool] = []
    for index in range(min(samples, len(dataset))):
        sample = dataset[index]
        arguments = (
            sample["frames"].numpy()[None],
            sample["physiology"].numpy()[None],
            sample["quality"].numpy()[None],
        )
        reference = float_runner.predict(*arguments)
        candidate = int8_runner.predict(*arguments)
        differences.append(np.abs(reference - candidate))
        agreements.append(bool(reference.argmax() == candidate.argmax()))
    delta = np.concatenate(differences)
    return {
        "maximum_absolute_probability_error": float(delta.max()),
        "mean_absolute_probability_error": float(delta.mean()),
        "argmax_agreement": float(np.mean(agreements)),
    }


def _onnx_bundle_size(path: Path) -> int:
    external = Path(str(path) + ".data")
    return path.stat().st_size + (external.stat().st_size if external.is_file() else 0)
