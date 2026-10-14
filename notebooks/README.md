# Notebooks

These notebooks provide an interactive walkthrough of the maintained command-line
workflow:

- `crash-detection-model.ipynb` mirrors model training and threshold calibration;
- `model-check.ipynb` mirrors held-out evaluation and decision-policy analysis.

Run them from the repository root so imports and relative artifact paths resolve
correctly. Install the root requirements, select a Python 3.11 kernel, and place
the local datasets according to `../data/README.md` first.

The command-line scripts under `../scripts/` are the reproducible source of truth.
Notebook outputs and execution counts are intentionally cleared before release to
avoid embedding stale metrics, machine-specific paths, or large generated data.
