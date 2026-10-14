# Results Index

The [complete results report](COMPLETE_RESULTS.md) is the human-readable entry point. Supporting
machine-readable evidence is grouped by research phase:

| Directory | Contents |
|---|---|
| `foundational/` | Curated inference, replay, quantization, long-soak, and historical control results |
| `final-validation/` | A-R validation outputs plus the frozen models, normalizer, thresholds, configuration, and artifact hashes |
| `final-closure/` | Corrected acquisition tests, high-range work, scheduler/service studies, model fidelity, provenance, figures, GPIO, and optional acquisition modes |
| `generated/` | Destination for future executions of the maintained Pi benchmark and research-suite scripts |

Result directories preserve the experiment-oriented names used by the source archive. Summary JSON,
CSV, NumPy, text, and image artifacts are retained where they add evidence. Large CSV captures are
losslessly gzip-compressed as `.csv.gz`; the decompressed bytes were checksum-verified before the
uncompressed public duplicate was removed.

Host process snapshots and exact boot UUIDs are intentionally excluded or redacted. These do not
change the measurements and are documented in
[selection and exclusions](../provenance/SELECTION_AND_EXCLUSIONS.md).

