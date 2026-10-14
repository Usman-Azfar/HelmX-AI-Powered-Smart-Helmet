"""Explicit download of versioned third-party runtime model assets."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)


def download_face_landmarker(destination: str | Path) -> tuple[Path, str]:
    """Download the official MediaPipe FaceLandmarker task and return its SHA-256."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    request = urllib.request.Request(FACE_LANDMARKER_URL, headers={"User-Agent": "HelmX/0.1"})
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
        partial.replace(path)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return path, digest.hexdigest()
