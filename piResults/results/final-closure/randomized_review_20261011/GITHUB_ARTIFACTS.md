# GitHub evidence packaging

The October D4/K1 results include successful full studies, earlier failed K1 attempts, smoke tests, the I²C diagnostic, scripts, source snapshots, paired analyses, and operator attestation. Failed captures remain labelled failed.

Original scheduler recordings are approximately 199 MiB each. GitHub copies therefore use adjacent `scheduler.data.gz` and `scheduler_timehist.txt.gz` files. These are lossless gzip copies, not summaries or downsampled traces. Every copy was decompressed and checked against the SHA-256 of its original before staging. `compressed_artifact_manifest.json` records both paths, byte counts, and both hashes. Original files remain on the collection Pi and are ignored by Git; all other raw sensor/score/resource files remain directly accessible.

After cloning, restore a recording before using perf or checking the original capture's saved hashes:

```bash
gzip -dk path/to/pair1_A/scheduler.data.gz
gzip -dk path/to/pair1_A/scheduler_timehist.txt.gz
```

Run these on a fresh checkout where the corresponding uncompressed files do not yet exist. Compare restored files with `original_sha256` in the manifest. Earlier verification reports deliberately retain the original file names and hashes.

The capture metadata and reports are preserved as recorded. The completion review supplies the later operator attestation and current status. Older release-candidate archives have not been rebuilt by this upload.
