# D4/K1 completion review — 11 October 2026

Both successful full studies completed six pairs (12 ten-minute recordings each), and every saved automated verification check passed. The operator confirmed verbatim “yes” that the helmet remained untouched, in the same position and orientation, throughout both successful studies. See operator_attestation.json for the exact scope and run identifiers.

| Study | Samples | Timing gaps | I²C errors | Alerts |
|---|---:|---:|---:|---:|
| D4 | 359,970 | 8 | 0 | 0 |
| K1 | 359,999 | 0 | 0 | 0 |

D4's eight gaps all occurred in the FIFO-scheduled conditions; normal scheduling had zero. FIFO had lower paired p99 processing and runnable-delay values, but the timing-gap reversals remain part of the result. K1 had zero gaps in both service profiles. These six-pair, instrumented comparisons do not establish a general scheduler advantage. Individual paired differences and descriptive bootstrap intervals are retained in summary.json and the original analyses.

Earlier interrupted K1 attempts remain failed and are preserved in the author's private evidence archive; they are not pooled with the successful six-pair study. The original captures and automated reports are unchanged but are not part of this public repository, which publishes this review, its summary.json and the operator attestation. The I²C diagnostic of the failed K1 attempt is published in `../i2c_diagnostic_20261011/`. This review adds operator attestation and checklist closure. Release archives have not been refreshed.
