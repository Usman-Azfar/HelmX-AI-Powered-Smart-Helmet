"""Deterministic training-window sampling policies."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd
import torch
from torch.utils.data import Sampler

SUBJECT_CLASS_COLUMNS = ["dataset", "subject_id", "label"]


class SubjectClassBalancedSampler(Sampler[int]):
    """Sample equal expected mass from every subject-class manifest cell."""

    def __init__(self, frame: pd.DataFrame, *, seed: int) -> None:
        missing = set(SUBJECT_CLASS_COLUMNS).difference(frame.columns)
        if missing:
            raise ValueError(f"sampling frame is missing columns: {sorted(missing)}")
        if frame.empty:
            raise ValueError("sampling frame cannot be empty")
        if frame[SUBJECT_CLASS_COLUMNS].isnull().any().any():
            raise ValueError("subject-class sampling fields cannot be null")

        counts = frame.groupby(SUBJECT_CLASS_COLUMNS, sort=False, observed=True)["label"].transform(
            "size"
        )
        self.weights = torch.as_tensor(1.0 / counts.to_numpy(dtype="float64"), dtype=torch.float64)
        self.num_samples = len(frame)
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        """Select the deterministic sampling stream for one 1-indexed training epoch."""

        if epoch < 1:
            raise ValueError("sampling epoch must be at least 1")
        self.epoch = epoch

    def __iter__(self) -> Iterator[int]:
        if self.epoch < 1:
            raise RuntimeError("set_epoch must be called before balanced sampling")
        generator = torch.Generator()
        generator.manual_seed(self.seed + self.epoch)
        indices = torch.multinomial(
            self.weights,
            self.num_samples,
            replacement=True,
            generator=generator,
        )
        return iter(indices.tolist())

    def __len__(self) -> int:
        return self.num_samples
