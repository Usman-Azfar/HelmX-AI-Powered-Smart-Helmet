"""Temporally consistent, physiology-aware training augmentation."""

from __future__ import annotations

import torch
from torch import Tensor

from helmx_drowsiness.datasets.sequences import IMAGENET_MEAN, IMAGENET_STD


class TemporalAugment:
    """Apply one transform consistently to every frame in a causal sequence."""

    def __init__(
        self,
        *,
        flip_probability: float = 0.5,
        photometric_probability: float = 0.8,
        occlusion_probability: float = 0.2,
    ) -> None:
        self.flip_probability = flip_probability
        self.photometric_probability = photometric_probability
        self.occlusion_probability = occlusion_probability

    def __call__(self, sample: dict[str, Tensor]) -> dict[str, Tensor]:
        if torch.rand(()) < self.flip_probability:
            self.horizontal_flip(sample)
        if torch.rand(()) < self.photometric_probability:
            self._photometric(sample)
        if torch.rand(()) < self.occlusion_probability:
            self._occlude(sample)
        return sample

    @staticmethod
    def horizontal_flip(sample: dict[str, Tensor]) -> None:
        """Flip appearance and sign-correct yaw/roll features and targets."""

        sample["frames"] = torch.flip(sample["frames"], dims=(-1,))
        physiology = sample["physiology"].clone()
        physiology[:, 9] *= -1  # relative yaw
        physiology[:, 10] *= -1  # relative roll
        sample["physiology"] = physiology
        if bool(sample["head_pose_mask"]):
            pose = sample["head_pose"].clone()
            pose[1:] *= -1
            sample["head_pose"] = pose

    @staticmethod
    def _photometric(sample: dict[str, Tensor]) -> None:
        pixels = sample["frames"] * IMAGENET_STD + IMAGENET_MEAN
        contrast = torch.empty(()).uniform_(0.8, 1.2)
        brightness = torch.empty(()).uniform_(-0.12, 0.12)
        pixels = ((pixels - 0.5) * contrast + 0.5 + brightness).clamp(0, 1)
        sample["frames"] = (pixels - IMAGENET_MEAN) / IMAGENET_STD

    @staticmethod
    def _occlude(sample: dict[str, Tensor]) -> None:
        frames = sample["frames"].clone()
        height, width = frames.shape[-2:]
        patch_height = max(1, round(height * 0.2))
        patch_width = max(1, round(width * 0.3))
        top = int(torch.randint(0, height - patch_height + 1, ()).item())
        left = int(torch.randint(0, width - patch_width + 1, ()).item())
        normalized_black = -IMAGENET_MEAN / IMAGENET_STD
        frames[:, :, top : top + patch_height, left : left + patch_width] = normalized_black
        sample["frames"] = frames
        quality = sample["quality"].clone()
        quality[:, 0] *= 0.4
        sample["quality"] = quality
