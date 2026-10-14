"""changesToMake.txt item 4: archive everything needed to reproduce the
published numbers -- dataset file hashes, exact split session IDs, random
seed, code commit, thresholds, and package versions -- into
results/reproducibility/reproducibility_manifest.json. Run this LAST, after training/
evaluation/export, so models/thresholds.json reflects the final run."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import sklearn
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest


def sha256_file(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(config.ROOT),
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None


def main():
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    # The live pipeline and all loaders use the canonical source directories
    # under data/. Raw files may be locally present while remaining excluded
    # from a public source release for licensing reasons (DATA_LICENSES.md).
    data_dir = config.DATA_DIR
    if not data_dir.is_dir():
        raise FileNotFoundError(
            f"Dataset directory not found: {data_dir}. "
            "See data/README.md for the expected local layout."
        )
    training_sources = ("carla", "darus", "fall", "near-fall", "road")
    missing_sources = [name for name in training_sources if not (data_dir / name).is_dir()]
    if missing_sources:
        raise FileNotFoundError(
            "Missing canonical training dataset directories: " + ", ".join(missing_sources)
        )

    # Hash only the five inputs consumed by load_all_sessions(). Evaluation-only
    # external datasets are intentionally separate and must not silently enter
    # the training snapshot.
    dataset_files = []
    for source_name in training_sources:
        dataset_files.extend(p for p in (data_dir / source_name).rglob("*") if p.is_file())

    file_hashes = {}
    for p in sorted(dataset_files):
        if p.is_file():
            rel = str(p.relative_to(config.ROOT)).replace("\\", "/")
            file_hashes[rel] = sha256_file(p)

    thresholds = {}
    thresholds_path = config.MODELS_DIR / "thresholds.json"
    if thresholds_path.exists():
        with open(thresholds_path) as f:
            thresholds = json.load(f)

    split_session_ids = {
        name: sorted(sid for sid, sp in split_of.items() if sp == name)
        for name in ("train", "val", "test")
    }

    out = {
        "git_commit": get_git_commit(),
        "git_note": (
            "Raw datasets may be excluded from the public repository. Treat the recorded "
            "file hashes and split IDs as the authoritative dataset snapshot; the git "
            "commit identifies the corresponding software revision."
        ),
        "random_seed_data_split": config.RANDOM_SEED,
        "model_seeds_multi_seed_experiment": config.SEEDS,
        "train_frac": config.TRAIN_FRAC,
        "val_frac": config.VAL_FRAC,
        "window_samples": config.WINDOW_SAMPLES,
        "stride_samples": config.STRIDE_SAMPLES,
        "target_rate_hz": config.TARGET_RATE_HZ,
        "anomaly_top_fraction": config.ANOMALY_TOP_FRACTION,
        "n_sessions_total": len(sessions),
        "split_session_ids": split_session_ids,
        "n_sessions_per_split": {k: len(v) for k, v in split_session_ids.items()},
        "dataset_file_sha256": file_hashes,
        "n_dataset_files_hashed": len(file_hashes),
        "thresholds": thresholds,
        "package_versions": {
            "tensorflow": tf.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    config.REPRODUCIBILITY_DIR.mkdir(exist_ok=True, parents=True)
    out_path = config.REPRODUCIBILITY_DIR / "reproducibility_manifest.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path} ({len(file_hashes)} dataset files hashed, "
          f"{out['n_sessions_total']} sessions, git_commit={out['git_commit']})")


if __name__ == "__main__":
    main()
