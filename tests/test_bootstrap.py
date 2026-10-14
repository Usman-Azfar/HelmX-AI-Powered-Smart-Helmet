import numpy as np

from helmx_drowsiness.evaluation.bootstrap import (
    clustered_bootstrap,
    clustered_prediction_bootstrap,
    paired_clustered_prediction_bootstrap,
)


def test_clustered_bootstrap_is_reproducible() -> None:
    values = np.array([0.1, 0.2, 0.8, 0.9])
    groups = np.array(["a", "a", "b", "b"])
    first = clustered_bootstrap(values, groups, resamples=100, seed=7)
    second = clustered_bootstrap(values, groups, resamples=100, seed=7)
    assert first == second
    assert first.lower <= first.estimate <= first.upper


def test_prediction_bootstrap_resamples_whole_subjects() -> None:
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([[0.8, 0.2], [0.7, 0.3], [0.1, 0.9], [0.2, 0.8]])
    groups = np.array(["a", "a", "b", "b"])

    def accuracy(targets: np.ndarray, scores: np.ndarray) -> float:
        return float(np.mean(targets == scores.argmax(axis=1)))

    result = clustered_prediction_bootstrap(
        labels, probabilities, groups, accuracy, resamples=100, seed=7
    )
    assert result.estimate == 1.0
    assert result.lower == 1.0


def test_paired_prediction_bootstrap_reports_candidate_minus_baseline() -> None:
    labels = np.array([0, 1, 0, 1])
    baseline = np.array([[0.4, 0.6], [0.6, 0.4], [0.4, 0.6], [0.6, 0.4]])
    candidate = np.array([[0.8, 0.2], [0.2, 0.8], [0.8, 0.2], [0.2, 0.8]])
    groups = np.array(["a", "a", "b", "b"])

    def accuracy(targets: np.ndarray, scores: np.ndarray) -> float:
        return float(np.mean(targets == scores.argmax(axis=1)))

    result = paired_clustered_prediction_bootstrap(
        labels, baseline, candidate, groups, accuracy, resamples=100, seed=7
    )
    assert result.estimate == 1.0
    assert result.lower == 1.0
