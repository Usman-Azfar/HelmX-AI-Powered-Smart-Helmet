
 — C3 saved phase verification: 06_moderate_rotation
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:41.746729+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/06_moderate_rotation_resume_verification
{
  "phase": "06_moderate_rotation",
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
    "raw_sensor.csv": "f90fac579570cb9fb313987a085dbeebb306fbd05e18ad75b55ae47698b426b5",
    "window_scores.csv": "13007c0414e48312e0a3c27af4420d26ba8911405ea51af3b6084aa2e100058b",
    "summary.json": "0ea07d0cc3d91a80e69aea53bcd0a3124bda1fc1fdb58de19cbf240ce178f161",
    "metadata.json": "303907c46a9493f76306604b774f14005f013f7b8964c3caa6653c2e56514963"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.",
  "cue_after_first_sample_s": 13.811872845999915,
  "recorded_time_after_cue_s": 76.18219474500006
}
