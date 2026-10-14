# Foundational Raspberry Pi Artifacts

These files document execution on a Raspberry Pi 4 Model B Rev 1.5. They supplement the
[complete hardware report](../COMPLETE_RESULTS.md) with compact, machine-readable evidence.

## `current/`

Selected canonical results used for the public summary:

- Isolated TFLite latency and model-load timing.
- Sustained CPU, memory, and thermal measurements.
- Physical movement and live GPIO trigger-path tests.
- Offline-versus-causal-streaming agreement.
- Keras/FP16/INT8 quantization comparison.
- Thread-count, concurrent-worker, logging, and robustness checks.
- A concise summary of the 180-minute live-sensor soak.

“Current” means selected as the canonical public artifact. Every JSON still records the environment
and configuration under which it was measured; historical measurements are not silently rewritten
to match later configuration changes.

## `raw/`

Selected detailed telemetry retained for independent inspection:

- Live sample-interval characterization.
- Live end-to-end pipeline timing.
- The full 180-minute soak resource series.
- Replay-paced pipeline measurements.

The full soak JSON is intentionally uncompressed so it remains directly inspectable and scriptable.
It is approximately 3.4 MiB and does not require Git LFS.

## `historical/`

Earlier, blocked, comparison, or post-fix confirmation runs. These files remain useful for tracing
how deployment weaknesses were found and closed, but they are not the first artifacts a reviewer
should use for headline numbers.

## `diagnostics/`

Model hashes, service policy, and the relevant crash-monitor journal extract. Full process listings,
kernel dumps, and device identity captures are deliberately excluded from the public package because
they contain unnecessary host fingerprints and do not improve interpretation of the reported model
or latency metrics.

For the complete experiment narrative, evidence chronology, superseded findings, and qualification
language, see [`COMPLETE_RESULTS.md`](../COMPLETE_RESULTS.md).

