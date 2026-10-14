
 — Boot 4 saved stationary verification
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-05T17:35:30.989253+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot4_baseline_review
{
  "boot": 4,
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
  "first_sample_uptime_s": 97.266535921,
  "samples": 29991,
  "windows": 1996,
  "elapsed_s": 600.00060187,
  "sample_rate_hz": 49.984949859263715,
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
    "raw_sensor.csv": "0ca85b2eb66ab1013ea6110f6d90b7f941e448afa397e97479155e45dc92e407",
    "window_scores.csv": "83e171fa4274a30e366d321cf77a077c6776031bd4f123a99cdf8926933a0a1e",
    "summary.json": "95360a74adc182693d754810a800251a36569fa127dd4ee2728ec88747e26328",
    "metadata.json": "f7305fc3059108f283512b2776fcf03dac5c5cfde624b695033e1a949d28f0c0"
  },
  "scope": "Offline verification only; physical conditions require operator attestation. H1 requires baseline and guided motion on three boots independently of A1 identity completion. Late recordings cannot supply I2 first-ten-minute coverage."
}
