
E2 — E2 sensor-stream analysis
Status: COMPLETE (HISTORICAL INPUTS)
UTC: 2026-09-29T19:29:42.883775+00:00
Evidence: piResults/final_pi_review_closure/stream_E2
{
  "recordings": [
    {
      "file": "piResults/final_pi_results/final_aba_acquisition_test/A1_polling/raw_sensor.csv",
      "sha256": "71709da0ebc32cb36a70db682b3d99247556c16507622a4633a5d30c2b58a498",
      "origin": "HISTORICAL recording; fresh analysis, not a fresh hardware trial",
      "invalid_rows_removed": 0,
      "reference": {
        "scored": 3997,
        "nominal_received_sample_positions": 3997,
        "nominal_elapsed_time_positions": 3997,
        "invalidations": 0,
        "V_T_scored_over_scored_plus_resets": 1.0,
        "C_D_received_sample_denominator": 1.0,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 1.0,
        "confirmed_alert_events": 0,
        "trigger_timestamps": [],
        "guard_threshold_s": 0.06,
        "run_lengths_samples": [
          60000
        ]
      },
      "dt": {
        "n": 59999,
        "mean_ms": 20.00031732335538,
        "median_ms": 19.994618000055198,
        "std_ms": 0.3754196376912626,
        "rms_error_from_20ms": 0.3754197717999822,
        "p90_ms": 20.11993019914371,
        "p95_ms": 20.309206298406934,
        "p99_ms": 21.090115117840465,
        "p99.9_ms": 23.054290589716604,
        "max_ms": 52.07183700258611,
        "histogram_edges_ms": [
          0,
          10,
          15,
          25,
          30,
          40,
          60,
          100,
          "inf"
        ],
        "counts_left_closed_right_open": [
          1,
          5,
          59987,
          5,
          0,
          1,
          0,
          0
        ],
        "deviation_counts": {
          "2": 421,
          "5": 12,
          "8": 4
        }
      },
      "window_jitter_correlation": {
        "classifier": null,
        "reconstruction": null
      },
      "caveat": "Pearson correlation is descriptive, overlapping windows are dependent. Null means constant score/jitter; no inferential p-value asserted."
    },
    {
      "file": "piResults/final_pi_results/clipping/motion_session_raw.csv",
      "sha256": "da43d694712a753ab68cb4ff8be98c83188dc943e682ec35c189e26c8cc6beef",
      "origin": "HISTORICAL recording; fresh analysis, not a fresh hardware trial",
      "invalid_rows_removed": 1,
      "reference": {
        "scored": 5585,
        "nominal_received_sample_positions": 5603,
        "nominal_elapsed_time_positions": 5604,
        "invalidations": 5,
        "V_T_scored_over_scored_plus_resets": 0.9991055456171736,
        "C_D_received_sample_denominator": 0.9967874353025165,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 0.9947030115462445,
        "confirmed_alert_events": 2,
        "trigger_timestamps": [
          527.213259593,
          594.002590444
        ],
        "guard_threshold_s": 0.06,
        "run_lengths_samples": [
          5654,
          6018,
          3756,
          2831,
          6104,
          59736
        ]
      },
      "dt": {
        "n": 84098,
        "mean_ms": 20.00374341650218,
        "median_ms": 19.9925084999677,
        "std_ms": 0.8436486758603826,
        "rms_error_from_20ms": 0.843656980915873,
        "p90_ms": 20.337823200048888,
        "p95_ms": 20.58840234997774,
        "p99_ms": 21.983182999997553,
        "p99.9_ms": 24.23335812591945,
        "max_ms": 125.8753600000091,
        "histogram_edges_ms": [
          0,
          10,
          15,
          25,
          30,
          40,
          60,
          100,
          "inf"
        ],
        "counts_left_closed_right_open": [
          9,
          38,
          84004,
          38,
          3,
          1,
          3,
          2
        ],
        "deviation_counts": {
          "2": 1681,
          "5": 94,
          "8": 31
        }
      },
      "window_jitter_correlation": {
        "classifier": -0.08363146034772884,
        "reconstruction": -0.04870297681998948
      },
      "caveat": "Pearson correlation is descriptive, overlapping windows are dependent. Null means constant score/jitter; no inferential p-value asserted."
    },
    {
      "file": "piResults/final_pi_results/clipping/motion_session_raw_part2.csv",
      "sha256": "ad69611ad17fefab595b08824d3039f51696d2fdefdecb9b19856efd2642307f",
      "origin": "HISTORICAL recording; fresh analysis, not a fresh hardware trial",
      "invalid_rows_removed": 0,
      "reference": {
        "scored": 1011,
        "nominal_received_sample_positions": 1014,
        "nominal_elapsed_time_positions": 1014,
        "invalidations": 1,
        "V_T_scored_over_scored_plus_resets": 0.9990118577075099,
        "C_D_received_sample_denominator": 0.9970414201183432,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 0.9941347040991169,
        "confirmed_alert_events": 2,
        "trigger_timestamps": [
          773.534649037,
          907.094906471
        ],
        "guard_threshold_s": 0.06,
        "run_lengths_samples": [
          11941,
          3322
        ]
      },
      "dt": {
        "n": 15262,
        "mean_ms": 20.00272314709736,
        "median_ms": 19.991365000009864,
        "std_ms": 0.9006105363305654,
        "rms_error_from_20ms": 0.9006146532672797,
        "p90_ms": 20.379633899995042,
        "p95_ms": 20.759547450001033,
        "p99_ms": 22.297716570018327,
        "p99.9_ms": 25.82088084303779,
        "max_ms": 60.61179699997865,
        "histogram_edges_ms": [
          0,
          10,
          15,
          25,
          30,
          40,
          60,
          100,
          "inf"
        ],
        "counts_left_closed_right_open": [
          6,
          23,
          15202,
          24,
          5,
          1,
          1,
          0
        ],
        "deviation_counts": {
          "2": 358,
          "5": 60,
          "8": 18
        }
      },
      "window_jitter_correlation": {
        "classifier": -0.2101200839974326,
        "reconstruction": -0.15767794800867257
      },
      "caveat": "Pearson correlation is descriptive, overlapping windows are dependent. Null means constant score/jitter; no inferential p-value asserted."
    }
  ],
  "policy_versions": "60 ms is frozen current deployment; 30 ms historical policy is explicit reference for F1/F2.",
  "class_specific_fidelity": "Not estimable for unlabeled physical recordings; no invented crash-class metric."
}
