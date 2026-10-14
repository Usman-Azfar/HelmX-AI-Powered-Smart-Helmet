"""Official-fold UTA-RLDD discovery and resumable preprocessing."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from helmx_drowsiness.config import DataConfig
from helmx_drowsiness.datasets.preprocess import (
    collect_neutral_calibration,
    preprocess_video,
)

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
LABEL_MAP = {"0": 0, "5": 1, "10": 2}
FOLD_PATTERN = re.compile(r"fold\s*(?P<fold>[1-5])", re.IGNORECASE)
LABEL_PATTERN = re.compile(r"^(?P<label>10|5|0)(?:[_-].+)?$")


@dataclass(frozen=True, slots=True)
class UtaVideo:
    path: Path
    fold: int
    subject_id: str
    label: int
    session_id: str


def discover_uta_videos(root: str | Path) -> list[UtaVideo]:
    """Discover the provider layout ``FoldX_partY/subject/{0,5,10}[_part].video``.

    Most subjects have the three files ``0``, ``5``, and ``10``. The official corpus splits
    the drowsy recording for a small number of subjects into files such as ``10_1`` and
    ``10_2``; those remain separate sessions with the same drowsy label.
    """

    dataset_root = Path(root).resolve()
    videos: list[UtaVideo] = []
    invalid: list[str] = []
    for path in sorted(dataset_root.rglob("*")):
        if path.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        label_match = LABEL_PATTERN.fullmatch(path.stem)
        if label_match is None or len(path.parents) < 2:
            invalid.append(str(path))
            continue
        fold = _fold_from_path(path, dataset_root)
        if fold is None:
            invalid.append(str(path))
            continue
        subject = path.parent.name
        session = _safe_identifier(path.stem)
        label = LABEL_MAP[label_match.group("label")]
        videos.append(UtaVideo(path, fold, subject, label, session))
    if invalid:
        raise ValueError(f"{len(invalid)} UTA video paths do not match the provider schema")
    if not videos:
        raise ValueError(f"no UTA-RLDD videos found under {dataset_root}")
    keys = [(item.fold, item.subject_id, item.label, item.session_id) for item in videos]
    if len(keys) != len(set(keys)):
        raise ValueError("UTA-RLDD discovery produced duplicate video identities")
    return videos


def preprocess_uta_rldd(
    root: str | Path,
    output_root: str | Path,
    face_landmarker: str | Path,
    data_config: DataConfig,
    *,
    test_fold: int,
    validation_fold: int,
) -> Path:
    """Preprocess all videos and write a nested, subject-disjoint fold manifest."""

    if (
        test_fold == validation_fold
        or test_fold not in range(1, 6)
        or validation_fold not in range(1, 6)
    ):
        raise ValueError("test and validation folds must be distinct values in 1..5")
    videos = discover_uta_videos(root)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, object]] = []
    by_subject: dict[tuple[int, str], list[UtaVideo]] = {}
    for video in videos:
        by_subject.setdefault((video.fold, video.subject_id), []).append(video)

    for (fold, subject), subject_videos in sorted(by_subject.items()):
        alert_videos = [item for item in subject_videos if item.label == 0]
        if len(alert_videos) != 1:
            raise ValueError(
                f"expected one alert calibration video for fold {fold}, subject {subject}"
            )
        baseline = collect_neutral_calibration(
            alert_videos[0].path,
            face_landmarker,
            sample_fps=data_config.sample_fps,
            seconds=20.0,
        )
        split = (
            "test" if fold == test_fold else "validation" if fold == validation_fold else "train"
        )
        for video in subject_videos:
            cache = output / f"records_fold{fold}_{subject}_{video.label}_{video.session_id}.json"
            if cache.is_file():
                records = json.loads(cache.read_text(encoding="utf-8"))
                for record in records:
                    record["split"] = split
                    record["fold"] = fold
            else:
                session_id = f"class{video.label}_{video.session_id}"
                processed = preprocess_video(
                    video.path,
                    output,
                    face_landmarker,
                    baseline,
                    data_config,
                    dataset="uta_rldd",
                    subject_id=f"fold{fold}_{subject}",
                    session_id=session_id,
                    label=video.label,
                    split=split,
                )
                records = [{**asdict(record), "fold": fold} for record in processed]
                temporary = cache.with_suffix(".tmp")
                temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
                temporary.replace(cache)
            all_records.extend(records)

    manifest = output / f"manifest_test{test_fold}_validation{validation_fold}.csv"
    pd.DataFrame(all_records).to_csv(manifest, index=False)
    return manifest


def build_uta_event_index(root: str | Path, output_path: str | Path, *, test_fold: int) -> Path:
    """Index raw test videos with each subject's alert recording as neutral calibration."""

    if test_fold not in range(1, 6):
        raise ValueError("test_fold must be in 1..5")
    videos = [item for item in discover_uta_videos(root) if item.fold == test_fold]
    by_subject: dict[str, list[UtaVideo]] = {}
    for video in videos:
        by_subject.setdefault(video.subject_id, []).append(video)
    rows: list[dict[str, object]] = []
    for subject, subject_videos in sorted(by_subject.items()):
        alert_videos = [item for item in subject_videos if item.label == 0]
        if len(alert_videos) != 1:
            raise ValueError(f"expected one alert calibration video for fold {test_fold}/{subject}")
        calibration_path = str(alert_videos[0].path.resolve())
        for video in sorted(subject_videos, key=lambda item: (item.label, item.session_id)):
            rows.append(
                {
                    "dataset": "uta_rldd",
                    "subject_id": f"fold{test_fold}_{subject}",
                    "session_id": f"class{video.label}_{video.session_id}",
                    "path": str(video.path.resolve()),
                    "calibration_path": calibration_path,
                    "label": video.label,
                    "fold": test_fold,
                }
            )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    pd.DataFrame(rows).to_csv(temporary, index=False)
    temporary.replace(destination)
    return destination


def _fold_from_path(path: Path, root: Path) -> int | None:
    for part in path.relative_to(root).parts:
        match = FOLD_PATTERN.search(part)
        if match:
            return int(match.group("fold"))
    return None


def _safe_identifier(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    if not result:
        raise ValueError("video filename cannot be converted to a safe session identifier")
    return result
