import pytest

from helmx_drowsiness.features.temporal import (
    OcularObservation,
    TemporalFeatureExtractor,
    fit_personal_baseline,
)


def observation(timestamp: float, ear: float = 0.30, quality: float = 1.0) -> OcularObservation:
    return OcularObservation(timestamp, ear, ear, 0.20, 1.0, 2.0, 3.0, quality)


def test_personal_baseline_uses_robust_median() -> None:
    samples = [observation(float(index)) for index in range(20)]
    samples.append(observation(21.0, ear=9.0))
    baseline = fit_personal_baseline(samples)
    assert baseline.ear == pytest.approx(0.30)
    assert baseline.eye_closed_threshold == pytest.approx(0.21)


def test_perclos_and_closure_duration_are_time_based() -> None:
    baseline = fit_personal_baseline([observation(float(index)) for index in range(20)])
    extractor = TemporalFeatureExtractor(baseline)
    extractor.update(observation(100.0, ear=0.30))
    extractor.update(observation(100.2, ear=0.10))
    features = extractor.update(observation(102.2, ear=0.10))
    assert features[2] == pytest.approx(2 / 3)
    assert features[5] == pytest.approx(2.0)


def test_low_quality_observations_reduce_valid_fraction() -> None:
    baseline = fit_personal_baseline([observation(float(index)) for index in range(20)])
    extractor = TemporalFeatureExtractor(baseline)
    extractor.update(observation(100.0))
    features = extractor.update(observation(101.0, quality=0.0))
    assert features[-1] == pytest.approx(0.5)


def test_blink_rate_floors_elapsed_duration_to_avoid_early_spikes() -> None:
    baseline = fit_personal_baseline([observation(float(index)) for index in range(20)])
    extractor = TemporalFeatureExtractor(baseline, minimum_elapsed_seconds=5.0)
    extractor.update(observation(100.0, ear=0.30))
    extractor.update(observation(100.1, ear=0.10))
    features = extractor.update(observation(100.2, ear=0.30))
    # One completed blink over an actual elapsed span of 0.2s would be 300/min uncapped;
    # the floor keeps the early-session estimate bounded to a plausible rate instead.
    assert features[3] == pytest.approx(60.0 / 5.0)


def test_minimum_elapsed_seconds_must_be_positive() -> None:
    baseline = fit_personal_baseline([observation(float(index)) for index in range(20)])
    with pytest.raises(ValueError, match="minimum_elapsed_seconds"):
        TemporalFeatureExtractor(baseline, minimum_elapsed_seconds=0.0)
