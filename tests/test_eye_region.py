from pathlib import Path

import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.eye_region import derive_dual_eye_dataset, derive_eye_region_dataset
from helmx_drowsiness.features.visual_input import derive_dual_eye_rgb, derive_eye_band_rgb


def test_eye_band_is_grayscale_three_channel_and_preserves_sequence_shape() -> None:
    frames = np.zeros((2, 30, 30, 3), dtype=np.uint8)
    frames[:, 4:11, :, 0] = 255

    result = derive_eye_band_rgb(frames)

    assert result.shape == frames.shape
    assert result.dtype == np.uint8
    np.testing.assert_array_equal(result[..., 0], result[..., 1])
    np.testing.assert_array_equal(result[..., 1], result[..., 2])
    assert result.mean() > 0


def test_dual_eye_packs_two_grayscale_square_crops_along_width() -> None:
    frames = np.zeros((2, 40, 40, 3), dtype=np.uint8)
    frames[:, 7:23, 2:19, 0] = 255
    frames[:, 7:23, 21:38, 2] = 180

    result = derive_dual_eye_rgb(frames)

    assert result.shape == (2, 40, 80, 3)
    assert result.dtype == np.uint8
    np.testing.assert_array_equal(result[..., 0], result[..., 1])
    np.testing.assert_array_equal(result[..., 1], result[..., 2])
    assert result[:, :, :40].mean() > 0
    assert result[:, :, 40:].mean() > 0


def test_eye_region_dataset_preserves_manifest_and_nonvisual_arrays(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    frames = np.full((4, 16, 16, 3), [10, 40, 90], dtype=np.uint8)
    physiology = np.arange(48, dtype=np.float32).reshape(4, 12)
    quality = np.ones((4, 2), dtype=np.float32)
    np.savez_compressed(
        source / "sample.npz", frames=frames, physiology=physiology, quality=quality
    )
    manifest = source / "manifest.csv"
    pd.DataFrame(
        [
            {
                "dataset": "uta_rldd",
                "subject_id": "s1",
                "session_id": "v1",
                "path": "sample.npz",
                "label": 0,
                "split": "train",
            }
        ]
    ).to_csv(manifest, index=False)

    derived_manifest = derive_eye_region_dataset(manifest, tmp_path / "derived")

    derived = pd.read_csv(derived_manifest)
    assert derived.to_dict(orient="records") == pd.read_csv(manifest).to_dict(orient="records")
    with np.load(derived_manifest.parent / "sample.npz", allow_pickle=False) as sample:
        np.testing.assert_array_equal(sample["physiology"], physiology)
        np.testing.assert_array_equal(sample["quality"], quality)
        assert sample["frames"].shape == frames.shape
        np.testing.assert_array_equal(sample["frames"][..., 0], sample["frames"][..., 1])


def test_dual_eye_dataset_preserves_nonvisual_arrays_and_doubles_width(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    frames = np.full((4, 16, 16, 3), [10, 40, 90], dtype=np.uint8)
    physiology = np.arange(48, dtype=np.float32).reshape(4, 12)
    quality = np.ones((4, 2), dtype=np.float32)
    np.savez_compressed(
        source / "sample.npz", frames=frames, physiology=physiology, quality=quality
    )
    manifest = source / "manifest.csv"
    pd.DataFrame(
        [
            {
                "dataset": "uta_rldd",
                "subject_id": "s1",
                "session_id": "v1",
                "path": "sample.npz",
                "label": 0,
                "split": "train",
            }
        ]
    ).to_csv(manifest, index=False)

    derived_manifest = derive_dual_eye_dataset(manifest, tmp_path / "derived")

    with np.load(derived_manifest.parent / "sample.npz", allow_pickle=False) as sample:
        np.testing.assert_array_equal(sample["physiology"], physiology)
        np.testing.assert_array_equal(sample["quality"], quality)
        assert sample["frames"].shape == (4, 16, 32, 3)
        np.testing.assert_array_equal(sample["frames"][..., 0], sample["frames"][..., 1])
