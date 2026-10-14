# Publication Package Validation

Validated on 2026-10-14 before GitHub publication.

## Outcome

The package is structurally complete for the experiment catalogue in
[`COMPLETE_RESULTS.md`](../results/COMPLETE_RESULTS.md). Each campaign has public evidence and the
available experiment scripts, while duplicate releases, private host metadata, and redundant raw
captures remain in the ignored source archive.

## Integrity checks

| Check | Result |
|---|---|
| Public files | 1,060 files; approximately 89.24 MiB |
| Largest individual file | 3.42 MiB; no file is near GitHub's 100 MB hard limit |
| Results | 887 files across foundational, final-validation, final-closure, and generated groups |
| Figures | 59 files across foundational, live-sensor, and final-closure groups |
| Experiment code | 83 Python and 10 shell scripts |
| JSON validation | 597/597 files parsed successfully |
| Markdown links | 0 unresolved relative links in the package |
| Exact-copy audit | 963 retained files matched their current source SHA-256 hashes |
| Compression audit | 22/22 large CSV files decompressed to the recorded original SHA-256 |
| Public manifest | Every listed file existed and matched its recorded byte count and SHA-256 |
| Empty result directories | 0 |
| Oversized files | 0 files at or above 100 MiB |
| Private host metadata | 0 `metadata.json` files retained |
| Sensitive-pattern scan | No boot UUID, local Windows user path, private-key marker, AWS key pattern, or removed process-helper name found |
| Source archive isolation | `piResults2/` and its contents matched the root `.gitignore` rule |

`FILE_MANIFEST.csv` intentionally excludes itself because a file cannot contain its own stable
cryptographic hash.

## Script coverage

| Script group | Coverage |
|---|---|
| Core Pi research suite | 38/38 suite files plus the device benchmark present with matching hashes |
| Final closure | 43/43 source files present; nine have documented privacy or reorganized-path adaptations |
| Final validation | All seven Python/shell sources present, including the three frozen deployment/export sources; runner paths target the organized package |
| Scheduler study | 5/5 source files present; one runner path targets the organized package |

The complete frozen validation bundle is also present under
`results/final-validation/frozen-artifacts/`: Keras, FP16, and INT8 models; normalizer; thresholds;
configuration; source; reproducibility manifest; and artifact hashes.

Maintained runners now write future Pi outputs to `piResults/results/generated/`; they no longer
create hardware result files under the root `results/` model-evaluation package.

## Evidence spot checks

- The four preserved power-cycle identity sequences each contain 100 reads and every read is
  decimal `112` (`0x70`).
- No public result directory is empty.
- All 55 closure requirements and the earlier A-R validation campaign are represented in the
  [coverage matrix](COVERAGE_MATRIX.md) and discussed in the complete report, including Q4 and P as
  explicitly unperformed rather than silently omitted.
- Superseded FIFO findings, interrupted attempts, discarded motion captures, and measurement limits
  remain disclosed in the report and historical documentation.

## Validation boundary

This validation checks packaging, file integrity, coverage, privacy, JSON readability, and internal
links. It does not rerun physical hardware experiments or convert research evidence into a safety
certification. The unmodified `piResults2/` archive remains the local audit source.

