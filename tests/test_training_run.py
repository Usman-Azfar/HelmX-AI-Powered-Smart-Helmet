from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from helmx_drowsiness.config import ProjectConfig, load_config
from helmx_drowsiness.models import QualityAwareTemporalNet
from helmx_drowsiness.training.run import run_training


@pytest.mark.parametrize("freeze_backbone", [False, True])
def test_training_orchestration_writes_calibrated_test_artifacts(
    tmp_path: Path, freeze_backbone: bool
) -> None:
    rows: list[dict[str, object]] = []
    for split in ("train", "validation", "test"):
        for label in range(3):
            name = f"{split}_{label}.npz"
            np.savez_compressed(
                tmp_path / name,
                frames=np.full((4, 64, 64, 3), 40 + label * 80, dtype=np.uint8),
                physiology=np.column_stack(
                    (np.zeros((4, 11), dtype=np.float32), np.ones(4, dtype=np.float32))
                ),
                quality=np.ones((4, 2), dtype=np.float32),
            )
            rows.append(
                {
                    "dataset": "synthetic",
                    "subject_id": f"{split}_{label}",
                    "session_id": name,
                    "path": name,
                    "label": label,
                    "split": split,
                }
            )
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    payload = load_config("configs/default.yaml").model_dump()
    payload["data"].update(
        {
            "manifest": manifest,
            "image_size": 64,
            "sequence_length": 4,
            "num_workers": 0,
            "augmentation": False,
        }
    )
    payload["model"].update(
        {
            "pretrained": False,
            "eye_pretraining_checkpoint": None,
            "hidden_size": 32,
            "temporal_blocks": 1,
            "dropout": 0.0,
        }
    )
    if freeze_backbone:
        eye_checkpoint = tmp_path / "eye.pt"
        eye_model = QualityAwareTemporalNet(pretrained=False)
        torch.save(
            {"visual_backbone_state": eye_model.visual_backbone.state_dict()}, eye_checkpoint
        )
        payload["model"]["eye_pretraining_checkpoint"] = eye_checkpoint
    payload["training"].update(
        {
            "epochs": 1,
            "batch_size": 3,
            "gradient_accumulation": 1,
            "early_stopping_patience": 1,
            "seeds": [7],
            "freeze_visual_backbone": freeze_backbone,
        }
    )
    config = ProjectConfig.model_validate(payload)
    output = tmp_path / "runs"
    checkpoint = run_training(config, config_path="configs/default.yaml", output_dir=output, seed=7)
    seed_output = output / "seed-7"
    assert checkpoint.is_file()
    assert (seed_output / "calibration.json").is_file()
    assert (seed_output / "test_metrics.json").is_file()
    predictions = pd.read_csv(seed_output / "test_predictions.csv")
    assert len(predictions) == 3
    assert (seed_output / "last.pt").is_file()
    provenance = pd.read_json(seed_output / "provenance.json", typ="series")
    assert bool(provenance["config"]["training"]["freeze_visual_backbone"]) is freeze_backbone
    assert provenance["window_sampling"] == "uniform_shuffle"

    # A completed run is an idempotent recovery target, not an exist_ok=False failure.
    resumed = run_training(config, config_path="configs/default.yaml", output_dir=output, seed=7)
    assert resumed == checkpoint
    assert len((seed_output / "history.jsonl").read_text(encoding="utf-8").splitlines()) == 1

    # Simulate an incomplete run whose config path is unchanged but whose in-memory sampling
    # policy was altered. Provenance must reject it before the recovery checkpoint is resumed.
    (seed_output / "test_metrics.json").unlink()
    mismatched = config.model_copy(
        update={
            "training": config.training.model_copy(
                update={"window_sampling": "subject_class_balanced"}
            )
        }
    )
    with pytest.raises(ValueError, match="provenance mismatch for window_sampling"):
        run_training(
            mismatched,
            config_path="configs/default.yaml",
            output_dir=output,
            seed=7,
        )


