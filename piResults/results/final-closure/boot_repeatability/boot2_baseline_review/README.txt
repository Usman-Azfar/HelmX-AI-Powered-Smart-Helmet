
 — Boot 2 saved stationary verification
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-06T14:15:33.764909+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot2_baseline_review
{
  "boot": 2,
  "capture": "stationary",
  "checks": {
    "raw_rows_match": true,
    "score_rows_match": true,
    "full_requested_duration": true,
    "protocol_duration_met": true,
    "no_exception": true,
    "indices_contiguous": true,
    "timestamps_increasing": true,
    "configuration_restored": true,
    "identity_100_reads": true,
    "identity_counts_match": true,
    "identity_baseline_same_boot": true,
    "replay_endpoints_exact": true,
    "replay_scores_exact": true,
    "replay_policy_exact": true,
    "event_count_matches": true
  },
  "identity_counts": {
    "0x70": 100
  },
  "power_off_seconds_user_reported": 10,
  "first_sample_uptime_s": 101.296416077,
  "samples": 14991,
  "windows": 996,
  "elapsed_s": 300.00589979299997,
  "sample_rate_hz": 49.96901731047152,
  "i2c_failures": 0,
  "gap_count": 0,
  "confirmed_policy_events": 0,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 0,
    "gz": 0
  },
  "source_hashes": {
    "raw_sensor.csv": "711f0735d5c1e9def2e100dbff28bfff0afd35b90f0e7c232118b8d915c126ec",
    "window_scores.csv": "b69b77db1e4190801a07bfbd468a7ede9de999fffbec8ff1f02aebd06c42e1e8",
    "summary.json": "6eb26eeaee5bfc8be70a6c9fbfa678e7592548ab05976594a29f70afa3d498fa",
    "metadata.json": "902e0956f2eddc556609f1ad3bc801a49d8050a633304f35c587a9b617f2218c"
  },
  "scope": "Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage."
}
