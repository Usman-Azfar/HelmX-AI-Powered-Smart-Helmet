# Contributing to HelmX

Thank you for your interest in improving HelmX.

## Ways to contribute

- report bugs and reproducibility issues
- suggest model or data preprocessing improvements
- improve documentation and examples
- help with tests, linting, and reproducibility checks
- contribute new experiments with clear validation rules

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[train,export,dev]"
```

## Quality bar

Before opening a pull request, please run:

```powershell
pytest
ruff check src tests
ruff format --check src tests
mypy src
python -m pip check
```

## Contribution guidelines

1. Keep changes focused and easy to review.
2. Prefer small, well-documented pull requests.
3. Include tests for bug fixes or behavior changes whenever possible.
4. Keep research claims explicit and avoid overstating model performance.
5. Document configuration changes and their validation status.
6. Never commit third-party datasets, model checkpoints, credentials, or identifiable recordings.
7. Keep model selection and threshold tuning isolated from locked test and external data.

## Pull request workflow

1. Create a dedicated branch for your change.
2. Make your edits with clear commit messages.
3. Run the required validation commands.
4. Open a pull request with a description of the problem, approach, and verification.

Use the pull-request template to record commands and results. A passing test suite is required, but
tests alone do not authorize a new research claim. Changes to an experiment's data, objective,
sampling, fusion, or selection rule must identify whether the run is exploratory or was frozen
before evaluation.

## Research and data responsibilities

This repository includes research artifacts, dataset-processing code, and model-evaluation tooling. When contributing:

- be explicit about dataset provenance and licensing
- avoid claiming final performance without subject-disjoint validation
- preserve reproducibility by documenting exact configs and run conditions
- treat model outputs as research evidence, not guaranteed deployment quality
- preserve negative results and do not select a model from an untouched test set

## Style

- Target Python 3.11 and use type annotations for public and internal interfaces.
- Keep lines within the configured 100-character limit.
- Prefer small pure functions around preprocessing and evaluation boundaries.
- Use elapsed timestamps for temporal behavior; do not convert persistence into frame counts.
- Add or update documentation when changing a tensor, manifest, ONNX, or CLI contract.

## Reporting results

Every reported experiment should include the Git commit, configuration, manifest provenance,
subject split, seed, selection set, primary metric, and important negative findings. Use
"time-to-first-alert within a drowsy-labelled clip" unless true physiological onset annotations
are available.

## Code of conduct

Please keep discussions respectful, constructive, and focused on technical quality.
