"""Validation-only probability calibration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from torch import Tensor


@dataclass(frozen=True, slots=True)
class TemperatureFit:
    temperature: float
    nll_before: float
    nll_after: float


def fit_temperature(logits: Tensor, labels: Tensor, *, max_iterations: int = 50) -> TemperatureFit:
    """Fit one positive temperature by minimizing validation negative log likelihood."""

    if logits.ndim != 2 or labels.ndim != 1 or logits.shape[0] != labels.shape[0]:
        raise ValueError("logits and labels have incompatible shapes")
    if len(labels) == 0:
        raise ValueError("calibration data cannot be empty")
    scores = logits.detach().to(dtype=torch.float64, device="cpu").numpy()
    targets = labels.detach().to(dtype=torch.long, device="cpu").numpy()

    def nll(log_temperature: float) -> float:
        scaled = scores / np.exp(log_temperature)
        shifted = scaled - scaled.max(axis=1, keepdims=True)
        log_normalizer = np.log(np.exp(shifted).sum(axis=1))
        return float(np.mean(log_normalizer - shifted[np.arange(len(targets)), targets]))

    before = nll(0.0)
    result = minimize_scalar(
        nll,
        bounds=(float(np.log(0.05)), float(np.log(20.0))),
        method="bounded",
        options={"maxiter": max_iterations},
    )
    temperature = float(np.exp(result.x))
    after = nll(float(result.x))
    if not np.isfinite(after) or after > before:
        return TemperatureFit(1.0, before, before)
    return TemperatureFit(temperature, before, after)
