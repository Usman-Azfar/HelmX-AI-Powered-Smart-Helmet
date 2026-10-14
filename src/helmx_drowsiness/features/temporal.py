"""Personalized temporal physiology features for causal inference."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class OcularObservation:
    timestamp: float
    left_ear: float
    right_ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float
    quality: float


@dataclass(frozen=True, slots=True)
class PersonalBaseline:
    ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float

    @property
    def eye_closed_threshold(self) -> float:
        return self.ear * 0.70

    @property
    def mouth_open_threshold(self) -> float:
        return max(self.mar * 1.8, self.mar + 0.15)


def fit_personal_baseline(
    observations: list[OcularObservation], *, minimum_quality: float = 0.65
) -> PersonalBaseline:
    """Fit robust neutral values from a short, explicitly alert calibration segment."""

    usable = [item for item in observations if item.quality >= minimum_quality]
    if len(usable) < 15:
        raise ValueError("at least 15 high-quality calibration observations are required")
    ears = [(item.left_ear + item.right_ear) / 2.0 for item in usable]
    return PersonalBaseline(
        ear=float(np.median(ears)),
        mar=float(np.median([item.mar for item in usable])),
        pitch=float(np.median([item.pitch for item in usable])),
        yaw=float(np.median([item.yaw for item in usable])),
        roll=float(np.median([item.roll for item in usable])),
    )


class TemporalFeatureExtractor:
    """Produce a fixed causal feature vector over a rolling time window."""

    feature_names = (
        "relative_ear",
        "ear_asymmetry",
        "perclos",
        "blink_rate_per_minute",
        "mean_blink_seconds",
        "current_closure_seconds",
        "relative_mar",
        "mouth_open_fraction",
        "relative_pitch",
        "relative_yaw",
        "relative_roll",
        "valid_fraction",
    )

    def __init__(
        self,
        baseline: PersonalBaseline,
        *,
        window_seconds: float = 60.0,
        minimum_quality: float = 0.35,
        minimum_elapsed_seconds: float = 5.0,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if minimum_elapsed_seconds <= 0:
            raise ValueError("minimum_elapsed_seconds must be positive")
        self.baseline = baseline
        self.window_seconds = window_seconds
        self.minimum_quality = minimum_quality
        self.minimum_elapsed_seconds = minimum_elapsed_seconds
        self._history: deque[OcularObservation] = deque()
        self._last_timestamp: float | None = None

    def update(self, observation: OcularObservation) -> NDArray[np.float32]:
        if self._last_timestamp is not None and observation.timestamp < self._last_timestamp:
            raise ValueError("observation timestamps must be monotonic")
        self._last_timestamp = observation.timestamp
        self._history.append(observation)
        cutoff = observation.timestamp - self.window_seconds
        while self._history and self._history[0].timestamp < cutoff:
            self._history.popleft()
        return self._features()

    def _features(self) -> NDArray[np.float32]:
        observations = list(self._history)
        valid = [item for item in observations if item.quality >= self.minimum_quality]
        if not valid:
            return np.zeros(len(self.feature_names), dtype=np.float32)

        ears = np.asarray(
            [(item.left_ear + item.right_ear) / 2.0 for item in valid], dtype=np.float64
        )
        closed = ears < self.baseline.eye_closed_threshold
        durations = _closed_run_durations(valid, closed)
        current_duration = durations[-1] if closed[-1] and durations else 0.0
        completed_blinks = durations[:-1] if closed[-1] and durations else durations
        # Floored to a real minimum, not just a divide-by-zero guard: early in a session the
        # rolling window has barely started filling, so a single blink over a tiny elapsed
        # span (e.g. one blink in 0.2s) would otherwise spike to hundreds of blinks/minute.
        elapsed = max(valid[-1].timestamp - valid[0].timestamp, self.minimum_elapsed_seconds)
        blink_rate = len(completed_blinks) * 60.0 / elapsed
        mean_blink = float(np.mean(completed_blinks)) if completed_blinks else 0.0
        latest = valid[-1]
        latest_ear = ears[-1]
        asymmetry = abs(latest.left_ear - latest.right_ear) / max(latest_ear, 1e-6)
        mouth_open = np.asarray(
            [item.mar > self.baseline.mouth_open_threshold for item in valid], dtype=np.float64
        )
        features = np.asarray(
            [
                latest_ear / max(self.baseline.ear, 1e-6),
                asymmetry,
                closed.mean(),
                blink_rate,
                mean_blink,
                current_duration,
                latest.mar / max(self.baseline.mar, 1e-6),
                mouth_open.mean(),
                latest.pitch - self.baseline.pitch,
                latest.yaw - self.baseline.yaw,
                latest.roll - self.baseline.roll,
                len(valid) / len(observations),
            ],
            dtype=np.float32,
        )
        return features


def _closed_run_durations(
    observations: list[OcularObservation], closed: NDArray[np.bool_]
) -> list[float]:
    durations: list[float] = []
    start: float | None = None
    for item, is_closed in zip(observations, closed, strict=True):
        if is_closed and start is None:
            start = item.timestamp
        elif not is_closed and start is not None:
            durations.append(max(0.0, item.timestamp - start))
            start = None
    if start is not None:
        durations.append(max(0.0, observations[-1].timestamp - start))
    return durations
