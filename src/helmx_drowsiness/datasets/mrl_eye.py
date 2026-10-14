"""Subject-aware index builder for the public MRL Eye auxiliary dataset."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

MRL_PATTERN = re.compile(
    r"^s(?P<subject>\d+)_(?P<image>\d+)_"
    r"(?P<gender>[01])_(?P<glasses>[01])_(?P<eye_state>[01])_"
    r"(?P<reflections>[012])_(?P<lighting>[01])_(?P<sensor>\d+)\.(?:png|jpg)$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MrlEyeRecord:
    path: str
    subject_id: str
    image_id: str
    gender: int
    glasses: int
    eye_state: int
    reflections: int
    lighting: int
    sensor_id: str
    fold: int


def parse_mrl_filename(path: str | Path, *, folds: int = 5) -> MrlEyeRecord:
    """Parse the provider's eight filename annotations and assign a subject fold."""

    if folds < 2:
        raise ValueError("folds must be at least 2")
    item = Path(path)
    match = MRL_PATTERN.match(item.name)
    if match is None:
        raise ValueError(f"not an MRL Eye filename: {item.name}")
    values = match.groupdict()
    subject = values["subject"]
    fold = int.from_bytes(hashlib.sha256(subject.encode()).digest()[:4], "big") % folds
    return MrlEyeRecord(
        path=str(item),
        subject_id=subject,
        image_id=values["image"],
        gender=int(values["gender"]),
        glasses=int(values["glasses"]),
        eye_state=int(values["eye_state"]),
        reflections=int(values["reflections"]),
        lighting=int(values["lighting"]),
        sensor_id=values["sensor"],
        fold=fold,
    )


def build_mrl_index(root: str | Path, output: str | Path, *, folds: int = 5) -> pd.DataFrame:
    """Index all MRL images while guaranteeing one fold per subject."""

    dataset_root = Path(root).resolve()
    records: list[MrlEyeRecord] = []
    invalid: list[str] = []
    for path in sorted(dataset_root.rglob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        try:
            record = parse_mrl_filename(path.relative_to(dataset_root), folds=folds)
        except ValueError:
            invalid.append(str(path))
        else:
            records.append(record)
    if invalid:
        raise ValueError(f"{len(invalid)} image filenames do not match the MRL schema")
    if not records:
        raise ValueError(f"no MRL Eye images found under {dataset_root}")
    frame = pd.DataFrame(asdict(record) for record in records)
    if (frame.groupby("subject_id")["fold"].nunique() != 1).any():
        raise AssertionError("subject fold assignment is inconsistent")
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame
