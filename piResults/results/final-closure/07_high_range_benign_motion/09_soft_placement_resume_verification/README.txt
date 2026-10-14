
 — C3 saved phase verification: 09_soft_placement
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:44.486898+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/09_soft_placement_resume_verification
{
  "phase": "09_soft_placement",
  "checks": {
    "sample_rows_match": true,
    "window_rows_match": true,
    "full_duration": true,
    "no_exception": true,
    "sample_indices_contiguous": true,
    "timestamps_increasing": true,
    "configuration_restored": true,
    "high_range_filtered_readback": true,
    "replay_endpoint_indices_exact": true,
    "replay_scores_exact": true,
    "replay_policy_exact": true,
    "event_count_matches": true
  },
  "source_hashes": {
    "raw_sensor.csv": "cf90249491802dd42e1c50a10b2e6c18feea68b2791b1c9425ea4b760c0c87ec",
    "window_scores.csv": "56bef12199ade2712b4c4657e9e151558977c291a9613c46c4cdf50e50ee6f20",
    "summary.json": "1af1007e719e86013c08d824b660eacf09712c902d63eb77297253af66ec76d5",
    "metadata.json": "4afa2b300e9dabdcf0d70f486cbd7e8bc86cb5c8f959f4a243fd5bb741d30a4c"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.",
  "cue_after_first_sample_s": 10.225451800999963,
  "recorded_time_after_cue_s": 79.76014192899993
}
