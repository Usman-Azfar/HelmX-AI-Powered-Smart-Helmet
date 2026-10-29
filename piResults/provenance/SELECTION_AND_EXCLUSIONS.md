# Publication Selection and Exclusions

## Source and preservation

The publication package was selected from the unmodified `piResults2/` working archive, which
contains 9,488 files and is approximately 4.37 GiB. The source archive remains local and is ignored
by Git. Files in this directory are either byte-for-byte copies, losslessly compressed copies, or
clearly identified public summaries.

## Included

- All distinct experiment families described in the consolidated report.
- The current Pi research-suite scripts, all final-validation/final-closure scripts, and the frozen
  deployment bundle used by the validation campaign.
- Authoritative summaries, tables, compact raw evidence, NumPy artifacts, and review figures.
- Earlier reports and protocols needed to understand chronology, corrections, and limitations.
- Failed, interrupted, discarded, and unperformed tests where they affect interpretation.

## Excluded from the public copy

- Duplicate timestamped releases and repeated copies of identical artifacts.
- Python environments, caches, temporary files, editor state, logs, and generated build material.
- Full host process snapshots, agent/session commands, and other workstation diagnostics that do
  not substantively support the experiment result. Paths required by archived scripts and method
  records are retained where they explain the evaluated deployment.
- Exact operating-system boot UUIDs. Distinct-boot evidence is represented by sanitized aggregate
  results and the underlying 100-read identity sequences.
- Oversized or redundant raw captures when an authoritative summary or equivalent selected raw
  evidence is already present.

## Transformations

- CSV files of at least 1 MiB were losslessly gzip-compressed. Each compressed stream was
  decompressed in memory and SHA-256 compared with the original public copy before removal.
- Eight public result records and one historical recovery-script note had only their boot UUID
  values replaced with `<redacted-boot-id>`.
- Four raw scheduler traces replaced the unrelated browser helper name with `background_proc`;
  timing values and event counts were unchanged.
- `summary_public.json` for A1 is a privacy-safe aggregate derived from the preserved identity
  records and closure report.

- In six scheduler-latency traces (`final-validation/scheduler_repeats/run*_sched_latency.txt`), a third-party development tool's process name was replaced with `devtool_proc` (distinct from the browser helper already relabelled `background_proc`); timing values and event counts were unchanged. Product names of that tool were likewise removed from prose in three historical reports, one status note, one experiment-conditions entry and two script comments. The disclosure that a coding-agent process was running during those tests is retained.
- `orchestrate_e3.sh`, `orchestrate_e4.sh` and `orchestrate_h2.sh` are the portable versions, which derive the repository root or accept `HELMX_ROOT`, replacing as-run copies that hard-coded the collection device's home path.
- The I²C diagnostic folders omit two `metadata.json` host snapshots (see the folder's `PUBLICATION_NOTE.md`). The D4/K1 raw captures are retained in the author's private archive; only the review, summary and attestation are published.

These transformations affect packaging and privacy only; reported numerical measurements were not
changed. `FILE_MANIFEST.csv` hashes every published file, while `COPY_AUDIT.csv` records retained
byte-identical source copies.

Maintained Pi runners use `piResults/results/generated/` for new output. The root `results/`
directory is reserved for model-development and external-validation evidence.

