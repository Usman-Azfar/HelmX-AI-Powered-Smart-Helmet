from pathlib import Path

import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.sequences import SequenceDataset
from helmx_drowsiness.quantize import SequenceCalibrationReader, _passes_parity, _stratified_rows


def test_quantization_reader_uses_named_float32_inputs(tmp_path: Path) -> None:
    np.savez(
        tmp_path / "sample.npz",
        frames=np.zeros((4, 16, 16, 3), dtype=np.uint8),
        physiology=np.zeros((4, 12), dtype=np.float32),
        quality=np.ones((4, 2), dtype=np.float32),
    )
    dataset = SequenceDataset(pd.DataFrame([{"path": "sample.npz", "label": 0}]), tmp_path)
    reader = SequenceCalibrationReader(dataset, samples=1)
    inputs = reader.get_next()
    assert inputs is not None
    assert set(inputs) == {"frames", "physiology", "quality"}
    assert all(value.dtype == np.float32 for value in inputs.values())
    assert reader.get_next() is None


def test_quantization_sampling_is_balanced_and_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "path": [f"{index}.npz" for index in range(100)],
            "label": [0] * 90 + [1] * 10,
        }
    )
    first = _stratified_rows(frame, 20)
    second = _stratified_rows(frame, 20)
    assert first.equals(second)
    assert first["label"].value_counts().to_dict() == {0: 10, 1: 10}


def test_quantization_parity_gate_rejects_decision_changes() -> None:
    assert _passes_parity(
        {
            "maximum_absolute_probability_error": 0.02,
            "mean_absolute_probability_error": 0.001,
            "argmax_agreement": 1.0,
        }
    )
    assert not _passes_parity(
        {
            "maximum_absolute_probability_error": 0.02,
            "mean_absolute_probability_error": 0.001,
            "argmax_agreement": 0.98,
        }
    )
