"""Subject-disjoint MRL Eye auxiliary pretraining."""

from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from torch import Tensor, nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

from helmx_drowsiness.models import QualityAwareTemporalNet
from helmx_drowsiness.training.engine import seed_everything
from helmx_drowsiness.training.provenance import (
    environment_snapshot,
    git_revision,
    sha256_file,
    write_json,
)

MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class MrlEyeDataset(Dataset[tuple[Tensor, Tensor, int]]):
    def __init__(self, frame: pd.DataFrame, root: str | Path, *, size: int, augment: bool) -> None:
        self.frame = frame.reset_index(drop=True)
        self.root = Path(root)
        self.size = size
        self.augment = augment

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor, int]:
        row = self.frame.iloc[index]
        image = cv2.imread(str(self.root / str(row["path"])), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(self.root / str(row["path"]))
        resized = np.asarray(cv2.resize(image, (self.size, self.size)), dtype=np.uint8)
        if self.augment:
            resized = _augment(resized)
        tensor = torch.from_numpy(resized.copy()).float().div_(255.0).repeat(3, 1, 1)
        tensor = (tensor - MEAN) / STD
        return tensor, torch.tensor(float(row["eye_state"])), index


class EyeStateNet(nn.Module):
    def __init__(self, *, pretrained: bool = True) -> None:
        super().__init__()
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = mobilenet_v3_small(weights=weights)
        features = model.classifier[0].in_features
        self.visual_backbone = model.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(features, 1)

    def forward(self, images: Tensor) -> Tensor:
        result: Tensor = self.classifier(
            self.pool(self.visual_backbone(images)).flatten(1)
        ).squeeze(-1)
        return result


def pretrain_mrl_eye(
    index_path: str | Path,
    root: str | Path,
    output_dir: str | Path,
    *,
    validation_fold: int = 0,
    test_fold: int = 1,
    epochs: int = 20,
    batch_size: int = 128,
    image_size: int = 128,
    seed: int = 2026,
) -> Path:
    """Train an eye-state auxiliary backbone and evaluate one untouched subject fold."""

    if validation_fold == test_fold:
        raise ValueError("validation and test folds must differ")
    seed_everything(seed)
    frame = pd.read_csv(index_path, dtype={"subject_id": str, "sensor_id": str})
    validation = frame.loc[frame["fold"] == validation_fold].reset_index(drop=True)
    test = frame.loc[frame["fold"] == test_fold].reset_index(drop=True)
    train = frame.loc[~frame["fold"].isin([validation_fold, test_fold])].reset_index(drop=True)
    if train.empty or validation.empty or test.empty:
        raise ValueError("MRL fold selection produced an empty split")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EyeStateNet(pretrained=True).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    objective = nn.BCEWithLogitsLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    train_loader = _loader(train, root, image_size, batch_size, train=True)
    validation_loader = _loader(validation, root, image_size, batch_size, train=False)
    best_f1 = float("-inf")
    checkpoint = output / "best_eye_backbone.pt"
    history: list[dict[str, float | int]] = []
    stale_epochs = 0

    for epoch in range(1, epochs + 1):
        learning_rate = float(optimizer.param_groups[0]["lr"])
        model.train()
        losses: list[float] = []
        for images, labels, _ in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device.type, enabled=device.type == "cuda"):
                loss = objective(model(images), labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(optimizer)
            scaler.update()
            losses.append(float(loss.detach()))
        metrics, _ = _evaluate(model, validation_loader, validation, device)
        history.append(
            {
                "epoch": epoch,
                "learning_rate": learning_rate,
                "train_loss": float(np.mean(losses)),
                **metrics,
            }
        )
        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            stale_epochs = 0
            temporary = checkpoint.with_suffix(".tmp")
            torch.save(
                {
                    "visual_backbone_state": model.visual_backbone.state_dict(),
                    "model_state": model.state_dict(),
                    "validation_macro_f1": best_f1,
                    "seed": seed,
                },
                temporary,
            )
            temporary.replace(checkpoint)
        else:
            stale_epochs += 1
            if stale_epochs >= 5:
                break
        next_learning_rate = 3e-4 * 0.5 * (1.0 + math.cos(math.pi * epoch / epochs))
        for parameter_group in optimizer.param_groups:
            parameter_group["lr"] = next_learning_rate

    payload = torch.load(checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(payload["model_state"], strict=True)
    test_metrics, predictions = _evaluate(
        model, _loader(test, root, image_size, batch_size, train=False), test, device
    )
    predictions.to_csv(output / "test_predictions.csv", index=False)
    write_json(
        output / "metrics.json",
        {
            "validation_best_macro_f1": best_f1,
            **test_metrics,
            "test_subgroups": _subgroup_metrics(predictions),
        },
    )
    write_json(
        output / "provenance.json",
        {
            "index_sha256": sha256_file(index_path),
            "checkpoint_sha256": sha256_file(checkpoint),
            "git_revision": git_revision(),
            "environment": environment_snapshot(),
            "validation_fold": validation_fold,
            "test_fold": test_fold,
            "epochs": epochs,
            "batch_size": batch_size,
            "image_size": image_size,
            "seed": seed,
        },
    )
    with (output / "history.jsonl").open("w", encoding="utf-8") as stream:
        for record in history:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    return checkpoint


def load_eye_backbone(model: QualityAwareTemporalNet, checkpoint: str | Path) -> None:
    """Strictly transfer an MRL-pretrained visual backbone into the temporal model."""

    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or "visual_backbone_state" not in payload:
        raise ValueError("eye checkpoint does not contain visual_backbone_state")
    model.visual_backbone.load_state_dict(payload["visual_backbone_state"], strict=True)


def _loader(
    frame: pd.DataFrame,
    root: str | Path,
    image_size: int,
    batch_size: int,
    *,
    train: bool,
) -> DataLoader[tuple[Tensor, Tensor, int]]:
    sampler = None
    if train:
        counts = frame["eye_state"].value_counts()
        weights = frame["eye_state"].map(lambda label: 1.0 / counts[label]).to_numpy()
        sampler = WeightedRandomSampler(weights.tolist(), len(frame), replacement=True)
    return DataLoader(
        MrlEyeDataset(frame, root, size=image_size, augment=train),
        batch_size=batch_size,
        sampler=sampler,
        shuffle=False,
        num_workers=4,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=True,
    )


@torch.inference_mode()
def _evaluate(
    model: EyeStateNet,
    loader: DataLoader[tuple[Tensor, Tensor, int]],
    frame: pd.DataFrame,
    device: torch.device,
) -> tuple[dict[str, float], pd.DataFrame]:
    model.eval()
    scores: list[NDArray[np.float64]] = []
    labels: list[NDArray[np.int64]] = []
    indices: list[NDArray[np.int64]] = []
    for images, targets, row_indices in loader:
        probability = model(images.to(device)).sigmoid().cpu().numpy()
        scores.append(np.asarray(probability, dtype=np.float64))
        labels.append(targets.numpy().astype(np.int64))
        indices.append(row_indices.numpy())
    y_true = np.concatenate(labels)
    y_score = np.concatenate(scores)
    y_pred = (y_score >= 0.5).astype(np.int64)
    result = frame.iloc[np.concatenate(indices)].reset_index(drop=True).copy()
    result["probability_open"] = y_score
    result["prediction"] = y_pred
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_score)),
    }
    return metrics, result


def _augment(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    result = image
    if torch.rand(()) < 0.5:
        result = np.fliplr(result)
    contrast = float(torch.empty(()).uniform_(0.8, 1.2))
    brightness = float(torch.empty(()).uniform_(-18, 18))
    adjusted = np.clip(result.astype(np.float32) * contrast + brightness, 0, 255)
    return np.asarray(adjusted, dtype=np.uint8)


def _subgroup_metrics(predictions: pd.DataFrame) -> dict[str, dict[str, dict[str, float | int]]]:
    result: dict[str, dict[str, dict[str, float | int]]] = {}
    for column in ("gender", "glasses", "reflections", "lighting", "sensor_id"):
        groups: dict[str, dict[str, float | int]] = {}
        for value, subset in predictions.groupby(column, dropna=False):
            groups[str(value)] = {
                "samples": len(subset),
                "accuracy": float(accuracy_score(subset["eye_state"], subset["prediction"])),
                "macro_f1": float(
                    f1_score(
                        subset["eye_state"],
                        subset["prediction"],
                        average="macro",
                        zero_division=0,
                    )
                ),
            }
        result[column] = groups
    return result
