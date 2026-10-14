"""Time-based, hysteretic drowsiness alert controller."""

from __future__ import annotations

from dataclasses import dataclass

from helmx_drowsiness.config import AlertConfig
from helmx_drowsiness.types import AlertDecision, AlertLevel, FrameEvidence


@dataclass(slots=True)
class _Timer:
    since: float | None = None

    def duration(self, now: float, active: bool) -> float:
        if not active:
            self.since = None
            return 0.0
        if self.since is None:
            self.since = now
        return max(0.0, now - self.since)


class AlertController:
    """Convert calibrated frame evidence into stable alerts using elapsed time.

    The controller never uses camera-reported FPS. Hysteresis prevents alert chatter,
    and low-quality/missing observations transition to UNAVAILABLE rather than being
    silently interpreted as an alert driver.
    """

    def __init__(self, config: AlertConfig, *, minimum_quality: float = 0.35) -> None:
        self.config = config
        self.minimum_quality = minimum_quality
        self.level = AlertLevel.ALERT
        self._last_timestamp: float | None = None
        self._last_alarm = float("-inf")
        self._poor_quality = _Timer()
        self._release = _Timer()
        self._caution = _Timer()
        self._warning = _Timer()
        self._critical = _Timer()

    def update(self, evidence: FrameEvidence) -> AlertDecision:
        self._validate(evidence)
        now = evidence.timestamp
        probability = evidence.drowsy_probability
        good_quality = evidence.quality >= self.minimum_quality

        poor_duration = self._poor_quality.duration(now, not good_quality)
        previous = self.level
        reason = "stable"

        if poor_duration >= self.config.unavailable_seconds:
            self.level = AlertLevel.UNAVAILABLE
            reason = "insufficient visual quality"
            self._reset_detection_timers()
        elif not good_quality:
            reason = "waiting for reliable visual evidence"
            self._reset_detection_timers()
        elif good_quality:
            release_duration = self._release.duration(
                now, probability <= self.config.release_probability
            )
            caution_duration = self._caution.duration(
                now, probability >= self.config.caution_probability
            )
            warning_duration = self._warning.duration(
                now, probability >= self.config.warning_probability
            )
            critical_duration = self._critical.duration(
                now, probability >= self.config.critical_probability
            )

            if critical_duration >= self.config.critical_seconds:
                self.level = AlertLevel.CRITICAL
                reason = "critical probability sustained"
            elif warning_duration >= self.config.warning_seconds:
                self.level = max(self.level, AlertLevel.WARNING)
                reason = "warning probability sustained"
            elif caution_duration >= self.config.caution_seconds:
                self.level = max(self.level, AlertLevel.CAUTION)
                reason = "caution probability sustained"
            elif release_duration >= self.config.release_seconds:
                self.level = AlertLevel.ALERT
                reason = "alertness probability sustained"

        changed = self.level != previous
        should_alarm = (
            good_quality
            and self.level >= AlertLevel.WARNING
            and now - self._last_alarm >= self.config.alarm_cooldown_seconds
        )
        if should_alarm:
            self._last_alarm = now

        self._last_timestamp = now
        return AlertDecision(
            timestamp=now,
            level=self.level,
            probability=probability,
            quality=evidence.quality,
            changed=changed,
            should_alarm=should_alarm,
            reason=reason,
        )

    def _validate(self, evidence: FrameEvidence) -> None:
        if self._last_timestamp is not None and evidence.timestamp < self._last_timestamp:
            raise ValueError("evidence timestamps must be monotonically non-decreasing")
        if not 0.0 <= evidence.drowsy_probability <= 1.0:
            raise ValueError("drowsy_probability must be in [0, 1]")
        if not 0.0 <= evidence.quality <= 1.0:
            raise ValueError("quality must be in [0, 1]")

    def _reset_detection_timers(self) -> None:
        for timer in (self._release, self._caution, self._warning, self._critical):
            timer.since = None
