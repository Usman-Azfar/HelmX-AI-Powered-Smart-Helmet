from pathlib import Path

import pandas as pd
import pytest

from helmx_drowsiness.datasets.uta_rldd import build_uta_event_index, discover_uta_videos


def test_uta_discovery_maps_provider_labels_and_folds(tmp_path: Path) -> None:
    for label in ("0", "5", "10"):
        directory = tmp_path / "Fold1_part1" / "01"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{label}.mov").touch()
    videos = discover_uta_videos(tmp_path)
    assert [item.label for item in videos] == [0, 2, 1]
    assert {item.fold for item in videos} == {1}
    assert {item.subject_id for item in videos} == {"01"}


def test_uta_discovery_preserves_split_drowsy_sessions(tmp_path: Path) -> None:
    directory = tmp_path / "Fold3_part2" / "32"
    directory.mkdir(parents=True)
    for name in ("0.mov", "5.mov", "10_1.mp4", "10_2.mp4"):
        (directory / name).touch()

    videos = discover_uta_videos(tmp_path)

    assert [item.session_id for item in videos] == ["0", "10_1", "10_2", "5"]
    assert [item.label for item in videos] == [0, 2, 2, 1]
    assert {item.fold for item in videos} == {3}


def test_uta_discovery_rejects_unrecognized_video_layout(tmp_path: Path) -> None:
    path = tmp_path / "unknown" / "video.mov"
    path.parent.mkdir()
    path.touch()
    with pytest.raises(ValueError, match="provider schema"):
        discover_uta_videos(tmp_path)


def test_uta_event_index_uses_subject_alert_video_for_calibration(tmp_path: Path) -> None:
    directory = tmp_path / "Fold1_part1" / "01"
    directory.mkdir(parents=True)
    for name in ("0.mov", "5.mov", "10.mov"):
        (directory / name).touch()

    output = build_uta_event_index(tmp_path, tmp_path / "events.csv", test_fold=1)
    frame = pd.read_csv(output)

    assert len(frame) == 3
    assert frame["subject_id"].eq("fold1_01").all()
    assert frame["calibration_path"].nunique() == 1
    assert Path(frame["calibration_path"].iloc[0]).name == "0.mov"
