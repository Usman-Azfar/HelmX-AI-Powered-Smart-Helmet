
 — Boot 3 saved guided_motion verification
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-05T17:03:50.421412+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot3_guided_motion_verification
{
  "boot": 3,
  "capture": "guided_motion",
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
  "power_off_seconds_user_reported": 10.0,
  "first_sample_uptime_s": 4248.022393239,
  "samples": 5985,
  "windows": 396,
  "elapsed_s": 120.0051983580006,
  "sample_rate_hz": 49.872839526046974,
  "i2c_failures": 0,
  "gap_count": 0,
  "confirmed_policy_events": 1,
  "rail_counts": {
    "ax": 2,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 4,
    "gz": 11
  },
  "source_hashes": {
    "raw_sensor.csv": "4221ff28be3565e995974a7262d4ca00ea42de11030eb6b1e69e266ae2f405c0",
    "window_scores.csv": "a3e8b3fb816299fc5e8ae0e704123bff283c353202fdcf52e7841df5bad5a468",
    "summary.json": "7d808589fe03fc83f22f41a8f96c0e7ec25fb10a17e5c457b1de3c090184ffee",
    "metadata.json": "2a3052cb869531520c01ce841506d1cc3daf7e04a9175f8c06cb86bc539b1dec"
  },
  "scope": "Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage."
}
