# Evidence packaging for the October D4/K1 studies

This public repository contains the completion review (`README.md`), the aggregated results and paired analyses (`summary.json`), and the operator attestation for the October D4/K1 studies. The I²C diagnostic of the failed K1 attempt is published in `../i2c_diagnostic_20261011/`.

The raw captures are not in this repository. They comprise the full six-pair studies, the earlier failed K1 attempts, the smoke tests, the per-recording scheduler traces (about 199 MiB each before compression), scripts and source snapshots. They are retained unchanged in the author's private evidence archive and are available on reasonable request.

`compressed_artifact_manifest.json` is kept as a record of how the scheduler traces were losslessly compressed for archiving. It lists original and compressed byte counts and SHA-256 hashes. Its paths refer to the private archive layout, not to files in this repository.

Failed captures remain labelled as failed and are not pooled with the successful studies.
