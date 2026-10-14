from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.image_pilot import convert_frame_pilot


def test_frame_pilot_is_explicitly_marked_unverified(tmp_path: Path) -> None:
    source = tmp_path / "source" / "train" / "alert"
    source.mkdir(parents=True)
    assert cv2.imwrite(str(source / "unknown.jpg"), np.full((20, 20, 3), 127, np.uint8))
    manifest = convert_frame_pilot(tmp_path / "source", tmp_path / "output")
    frame = pd.read_csv(manifest)
    assert len(frame) == 1
    assert not bool(frame.iloc[0]["subject_identity_verified"])
    assert str(frame.iloc[0]["subject_id"]).startswith("train_unverified_")
    with np.load(manifest.parent / frame.iloc[0]["path"]) as sample:
        assert sample["frames"].shape == (4, 128, 128, 3)
