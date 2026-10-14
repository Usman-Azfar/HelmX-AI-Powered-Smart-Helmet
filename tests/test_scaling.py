from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from helmx_drowsiness.datasets.scaling import fit_physiology_scaler
from helmx_drowsiness.models import QualityAwareTemporalNet


def test_scaler_uses_only_valid_training_observations(tmp_path: Path) -> None:
    physiology = np.zeros((3, 12), dtype=np.float32)
    physiology[1:, 0] = [2.0, 4.0]
    physiology[1:, -1] = 1.0
    np.savez(tmp_path / "sample.npz", physiology=physiology)
    scaler = fit_physiology_scaler(pd.DataFrame({"path": ["sample.npz"]}), tmp_path)
    assert scaler.observations == 2
    assert scaler.center[0] == pytest.approx(3.0)
    assert (scaler.scale > 0).all()


def test_model_rejects_invalid_physiology_scaler() -> None:
    model = QualityAwareTemporalNet(physiology_features=12, hidden_size=32, temporal_blocks=1)
    with pytest.raises(ValueError, match="positive"):
        model.set_physiology_scaler(torch.zeros(12), torch.zeros(12))


def test_model_clips_robust_standardized_physiology() -> None:
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        physiology_standardized_clip=10.0,
    )
    model.set_physiology_scaler(torch.zeros(12), torch.ones(12))

    standardized = model.standardize_physiology(torch.tensor([[[-1000.0, 1000.0, *([0.0] * 10)]]]))

    assert standardized.min().item() == -10.0
    assert standardized.max().item() == 10.0
