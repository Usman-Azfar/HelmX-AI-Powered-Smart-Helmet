from pathlib import Path

import pandas as pd
import pytest
from torch.utils.data import RandomSampler, SequentialSampler

from helmx_drowsiness.config import ProjectConfig, load_config
from helmx_drowsiness.training.run import _loader
from helmx_drowsiness.training.sampling import SubjectClassBalancedSampler


def _sampling_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"dataset": "uta", "subject_id": "a", "session_id": "alert", "label": 0},
            {"dataset": "uta", "subject_id": "a", "session_id": "drowsy_1", "label": 2},
            {"dataset": "uta", "subject_id": "a", "session_id": "drowsy_1", "label": 2},
            {"dataset": "uta", "subject_id": "a", "session_id": "drowsy_2", "label": 2},
            {"dataset": "uta", "subject_id": "b", "session_id": "alert", "label": 0},
            {"dataset": "uta", "subject_id": "b", "session_id": "alert", "label": 0},
        ]
    )


def test_subject_class_weights_give_each_cell_equal_mass_across_split_sessions() -> None:
    frame = _sampling_frame()
    sampler = SubjectClassBalancedSampler(frame, seed=13)
    weighted = frame.assign(weight=sampler.weights.numpy())

    assert sampler.weights.tolist() == pytest.approx([1.0, 1 / 3, 1 / 3, 1 / 3, 0.5, 0.5])
    cell_mass = weighted.groupby(["dataset", "subject_id", "label"])["weight"].sum()
    assert cell_mass.tolist() == pytest.approx([1.0, 1.0, 1.0])


def test_subject_class_sampler_is_epoch_deterministic_and_resume_safe() -> None:
    frame = _sampling_frame()
    uninterrupted = SubjectClassBalancedSampler(frame, seed=13)
    repeated = SubjectClassBalancedSampler(frame, seed=13)
    resumed = SubjectClassBalancedSampler(frame, seed=13)

    uninterrupted.set_epoch(1)
    epoch_one = list(uninterrupted)
    repeated.set_epoch(1)
    assert list(repeated) == epoch_one
    assert len(epoch_one) == len(frame)

    uninterrupted.set_epoch(2)
    epoch_two = list(uninterrupted)
    resumed.set_epoch(2)
    assert list(resumed) == epoch_two
    assert epoch_two != epoch_one


def test_balanced_sampler_requires_epoch_to_be_set() -> None:
    sampler = SubjectClassBalancedSampler(_sampling_frame(), seed=13)
    with pytest.raises(RuntimeError, match="set_epoch"):
        list(sampler)


def test_loader_changes_only_training_sampling_policy(tmp_path: Path) -> None:
    frame = _sampling_frame().assign(
        path=[f"sample_{index}.npz" for index in range(6)], split="train"
    )
    payload = load_config("configs/default.yaml").model_dump()
    payload["data"].update({"num_workers": 0, "augmentation": False})
    payload["training"]["window_sampling"] = "subject_class_balanced"
    candidate = ProjectConfig.model_validate(payload)

    train_loader = _loader(frame, tmp_path, candidate, shuffle=True, seed=13)
    validation_loader = _loader(frame, tmp_path, candidate, shuffle=False)
    assert isinstance(train_loader.sampler, SubjectClassBalancedSampler)
    assert isinstance(validation_loader.sampler, SequentialSampler)

    payload["training"]["window_sampling"] = "uniform_shuffle"
    baseline = ProjectConfig.model_validate(payload)
    historical_loader = _loader(frame, tmp_path, baseline, shuffle=True, seed=13)
    assert isinstance(historical_loader.sampler, RandomSampler)
    assert not historical_loader.sampler.replacement
