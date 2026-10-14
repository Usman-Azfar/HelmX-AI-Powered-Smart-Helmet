"""Shared, framework-independent domain types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class AlertLevel(IntEnum):
    """Ordered alert severity emitted by the temporal decision layer."""

    UNAVAILABLE = -1
    ALERT = 0
    CAUTION = 1
    WARNING = 2
    CRITICAL = 3


@dataclass(frozen=True, slots=True)
class FrameEvidence:
    """Calibrated evidence supplied to the time-based alert controller."""

    timestamp: float
    drowsy_probability: float
    quality: float


@dataclass(frozen=True, slots=True)
class AlertDecision:
    """A single controller decision suitable for UI, logging, or an alarm backend."""

    timestamp: float
    level: AlertLevel
    probability: float
    quality: float
    changed: bool
    should_alarm: bool
    reason: str
