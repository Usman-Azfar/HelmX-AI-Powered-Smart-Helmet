from pathlib import Path

import pytest
from pydantic import ValidationError

from helmx_drowsiness.config import ProjectConfig, load_config


def test_default_config_is_internally_consistent() -> None:
    config = load_config(Path("configs/default.yaml"))
    assert len(config.data.label_names) == config.model.num_classes
    assert config.model.physiology_standardized_clip == 10.0


def test_config_rejects_label_model_dimension_mismatch() -> None:
    payload = load_config(Path("configs/default.yaml")).model_dump()
    payload["model"]["num_classes"] = 4
    with pytest.raises(ValidationError, match="label_names length"):
        ProjectConfig.model_validate(payload)


@pytest.mark.parametrize(
    "path",
    [Path("configs/default.yaml"), Path("configs/pilot.yaml"), Path("configs/uta-pilot.yaml")],
)
def test_auxiliary_loss_weights_stay_zero_until_a_dataset_supplies_those_labels(
    path: Path,
) -> None:
    # SequenceDataset never emits eye_closure/yawn/head_pose/quality_target arrays for any
    # dataset this repository currently preprocesses, so a nonzero weight here would not add
    # supervision - it would only misreport a classification-only run as multi-task. Flip
    # this back on deliberately once a dataset with real masked targets is in the manifest.
    weights = load_config(path).training.loss_weights
    assert weights.classification > 0
    assert weights.eye_closure == 0
    assert weights.yawn == 0
    assert weights.head_pose == 0
    assert weights.quality == 0


@pytest.mark.parametrize(
    "path",
    [Path("configs/default.yaml"), Path("configs/pilot.yaml"), Path("configs/uta-pilot.yaml")],
)
def test_backbone_learning_rate_is_lower_than_the_head_rate(path: Path) -> None:
    training = load_config(path).training
    assert training.backbone_learning_rate is not None
    assert training.backbone_learning_rate < training.learning_rate


def test_official_uta_pilot_is_one_seed_on_the_frozen_manifest() -> None:
    config = load_config("configs/uta-pilot.yaml")

    assert config.seed == 13
    assert config.training.seeds == (13,)
    assert config.data.manifest == Path("data/processed/uta-rldd/manifest_test1_validation2.csv")


def test_video_bag_supervision_requires_an_explicit_validation_gate() -> None:
    payload = load_config("configs/default.yaml").model_dump()
    payload["training"]["supervision_unit"] = "video_bag"
    with pytest.raises(ValidationError, match="requires video_validation_macro_f1_gate"):
        ProjectConfig.model_validate(payload)

    payload["training"]["video_validation_macro_f1_gate"] = 0.48629
    config = ProjectConfig.model_validate(payload)
    assert config.training.supervision_unit == "video_bag"


def test_frozen_visual_backbone_requires_eye_pretraining() -> None:
    payload = load_config("configs/default.yaml").model_dump()
    payload["training"]["freeze_visual_backbone"] = True
    payload["model"]["eye_pretraining_checkpoint"] = None
    with pytest.raises(ValidationError, match="requires an eye_pretraining_checkpoint"):
        ProjectConfig.model_validate(payload)


def test_historical_configs_default_to_categorical_window_selection() -> None:
    config = load_config("configs/uta-pilot.yaml")
    assert config.training.classification_objective == "categorical_cross_entropy"
    assert config.training.window_sampling == "uniform_shuffle"
    assert config.training.checkpoint_selection_unit is None
    assert config.training.test_evaluation == "enabled"


def test_d2_baseline_and_ordinal_configs_differ_only_in_objective() -> None:
    baseline = load_config("configs/uta-multifold-d2-categorical.yaml")
    candidate = load_config("configs/uta-multifold-d2-ordinal.yaml")
    assert baseline.training.checkpoint_selection_unit == "video"
    assert baseline.training.test_evaluation == "disabled"
    candidate_as_baseline = candidate.model_copy(
        update={
            "training": candidate.training.model_copy(
                update={"classification_objective": "categorical_cross_entropy"}
            )
        }
    )
    assert candidate_as_baseline == baseline


@pytest.mark.parametrize(
    "objective", ["cumulative_ordinal", "categorical_with_ordinal_regularization"]
)
def test_non_categorical_objective_is_rejected_for_video_bag_supervision(
    objective: str,
) -> None:
    payload = load_config("configs/uta-pilot-dual-eye-video-mil.yaml").model_dump()
    payload["training"]["classification_objective"] = objective
    with pytest.raises(ValidationError, match="window supervision only"):
        ProjectConfig.model_validate(payload)


def test_subject_class_balancing_is_rejected_for_video_bag_supervision() -> None:
    payload = load_config("configs/uta-pilot-dual-eye-video-mil.yaml").model_dump()
    payload["training"]["window_sampling"] = "subject_class_balanced"
    with pytest.raises(ValidationError, match="requires window supervision"):
        ProjectConfig.model_validate(payload)


@pytest.mark.parametrize("fold", [2, 3, 4, 5])
def test_hybrid_configs_differ_from_categorical_only_in_objective(fold: int) -> None:
    baseline = load_config(f"configs/uta-multifold-d{fold}-categorical.yaml")
    candidate = load_config(f"configs/uta-multifold-d{fold}-hybrid.yaml")
    candidate_as_baseline = candidate.model_copy(
        update={
            "training": candidate.training.model_copy(
                update={"classification_objective": "categorical_cross_entropy"}
            )
        }
    )
    assert candidate_as_baseline == baseline


@pytest.mark.parametrize("fold", [2, 3, 4, 5])
def test_quality_concat_configs_differ_from_categorical_only_in_fusion(fold: int) -> None:
    baseline = load_config(f"configs/uta-multifold-d{fold}-categorical.yaml")
    candidate = load_config(f"configs/uta-multifold-d{fold}-quality-concat.yaml")
    candidate_as_baseline = candidate.model_copy(
        update={"model": candidate.model.model_copy(update={"fusion_mode": "quality_gated"})}
    )
    assert candidate_as_baseline == baseline


@pytest.mark.parametrize("fold", [2, 3, 4, 5])
def test_frozen_backbone_configs_differ_from_categorical_only_in_freeze_flag(fold: int) -> None:
    baseline = load_config(f"configs/uta-multifold-d{fold}-categorical.yaml")
    candidate = load_config(f"configs/uta-multifold-d{fold}-frozen-backbone.yaml")
    candidate_as_baseline = candidate.model_copy(
        update={"training": candidate.training.model_copy(update={"freeze_visual_backbone": False})}
    )
    assert candidate_as_baseline == baseline


@pytest.mark.parametrize("fold", [2, 3, 4, 5])
def test_balanced_sampling_configs_differ_from_categorical_only_in_sampler(fold: int) -> None:
    baseline = load_config(f"configs/uta-multifold-d{fold}-categorical.yaml")
    candidate = load_config(f"configs/uta-multifold-d{fold}-subject-class-balanced.yaml")
    candidate_as_baseline = candidate.model_copy(
        update={
            "training": candidate.training.model_copy(update={"window_sampling": "uniform_shuffle"})
        }
    )
    assert candidate_as_baseline == baseline
