import numpy as np
import pytest

from helmx_drowsiness.evaluation.metrics import (
    classification_metrics,
    expected_calibration_error,
)


def test_perfect_predictions_have_perfect_discrimination() -> None:
    labels = np.array([0, 1, 2, 0, 1, 2])
    probabilities = np.eye(3)[labels] * 0.98 + (1 - np.eye(3)[labels]) * 0.01
    metrics = classification_metrics(labels, probabilities)
    assert metrics.accuracy == 1.0
    assert metrics.macro_f1 == 1.0
    assert metrics.macro_roc_auc_ovr == 1.0
    assert metrics.expected_calibration_error == pytest.approx(0.02)


def test_invalid_probability_rows_are_rejected() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        expected_calibration_error([0], [[0.2, 0.2, 0.2]])
