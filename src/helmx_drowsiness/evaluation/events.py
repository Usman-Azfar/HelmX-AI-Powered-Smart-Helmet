"""Event-level alert metrics for irregularly sampled driving sessions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True, slots=True)
class EventMetrics:
    true_events: int
    detected_events: int
    missed_events: int
    event_sensitivity: float
    false_alert_events: int
    non_drowsy_hours: float
    false_alerts_per_hour: float
    median_detection_delay_seconds: float
    p95_detection_delay_seconds: float


def event_metrics(
    timestamps: ArrayLike,
    drowsy_ground_truth: ArrayLike,
    alert_active: ArrayLike,
) -> EventMetrics:
    """Score contiguous drowsiness and alert episodes without assuming fixed FPS."""

    times = np.asarray(timestamps, dtype=np.float64)
    truth = np.asarray(drowsy_ground_truth, dtype=np.bool_)
    alerts = np.asarray(alert_active, dtype=np.bool_)
    if times.ndim != 1 or truth.shape != times.shape or alerts.shape != times.shape:
        raise ValueError("timestamps, truth, and alerts must be equal-length vectors")
    if len(times) < 2:
        raise ValueError("at least two observations are required")
    if not np.isfinite(times).all() or (np.diff(times) < 0).any():
        raise ValueError("timestamps must be finite and monotonic")

    events = _runs(truth)
    delays: list[float] = []
    for start, end in events:
        detected = np.flatnonzero(alerts[start : end + 1])
        if detected.size:
            delays.append(float(times[start + detected[0]] - times[start]))

    false_active = alerts & ~truth
    false_alert_events = len(_runs(false_active))
    delta = np.diff(times, append=times[-1])
    non_drowsy_hours = float(delta[~truth].sum() / 3600.0)
    false_rate = false_alert_events / non_drowsy_hours if non_drowsy_hours > 0 else float("nan")
    detected_events = len(delays)
    sensitivity = detected_events / len(events) if events else float("nan")
    return EventMetrics(
        true_events=len(events),
        detected_events=detected_events,
        missed_events=len(events) - detected_events,
        event_sensitivity=float(sensitivity),
        false_alert_events=false_alert_events,
        non_drowsy_hours=non_drowsy_hours,
        false_alerts_per_hour=float(false_rate),
        median_detection_delay_seconds=float(np.median(delays)) if delays else float("nan"),
        p95_detection_delay_seconds=float(np.percentile(delays, 95)) if delays else float("nan"),
    )


def _runs(values: np.ndarray[tuple[int, ...], np.dtype[np.bool_]]) -> list[tuple[int, int]]:
    padded = np.pad(values.astype(np.int8), (1, 1))
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1) - 1
    return list(zip(starts.tolist(), ends.tolist(), strict=True))
