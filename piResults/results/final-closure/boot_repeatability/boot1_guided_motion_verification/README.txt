
 — Boot 1 saved guided_motion verification
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-06T14:15:45.008853+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_guided_motion_verification
{
  "boot": 1,
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
  "power_off_seconds_user_reported": 10,
  "first_sample_uptime_s": 1036.215948798,
  "samples": 5989,
  "windows": 396,
  "elapsed_s": 120.01308030900009,
  "sample_rate_hz": 49.9028937894103,
  "i2c_failures": 0,
  "gap_count": 0,
  "confirmed_policy_events": 1,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 4,
    "gz": 2
  },
  "source_hashes": {
    "raw_sensor.csv": "55863df8d4928bd1448fb02ff6442e81fa9195f109c230bf4d192e3253432e4b",
    "window_scores.csv": "96611f4d6bdeddf6418dc19c9bee48146daa2acd57bc56d8d27f1ef7d52dcaa1",
    "summary.json": "fa1c58f0af44324aa009e6974a47c2d3a7bcdf41f9fb998f2d53c9e867d6ab50",
    "metadata.json": "eab037a7434b3d9e590659db888eb5b9f9f2a4a35eac4cd9ee07fe258cea8ee5"
  },
  "scope": "Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage."
}
