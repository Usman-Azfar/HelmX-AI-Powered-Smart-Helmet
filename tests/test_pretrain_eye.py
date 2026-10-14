from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from helmx_drowsiness.training.pretrain_eye import MrlEyeDataset


def test_mrl_eye_dataset_loads_normalized_three_channel_image(tmp_path: Path) -> None:
    image = np.full((20, 30), 128, dtype=np.uint8)
    assert cv2.imwrite(str(tmp_path / "eye.png"), image)
    frame = pd.DataFrame([{"path": "eye.png", "eye_state": 1}])
    sample, label, index = MrlEyeDataset(frame, tmp_path, size=32, augment=False)[0]
    assert sample.shape == (3, 32, 32)
    assert label.item() == 1.0
    assert index == 0
