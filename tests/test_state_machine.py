from helmx_drowsiness.config import AlertConfig
from helmx_drowsiness.state_machine import AlertController
from helmx_drowsiness.types import AlertLevel, FrameEvidence


def config() -> AlertConfig:
    return AlertConfig(
        caution_probability=0.55,
        warning_probability=0.72,
        critical_probability=0.88,
        release_probability=0.40,
        caution_seconds=1.0,
        warning_seconds=2.0,
        critical_seconds=3.0,
        release_seconds=1.0,
        unavailable_seconds=0.5,
        alarm_cooldown_seconds=3.0,
    )


def test_alerts_use_elapsed_time_not_frame_count() -> None:
    controller = AlertController(config())
    controller.update(FrameEvidence(10.0, 0.8, 1.0))
    assert controller.update(FrameEvidence(11.0, 0.8, 1.0)).level == AlertLevel.CAUTION
    decision = controller.update(FrameEvidence(12.01, 0.8, 1.0))
    assert decision.level == AlertLevel.WARNING
    assert decision.should_alarm


def test_hysteresis_requires_sustained_release() -> None:
    controller = AlertController(config())
    controller.update(FrameEvidence(0.0, 0.8, 1.0))
    controller.update(FrameEvidence(2.1, 0.8, 1.0))
    assert controller.level == AlertLevel.WARNING
    assert controller.update(FrameEvidence(2.2, 0.2, 1.0)).level == AlertLevel.WARNING
    assert controller.update(FrameEvidence(3.21, 0.2, 1.0)).level == AlertLevel.ALERT


def test_bad_quality_becomes_unavailable() -> None:
    controller = AlertController(config())
    controller.update(FrameEvidence(0.0, 0.99, 0.0))
    decision = controller.update(FrameEvidence(0.6, 0.99, 0.0))
    assert decision.level == AlertLevel.UNAVAILABLE
    assert not decision.should_alarm


def test_bad_quality_resets_persistence_and_never_alarms() -> None:
    controller = AlertController(config())
    controller.update(FrameEvidence(0.0, 0.8, 1.0))
    controller.update(FrameEvidence(1.9, 0.8, 0.0))
    decision = controller.update(FrameEvidence(2.0, 0.8, 1.0))
    assert decision.level == AlertLevel.ALERT
    assert not decision.should_alarm
