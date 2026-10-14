"""Training-only robust physiology scaling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class PhysiologyScaler:
    center: NDArray[np.float32]
    scale: NDArray[np.float32]
    observations: int


def fit_physiology_scaler(frame: pd.DataFrame, root: str | Path) -> PhysiologyScaler:
    """Fit median/IQR statistics using only valid training observations."""

    arrays: list[NDArray[np.float32]] = []
    for relative in frame["path"].drop_duplicates():
        with np.load(Path(root) / str(relative), allow_pickle=False) as sample:
            physiology = np.asarray(sample["physiology"], dtype=np.float32)
        if physiology.ndim != 2:
            raise ValueError(f"physiology must be two-dimensional: {relative}")
        valid = physiology[:, -1] > 0
        if valid.any():
            arrays.append(physiology[valid])
    if not arrays:
        raise ValueError("training data contains no valid physiology observations")
    values = np.concatenate(arrays, axis=0).astype(np.float64)
    center = np.median(values, axis=0)
    lower, upper = np.percentile(values, [25, 75], axis=0)
    scale = (upper - lower) / 1.349
    fallback = np.std(values, axis=0)
    scale = np.where(scale > 1e-3, scale, np.where(fallback > 1e-3, fallback, 1.0))
    return PhysiologyScaler(
        np.asarray(center, dtype=np.float32),
        np.asarray(scale, dtype=np.float32),
        len(values),
    )
