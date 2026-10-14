"""Metrics that remain informative under class imbalance."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    cohen_kappa_score,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    """Core discrimination and calibration metrics for a multi-class experiment."""

    samples: int
    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    weighted_f1: float
    macro_precision: float
    macro_recall: float
    matthews_correlation: float
    quadratic_kappa: float
    macro_roc_auc_ovr: float
    macro_pr_auc: float
    negative_log_likelihood: float
    multiclass_brier: float
    expected_calibration_error: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def expected_calibration_error(
    labels: ArrayLike, probabilities: ArrayLike, *, bins: int = 15
) -> float:
    """Top-label ECE using equal-width confidence bins."""

    targets = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    _validate_inputs(targets, scores)
    scores = scores / scores.sum(axis=1, keepdims=True)
    if bins < 2:
        raise ValueError("bins must be at least 2")
    confidence = scores.max(axis=1)
    predictions = scores.argmax(axis=1)
    correctness = predictions == targets
    edges = np.linspace(0.0, 1.0, bins + 1)
    result = 0.0
    for index in range(bins):
        lower, upper = edges[index], edges[index + 1]
        included = (confidence > lower) & (confidence <= upper)
        if index == 0:
            included |= confidence == 0.0
        if included.any():
            weight = included.mean()
            result += weight * abs(correctness[included].mean() - confidence[included].mean())
    return float(result)


def classification_metrics(labels: ArrayLike, probabilities: ArrayLike) -> ClassificationMetrics:
    """Compute a publication-ready metric set from calibrated class probabilities."""

    targets = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    _validate_inputs(targets, scores)
    scores = scores / scores.sum(axis=1, keepdims=True)
    predictions = scores.argmax(axis=1)
    classes = np.arange(scores.shape[1])
    one_hot = label_binarize(targets, classes=classes)
    if scores.shape[1] == 2 and one_hot.shape[1] == 1:
        one_hot = np.column_stack((1 - one_hot[:, 0], one_hot[:, 0]))

    roc_auc = _safe_metric(
        lambda: roc_auc_score(one_hot, scores, average="macro", multi_class="ovr")
    )
    pr_auc = _safe_metric(lambda: average_precision_score(one_hot, scores, average="macro"))
    brier = float(
        np.mean([brier_score_loss(one_hot[:, index], scores[:, index]) for index in classes])
    )
    return ClassificationMetrics(
        samples=len(targets),
        accuracy=float(accuracy_score(targets, predictions)),
        balanced_accuracy=float(balanced_accuracy_score(targets, predictions)),
        macro_f1=float(f1_score(targets, predictions, average="macro", zero_division=0)),
        weighted_f1=float(f1_score(targets, predictions, average="weighted", zero_division=0)),
        macro_precision=float(
            precision_score(targets, predictions, average="macro", zero_division=0)
        ),
        macro_recall=float(recall_score(targets, predictions, average="macro", zero_division=0)),
        matthews_correlation=float(matthews_corrcoef(targets, predictions)),
        quadratic_kappa=float(cohen_kappa_score(targets, predictions, weights="quadratic")),
        macro_roc_auc_ovr=roc_auc,
        macro_pr_auc=pr_auc,
        negative_log_likelihood=float(log_loss(targets, scores, labels=classes)),
        multiclass_brier=brier,
        expected_calibration_error=expected_calibration_error(targets, scores),
    )


def _validate_inputs(labels: NDArray[np.int64], probabilities: NDArray[np.float64]) -> None:
    if labels.ndim != 1:
        raise ValueError("labels must be one-dimensional")
    if probabilities.ndim != 2 or probabilities.shape[0] != len(labels):
        raise ValueError("probabilities must have shape [samples, classes]")
    if len(labels) == 0:
        raise ValueError("evaluation inputs cannot be empty")
    if not np.isfinite(probabilities).all():
        raise ValueError("probabilities must be finite")
    if (probabilities < 0).any() or (probabilities > 1).any():
        raise ValueError("probabilities must be in [0, 1]")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-5):
        raise ValueError("each probability row must sum to 1")
    if labels.min() < 0 or labels.max() >= probabilities.shape[1]:
        raise ValueError("labels are outside the class range")


def _safe_metric(function: object) -> float:
    try:
        return float(function())  # type: ignore[operator]
    except ValueError:
        return float("nan")
