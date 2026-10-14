"""Efficient loading of preprocessed temporal samples."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import Tensor
from torch.utils.data import Dataset

IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class SequenceDataset(Dataset[dict[str, Tensor]]):
    """Read compressed, face-aligned temporal samples referenced by a manifest.

    Required NPZ arrays are ``frames`` (T,H,W,3 uint8; W may be 2H for packed eyes),
    ``physiology`` (T,F), and
    ``quality`` (T,2). Optional auxiliary arrays are masked when absent. Raw videos
    are deliberately preprocessed once so training runs do not depend on landmark
    detector timing or version-specific nondeterminism.
    """

    def __init__(self, manifest: pd.DataFrame, root: str | Path, *, augment: bool = False) -> None:
        self.manifest = manifest.reset_index(drop=True)
        self.root = Path(root)
        self.augment = augment

    def __len__(self) -> int:
        return len(self.manifest)

    def __getitem__(self, index: int) -> dict[str, Tensor]:
        row = self.manifest.iloc[index]
        sample_path = self.root / str(row["path"])
        with np.load(sample_path, allow_pickle=False) as sample:
            frames = _frames_to_tensor(sample["frames"])
            physiology = torch.from_numpy(sample["physiology"].astype(np.float32))
            quality = torch.from_numpy(sample["quality"].astype(np.float32))
            if frames.shape[:1] != physiology.shape[:1] or frames.shape[:1] != quality.shape[:1]:
                raise ValueError(f"temporal dimensions differ in {sample_path}")
            result: dict[str, Tensor] = {
                "frames": frames,
                "physiology": physiology,
                "quality": quality,
                "label": torch.tensor(int(row["label"]), dtype=torch.long),
                "sample_weight": torch.tensor(
                    float(row["label_confidence"]) if "label_confidence" in row.index else 1.0,
                    dtype=torch.float32,
                ),
            }
            result.update(_optional_target(sample, "eye_closure", scalar=True))
            result.update(_optional_target(sample, "yawn", scalar=True))
            result.update(_optional_target(sample, "head_pose", scalar=False, width=3))
            result.update(_optional_target(sample, "quality_target", scalar=True))
            if self.augment:
                from helmx_drowsiness.datasets.augmentation import TemporalAugment

                result = TemporalAugment()(result)
            return result


class VideoBagDataset(Dataset[dict[str, Tensor]]):
    """Group causal windows by video for deterministic weak supervision."""

    def __init__(
        self,
        manifest: pd.DataFrame,
        root: str | Path,
        *,
        augment: bool,
        seed: int,
        windows_per_third: int = 1,
        all_windows: bool = False,
    ) -> None:
        frame = manifest.reset_index(drop=True)
        required = {"subject_id", "session_id", "label", "start_seconds", "end_seconds"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"video-bag manifest is missing columns: {sorted(missing)}")
        if windows_per_third < 1:
            raise ValueError("windows_per_third must be positive")
        self.sequences = SequenceDataset(frame, root, augment=augment)
        self.seed = seed
        self.windows_per_third = windows_per_third
        self.all_windows = all_windows
        self.epoch = 0
        groups: list[tuple[str, str, int, tuple[tuple[int, ...], ...], tuple[int, ...]]] = []
        for (subject, session), group in frame.groupby(
            ["subject_id", "session_id"], sort=True, observed=True
        ):
            labels = group["label"].unique()
            if len(labels) != 1:
                raise ValueError(f"video has multiple labels: {subject}/{session}")
            positions = tuple(int(index) for index in group.index)
            video_start = float(group["start_seconds"].min())
            video_end = float(group["end_seconds"].max())
            midpoint = (group["start_seconds"] + group["end_seconds"]) / 2.0
            progress = (midpoint - video_start) / max(video_end - video_start, 1e-6)
            bins = (
                tuple(int(index) for index in group.index[progress <= 1.0 / 3.0]),
                tuple(
                    int(index)
                    for index in group.index[(progress > 1.0 / 3.0) & (progress <= 2.0 / 3.0)]
                ),
                tuple(int(index) for index in group.index[progress > 2.0 / 3.0]),
            )
            if any(not candidates for candidates in bins):
                raise ValueError(f"video does not cover all temporal thirds: {subject}/{session}")
            groups.append((str(subject), str(session), int(labels[0]), bins, positions))
        if not groups:
            raise ValueError("video-bag dataset contains no videos")
        self.groups = groups

    def __len__(self) -> int:
        return len(self.groups)

    def set_epoch(self, epoch: int) -> None:
        if epoch < 1:
            raise ValueError("video-bag epoch must be positive")
        self.epoch = epoch

    def __getitem__(self, index: int) -> dict[str, Tensor]:
        subject, session, label, bins, positions = self.groups[index]
        selected = positions if self.all_windows else self._select_windows(subject, session, bins)
        samples = [self.sequences[position] for position in selected]
        return {
            "frames": torch.stack([sample["frames"] for sample in samples]),
            "physiology": torch.stack([sample["physiology"] for sample in samples]),
            "quality": torch.stack([sample["quality"] for sample in samples]),
            "label": torch.tensor(label, dtype=torch.long),
        }

    def _select_windows(
        self, subject: str, session: str, bins: tuple[tuple[int, ...], ...]
    ) -> tuple[int, ...]:
        selected: list[int] = []
        for bin_index, candidates in enumerate(bins):
            digest = hashlib.sha256(
                f"{self.seed}:{self.epoch}:{subject}:{session}:{bin_index}".encode()
            ).digest()
            start = int.from_bytes(digest[:8], "big") % len(candidates)
            selected.extend(
                candidates[(start + offset) % len(candidates)]
                for offset in range(self.windows_per_third)
            )
        return tuple(selected)


def _frames_to_tensor(frames: np.ndarray[Any, Any]) -> Tensor:
    if frames.ndim != 4 or frames.shape[-1] != 3 or frames.dtype != np.uint8:
        raise ValueError("frames must be uint8 with shape [T, H, W, 3]")
    tensor = torch.from_numpy(frames.copy()).permute(0, 3, 1, 2).float().div_(255.0)
    return (tensor - IMAGENET_MEAN) / IMAGENET_STD


def _optional_target(
    sample: Any,
    key: str,
    *,
    scalar: bool,
    width: int = 1,
) -> dict[str, Tensor]:
    if key in sample:
        value = np.asarray(sample[key], dtype=np.float32)
        if scalar:
            value = value.reshape(-1)[-1]
            tensor = torch.tensor(value, dtype=torch.float32)
        else:
            tensor = torch.from_numpy(value.reshape(-1, width)[-1].copy())
        return {key: tensor, f"{key}_mask": torch.tensor(True)}
    default = torch.tensor(0.0) if scalar else torch.zeros(width)
    return {key: default, f"{key}_mask": torch.tensor(False)}
