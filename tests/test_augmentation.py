import torch

from helmx_drowsiness.datasets.augmentation import TemporalAugment


def test_horizontal_flip_corrects_pose_feature_signs() -> None:
    sample = {
        "frames": torch.arange(12.0).reshape(1, 3, 2, 2),
        "physiology": torch.ones(1, 12),
        "quality": torch.ones(1, 2),
        "head_pose": torch.tensor([2.0, 3.0, 4.0]),
        "head_pose_mask": torch.tensor(True),
    }
    original = sample["frames"].clone()
    TemporalAugment.horizontal_flip(sample)
    assert torch.equal(sample["frames"], torch.flip(original, dims=(-1,)))
    assert sample["physiology"][0, 9].item() == -1.0
    assert sample["physiology"][0, 10].item() == -1.0
    torch.testing.assert_close(sample["head_pose"], torch.tensor([2.0, -3.0, -4.0]))
