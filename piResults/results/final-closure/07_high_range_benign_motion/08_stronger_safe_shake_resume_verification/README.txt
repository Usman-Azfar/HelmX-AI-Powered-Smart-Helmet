
 — C3 saved phase verification: 08_stronger_safe_shake
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:43.619464+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/08_stronger_safe_shake_resume_verification
{
  "phase": "08_stronger_safe_shake",
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
    "raw_sensor.csv": "86398bb044c2f6de65d48fabd0d07328f8bafff5fc2fd03c538311b4c6273a60",
    "window_scores.csv": "093b2d051bd1931514411027cf8ac1e8904ab5da6e7f8f823386436729f624a2",
    "summary.json": "c39daa3fabe46613d0e8b66d49f851b2ab1663cce4a19179055b53cf6ad8f5bd",
    "metadata.json": "7d1f89c1fad2a10ee604fb507ecdbfeef10829909803b7f8a0ea3d78027dda3d"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.",
  "cue_after_first_sample_s": 10.92022185199994,
  "recorded_time_after_cue_s": 79.06442397599994
}
