"""Backward-compatible launcher for the maintained HelmX runtime.

The original monolithic H5/threshold prototype was retired. Its history remains available in Git;
the legacy H5 artifact is retained only for controlled baseline evaluation.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from helmx_drowsiness.cli import run  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run(["run", *sys.argv[1:]]))
