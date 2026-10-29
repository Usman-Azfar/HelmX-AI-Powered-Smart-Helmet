# Public Result Packaging Notes

The original `results/` directory was preserved locally as `results2/` before this public package
was created. No source measurement was overwritten.

## Included

- All headline model metrics and figures.
- All architecture and training ablation JSON files.
- All external-validation JSON files.
- Reproducibility metadata.
- Canonical Raspberry Pi results, historical controls, raw telemetry, and deployment diagnostics
  are published in the dedicated [`piResults/`](../piResults/) package.

## Retained only in the ignored local archive

| Artifact | Reason not published in the curated folder |
|---|---|
| `exp1_run.log`, `exp2_run.log`, `exp3_run.log` | Console logs duplicate JSON outputs and contain local development paths and framework startup noise. |
| `unseen_experiment_model.keras` | Generated experimental weight file is misplaced under results, and public redistribution of dataset-derived weights requires a separate licensing decision. |
| `pi_environment_final.txt` | Contains the device serial number, hostname, full package inventory, and storage details. |
| `process_snapshot.txt` | Contains usernames, local shell paths, editor/tool commands, process identifiers, and unrelated services. |
| `dmesg.txt` | Raw kernel dump is noisy host-level evidence; relevant conclusions are preserved in the reviewed reports. |

Absolute model paths in the public benchmark JSON files were replaced with repository-relative paths.
Numerical measurements were not changed.

## Integrity note

The former `results/pi_research/w2_live3_soak.json` duplicate was verified byte-for-byte by SHA-256.
Its authoritative public copy was relocated; a Windows reader still holds the legacy local file
open, so that non-public duplicate remains ignored until the handle is released:

```text
ba0aff180404c4d50ed0a11de69c412453315c1de550919b961343cef30db1b2
```

The authoritative public copy is now
[`piResults/results/foundational/raw/w2_live3_soak.json`](../piResults/results/foundational/raw/w2_live3_soak.json).

