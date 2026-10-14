from pathlib import Path

import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.sequences import SequenceDataset, VideoBagDataset


def test_sequence_dataset_masks_unavailable_targets(tmp_path: Path) -> None:
    np.savez_compressed(
        tmp_path / "sample.npz",
        frames=np.zeros((4, 32, 32, 3), dtype=np.uint8),
        physiology=np.zeros((4, 12), dtype=np.float32),
        quality=np.ones((4, 2), dtype=np.float32),
    )
    manifest = pd.DataFrame([{"path": "sample.npz", "label": 2}])
    sample = SequenceDataset(manifest, tmp_path)[0]
    assert sample["frames"].shape == (4, 3, 32, 32)
    assert sample["physiology"].shape == (4, 12)
    assert sample["quality"].shape == (4, 2)
    assert sample["label"].item() == 2
    assert sample["sample_weight"].item() == 1.0
    assert not sample["eye_closure_mask"].item()
    assert not sample["head_pose_mask"].item()
    assert not sample["quality_target_mask"].item()


def test_sequence_dataset_reads_label_confidence_as_sample_weight(tmp_path: Path) -> None:
    np.savez_compressed(
        tmp_path / "sample.npz",
        frames=np.zeros((4, 32, 32, 3), dtype=np.uint8),
        physiology=np.zeros((4, 12), dtype=np.float32),
        quality=np.ones((4, 2), dtype=np.float32),
    )
    manifest = pd.DataFrame([{"path": "sample.npz", "label": 2, "label_confidence": 0.75}])
    sample = SequenceDataset(manifest, tmp_path)[0]
    assert sample["sample_weight"].item() == 0.75


def test_video_bag_dataset_samples_temporal_thirds_deterministically(tmp_path: Path) -> None:
    rows = []
    for index in range(9):
        name = f"window_{index}.npz"
        np.savez_compressed(
            tmp_path / name,
            frames=np.zeros((4, 64, 64, 3), dtype=np.uint8),
            physiology=np.full((4, 12), index, dtype=np.float32),
            quality=np.ones((4, 2), dtype=np.float32),
        )
        rows.append(
            {
                "subject_id": "subject",
                "session_id": "video",
                "path": name,
                "label": 2,
                "start_seconds": index * 10.0,
                "end_seconds": (index + 1) * 10.0,
            }
        )
    frame = pd.DataFrame(rows)
    dataset = VideoBagDataset(frame, tmp_path, augment=False, seed=13)
    dataset.set_epoch(1)
    first = dataset[0]
    assert first["frames"].shape == (3, 4, 3, 64, 64)
    assert first["label"].item() == 2
    first_selection = tuple(first["physiology"][:, 0, 0].tolist())
    assert first_selection == tuple(dataset[0]["physiology"][:, 0, 0].tolist())
    observed = {first_selection}
    for epoch in range(2, 12):
        dataset.set_epoch(epoch)
        observed.add(tuple(dataset[0]["physiology"][:, 0, 0].tolist()))
    assert len(observed) > 1

    all_windows = VideoBagDataset(frame, tmp_path, augment=False, seed=13, all_windows=True)[0]
    assert all_windows["frames"].shape[0] == 9
