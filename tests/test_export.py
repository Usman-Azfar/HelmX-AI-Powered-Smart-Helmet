from __future__ import annotations

import numpy as np
import pytest
import torch

from helmx_drowsiness.config import load_config
from helmx_drowsiness.export import export_checkpoint, export_onnx
from helmx_drowsiness.models import QualityAwareTemporalNet
from helmx_drowsiness.runtime.onnx_runner import OnnxTemporalRunner


@pytest.mark.parametrize("fusion_mode", ["quality_gated", "quality_concat"])
def test_onnx_export_has_dynamic_batch_and_matches_pytorch(tmp_path, fusion_mode: str) -> None:
    torch.manual_seed(7)
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        num_classes=3,
        dropout=0.0,
        pretrained=False,
        fusion_mode=fusion_mode,
    ).eval()
    destination = tmp_path / "nested" / f"{fusion_mode}.onnx"
    export_onnx(
        model,
        destination,
        sequence_length=4,
        image_size=64,
        physiology_features=12,
    )

    frames = torch.randn(2, 4, 3, 64, 64)
    physiology = torch.randn(2, 4, 12)
    quality = torch.rand(2, 4, 2).clamp_min(0.1)
    expected = model(frames, physiology, quality)["logits"].softmax(-1).detach().numpy()
    actual = OnnxTemporalRunner(destination).predict(
        frames.numpy(), physiology.numpy(), quality.numpy()
    )

    assert actual.shape == (2, 3)
    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)


def test_checkpoint_export_rejects_unknown_payload(tmp_path) -> None:
    checkpoint = tmp_path / "invalid.pt"
    torch.save({"weights": {}}, checkpoint)
    with pytest.raises(ValueError, match="model_state"):
        export_checkpoint(checkpoint, tmp_path / "model.onnx", load_config("configs/default.yaml"))


def test_dual_eye_onnx_export_matches_pytorch(tmp_path) -> None:
    torch.manual_seed(17)
    model = QualityAwareTemporalNet(
        physiology_features=12,
        hidden_size=32,
        temporal_blocks=1,
        num_classes=3,
        dropout=0.0,
        pretrained=False,
        fusion_mode="visual_only",
    ).eval()
    destination = tmp_path / "dual_eye.onnx"
    export_onnx(
        model,
        destination,
        sequence_length=4,
        image_size=64,
        physiology_features=12,
        visual_region="dual_eye",
    )
    frames = torch.randn(2, 4, 3, 64, 128)
    physiology = torch.randn(2, 4, 12)
    quality = torch.rand(2, 4, 2).clamp_min(0.1)

    expected = model(frames, physiology, quality)["logits"].softmax(-1).detach().numpy()
    actual = OnnxTemporalRunner(destination).predict(
        frames.numpy(), physiology.numpy(), quality.numpy()
    )

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)
