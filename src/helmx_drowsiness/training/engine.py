"""Deterministic training/evaluation primitives with mixed precision support."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from helmx_drowsiness.evaluation.metrics import ClassificationMetrics, classification_metrics
from helmx_drowsiness.training.losses import MultiTaskLoss


@dataclass(frozen=True, slots=True)
class EpochResult:
    loss: float
    component_losses: dict[str, float]
    metrics: ClassificationMetrics


@dataclass(frozen=True, slots=True)
class TrainEpochResult:
    loss: float
    component_losses: dict[str, float]


def seed_everything(seed: int) -> None:
    """Seed supported random generators and request deterministic algorithms."""

    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cudnn.benchmark = False


def train_epoch(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    objective: MultiTaskLoss,
    optimizer: torch.optim.Optimizer,
    *,
    device: torch.device,
    accumulation_steps: int = 1,
    mixed_precision: bool = True,
) -> TrainEpochResult:
    if accumulation_steps < 1:
        raise ValueError("accumulation_steps must be positive")
    model.train()
    optimizer.zero_grad(set_to_none=True)
    scaler = torch.amp.GradScaler("cuda", enabled=mixed_precision and device.type == "cuda")
    total_loss = 0.0
    component_totals: dict[str, float] = {}
    sample_count = 0
    steps = 0
    for steps, batch in enumerate(batches, start=1):
        moved = _to_device(batch, device)
        with torch.amp.autocast(device.type, enabled=mixed_precision and device.type == "cuda"):
            outputs = model(moved["frames"], moved["physiology"], moved["quality"])
            losses = objective(outputs, moved)
            scaled_loss = losses["total"] / accumulation_steps
        scaler.scale(scaled_loss).backward()
        if steps % accumulation_steps == 0:
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
        batch_size = moved["label"].shape[0]
        total_loss += float(losses["total"].detach()) * batch_size
        for name, value in losses.items():
            component_totals[name] = (
                component_totals.get(name, 0.0) + float(value.detach()) * batch_size
            )
        sample_count += batch_size

    if steps and steps % accumulation_steps:
        scaler.unscale_(optimizer)
        remainder = steps % accumulation_steps
        correction = accumulation_steps / remainder
        for parameter in model.parameters():
            if parameter.grad is not None:
                parameter.grad.mul_(correction)
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)
    if sample_count == 0:
        raise ValueError("training loader produced no samples")
    return TrainEpochResult(
        total_loss / sample_count,
        {name: value / sample_count for name, value in component_totals.items()},
    )


def train_video_bag_epoch(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    optimizer: torch.optim.Optimizer,
    *,
    device: torch.device,
    label_smoothing: float,
    accumulation_steps: int = 1,
    mixed_precision: bool = True,
) -> TrainEpochResult:
    """Train from one mean-logit classification loss per provider video."""

    if accumulation_steps < 1:
        raise ValueError("accumulation_steps must be positive")
    model.train()
    optimizer.zero_grad(set_to_none=True)
    scaler = torch.amp.GradScaler("cuda", enabled=mixed_precision and device.type == "cuda")
    total_loss = 0.0
    video_count = 0
    steps = 0
    for steps, batch in enumerate(batches, start=1):
        moved = _to_device(batch, device)
        with torch.amp.autocast(device.type, enabled=mixed_precision and device.type == "cuda"):
            logits = _mean_video_logits(model, moved)
            loss = nn.functional.cross_entropy(
                logits, moved["label"], label_smoothing=label_smoothing
            )
            scaled_loss = loss / accumulation_steps
        scaler.scale(scaled_loss).backward()  # type: ignore[no-untyped-call]
        if steps % accumulation_steps == 0:
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
        batch_size = moved["label"].shape[0]
        total_loss += float(loss.detach()) * batch_size
        video_count += batch_size
    if steps and steps % accumulation_steps:
        scaler.unscale_(optimizer)
        remainder = steps % accumulation_steps
        correction = accumulation_steps / remainder
        for parameter in model.parameters():
            if parameter.grad is not None:
                parameter.grad.mul_(correction)
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)
    if video_count == 0:
        raise ValueError("video-bag training loader produced no videos")
    average = total_loss / video_count
    return TrainEpochResult(
        average,
        {
            "total": average,
            "classification": average,
            "eye_closure": 0.0,
            "yawn": 0.0,
            "head_pose": 0.0,
            "quality": 0.0,
        },
    )


@torch.inference_mode()
def evaluate(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    objective: MultiTaskLoss,
    *,
    device: torch.device,
) -> EpochResult:
    model.eval()
    labels: list[np.ndarray[Any, Any]] = []
    probabilities: list[np.ndarray[Any, Any]] = []
    total_loss = 0.0
    component_totals: dict[str, float] = {}
    sample_count = 0
    for batch in batches:
        moved = _to_device(batch, device)
        outputs = model(moved["frames"], moved["physiology"], moved["quality"])
        losses = objective(outputs, moved)
        loss = losses["total"]
        batch_size = moved["label"].shape[0]
        total_loss += float(loss) * batch_size
        for name, value in losses.items():
            component_totals[name] = component_totals.get(name, 0.0) + float(value) * batch_size
        sample_count += batch_size
        labels.append(moved["label"].cpu().numpy())
        probabilities.append(outputs["logits"].softmax(dim=-1).cpu().numpy())
    if sample_count == 0:
        raise ValueError("evaluation loader produced no samples")
    all_labels = np.concatenate(labels)
    all_probabilities = np.concatenate(probabilities)
    return EpochResult(
        loss=total_loss / sample_count,
        component_losses={name: value / sample_count for name, value in component_totals.items()},
        metrics=classification_metrics(all_labels, all_probabilities),
    )


@torch.inference_mode()
def evaluate_video_bags(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    *,
    device: torch.device,
    label_smoothing: float,
    objective: MultiTaskLoss | None = None,
) -> EpochResult:
    """Evaluate deterministic all-window mean logits at the video level."""

    model.eval()
    labels: list[np.ndarray[Any, Any]] = []
    probabilities: list[np.ndarray[Any, Any]] = []
    total_loss = 0.0
    video_count = 0
    for batch in batches:
        moved = _to_device(batch, device)
        logits = _mean_video_logits(model, moved)
        loss = (
            objective.classification_loss(logits, moved["label"])
            if objective is not None
            else nn.functional.cross_entropy(
                logits, moved["label"], label_smoothing=label_smoothing
            )
        )
        batch_size = moved["label"].shape[0]
        total_loss += float(loss) * batch_size
        video_count += batch_size
        labels.append(moved["label"].cpu().numpy())
        probabilities.append(logits.softmax(dim=-1).cpu().numpy())
    if video_count == 0:
        raise ValueError("video-bag evaluation loader produced no videos")
    all_labels = np.concatenate(labels)
    all_probabilities = np.concatenate(probabilities)
    average = total_loss / video_count
    return EpochResult(
        loss=average,
        component_losses={
            "total": average,
            "classification": average,
            "eye_closure": 0.0,
            "yawn": 0.0,
            "head_pose": 0.0,
            "quality": 0.0,
        },
        metrics=classification_metrics(all_labels, all_probabilities),
    )


@torch.inference_mode()
def collect_logits(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    *,
    device: torch.device,
) -> tuple[Tensor, Tensor]:
    """Collect validation logits and labels without changing their order."""

    model.eval()
    logits: list[Tensor] = []
    labels: list[Tensor] = []
    for batch in batches:
        moved = _to_device(batch, device)
        output = model(moved["frames"], moved["physiology"], moved["quality"])
        logits.append(output["logits"].cpu())
        labels.append(moved["label"].cpu())
    if not labels:
        raise ValueError("calibration loader produced no samples")
    return torch.cat(logits), torch.cat(labels)


@torch.inference_mode()
def collect_video_bag_logits(
    model: nn.Module,
    batches: Iterable[dict[str, Tensor]],
    *,
    device: torch.device,
) -> tuple[Tensor, Tensor]:
    """Collect one deterministic all-window mean logit per video."""

    model.eval()
    logits: list[Tensor] = []
    labels: list[Tensor] = []
    for batch in batches:
        moved = _to_device(batch, device)
        logits.append(_mean_video_logits(model, moved).cpu())
        labels.append(moved["label"].cpu())
    if not labels:
        raise ValueError("video-bag calibration loader produced no videos")
    return torch.cat(logits), torch.cat(labels)


def _mean_video_logits(model: nn.Module, batch: dict[str, Tensor]) -> Tensor:
    frames = batch["frames"]
    physiology = batch["physiology"]
    quality = batch["quality"]
    batch_size, instances = frames.shape[:2]
    output = model(
        frames.reshape(batch_size * instances, *frames.shape[2:]),
        physiology.reshape(batch_size * instances, *physiology.shape[2:]),
        quality.reshape(batch_size * instances, *quality.shape[2:]),
    )
    result: Tensor = output["logits"].reshape(batch_size, instances, -1).mean(dim=1)
    return result


def _to_device(batch: dict[str, Tensor], device: torch.device) -> dict[str, Tensor]:
    return {key: value.to(device, non_blocking=True) for key, value in batch.items()}
