# Core pipeline

This package contains the reusable crash-detection pipeline:

- `io_loaders.py`: source-specific loading and session construction;
- `resampling.py`: timestamp correction, interpolation, and stream alignment;
- `preprocess.py`, `units.py`, `features.py`: canonical units and features;
- `manifest.py`: deterministic session-level splits and window creation;
- `model.py`, `normalize.py`: model and fitted normalization;
- `evaluate.py`, `export.py`: evaluation policies and TensorFlow Lite export.

All training/evaluation entry points live in `scripts/`. The deployment runtime
is isolated under `deploy/` and consumes exported artifacts rather than
reimplementing the offline pipeline.
