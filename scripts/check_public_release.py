"""Fail when a proposed Git release contains private or oversized artifacts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAX_FILE_BYTES = 95 * 1024 * 1024
FORBIDDEN_PREFIXES = (
    "Final Results/",
    "crash-legacy/",
    "data_local_archive/",
    "piResults2/",
    "results2/",
)
FORBIDDEN_EXACT = {
    "crash-legacy.zip",
    "changesToMake.txt",
    "changesToMake2.txt",
    "ExperimentsToPerform.txt",
    "HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md",
    "plan.txt",
    "SESSION_CONTEXT.md",
    "changes.md",
}
PRIVATE_MODEL_SUFFIXES = {".keras", ".tflite", ".npz"}
WINDOWS_ABSOLUTE_PATH = re.compile(r"[A-Za-z]:\\(?:Users|Courses)\\", re.IGNORECASE)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def violations(paths: list[str]) -> list[str]:
    problems = []
    for relative in paths:
        normalized = relative.replace("\\", "/")
        path = ROOT / relative
        if normalized in FORBIDDEN_EXACT or normalized.startswith(FORBIDDEN_PREFIXES):
            problems.append(f"private or superseded path is tracked: {normalized}")
        if normalized.startswith("data/") and normalized != "data/README.md":
            problems.append(f"raw dataset path is tracked: {normalized}")
        if normalized.startswith("models/") and path.suffix.lower() in PRIVATE_MODEL_SUFFIXES:
            problems.append(f"unlicensed derived model artifact is tracked: {normalized}")
        if path.is_file() and path.stat().st_size > MAX_FILE_BYTES:
            size_mib = path.stat().st_size / (1024 * 1024)
            problems.append(f"file exceeds {MAX_FILE_BYTES // (1024 * 1024)} MiB: {normalized} ({size_mib:.1f} MiB)")
        if path.is_file() and path.suffix.lower() == ".ipynb":
            try:
                notebook = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(f"invalid notebook JSON: {normalized} ({exc})")
                continue
            code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
            if any(cell.get("outputs") for cell in code_cells):
                problems.append(f"notebook contains saved outputs: {normalized}")
            if any(cell.get("execution_count") is not None for cell in code_cells):
                problems.append(f"notebook contains execution counts: {normalized}")
            serialized = json.dumps(notebook, ensure_ascii=False)
            if WINDOWS_ABSOLUTE_PATH.search(serialized):
                problems.append(f"notebook contains a machine-specific absolute path: {normalized}")
    return problems


def main() -> int:
    try:
        paths = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Unable to inspect Git index: {exc}", file=sys.stderr)
        return 2

    problems = violations(paths)
    if problems:
        print("Public-release check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print(f"Public-release check passed ({len(paths)} tracked files inspected).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
