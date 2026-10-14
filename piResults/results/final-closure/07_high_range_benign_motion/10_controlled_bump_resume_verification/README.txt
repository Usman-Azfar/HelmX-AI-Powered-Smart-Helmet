
 — C3 saved phase verification: 10_controlled_bump
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:45.566668+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/10_controlled_bump_resume_verification
{
  "phase": "10_controlled_bump",
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
    "raw_sensor.csv": "450dd2f15d2ed86827092a75275ef2ba665ca2c8664733145e931e59b1e0433d",
    "window_scores.csv": "a9aab3caef33a04fba47448e9ca19582cb5409e4beece1f1efe143dd1fa94abd",
    "summary.json": "dbcb2bdf77e7bb7290940b3dd514c9fe424df4f4dc7b41d70f94ba822395ca83",
    "metadata.json": "2ee942f707b66958fa77e8a5c340fc9e8f7ff853e2f325720032880e2f483b58"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.",
  "cue_after_first_sample_s": 9.27279023799997,
  "recorded_time_after_cue_s": 80.72284433600021
}
