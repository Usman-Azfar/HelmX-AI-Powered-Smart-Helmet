from pathlib import Path
from zipfile import ZipFile

import pytest

from helmx_drowsiness.datasets.archive import safe_extract_zip


def test_safe_zip_extracts_regular_files(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("fold/subject/video.txt", "ok")
    extracted = safe_extract_zip(archive, tmp_path / "output")
    assert len(extracted) == 1
    assert extracted[0].read_text() == "ok"


def test_safe_zip_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "bad")
    with pytest.raises(ValueError, match="escapes"):
        safe_extract_zip(archive, tmp_path / "output")
