"""Masked multi-task objective for heterogeneous drowsiness datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch
from torch import Tensor, nn


@dataclass(frozen=True, slots=True)
class MultiTaskLossWeights:
    classification: float = 1.0
    eye_closure: float = 0.20
    yawn: float = 0.15
    head_pose: float = 0.05
    quality: float = 0.05


def masked_mean(values: Tensor, mask: Tensor) -> Tensor:
    """Mean over available labels while keeping a differentiable zero for empty masks."""

    selected = values * mask.to(values.dtype)
    denominator = mask.sum().clamp_min(1).to(values.dtype)
    return selected.sum() / denominator


def _weighted_mean(values: Tensor, weight: Tensor | None) -> Tensor:
    """Weighted mean of per-sample ``values``, equal to a plain mean when weight is None."""

    if weight is None:
        return values.mean()
    weight = weight.to(values.dtype)
    denominator = weight.sum().clamp_min(1e-8)
    return (values * weight).sum() / denominator


class MultiTaskLoss(nn.Module):
    """Combine primary and optional auxiliary supervision without fabricating labels.

    Auxiliary targets use a matching ``*_mask`` tensor. Samples from datasets that do
    not provide a target contribute zero to that head rather than receiving pseudo-ground
    truth by default.
    """

    def __init__(
        self,
        weights: MultiTaskLossWeights | None = None,
        label_smoothing: float = 0.0,
        classification_objective: Literal[
            "categorical_cross_entropy",
            "cumulative_ordinal",
            "categorical_with_ordinal_regularization",
        ] = "categorical_cross_entropy",
    ):
        super().__init__()
        if not 0 <= label_smoothing < 1:
            raise ValueError("label_smoothing must be in [0, 1)")
        self.weights = weights or MultiTaskLossWeights()
        self.label_smoothing = label_smoothing
        self.classification_objective = classification_objective
        self.categorical_classification = nn.CrossEntropyLoss(
            label_smoothing=label_smoothing, reduction="none"
        )

    def classification_loss(
        self, logits: Tensor, labels: Tensor, sample_weight: Tensor | None = None
    ) -> Tensor:
        """Evaluate the configured categorical or frozen cumulative ordinal objective.

        ``sample_weight`` down-weights individual windows (e.g. temporally ambiguous
        UTA-RLDD windows via ``datasets.label_confidence``) without changing the mean
        loss when every weight is 1.0.
        """

        if self.classification_objective == "categorical_cross_entropy":
            per_sample = self.categorical_classification(logits, labels)
            return _weighted_mean(per_sample, sample_weight)
        ordinal = cumulative_ordinal_loss(
            logits, labels, label_smoothing=self.label_smoothing, sample_weight=sample_weight
        )
        if self.classification_objective == "cumulative_ordinal":
            return ordinal
        categorical = _weighted_mean(self.categorical_classification(logits, labels), sample_weight)
        return categorical + 0.5 * ordinal

    def forward(self, outputs: dict[str, Tensor], targets: dict[str, Tensor]) -> dict[str, Tensor]:
        losses: dict[str, Tensor] = {
            "classification": self.classification_loss(
                outputs["logits"], targets["label"], targets.get("sample_weight")
            )
        }
        losses["eye_closure"] = self._masked_binary(
            outputs["eye_closure_logits"], targets, "eye_closure"
        )
        losses["yawn"] = self._masked_binary(outputs["yawn_logits"], targets, "yawn")
        losses["quality"] = self._masked_binary(
            outputs["quality_logits"], targets, "quality_target"
        )

        pose_error = nn.functional.smooth_l1_loss(
            outputs["head_pose"], targets["head_pose"], reduction="none"
        ).mean(dim=-1)
        losses["head_pose"] = masked_mean(pose_error, targets["head_pose_mask"].bool())

        total = (
            self.weights.classification * losses["classification"]
            + self.weights.eye_closure * losses["eye_closure"]
            + self.weights.yawn * losses["yawn"]
            + self.weights.head_pose * losses["head_pose"]
            + self.weights.quality * losses["quality"]
        )
        losses["total"] = total
        return losses

    @staticmethod
    def _masked_binary(logits: Tensor, targets: dict[str, Tensor], name: str) -> Tensor:
        values = nn.functional.binary_cross_entropy_with_logits(
            logits, targets[name].to(logits.dtype), reduction="none"
        )
        return masked_mean(values, targets[f"{name}_mask"].bool())


def cumulative_ordinal_logits(logits: Tensor) -> Tensor:
    """Convert three class logits into logits for y>0 and y>1."""

    if logits.ndim != 2 or logits.shape[1] != 3:
        raise ValueError("cumulative ordinal loss requires logits with shape [batch, 3]")
    above_zero = torch.logsumexp(logits[:, 1:], dim=1) - logits[:, 0]
    above_one = logits[:, 2] - torch.logsumexp(logits[:, :2], dim=1)
    return torch.stack((above_zero, above_one), dim=1)


def cumulative_ordinal_targets(
    labels: Tensor,
    *,
    label_smoothing: float = 0.0,
    dtype: torch.dtype = torch.float32,
) -> Tensor:
    """Return smoothed [y>0, y>1] targets for ordered labels 0, 1, and 2."""

    if labels.ndim != 1 or bool(((labels < 0) | (labels > 2)).any()):
        raise ValueError("cumulative ordinal labels must be one-dimensional values in {0,1,2}")
    if not 0 <= label_smoothing < 1:
        raise ValueError("label_smoothing must be in [0, 1)")
    targets = torch.stack((labels > 0, labels > 1), dim=1).to(dtype=dtype)
    return targets * (1.0 - label_smoothing) + label_smoothing / 2.0


def cumulative_ordinal_loss(
    logits: Tensor,
    labels: Tensor,
    *,
    label_smoothing: float = 0.0,
    sample_weight: Tensor | None = None,
) -> Tensor:
    """Mean binary log loss across the two ordered class boundaries."""

    boundary_logits = cumulative_ordinal_logits(logits)
    boundary_targets = cumulative_ordinal_targets(
        labels, label_smoothing=label_smoothing, dtype=logits.dtype
    )
    per_boundary = nn.functional.binary_cross_entropy_with_logits(
        boundary_logits, boundary_targets, reduction="none"
    )
    return _weighted_mean(per_boundary.mean(dim=1), sample_weight)
