"""Trainable drowsiness models."""

from helmx_drowsiness.config import ModelConfig
from helmx_drowsiness.models.fusion import QualityAwareTemporalNet


def build_model(config: ModelConfig, *, pretrained: bool | None = None) -> QualityAwareTemporalNet:
    """Construct the configured architecture from one shared factory."""

    return QualityAwareTemporalNet(
        physiology_features=config.physiology_features,
        physiology_standardized_clip=config.physiology_standardized_clip,
        hidden_size=config.hidden_size,
        temporal_blocks=config.temporal_blocks,
        num_classes=config.num_classes,
        dropout=config.dropout,
        pretrained=config.pretrained if pretrained is None else pretrained,
        fusion_mode=config.fusion_mode,
        modality_dropout_probability=config.modality_dropout_probability,
    )


__all__ = ["QualityAwareTemporalNet", "build_model"]
