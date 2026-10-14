"""Detailed per-class publication tables."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def detailed_classification_report(
    labels: ArrayLike,
    probabilities: ArrayLike,
    label_names: tuple[str, ...],
) -> dict[str, object]:
    targets = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    if scores.ndim != 2 or scores.shape[1] != len(label_names) or len(targets) != len(scores):
        raise ValueError("labels, probabilities, and label_names are inconsistent")
    predictions = scores.argmax(axis=1)
    classes = np.arange(len(label_names))
    precision, recall, f1, support = precision_recall_fscore_support(
        targets,
        predictions,
        labels=classes,
        zero_division=0,
    )
    matrix = confusion_matrix(targets, predictions, labels=classes)
    row_totals = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(
        matrix,
        row_totals,
        out=np.zeros_like(matrix, dtype=np.float64),
        where=row_totals > 0,
    )
    return {
        "per_class": {
            name: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, name in enumerate(label_names)
        },
        "confusion_matrix": matrix.tolist(),
        "row_normalized_confusion_matrix": normalized.tolist(),
    }
