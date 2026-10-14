import numpy as np
import pytest

from helmx_drowsiness.evaluation.events import event_metrics


def test_event_metrics_use_time_and_contiguous_episodes() -> None:
    timestamps = np.arange(0.0, 10.0)
    truth = np.array([0, 0, 1, 1, 1, 0, 0, 1, 1, 0], dtype=bool)
    alerts = np.array([0, 1, 0, 1, 1, 0, 0, 0, 0, 0], dtype=bool)
    metrics = event_metrics(timestamps, truth, alerts)
    assert metrics.true_events == 2
    assert metrics.detected_events == 1
    assert metrics.event_sensitivity == pytest.approx(0.5)
    assert metrics.false_alert_events == 1
    assert metrics.median_detection_delay_seconds == pytest.approx(1.0)
