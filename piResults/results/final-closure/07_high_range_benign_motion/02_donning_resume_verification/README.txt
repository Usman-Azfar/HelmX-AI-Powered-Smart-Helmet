
 — C3 saved phase verification: 02_donning
Status: PASS (OFFLINE VERIFICATION)
UTC: 2026-10-04T17:18:37.559222+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/02_donning_resume_verification
{
  "phase": "02_donning",
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
    "raw_sensor.csv": "5adbc49e4c20acdd07d35bbba46b9b2b1ecf2e82103a35dedd1e4f756a0b0401",
    "window_scores.csv": "b19261bae159c53d48fe59bff73da391983e0c0dede78320edbe269e11241841",
    "summary.json": "afd122c400b9f7dd848516e0d02dc279eeb68e9aa6fed3f91fcf5cc11edaf576",
    "metadata.json": "4651a845a1ed22ede67d8fa2968f161f90641c45cac3e3b715b55f2660436bb8"
  },
  "max_abs_replay_score_error": [
    0.0,
    0.0
  ],
  "scope": "Offline integrity/replay verification of the saved capture, not a new physical trial. Policy replay uses recorded decision timestamps. Operator motion and reaction latency are not independently verified."
}
