
 — C3 saved phase verification: 04_gentle_rotation
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:39.146234+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/04_gentle_rotation_resume_verification
{
  "phase": "04_gentle_rotation",
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
    "raw_sensor.csv": "6614d81cac1144481fb0b2973a7af7dec0b5da5f1dc1e92393c8042cc089fe43",
    "window_scores.csv": "22ab6213109c746d8b1137582f7758e1fef53651efd1cab195b6558a40c11c99",
    "summary.json": "b987e4e1c3b9ff65590b8f84fda81e01bebb23315abbb772129366eaee6bbc7e",
    "metadata.json": "c91d523bc726b027867f4c9476c1226f543500d13983fe466b20b8591ddac31c"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified.",
  "cue_after_first_sample_s": 20.22762276000003,
  "recorded_time_after_cue_s": 54.754929204999826
}
