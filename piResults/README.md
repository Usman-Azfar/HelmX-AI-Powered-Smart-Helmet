# Raspberry Pi Research Results

This directory is the publication-ready Raspberry Pi evidence package for HelmX crash detection.
It contains the experiment implementations, machine-readable results, selected figures, protocols,
and provenance records needed to review the work without publishing the 4.37 GiB working archive.

## Start here

1. Read the [complete results report](results/COMPLETE_RESULTS.md) for every test, result, failed
   attempt, limitation, and superseded claim.
2. Use the [results index](results/README.md) to locate machine-readable evidence.
3. Use the [experiment index](experiments/README.md) to locate the scripts that produced or
   analyzed the evidence.
4. See [selection and exclusions](provenance/SELECTION_AND_EXCLUSIONS.md) and the generated
   manifests for audit details.

## Directory layout

| Path | Purpose |
|---|---|
| `results/` | Consolidated report plus foundational, validation, and final-closure evidence |
| `experiments/` | Acquisition, benchmark, replay, analysis, and closure scripts |
| `figures/` | Review-ready plots and their related presentation data |
| `documentation/` | Test protocols, checklists, historical reports, and status records |
| `provenance/` | Coverage notes, selection policy, file hashes, and source-to-public copy audit |

Large CSV captures are stored as standard `.csv.gz` files. They can be opened directly by common
data tools or decompressed with `gzip -d <file>.csv.gz`. No individual file approaches GitHub's
100 MB hard limit.

## Evidence boundaries

This package reports experiments on the evaluated Raspberry Pi and IMU configuration. It does not
claim safety certification, real-world crash validation, guaranteed hard real-time behavior, or
end-to-end GPS/GSM dispatch validation. Read each result together with the limitations in the
[complete report](results/COMPLETE_RESULTS.md).

The unmodified local source archive remains in `piResults2/` and is excluded by `.gitignore`.

