# Headless 40-minute results — 7 October 2026

Reviewed run: `headless_20261006T194644Z`; console: `headless_console_20261006T194643Z`. Capture approximately 00:46–01:26 Pakistan time on 7 October (UTC filenames retain 6 October). Two sequential 1200-second captures on CPU core 3. Both use sensor polling; `fifo` denotes SCHED_FIFO priority 10, not sensor FIFO acquisition. Normal uses SCHED_OTHER priority 0. Exact commands are preserved in the run plan.

Session exit status 0; restoration failed 0. All 12 original verification checks and all 7 additional raw/replay checks passed for each condition. Frozen artifact hashes matched. Raw sample indices are contiguous and timestamps strictly increase; scores, window endpoints and policy decisions replay exactly.

| Metric | Normal | SCHED_FIFO |
|---|---:|---:|
| Elapsed seconds | 1200.0021216810005 | 1200.0188396250005 |
| Samples | 60000 | 59987 |
| Scored windows | 3997 | 3982 |
| Sample rate Hz | 49.99991159678128 | 49.98838186469274 |
| Timing gaps | 0 | 4 |
| C_D | 1.0 | 0.9964964964964965 |
| V_T | 1.0 | 0.9989964877069744 |
| 90-sample survival | 1.0 | 0.9940565628234665 |
| I2C failures | 0 | 0 |
| Policy alerts | 0 | 0 |
| dt mean_ms | 20.000002 | 20.004641 |
| dt median_ms | 19.998390 | 19.998604 |
| dt std_ms | 0.823766 | 1.049625 |
| dt rms_error_from_20ms | 0.823766 | 1.049635 |
| dt p90_ms | 20.259311 | 20.145355 |
| dt p95_ms | 21.657501 | 21.676004 |
| dt p99_ms | 22.006960 | 21.816271 |
| dt p99.9_ms | 24.303021 | 23.281511 |
| dt max_ms | 33.785445 | 156.652341 |
| Processing p99 ms | 2.643990 | 2.646337 |
| Processing maximum ms | 5.992515 | 3.512945 |

Normal: 0 gaps/min; SCHED_FIFO: approximately 0.200 gaps/min. Neither run had clipping, positive windows, capture exceptions, processing over 300 ms, or throttling at completion (0x0). All classifier and reconstruction outputs were zero. This verifies reproducibility, not crash sensitivity.

normal: mean process CPU 2.171%; RSS 47.977–50.668 MiB; CPU temperature 41.381–45.277 °C. Research buffers contribute to RSS growth.
fifo: mean process CPU 2.108%; RSS 47.980–50.617 MiB; CPU temperature 40.894–45.277 °C. Research buffers contribute to RSS growth.

The normal condition contains a transient gyro magnitude peak of 72.956 degrees/s versus 4.549 degrees/s under SCHED_FIFO. Physical cause is unknown. The operator subsequently confirmed the helmet stayed untouched throughout both runs; the recorded transient remains unexplained and retained. SCHED_FIFO has a lower p99 interval but worse maximum interval and four gaps; this pair does not establish an overall scheduling improvement.

D1/D2/D3: COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED). Capture, raw-data, replay and resource review passed. On 7 October 2026 the operator confirmed the helmet stayed untouched throughout both runs: "yes untouched". Attestation is preserved in `operator_attestation.json`. Ten-second process observations found no interactive applications but cannot exclude shorter activity. D4/K1 randomized repeats are not satisfied. No physical alarm or SMS was exercised. Existing release archives predate this review; no archive refresh is claimed.

Full metrics, histogram counts, resources, source SHA-256 hashes and verification checks: `summary.json`. Reproducible offline review: `review.py`.
