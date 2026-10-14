# Reproducibility guide

## Scope

This guide explains how to reconstruct the software environment and experimental workflow. It does
not grant access to third-party datasets or redistribute their contents. Obtain every dataset from
its provider and comply with its license, consent, and citation requirements.

## Environment

The reference development environment uses Python 3.11. Install from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[train,export,dev]"
```

`requirements-lock.txt` records the resolved reference environment. It is useful for audit and
same-platform reconstruction, but it is not a portable lock across operating systems, CPU/GPU
targets, or CUDA versions. `pyproject.toml` is the authoritative dependency specification.

Run the engineering gate before an experiment:

```powershell
pytest -q
ruff check src tests
ruff format --check src tests
mypy src
python -m pip check
helmx-drowsiness validate-config configs/default.yaml
```

## Local artifact layout

The following paths are intentionally ignored by Git:

```text
data/raw/                    provider-supplied archives and extracted datasets
data/processed/              manifests, video caches, and NPZ windows
artifacts/models/            MediaPipe assets and exported ONNX bundles
runs/<experiment>/           checkpoints, logs, predictions, and reports
```

Do not commit personal data, licensed dataset samples, credentials, or generated checkpoints.
Published result claims should instead identify the exact configuration and provide cryptographic
hashes for private artifacts where redistribution is prohibited.

## Deterministic workflow

1. Download the FaceLandmarker asset with `helmx-drowsiness download-assets`.
2. Acquire and verify the relevant dataset under the provider's terms.
3. Build or preprocess a manifest with the corresponding CLI command.
4. Run `validate-manifest` and `data-quality-report` before training.
5. Train only the declared development configuration and seed.
6. Preserve the best checkpoint, recovery checkpoint, history, predictions, and provenance hashes.
7. Select temperature, model variants, and controller thresholds using validation data only.
8. Export ONNX and require numerical/decision parity before deployment evaluation.
9. Replay original continuous videos for event-level metrics; do not infer events from overlapping
   preprocessed windows.
10. Evaluate a locked test or external set only after the protocol's advancement gate authorizes
    it.

## Principal commands

```text
helmx-drowsiness validate-config configs/default.yaml
helmx-drowsiness download-assets
helmx-drowsiness index-mrl <root> <index.csv>
helmx-drowsiness pretrain-eye <index.csv> <root>
helmx-drowsiness preprocess-uta <root> --test-fold <N> --validation-fold <N>
helmx-drowsiness validate-manifest <manifest.csv>
helmx-drowsiness data-quality-report <manifest.csv>
helmx-drowsiness train --config <config.yaml> --output <run-dir> --seed <seed>
helmx-drowsiness predict-split <checkpoint.pt> --config <config.yaml> --split validation
helmx-drowsiness export <checkpoint.pt> --config <config.yaml> --output <model.onnx>
helmx-drowsiness evaluate-events <videos.csv> --config <config.yaml> --model <model.onnx>
helmx-drowsiness tune-event-thresholds <event-cache> --config <config.yaml>
helmx-drowsiness quantize <model.onnx> --config <config.yaml>
```

Use each command's `--help` output for the complete and current interface.

## Evidence rules

- Split by subject or session, never randomly by frame or overlapping window.
- Fit preprocessing statistics on training data only.
- Use validation data for checkpoint, temperature, candidate, and alert-policy selection.
- Preserve negative experiments and the selection rule that rejected them.
- Report class-wise metrics, calibration, and event behavior rather than accuracy alone.
- Use clustered subject-level intervals when samples within a subject are correlated.
- Treat clip-start timing as time-to-first-alert within a labelled clip unless true onset
  annotations exist.
- Do not present MRL Eye eye-state accuracy as drowsiness performance.
- Do not present workstation latency as target-device latency.

The frozen experimental decisions are in `RESEARCH_PROTOCOL.md` and
`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. The consolidated numerical record is in
`FINAL_RESULTS_SUMMARY.md`.

## Verifying an exported model

An export is acceptable only if its inputs match the documented frame, physiology, and quality
contracts; its class probabilities agree with the selected PyTorch checkpoint within the tested
tolerance; and its predicted classes agree on representative real windows. Quantized exports must
also pass their configured probability-error, agreement, and evaluation-metric gates.

## Reporting deviations

If hardware, dependency versions, data availability, or a recovered checkpoint differs from the
reference run, record the deviation before running the experiment. A reproducibility report should
include the Git commit, configuration hash, manifest hash, seed, platform, relevant dependency
versions, checkpoint hash, and exact command.
