"""Non-publication adapter for frame-only UTA-RLDD mirrors."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from helmx_drowsiness.features.quality import visual_quality

# The inspected minhngt02/uta-rldd mirror is binary, despite the official
# UTA-RLDD dataset having three stages. Keep the adapter faithful to the files
# instead of inventing a low-vigilance class. The synonyms make small fixtures
# and compatible binary mirrors usable without changing the semantic contract.
LABELS = {"active": 0, "alert": 0, "fatigue": 1, "drowsy": 1}
SPLITS = {"train": "train", "val": "validation", "validation": "validation", "test": "test"}


def convert_frame_pilot(
    root: str | Path,
    output_root: str | Path,
    *,
    image_size: int = 128,
    sequence_length: int = 4,
) -> Path:
    """Convert a frame mirror to repeated-frame samples, explicitly marked unverified."""

    source = Path(root).resolve()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for path in sorted(source.rglob("*.jpg")):
        label_name = path.parent.name.lower()
        split_name = next(
            (SPLITS[part.lower()] for part in path.parts if part.lower() in SPLITS), None
        )
        if label_name not in LABELS or split_name is None:
            continue
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"cannot decode pilot image: {path}")
        resized = np.asarray(cv2.resize(image, (image_size, image_size)), dtype=np.uint8)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        visual, _ = visual_quality(resized, detection_confidence=1.0, face_fraction=0.5)
        digest = hashlib.sha256(str(path.relative_to(source)).encode()).hexdigest()[:16]
        destination = output / f"pilot_{digest}.npz"
        np.savez_compressed(
            destination,
            frames=np.repeat(rgb[None], sequence_length, axis=0).astype(np.uint8),
            physiology=np.zeros((sequence_length, 12), dtype=np.float32),
            quality=np.repeat(
                np.asarray([[visual, 0.0]], dtype=np.float32), sequence_length, axis=0
            ),
        )
        rows.append(
            {
                "dataset": "uta_rldd_frame_mirror_pilot",
                # Filenames such as image_0162 are frame IDs, not subjects. A
                # split-scoped synthetic ID prevents accidental cross-split
                # matches while making the missing identity explicit.
                "subject_id": f"{split_name}_unverified_{digest}",
                "session_id": digest,
                "path": destination.name,
                "label": LABELS[label_name],
                "split": split_name,
                "subject_identity_verified": False,
            }
        )
    if not rows:
        raise ValueError(f"no split/class JPG images found under {source}")
    manifest = output / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    return manifest
