
B4 — Corrected A–B–A additional timing and coverage metrics
Status: COMPLETE (CONFIGURATION QUALIFIED)
UTC: 2026-09-30T14:01:03.445914+00:00
Evidence: piResults/final_pi_review_closure/05_corrected_aba_metrics
{
  "arms": {
    "A1_polling": {
      "raw_sha256": "69c7813afbc46fb49793cb565373f3fe108c244a4bed5f686fe3ac5a6b4771af",
      "windows_sha256": "860bb12d16b4ec7c87013fae34adc2445d38cc0556c6776e0208554d8300a3aa",
      "dt_bins": {
        "lt10ms": 250,
        "10_to_30ms_inclusive": 59151,
        "above30_to_60ms_inclusive": 435,
        "above60ms": 0
      },
      "guard_cutoff_s": 0.06,
      "gaps_per_min": 0.0,
      "guard_suspected_dropped_equivalent": 0,
      "guard_dropped_equivalent_per_min": 0.0,
      "nominal_elapsed_time_positions": 3997,
      "nominal_received_sample_positions": 3986,
      "scored_windows": 3986,
      "unformed_received_sample_positions": 0,
      "elapsed_time_nominal_minus_scored_signed": 11,
      "C_D_elapsed_time_denominator": 0.9972479359519639,
      "longest_positive_scored_window_run": 0,
      "cpu_frequency_khz_observed_unique": [
        1800000
      ],
      "cpu_temp_min_max_c": [
        46.251,
        51.121
      ],
      "timing_note": "FIFO intervals reflect host batch availability; dropped-equivalent is the guard heuristic, not verified missing FIFO packets.",
      "coverage_note": "Resets are counted by the live guard; they are not the count of every unformed candidate. Received-sample and nominal elapsed-time denominators are both supplied. If measured sample rate exceeds 50 Hz, the elapsed-time count ratio can exceed one and its signed deficit can be negative; neither is a probability or a count of lost windows."
    },
    "B_fifo": {
      "raw_sha256": "2ab88e0f28fe57f3f397b88f5c555a5b969ea3db90431c95bb2a81c6fb58a340",
      "windows_sha256": "2641d796a2c6af742431bae9a611e37d64fcbfe3bed7f5859f7a451fc325cd44",
      "dt_bins": {
        "lt10ms": 143,
        "10_to_30ms_inclusive": 60278,
        "above30_to_60ms_inclusive": 171,
        "above60ms": 2
      },
      "guard_cutoff_s": 0.06,
      "gaps_per_min": 0.09999943852581929,
      "guard_suspected_dropped_equivalent": 11,
      "guard_dropped_equivalent_per_min": 0.5499969118920061,
      "nominal_elapsed_time_positions": 3997,
      "nominal_received_sample_positions": 4036,
      "scored_windows": 4029,
      "unformed_received_sample_positions": 7,
      "elapsed_time_nominal_minus_scored_signed": -32,
      "C_D_elapsed_time_denominator": 1.0080060045033776,
      "longest_positive_scored_window_run": 0,
      "cpu_frequency_khz_observed_unique": [
        1800000
      ],
      "cpu_temp_min_max_c": [
        45.277,
        52.095
      ],
      "timing_note": "FIFO intervals reflect host batch availability; dropped-equivalent is the guard heuristic, not verified missing FIFO packets.",
      "coverage_note": "Resets are counted by the live guard; they are not the count of every unformed candidate. Received-sample and nominal elapsed-time denominators are both supplied. If measured sample rate exceeds 50 Hz, the elapsed-time count ratio can exceed one and its signed deficit can be negative; neither is a probability or a count of lost windows."
    },
    "A2_polling": {
      "raw_sha256": "035779e40aba2c46009c17a0cfe25ef269bc43c0a8a35ba799bc7616e4e2ab97",
      "windows_sha256": "0ef0d63f61a57a2e3da1b10dfa30507cd587457d460d289bb95ae2d30ece6791",
      "dt_bins": {
        "lt10ms": 84,
        "10_to_30ms_inclusive": 59750,
        "above30_to_60ms_inclusive": 121,
        "above60ms": 0
      },
      "guard_cutoff_s": 0.06,
      "gaps_per_min": 0.0,
      "guard_suspected_dropped_equivalent": 0,
      "guard_dropped_equivalent_per_min": 0.0,
      "nominal_elapsed_time_positions": 3997,
      "nominal_received_sample_positions": 3994,
      "scored_windows": 3994,
      "unformed_received_sample_positions": 0,
      "elapsed_time_nominal_minus_scored_signed": 3,
      "C_D_elapsed_time_denominator": 0.9992494370778083,
      "longest_positive_scored_window_run": 0,
      "cpu_frequency_khz_observed_unique": [
        1800000
      ],
      "cpu_temp_min_max_c": [
        41.868,
        51.608
      ],
      "timing_note": "FIFO intervals reflect host batch availability; dropped-equivalent is the guard heuristic, not verified missing FIFO packets.",
      "coverage_note": "Resets are counted by the live guard; they are not the count of every unformed candidate. Received-sample and nominal elapsed-time denominators are both supplied. If measured sample rate exceeds 50 Hz, the elapsed-time count ratio can exceed one and its signed deficit can be negative; neither is a probability or a count of lost windows."
    }
  },
  "scope": "Derived from the completed fresh three-arm acquisition. Main per-arm summaries retain scores, signal statistics, errors, latency, guard telemetry and alert counts."
}
