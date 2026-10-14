"""Resumable derivation of eye-focused tensors from cached full-face NPZ windows."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from helmx_drowsiness.datasets.manifest import read_manifest
from helmx_drowsiness.features.visual_input import derive_dual_eye_rgb, derive_eye_band_rgb
from helmx_drowsiness.training.provenance import sha256_file, write_json


def derive_eye_region_dataset(manifest_path: str | Path, output_root: str | Path) -> Path:
    """Create an atomic, resumable eye-band cache while preserving split identities."""

    source_manifest = Path(manifest_path)
    provenance = {
        "schema_version": 1,
        "source_manifest": str(source_manifest.resolve()),
        "source_manifest_sha256": sha256_file(source_manifest),
        "visual_region": "eye_band",
        "eye_band": {"x_fraction": [0.05, 0.95], "y_fraction": [0.18, 0.55]},
        "color": "grayscale_replicated_to_rgb",
    }
    return _derive_dataset(
        source_manifest,
        Path(output_root),
        provenance,
        derive_eye_band_rgb,
        cache_name="eye-region",
    )


def derive_dual_eye_dataset(manifest_path: str | Path, output_root: str | Path) -> Path:
    """Create packed, symmetric dual-eye tensors without changing sample identities."""

    source_manifest = Path(manifest_path)
    provenance = {
        "schema_version": 1,
        "source_manifest": str(source_manifest.resolve()),
        "source_manifest_sha256": sha256_file(source_manifest),
        "visual_region": "dual_eye",
        "left_eye": {"x_fraction": [0.05, 0.48], "y_fraction": [0.18, 0.55]},
        "right_eye": {"x_fraction": [0.52, 0.95], "y_fraction": [0.18, 0.55]},
        "color": "grayscale_replicated_to_rgb",
        "packing": "left_then_right_along_width",
        "model_pooling": "shared_backbone_arithmetic_mean",
    }
    return _derive_dataset(
        source_manifest,
        Path(output_root),
        provenance,
        derive_dual_eye_rgb,
        cache_name="dual-eye",
    )


def _derive_dataset(
    source_manifest: Path,
    output_root: Path,
    provenance: dict[str, Any],
    transform: Callable[[Any], Any],
    *,
    cache_name: str,
) -> Path:
    source_root = source_manifest.parent.resolve()
    frame = read_manifest(source_manifest)
    output = output_root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    provenance_path = output / "provenance.json"
    if provenance_path.is_file():
        existing = json.loads(provenance_path.read_text(encoding="utf-8"))
        if existing != provenance:
            raise ValueError(f"{cache_name} cache provenance does not match source/contract")
    else:
        unexpected = [path for path in output.iterdir() if path.name != provenance_path.name]
        if unexpected:
            raise ValueError("eye-region output is non-empty but has no provenance")
        write_json(provenance_path, provenance)

    for value in frame["path"].astype(str):
        relative = _safe_relative_path(value)
        source = source_root / relative
        destination = output / relative
        if destination.is_file():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with np.load(source, allow_pickle=False) as sample:
            payload = {key: np.asarray(sample[key]) for key in sample.files}
        payload["frames"] = transform(payload["frames"])
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with temporary.open("wb") as stream:
            np.savez_compressed(stream, **payload)  # type: ignore[arg-type]
        temporary.replace(destination)

    destination_manifest = output / source_manifest.name
    temporary_manifest = destination_manifest.with_suffix(".tmp")
    frame.to_csv(temporary_manifest, index=False)
    temporary_manifest.replace(destination_manifest)
    return destination_manifest


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"manifest sample path must remain relative: {value}")
    return path
