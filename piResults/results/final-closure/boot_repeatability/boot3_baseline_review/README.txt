
 — Boot 3 saved stationary verification
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-05T17:01:08.620236+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot3_baseline_review
{
  "boot": 3,
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
  "power_off_seconds_user_reported": 10.0,
  "first_sample_uptime_s": 3901.861378966,
  "samples": 14988,
  "windows": 996,
  "elapsed_s": 300.0110729039998,
  "sample_rate_hz": 49.958156060446456,
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
    "raw_sensor.csv": "dbce5fdf4e833b9068215d11c3b3daadce263fcae71960053553c989f40b1b6a",
    "window_scores.csv": "019d24f9fc65772c4637cdfecb12fb4ba8454b1628599173c68ad8cfb3f983e0",
    "summary.json": "588fbe297690d290a4d785cab6e86e03d78eaf03c275d063810c02bfafcea792",
    "metadata.json": "b8f220aefbad104736faf764925fd2e15104a0b84c03785ed853f90cb95fbe9f"
  },
  "scope": "Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage."
}
