"""ONNX export contract for the temporal model."""

from __future__ import annotations

from pathlib import Path

import torch
from torch import Tensor, nn

from helmx_drowsiness.config import ProjectConfig
from helmx_drowsiness.features.visual_input import VisualRegion
from helmx_drowsiness.models import QualityAwareTemporalNet, build_model


class _ExportWrapper(nn.Module):
    def __init__(self, model: QualityAwareTemporalNet) -> None:
        super().__init__()
        self.model = model

    def forward(self, frames: Tensor, physiology: Tensor, quality: Tensor) -> tuple[Tensor, ...]:
        output = self.model(frames, physiology, quality)
        return (
            output["logits"],
            output["eye_closure_logits"],
            output["yawn_logits"],
            output["head_pose"],
            output["quality_logits"],
            output["modality_weights"],
        )


def export_onnx(
    model: QualityAwareTemporalNet,
    output_path: str | Path,
    *,
    sequence_length: int,
    image_size: int,
    physiology_features: int,
    visual_region: VisualRegion = "full_face",
) -> None:
    """Export an eval-mode model with stable input/output names and dynamic batch size."""

    wrapper = _ExportWrapper(model.eval()).eval()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image_width = image_size * 2 if visual_region == "dual_eye" else image_size
    examples = (
        torch.zeros(1, sequence_length, 3, image_size, image_width),
        torch.zeros(1, sequence_length, physiology_features),
        torch.ones(1, sequence_length, 2),
    )
    batch = torch.export.Dim("batch", min=1)
    torch.onnx.export(
        wrapper,
        examples,
        str(destination),
        input_names=["frames", "physiology", "quality"],
        output_names=[
            "logits",
            "eye_closure_logits",
            "yawn_logits",
            "head_pose",
            "quality_logits",
            "modality_weights",
        ],
        dynamic_shapes={
            "frames": {0: batch},
            "physiology": {0: batch},
            "quality": {0: batch},
        },
        opset_version=18,
        dynamo=True,
        verbose=False,
    )


def export_checkpoint(
    checkpoint_path: str | Path,
    output_path: str | Path,
    config: ProjectConfig,
) -> Path:
    """Load a training checkpoint strictly and export its inference graph."""

    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or "model_state" not in payload:
        raise ValueError("checkpoint does not contain model_state")
    model = build_model(config.model, pretrained=False)
    model.load_state_dict(payload["model_state"], strict=True)
    destination = Path(output_path)
    export_onnx(
        model,
        destination,
        sequence_length=config.data.sequence_length,
        image_size=config.data.image_size,
        physiology_features=config.model.physiology_features,
        visual_region=config.data.visual_region,
    )
    return destination
