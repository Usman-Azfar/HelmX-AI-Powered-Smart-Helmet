"""Quality-aware visual/physiological temporal fusion network."""

from __future__ import annotations

from typing import Self

import torch
from torch import Tensor, nn
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


class CausalResidualBlock(nn.Module):
    """Depthwise-separable causal temporal block suitable for edge inference."""

    def __init__(self, channels: int, dilation: int, dropout: float) -> None:
        super().__init__()
        kernel_size = 3
        self.left_padding = dilation * (kernel_size - 1)
        self.depthwise = nn.Conv1d(
            channels,
            channels,
            kernel_size,
            dilation=dilation,
            groups=channels,
        )
        self.pointwise = nn.Conv1d(channels, channels, 1)
        self.norm = nn.GroupNorm(1, channels)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, inputs: Tensor) -> Tensor:
        residual = inputs
        output = nn.functional.pad(inputs, (self.left_padding, 0))
        output = self.depthwise(output)
        output = self.pointwise(output)
        output = self.norm(output)
        output = self.dropout(self.activation(output))
        result: Tensor = residual + output
        return result


class QualityAwareTemporalNet(nn.Module):
    """Fuse face appearance and interpretable physiology with learned reliability gates.

    Inputs:
        frames: ``[batch, time, 3, height, width]`` RGB tensors. Width may equal height for a
            single visual crop or twice height for packed left/right eye crops.
        physiology: ``[batch, time, physiology_features]`` standardized features.
        quality: ``[batch, time, 2]`` visual and physiological reliability in [0, 1].

    The auxiliary heads make the representation auditable and support multi-task
    supervision for eye closure, yawning, head pose, and input quality.
    """

    def __init__(
        self,
        *,
        physiology_features: int = 12,
        physiology_standardized_clip: float = 10.0,
        hidden_size: int = 192,
        temporal_blocks: int = 4,
        num_classes: int = 3,
        dropout: float = 0.2,
        pretrained: bool = False,
        fusion_mode: str = "quality_gated",
        modality_dropout_probability: float = 0.0,
    ) -> None:
        super().__init__()
        valid_modes = {
            "quality_gated",
            "quality_concat",
            "equal",
            "visual_only",
            "physiology_only",
        }
        if fusion_mode not in valid_modes:
            raise ValueError(f"fusion_mode must be one of {sorted(valid_modes)}")
        if physiology_standardized_clip <= 0:
            raise ValueError("physiology_standardized_clip must be positive")
        if not 0.0 <= modality_dropout_probability <= 1.0:
            raise ValueError("modality_dropout_probability must be in [0, 1]")
        self.fusion_mode = fusion_mode
        self.modality_dropout_probability = modality_dropout_probability
        self.physiology_standardized_clip = physiology_standardized_clip
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        backbone = mobilenet_v3_small(weights=weights)
        visual_features = backbone.classifier[0].in_features
        self.visual_backbone = backbone.features
        self._visual_backbone_frozen = False
        self.visual_pool = nn.AdaptiveAvgPool2d(1)
        self.visual_projection = nn.Sequential(
            nn.Linear(visual_features, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )
        self.physiology_projection = nn.Sequential(
            nn.Linear(physiology_features, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.reliability_gate = nn.Sequential(
            nn.Linear(hidden_size * 2 + 2, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, 2),
        )
        self.fusion_projection: nn.Module
        if fusion_mode == "quality_concat":
            self.fusion_projection = nn.Sequential(
                nn.Linear(hidden_size * 2 + 2, hidden_size),
                nn.LayerNorm(hidden_size),
                nn.GELU(),
            )
        else:
            self.fusion_projection = nn.Identity()
        blocks = [
            CausalResidualBlock(hidden_size, dilation=2**index, dropout=dropout)
            for index in range(temporal_blocks)
        ]
        self.temporal = nn.Sequential(*blocks)
        self.classifier = nn.Linear(hidden_size, num_classes)
        self.eye_head = nn.Linear(hidden_size, 1)
        self.yawn_head = nn.Linear(hidden_size, 1)
        self.head_pose_head = nn.Linear(hidden_size, 3)
        self.quality_head = nn.Linear(hidden_size, 1)
        self.calibration_temperature: Tensor
        self.register_buffer("calibration_temperature", torch.ones(()))
        self.physiology_center: Tensor
        self.physiology_scale: Tensor
        self.register_buffer("physiology_center", torch.zeros(physiology_features))
        self.register_buffer("physiology_scale", torch.ones(physiology_features))

    def freeze_visual_backbone(self) -> None:
        """Freeze pretrained visual parameters and their BatchNorm running statistics."""

        self._visual_backbone_frozen = True
        self.visual_backbone.requires_grad_(False)
        self.visual_backbone.eval()

    def train(self, mode: bool = True) -> Self:
        """Keep a frozen visual backbone in evaluation mode during downstream training."""

        super().train(mode)
        if self._visual_backbone_frozen:
            self.visual_backbone.eval()
        return self

    def forward(self, frames: Tensor, physiology: Tensor, quality: Tensor) -> dict[str, Tensor]:
        self._validate_shapes(frames, physiology, quality)
        batch, steps = frames.shape[:2]
        flat_frames = frames.reshape(batch * steps, *frames.shape[2:])
        visual = self._encode_visual(flat_frames)
        visual = self.visual_projection(visual).reshape(batch, steps, -1)
        standardized = self.standardize_physiology(physiology)
        physical = self.physiology_projection(standardized)

        fused, gates = self._fuse_modalities(visual, physical, quality)

        temporal = self.temporal(fused.transpose(1, 2)).transpose(1, 2)
        representation = temporal[:, -1]
        return {
            "logits": self.classifier(representation)
            / self.calibration_temperature.clamp_min(0.05),
            "eye_closure_logits": self.eye_head(representation).squeeze(-1),
            "yawn_logits": self.yawn_head(representation).squeeze(-1),
            "head_pose": self.head_pose_head(representation),
            "quality_logits": self.quality_head(representation).squeeze(-1),
            "modality_weights": gates,
        }

    def set_temperature(self, value: float) -> None:
        if not 0.05 <= value <= 20.0:
            raise ValueError("temperature must be in [0.05, 20]")
        self.calibration_temperature.fill_(value)

    def set_physiology_scaler(self, center: Tensor, scale: Tensor) -> None:
        if (
            center.shape != self.physiology_center.shape
            or scale.shape != self.physiology_scale.shape
        ):
            raise ValueError("physiology scaler has the wrong feature dimension")
        if (
            not torch.isfinite(center).all()
            or not torch.isfinite(scale).all()
            or (scale <= 0).any()
        ):
            raise ValueError("physiology scaler must be finite with positive scales")
        self.physiology_center.copy_(center)
        self.physiology_scale.copy_(scale)

    def standardize_physiology(self, physiology: Tensor) -> Tensor:
        """Apply the training-only robust scaler and its frozen outlier bound."""

        standardized = (physiology - self.physiology_center) / self.physiology_scale
        return standardized.clamp(
            min=-self.physiology_standardized_clip,
            max=self.physiology_standardized_clip,
        )

    def _encode_visual(self, flat_frames: Tensor) -> Tensor:
        """Encode one crop or symmetrically pool two packed single-eye crops."""

        height, width = flat_frames.shape[-2:]
        if width == height:
            encoded: Tensor = self.visual_backbone(flat_frames)
            pooled: Tensor = self.visual_pool(encoded).flatten(1)
            return pooled
        left, right = flat_frames[..., :height], flat_frames[..., height:]
        eyes = torch.cat((left, right), dim=0)
        encoded = self.visual_pool(self.visual_backbone(eyes)).flatten(1)
        # Packing order cannot become a shortcut: both eyes share weights and their
        # representations are averaged before projection/temporal processing.
        pooled = encoded.reshape(2, flat_frames.shape[0], -1).mean(dim=0)
        return pooled

    def _modality_weights(self, visual: Tensor, physical: Tensor, quality: Tensor) -> Tensor:
        if self.fusion_mode == "quality_gated":
            gate_logits = self.reliability_gate(torch.cat((visual, physical, quality), dim=-1))
            quality_log = torch.clamp(quality, min=1e-4).log()
            weights = torch.softmax(gate_logits + quality_log, dim=-1)
            if self.training and self.modality_dropout_probability > 0.0:
                # Draw once per sample, then hold the forced modality constant across its
                # temporal sequence. Half of selected samples train each modality alone;
                # unselected samples retain the learned quality-aware gate.
                draw = torch.rand((weights.shape[0], 1, 1), device=weights.device)
                force_visual = draw < self.modality_dropout_probability / 2.0
                force_physiology = (draw >= self.modality_dropout_probability / 2.0) & (
                    draw < self.modality_dropout_probability
                )
                visual_only = torch.zeros_like(weights)
                visual_only[..., 0] = 1.0
                physiology_only = torch.zeros_like(weights)
                physiology_only[..., 1] = 1.0
                weights = torch.where(force_visual, visual_only, weights)
                weights = torch.where(force_physiology, physiology_only, weights)
            return weights
        if self.fusion_mode == "quality_concat":
            quality_safe = quality.clamp_min(1e-4)
            return quality_safe / quality_safe.sum(dim=-1, keepdim=True)
        weights = torch.empty_like(quality)
        if self.fusion_mode == "equal":
            weights.fill_(0.5)
        elif self.fusion_mode == "visual_only":
            weights[..., 0] = 1.0
            weights[..., 1] = 0.0
        else:
            weights[..., 0] = 0.0
            weights[..., 1] = 1.0
        return weights

    def _fuse_modalities(
        self, visual: Tensor, physical: Tensor, quality: Tensor
    ) -> tuple[Tensor, Tensor]:
        weights = self._modality_weights(visual, physical, quality)
        if self.fusion_mode == "quality_concat":
            concatenated = torch.cat(
                (weights[..., :1] * visual, weights[..., 1:] * physical, quality),
                dim=-1,
            )
            return self.fusion_projection(concatenated), weights
        return weights[..., :1] * visual + weights[..., 1:] * physical, weights

    @staticmethod
    def _validate_shapes(frames: Tensor, physiology: Tensor, quality: Tensor) -> None:
        if frames.ndim != 5 or frames.shape[2] != 3:
            raise ValueError("frames must have shape [B, T, 3, H, W]")
        if frames.ndim == 5 and frames.shape[-1] not in {
            frames.shape[-2],
            2 * frames.shape[-2],
        }:
            raise ValueError("frame width must equal H (single crop) or 2H (packed dual eye)")
        if physiology.ndim != 3:
            raise ValueError("physiology must have shape [B, T, F]")
        if quality.ndim != 3 or quality.shape[-1] != 2:
            raise ValueError("quality must have shape [B, T, 2]")
        if frames.shape[:2] != physiology.shape[:2] or frames.shape[:2] != quality.shape[:2]:
            raise ValueError("all inputs must share batch and time dimensions")
