"""Reproducible single-seed training orchestration."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader

from helmx_drowsiness.config import ProjectConfig
from helmx_drowsiness.datasets.manifest import read_manifest, validate_label_space
from helmx_drowsiness.datasets.scaling import PhysiologyScaler, fit_physiology_scaler
from helmx_drowsiness.datasets.sequences import SequenceDataset, VideoBagDataset
from helmx_drowsiness.evaluation.bootstrap import clustered_prediction_bootstrap
from helmx_drowsiness.evaluation.calibration import fit_temperature
from helmx_drowsiness.evaluation.metrics import classification_metrics
from helmx_drowsiness.evaluation.report import detailed_classification_report
from helmx_drowsiness.models import QualityAwareTemporalNet, build_model
from helmx_drowsiness.training.engine import (
    collect_logits,
    collect_video_bag_logits,
    evaluate,
    evaluate_video_bags,
    seed_everything,
    train_epoch,
    train_video_bag_epoch,
)
from helmx_drowsiness.training.losses import MultiTaskLoss, MultiTaskLossWeights
from helmx_drowsiness.training.provenance import (
    environment_snapshot,
    git_revision,
    sha256_file,
    write_json,
)
from helmx_drowsiness.training.sampling import SubjectClassBalancedSampler


def run_training(
    config: ProjectConfig,
    *,
    config_path: str | Path,
    output_dir: str | Path,
    seed: int,
) -> Path:
    """Train one frozen-split seed and return the best checkpoint path."""

    seed_everything(seed)
    output = Path(output_dir) / f"seed-{seed}"
    output.mkdir(parents=True, exist_ok=True)
    best_checkpoint = output / "best.pt"
    completed_metrics = output / "test_metrics.json"
    development_complete = output / "development_complete.json"
    validation_decision = output / "validation_decision.json"
    if completed_metrics.is_file() and best_checkpoint.is_file():
        return best_checkpoint
    if development_complete.is_file() and best_checkpoint.is_file():
        return best_checkpoint
    if (
        config.training.supervision_unit == "video_bag"
        and validation_decision.is_file()
        and best_checkpoint.is_file()
    ):
        decision = json.loads(validation_decision.read_text(encoding="utf-8"))
        if not bool(decision["passed"]):
            return best_checkpoint
    video_supervision = config.training.supervision_unit == "video_bag"
    video_selection = video_supervision or config.training.checkpoint_selection_unit == "video"
    test_enabled = config.training.test_evaluation == "enabled"
    # A gated video experiment must not even probe held-out test artifacts before
    # validation passes; the selected train/validation files are opened by their loaders.
    manifest = read_manifest(
        config.data.manifest, check_paths=test_enabled and not video_supervision
    )
    train_frame = _select_split(manifest, "train")
    validation_frame = _select_split(manifest, "validation")
    validate_label_space(train_frame, config.model.num_classes, require_all=True)
    validate_label_space(validation_frame, config.model.num_classes, require_all=True)
    root = Path(config.data.manifest).parent
    if video_supervision:
        train_video_dataset = VideoBagDataset(
            train_frame,
            root,
            augment=config.data.augmentation,
            seed=seed,
            windows_per_third=config.training.video_bag_windows_per_third,
        )
        train_loader = _video_bag_loader(train_video_dataset, config, shuffle=True)
    else:
        train_video_dataset = None
        train_loader = _loader(train_frame, root, config, shuffle=True, seed=seed)
    if video_selection:
        validation_video_dataset = VideoBagDataset(
            validation_frame,
            root,
            augment=False,
            seed=seed,
            all_windows=True,
        )
        validation_loader = _video_bag_loader(
            validation_video_dataset,
            config,
            shuffle=False,
        )
    else:
        validation_video_dataset = None
        validation_loader = _loader(validation_frame, root, config, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(
        config.model,
        pretrained=False if config.model.eye_pretraining_checkpoint is not None else None,
    ).to(device)
    physiology_scaler = (
        PhysiologyScaler(
            np.zeros(config.model.physiology_features, dtype=np.float32),
            np.ones(config.model.physiology_features, dtype=np.float32),
            0,
        )
        if config.model.fusion_mode == "visual_only"
        else fit_physiology_scaler(train_frame, root)
    )
    model.set_physiology_scaler(
        torch.from_numpy(physiology_scaler.center).to(device),
        torch.from_numpy(physiology_scaler.scale).to(device),
    )
    if config.model.eye_pretraining_checkpoint is not None:
        from helmx_drowsiness.training.pretrain_eye import load_eye_backbone

        load_eye_backbone(model, config.model.eye_pretraining_checkpoint)
    if config.training.freeze_visual_backbone:
        model.freeze_visual_backbone()
    objective = MultiTaskLoss(
        weights=MultiTaskLossWeights(**config.training.loss_weights.model_dump()),
        label_smoothing=config.training.label_smoothing,
        classification_objective=config.training.classification_objective,
    )
    optimizer = _build_optimizer(model, config)

    provenance_path = output / "provenance.json"
    provenance = {
        "seed": seed,
        "window_sampling": config.training.window_sampling,
        "device": str(device),
        "git_revision": git_revision(),
        "config_sha256": sha256_file(config_path),
        "manifest_sha256": sha256_file(config.data.manifest),
        "eye_pretraining_sha256": (
            sha256_file(config.model.eye_pretraining_checkpoint)
            if config.model.eye_pretraining_checkpoint is not None
            else None
        ),
        "environment": environment_snapshot(),
        "physiology_scaler": {
            "center": physiology_scaler.center.tolist(),
            "scale": physiology_scaler.scale.tolist(),
            "observations": physiology_scaler.observations,
        },
        "config": config.model_dump(mode="json"),
    }
    if provenance_path.is_file():
        existing = json.loads(provenance_path.read_text(encoding="utf-8"))
        for key in (
            "seed",
            "window_sampling",
            "config_sha256",
            "manifest_sha256",
            "eye_pretraining_sha256",
        ):
            if existing.get(key) != provenance[key]:
                raise ValueError(f"cannot resume training: provenance mismatch for {key}")
    else:
        write_json(provenance_path, provenance)
    best_score = float("-inf")
    stale_epochs = 0
    start_epoch = 1
    history_path = output / "history.jsonl"
    # Captured once so the cosine schedule scales each parameter group from its own base
    # learning rate (head/temporal layers vs. the pretrained visual backbone) rather than
    # collapsing every group onto a single rate after the first epoch.
    base_learning_rates = [float(group["lr"]) for group in optimizer.param_groups]
    recovery_checkpoint = output / "last.pt"
    if recovery_checkpoint.is_file():
        recovery = torch.load(recovery_checkpoint, map_location=device, weights_only=True)
        model.load_state_dict(recovery["model_state"], strict=True)
        optimizer.load_state_dict(recovery["optimizer_state"])
        start_epoch = int(recovery["epoch"]) + 1
        best_score = float(recovery["best_score"])
        stale_epochs = int(recovery["stale_epochs"])
        if stale_epochs >= config.training.early_stopping_patience:
            start_epoch = config.training.epochs + 1
        torch.set_rng_state(recovery["torch_rng_state"].cpu())
        if torch.cuda.is_available() and "cuda_rng_states" in recovery:
            torch.cuda.set_rng_state_all(recovery["cuda_rng_states"])

    for epoch in range(start_epoch, config.training.epochs + 1):
        if isinstance(train_loader.sampler, SubjectClassBalancedSampler):
            train_loader.sampler.set_epoch(epoch)
        learning_rates = [float(group["lr"]) for group in optimizer.param_groups]
        if video_supervision:
            assert train_video_dataset is not None
            train_video_dataset.set_epoch(epoch)
            train_result = train_video_bag_epoch(
                model,
                train_loader,
                optimizer,
                device=device,
                label_smoothing=config.training.label_smoothing,
                accumulation_steps=config.training.gradient_accumulation,
                mixed_precision=config.training.mixed_precision,
            )
        else:
            train_result = train_epoch(
                model,
                train_loader,
                objective,
                optimizer,
                device=device,
                accumulation_steps=config.training.gradient_accumulation,
                mixed_precision=config.training.mixed_precision,
            )
        if video_selection:
            result = evaluate_video_bags(
                model,
                validation_loader,
                device=device,
                label_smoothing=config.training.label_smoothing,
                objective=objective,
            )
        else:
            result = evaluate(model, validation_loader, objective, device=device)
        record = {
            "epoch": epoch,
            "validation_unit": "video" if video_selection else "window",
            "learning_rate": learning_rates[0],
            "backbone_learning_rate": learning_rates[-1],
            "train_loss": train_result.loss,
            "validation_loss": result.loss,
            **{
                f"train_loss_{name}": value
                for name, value in train_result.component_losses.items()
                if name != "total"
            },
            **{
                f"validation_loss_{name}": value
                for name, value in result.component_losses.items()
                if name != "total"
            },
            **result.metrics.to_dict(),
        }
        with history_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

        score = result.metrics.macro_f1
        stop_after_epoch = False
        if score > best_score:
            best_score = score
            stale_epochs = 0
            _save_checkpoint(best_checkpoint, model, optimizer, epoch, score, seed)
        else:
            stale_epochs += 1
            if stale_epochs >= config.training.early_stopping_patience:
                stop_after_epoch = True
        cosine_factor = 0.5 * (1.0 + math.cos(math.pi * epoch / config.training.epochs))
        for parameter_group, base_lr in zip(
            optimizer.param_groups, base_learning_rates, strict=True
        ):
            parameter_group["lr"] = base_lr * cosine_factor
        _save_recovery_checkpoint(
            recovery_checkpoint,
            model,
            optimizer,
            epoch=epoch,
            best_score=best_score,
            stale_epochs=stale_epochs,
        )
        if stop_after_epoch:
            break

    best_payload = torch.load(best_checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(best_payload["model_state"], strict=True)
    if not bool(best_payload.get("calibrated", False)):
        if video_selection:
            validation_logits, validation_labels = collect_video_bag_logits(
                model, validation_loader, device=device
            )
        else:
            validation_logits, validation_labels = collect_logits(
                model,
                _loader(validation_frame, root, config, shuffle=False),
                device=device,
            )
        calibration = fit_temperature(validation_logits, validation_labels)
        model.set_temperature(calibration.temperature)
        calibration_record = asdict(calibration)
        best_payload["model_state"] = model.state_dict()
        best_payload["temperature"] = calibration.temperature
        best_payload["calibrated"] = True
        best_payload["calibration"] = calibration_record
        temporary_checkpoint = best_checkpoint.with_suffix(".calibrated.tmp")
        torch.save(best_payload, temporary_checkpoint)
        temporary_checkpoint.replace(best_checkpoint)
        write_json(output / "calibration.json", calibration_record)
    elif not (output / "calibration.json").is_file() and "calibration" in best_payload:
        write_json(output / "calibration.json", best_payload["calibration"])

    if video_selection:
        assert validation_video_dataset is not None
        validation_result = evaluate_video_bags(
            model,
            validation_loader,
            device=device,
            label_smoothing=config.training.label_smoothing,
            objective=objective,
        )
        write_json(
            output / "validation_video_metrics.json",
            {"loss": validation_result.loss, **validation_result.metrics.to_dict()},
        )
        predict_video_dataset_to_csv(
            model,
            validation_video_dataset,
            output / "validation_video_predictions.csv",
            device=device,
        )
    if video_supervision:
        gate = config.training.video_validation_macro_f1_gate
        assert gate is not None
        passed = best_score > gate
        write_json(
            validation_decision,
            {
                "passed": passed,
                "criterion": "best fold-2 video macro_f1 strictly exceeds frozen baseline",
                "best_validation_video_macro_f1": best_score,
                "frozen_baseline_video_macro_f1": gate,
                "test_fold_authorized": passed,
                "test_fold_accessed": False,
            },
        )
        if not passed:
            return best_checkpoint

    if not test_enabled:
        write_json(
            development_complete,
            {
                "best_validation_macro_f1": best_score,
                "checkpoint_selection_unit": "video" if video_selection else "window",
                "test_evaluation": "disabled",
                "test_split_accessed": False,
            },
        )
        return best_checkpoint

    test_frame = _select_split(manifest, "test")
    validate_label_space(test_frame, config.model.num_classes, require_all=True)
    test_result = evaluate(
        model,
        _loader(test_frame, root, config, shuffle=False),
        objective,
        device=device,
    )
    test_probabilities = predict_to_csv(
        model,
        test_frame,
        root,
        config,
        output / "test_predictions.csv",
        device=device,
    )
    write_json(
        output / "test_metrics.json",
        {
            "loss": test_result.loss,
            **test_result.metrics.to_dict(),
            "detailed": detailed_classification_report(
                test_frame["label"].to_numpy(),
                test_probabilities,
                config.data.label_names,
            ),
        },
    )
    if video_supervision:
        test_video_result = evaluate_video_bags(
            model,
            _video_bag_loader(
                VideoBagDataset(
                    test_frame,
                    root,
                    augment=False,
                    seed=seed,
                    all_windows=True,
                ),
                config,
                shuffle=False,
            ),
            device=device,
            label_smoothing=config.training.label_smoothing,
        )
        write_json(
            output / "test_video_metrics.json",
            {"loss": test_video_result.loss, **test_video_result.metrics.to_dict()},
        )
        write_json(
            validation_decision,
            {
                "passed": True,
                "criterion": "best fold-2 video macro_f1 strictly exceeds frozen baseline",
                "best_validation_video_macro_f1": best_score,
                "frozen_baseline_video_macro_f1": config.training.video_validation_macro_f1_gate,
                "test_fold_authorized": True,
                "test_fold_accessed": True,
            },
        )

    return best_checkpoint


def run_all_seeds(
    config: ProjectConfig,
    *,
    config_path: str | Path,
    output_dir: str | Path,
) -> list[Path]:
    """Train every preregistered seed and write an ensemble/uncertainty summary."""

    checkpoints = [
        run_training(
            config,
            config_path=config_path,
            output_dir=output_dir,
            seed=seed,
        )
        for seed in config.training.seeds
    ]
    if config.training.test_evaluation == "disabled":
        return checkpoints
    if config.training.supervision_unit == "video_bag" and any(
        not json.loads(
            (Path(output_dir) / f"seed-{seed}" / "validation_decision.json").read_text(
                encoding="utf-8"
            )
        )["passed"]
        for seed in config.training.seeds
    ):
        return checkpoints
    _aggregate_seed_results(Path(output_dir), config.training.seeds)
    return checkpoints


def _aggregate_seed_results(output: Path, seeds: tuple[int, ...]) -> None:
    per_seed = [
        json.loads((output / f"seed-{seed}" / "test_metrics.json").read_text(encoding="utf-8"))
        for seed in seeds
    ]
    numeric_keys = [key for key, value in per_seed[0].items() if isinstance(value, int | float)]
    mean = {key: float(np.mean([record[key] for record in per_seed])) for key in numeric_keys}
    standard_deviation = {
        key: float(np.std([record[key] for record in per_seed], ddof=1))
        if len(per_seed) > 1
        else 0.0
        for key in numeric_keys
    }

    predictions = [pd.read_csv(output / f"seed-{seed}" / "test_predictions.csv") for seed in seeds]
    identity = ["dataset", "subject_id", "session_id", "path", "label"]
    reference = predictions[0][identity].reset_index(drop=True)
    if any(
        not reference.equals(frame[identity].reset_index(drop=True)) for frame in predictions[1:]
    ):
        raise ValueError("seed prediction files do not contain identical ordered samples")
    probability_columns = sorted(
        [column for column in predictions[0] if column.startswith("probability_")]
    )
    ensemble_scores = np.mean(
        [frame[probability_columns].to_numpy(dtype=np.float64) for frame in predictions], axis=0
    )
    ensemble = reference.copy()
    ensemble["prediction"] = ensemble_scores.argmax(axis=1)
    ensemble[probability_columns] = ensemble_scores
    ensemble.to_csv(output / "ensemble_predictions.csv", index=False)

    labels = reference["label"].to_numpy(dtype=np.int64)
    groups = (
        reference["dataset"].astype(str) + "::" + reference["subject_id"].astype(str)
    ).to_numpy()
    ensemble_metrics = classification_metrics(labels, ensemble_scores)

    def macro_f1(targets: np.ndarray[Any, Any], scores: np.ndarray[Any, Any]) -> float:
        return float(
            f1_score(
                targets,
                scores.argmax(axis=1),
                labels=np.arange(scores.shape[1]),
                average="macro",
                zero_division=0,
            )
        )

    interval = clustered_prediction_bootstrap(labels, ensemble_scores, groups, macro_f1)
    write_json(
        output / "summary.json",
        {
            "seeds": list(seeds),
            "per_seed": per_seed,
            "mean": mean,
            "sample_standard_deviation": standard_deviation,
            "ensemble": ensemble_metrics.to_dict(),
            "ensemble_macro_f1_subject_clustered_ci": asdict(interval),
        },
    )


def predict_to_csv(
    model: QualityAwareTemporalNet,
    frame: pd.DataFrame,
    root: Path,
    config: ProjectConfig,
    destination: str | Path,
    *,
    device: torch.device,
) -> np.ndarray[Any, Any]:
    """Write auditable per-sample probabilities with dataset/subject/session identifiers."""

    loader = _loader(frame, root, config, shuffle=False)
    model.eval()
    rows: list[dict[str, Any]] = []
    all_probabilities: list[np.ndarray[Any, Any]] = []
    offset = 0
    with torch.inference_mode():
        for batch in loader:
            output = model(
                batch["frames"].to(device),
                batch["physiology"].to(device),
                batch["quality"].to(device),
            )
            logits = output["logits"]
            scores = logits.softmax(dim=-1).cpu().numpy()
            modality_weights = output["modality_weights"].mean(dim=1).cpu().numpy()
            all_probabilities.append(scores)
            for local_index, probability in enumerate(scores):
                source = frame.iloc[offset + local_index]
                row = {
                    "dataset": source["dataset"],
                    "subject_id": source["subject_id"],
                    "session_id": source["session_id"],
                    "path": source["path"],
                    "label": int(source["label"]),
                    "prediction": int(probability.argmax()),
                }
                for optional in ("fold", "start_seconds", "end_seconds"):
                    if optional in source.index:
                        row[optional] = source[optional]
                row.update(
                    {f"probability_{i}": float(value) for i, value in enumerate(probability)}
                )
                row["mean_visual_weight"] = float(modality_weights[local_index, 0])
                row["mean_physiology_weight"] = float(modality_weights[local_index, 1])
                rows.append(row)
            offset += len(scores)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write predictions for an empty data frame")
    with destination_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return np.concatenate(all_probabilities)


def predict_video_dataset_to_csv(
    model: QualityAwareTemporalNet,
    dataset: VideoBagDataset,
    destination: str | Path,
    *,
    device: torch.device,
) -> np.ndarray[Any, Any]:
    """Write one calibrated all-window mean-logit prediction per provider video."""

    logits, labels = collect_video_bag_logits(
        model,
        DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0),
        device=device,
    )
    probabilities = logits.softmax(dim=-1).numpy()
    rows: list[dict[str, Any]] = []
    for group, label, probability in zip(
        dataset.groups, labels.numpy(), probabilities, strict=True
    ):
        subject, session, _, _, positions = group
        source = dataset.sequences.manifest.iloc[positions[0]]
        row: dict[str, Any] = {
            "dataset": source["dataset"],
            "subject_id": subject,
            "session_id": session,
            "label": int(label),
            "prediction": int(probability.argmax()),
            "windows": len(positions),
        }
        if "fold" in source.index:
            row["fold"] = int(source["fold"])
        row.update(
            {f"probability_{index}": float(value) for index, value in enumerate(probability)}
        )
        rows.append(row)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return probabilities


def predict_checkpoint_split(
    checkpoint_path: str | Path,
    config: ProjectConfig,
    destination: str | Path,
    *,
    split: str,
    fusion_mode: str | None = None,
) -> np.ndarray[Any, Any]:
    """Write auditable predictions for one manifest split from an existing checkpoint."""

    manifest = read_manifest(config.data.manifest)
    frame = _select_split(manifest, split)
    model_config = (
        config.model.model_copy(update={"fusion_mode": fusion_mode})
        if fusion_mode is not None
        else config.model
    )
    model = build_model(model_config, pretrained=False)
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or "model_state" not in payload:
        raise ValueError("checkpoint does not contain model_state")
    model.load_state_dict(payload["model_state"], strict=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return predict_to_csv(
        model,
        frame,
        Path(config.data.manifest).parent,
        config,
        destination,
        device=device,
    )


def _build_optimizer(
    model: QualityAwareTemporalNet, config: ProjectConfig
) -> torch.optim.Optimizer:
    """Use a discriminative learning rate for the pretrained visual backbone.

    Fine-tuning the backbone at the same rate as the newly initialized temporal/fusion/head
    layers risks overwriting what MRL Eye (or ImageNet) pretraining already learned before
    the new layers have caught up, especially on a drowsiness split far smaller than the
    pretraining data. Falls back to a single rate if none is configured.
    """

    backbone_ids = {id(parameter) for parameter in model.visual_backbone.parameters()}
    head_parameters = [
        parameter for parameter in model.parameters() if id(parameter) not in backbone_ids
    ]
    backbone_parameters = list(model.visual_backbone.parameters())
    backbone_learning_rate = config.training.backbone_learning_rate or config.training.learning_rate
    return torch.optim.AdamW(
        [
            {"params": head_parameters, "lr": config.training.learning_rate},
            {"params": backbone_parameters, "lr": backbone_learning_rate},
        ],
        weight_decay=config.training.weight_decay,
    )


def _select_split(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    selected = frame.loc[frame["split"] == split].reset_index(drop=True)
    if selected.empty:
        raise ValueError(f"manifest split is empty: {split}")
    return selected


def _loader(
    frame: pd.DataFrame,
    root: Path,
    config: ProjectConfig,
    *,
    shuffle: bool,
    seed: int | None = None,
) -> DataLoader[dict[str, torch.Tensor]]:
    sampler: SubjectClassBalancedSampler | None = None
    if shuffle and config.training.window_sampling == "subject_class_balanced":
        if seed is None:
            raise ValueError("balanced training sampling requires an explicit seed")
        sampler = SubjectClassBalancedSampler(frame, seed=seed)
    return DataLoader(
        SequenceDataset(frame, root, augment=shuffle and config.data.augmentation),
        batch_size=config.training.batch_size,
        shuffle=shuffle and sampler is None,
        sampler=sampler,
        num_workers=config.data.num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=config.data.num_workers > 0,
        drop_last=False,
    )


def _video_bag_loader(
    dataset: VideoBagDataset,
    config: ProjectConfig,
    *,
    shuffle: bool,
) -> DataLoader[dict[str, torch.Tensor]]:
    return DataLoader(
        dataset,
        batch_size=config.training.batch_size if shuffle else 1,
        shuffle=shuffle,
        num_workers=config.data.num_workers,
        pin_memory=torch.cuda.is_available(),
        # set_epoch mutates the main-process dataset; recreating workers each epoch
        # ensures deterministic epoch-specific selections are visible to workers.
        persistent_workers=False,
        drop_last=False,
    )


def _save_checkpoint(
    path: Path,
    model: QualityAwareTemporalNet,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    score: float,
    seed: int,
) -> None:
    temporary = path.with_suffix(".tmp")
    torch.save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "epoch": epoch,
            "validation_macro_f1": score,
            "seed": seed,
        },
        temporary,
    )
    temporary.replace(path)


def _save_recovery_checkpoint(
    path: Path,
    model: QualityAwareTemporalNet,
    optimizer: torch.optim.Optimizer,
    *,
    epoch: int,
    best_score: float,
    stale_epochs: int,
) -> None:
    """Atomically save everything needed to resume at the next epoch boundary."""

    temporary = path.with_suffix(".tmp")
    payload: dict[str, Any] = {
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "epoch": epoch,
        "best_score": best_score,
        "stale_epochs": stale_epochs,
        "torch_rng_state": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        payload["cuda_rng_states"] = torch.cuda.get_rng_state_all()
    torch.save(payload, temporary)
    temporary.replace(path)
