"""Safe extraction helpers for downloaded research archives."""

from __future__ import annotations

import zipfile
from pathlib import Path


def safe_extract_zip(archive: str | Path, destination: str | Path) -> list[Path]:
    """Extract a ZIP while rejecting traversal, absolute paths, and symlinks."""

    source = Path(archive).resolve(strict=True)
    output = Path(destination).resolve()
    output.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(source) as bundle:
        for member in bundle.infolist():
            target = (output / member.filename).resolve()
            if output != target and output not in target.parents:
                raise ValueError(f"archive member escapes destination: {member.filename}")
            unix_mode = member.external_attr >> 16
            if unix_mode & 0o170000 == 0o120000:
                raise ValueError(f"archive contains a symbolic link: {member.filename}")
        for member in bundle.infolist():
            bundle.extract(member, output)
            if not member.is_dir():
                extracted.append((output / member.filename).resolve())
    return extracted
