"""Validated configuration loading for training and real-time inference."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataConfig(StrictModel):
    manifest: Path
    visual_region: Literal["full_face", "eye_band", "dual_eye"] = "full_face"
    image_size: int = Field(ge=64, le=512)
    sequence_length: int = Field(ge=4, le=512)
    sample_fps: float = Field(gt=0, le=60)
    calibration_seconds: float = Field(ge=3, le=30)
    window_stride: int = Field(ge=1, le=512)
    num_workers: int = Field(ge=0, le=64)
    augmentation: bool
    label_names: tuple[str, ...] = Field(min_length=2)


class ModelConfig(StrictModel):
    fusion_mode: Literal[
        "quality_gated", "quality_concat", "equal", "visual_only", "physiology_only"
    ]
    modality_dropout_probability: float = Field(default=0.0, ge=0, le=1)
    backbone: Literal["mobilenetv3_small_100"]
    pretrained: bool
    eye_pretraining_checkpoint: Path | None
    physiology_features: int = Field(ge=1, le=128)
    physiology_standardized_clip: float = Field(default=10.0, gt=0, le=100)
    hidden_size: int = Field(ge=32, le=1024)
    temporal_blocks: int = Field(ge=1, le=12)
    dropout: float = Field(ge=0, lt=1)
    num_classes: int = Field(ge=2, le=20)


class LossWeightsConfig(StrictModel):
    """Multi-task loss weights.

    Auxiliary weights should stay zero unless the manifest actually supplies that target
    (see ``SequenceDataset``'s per-sample mask). A nonzero weight for a head no dataset
    labels adds no supervision, since the masked loss already contributes zero for
    unlabeled samples; it only misrepresents what the run actually trained.
    """

    classification: float = Field(ge=0)
    eye_closure: float = Field(ge=0)
    yawn: float = Field(ge=0)
    head_pose: float = Field(ge=0)
    quality: float = Field(ge=0)


class TrainingConfig(StrictModel):
    supervision_unit: Literal["window", "video_bag"] = "window"
    window_sampling: Literal["uniform_shuffle", "subject_class_balanced"] = "uniform_shuffle"
    classification_objective: Literal[
        "categorical_cross_entropy",
        "cumulative_ordinal",
        "categorical_with_ordinal_regularization",
    ] = "categorical_cross_entropy"
    checkpoint_selection_unit: Literal["window", "video"] | None = None
    test_evaluation: Literal["enabled", "disabled"] = "enabled"
    video_bag_windows_per_third: int = Field(default=1, ge=1, le=8)
    video_logit_pooling: Literal["mean"] = "mean"
    video_validation_macro_f1_gate: float | None = Field(default=None, ge=0, le=1)
    epochs: int = Field(ge=1)
    batch_size: int = Field(ge=1)
    learning_rate: float = Field(gt=0)
    backbone_learning_rate: float | None = Field(default=None, gt=0)
    freeze_visual_backbone: bool = False
    weight_decay: float = Field(ge=0)
    label_smoothing: float = Field(ge=0, lt=1)
    mixed_precision: bool
    gradient_accumulation: int = Field(ge=1)
    early_stopping_patience: int = Field(ge=1)
    seeds: tuple[int, ...] = Field(min_length=1)
    loss_weights: LossWeightsConfig = Field(
        default_factory=lambda: LossWeightsConfig(
            classification=1.0, eye_closure=0.20, yawn=0.15, head_pose=0.05, quality=0.05
        )
    )

    @model_validator(mode="after")
    def video_supervision_has_an_explicit_gate(self) -> TrainingConfig:
        if self.supervision_unit == "video_bag" and self.video_validation_macro_f1_gate is None:
            raise ValueError("video_bag supervision requires video_validation_macro_f1_gate")
        if self.supervision_unit == "window" and self.video_validation_macro_f1_gate is not None:
            raise ValueError("video_validation_macro_f1_gate applies only to video_bag supervision")
        if (
            self.supervision_unit == "video_bag"
            and self.classification_objective != "categorical_cross_entropy"
        ):
            raise ValueError("non-categorical objectives are frozen for window supervision only")
        if self.supervision_unit == "video_bag" and self.window_sampling != "uniform_shuffle":
            raise ValueError("subject-class-balanced sampling requires window supervision")
        return self


class AlertConfig(StrictModel):
    caution_probability: float = Field(ge=0, le=1)
    warning_probability: float = Field(ge=0, le=1)
    critical_probability: float = Field(ge=0, le=1)
    release_probability: float = Field(ge=0, le=1)
    caution_seconds: float = Field(gt=0)
    warning_seconds: float = Field(gt=0)
    critical_seconds: float = Field(gt=0)
    release_seconds: float = Field(gt=0)
    unavailable_seconds: float = Field(gt=0)
    alarm_cooldown_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def thresholds_are_ordered(self) -> AlertConfig:
        if not (
            self.release_probability
            < self.caution_probability
            < self.warning_probability
            < self.critical_probability
        ):
            raise ValueError("probability thresholds must increase from release to critical")
        if not self.caution_seconds <= self.warning_seconds <= self.critical_seconds:
            raise ValueError("severity durations must increase from caution to critical")
        return self


class ProjectConfig(StrictModel):
    schema_version: int = Field(ge=1)
    seed: int
    data: DataConfig
    model: ModelConfig
    training: TrainingConfig
    alert: AlertConfig

    @model_validator(mode="after")
    def experiment_dimensions_are_consistent(self) -> ProjectConfig:
        if len(self.data.label_names) != self.model.num_classes:
            raise ValueError("label_names length must equal model.num_classes")
        if len(set(self.data.label_names)) != len(self.data.label_names):
            raise ValueError("label_names must be unique")
        if len(set(self.training.seeds)) != len(self.training.seeds):
            raise ValueError("training seeds must be unique")
        if self.training.freeze_visual_backbone and self.model.eye_pretraining_checkpoint is None:
            raise ValueError("freeze_visual_backbone requires an eye_pretraining_checkpoint")
        return self


def load_config(path: str | Path) -> ProjectConfig:
    """Load YAML and reject unknown or invalid fields."""

    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return ProjectConfig.model_validate(payload)