def test_video_bag_gate_keeps_failed_run_away_from_test_files(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for split in ("train", "validation", "test"):
        for label in range(3):
            for window in range(3):
                name = f"{split}_{label}_{window}.npz"
                if split != "test":
                    np.savez_compressed(
                        tmp_path / name,
                        frames=np.full((4, 64, 64, 3), 40 + label * 80, dtype=np.uint8),
                        physiology=np.zeros((4, 12), dtype=np.float32),
                        quality=np.ones((4, 2), dtype=np.float32),
                    )
                rows.append(
                    {
                        "dataset": "synthetic",
                        "subject_id": f"{split}_{label}",
                        "session_id": f"video_{label}",
                        "path": name,
                        "label": label,
                        "split": split,
                        "start_seconds": window * 10.0,
                        "end_seconds": (window + 1) * 10.0,
                    }
                )
    manifest = tmp_path / "video_manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    payload = load_config("configs/default.yaml").model_dump()
    payload["data"].update(
        {
            "manifest": manifest,
            "image_size": 64,
            "sequence_length": 4,
            "num_workers": 0,
            "augmentation": False,
        }
    )
    payload["model"].update(
        {
            "fusion_mode": "visual_only",
            "pretrained": False,
            "eye_pretraining_checkpoint": None,
            "hidden_size": 32,
            "temporal_blocks": 1,
            "dropout": 0.0,
        }
    )
    payload["training"].update(
        {
            "supervision_unit": "video_bag",
            "video_validation_macro_f1_gate": 1.0,
            "epochs": 1,
            "batch_size": 3,
            "gradient_accumulation": 1,
            "early_stopping_patience": 1,
            "seeds": [7],
        }
    )
    config = ProjectConfig.model_validate(payload)
    output = tmp_path / "video_runs"
    checkpoint = run_training(config, config_path="configs/default.yaml", output_dir=output, seed=7)
    seed_output = output / "seed-7"
    assert checkpoint.is_file()
    decision = pd.read_json(seed_output / "validation_decision.json", typ="series")
    assert not bool(decision["passed"])
    assert not bool(decision["test_fold_accessed"])
    assert not (seed_output / "test_metrics.json").exists()

    resumed = run_training(config, config_path="configs/default.yaml", output_dir=output, seed=7)
    assert resumed == checkpoint
    assert len((seed_output / "history.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_ordinal_video_selection_development_run_never_accesses_test(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for split in ("train", "validation", "test"):
        for label in range(3):
            for window in range(3):
                name = f"{split}_{label}_{window}.npz"
                if split != "test":
                    physiology = np.zeros((4, 12), dtype=np.float32)
                    physiology[:, -1] = 1.0
                    np.savez_compressed(
                        tmp_path / name,
                        frames=np.full((4, 64, 64, 3), 40 + label * 80, dtype=np.uint8),
                        physiology=physiology,
                        quality=np.ones((4, 2), dtype=np.float32),
                    )
                rows.append(
                    {
                        "dataset": "synthetic",
                        "subject_id": f"{split}_{label}",
                        "session_id": f"video_{label}",
                        "path": name,
                        "label": label,
                        "split": split,
                        "start_seconds": window * 10.0,
                        "end_seconds": (window + 1) * 10.0,
                    }
                )
    manifest = tmp_path / "ordinal_manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    payload = load_config("configs/default.yaml").model_dump()
    payload["data"].update(
        {
            "manifest": manifest,
            "image_size": 64,
            "sequence_length": 4,
            "num_workers": 0,
            "augmentation": False,
        }
    )
    payload["model"].update(
        {
            "pretrained": False,
            "eye_pretraining_checkpoint": None,
            "hidden_size": 32,
            "temporal_blocks": 1,
            "dropout": 0.0,
        }
    )
    payload["training"].update(
        {
            "classification_objective": "cumulative_ordinal",
            "checkpoint_selection_unit": "video",
            "test_evaluation": "disabled",
            "epochs": 1,
            "batch_size": 3,
            "gradient_accumulation": 1,
            "early_stopping_patience": 1,
            "seeds": [7],
        }
    )
    config = ProjectConfig.model_validate(payload)
    output = tmp_path / "ordinal_runs"
    checkpoint = run_training(config, config_path="configs/default.yaml", output_dir=output, seed=7)
    seed_output = output / "seed-7"
    assert checkpoint.is_file()
    completion = pd.read_json(seed_output / "development_complete.json", typ="series")
    assert completion["checkpoint_selection_unit"] == "video"
    assert not bool(completion["test_split_accessed"])
    assert (seed_output / "validation_video_metrics.json").is_file()
    video_predictions = pd.read_csv(seed_output / "validation_video_predictions.csv")
    assert len(video_predictions) == 3
    assert video_predictions["windows"].tolist() == [3, 3, 3]
    assert not (seed_output / "test_metrics.json").exists()
    history = pd.read_json(seed_output / "history.jsonl", lines=True)
    assert history.loc[0, "validation_unit"] == "video"
