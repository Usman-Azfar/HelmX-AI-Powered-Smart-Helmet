
E3 — E3 sensor-stream analysis
Status: COMPLETE (HISTORICAL INPUTS)
UTC: 2026-09-29T19:31:03.479353+00:00
Evidence: piResults/final_pi_review_closure/stream_E3
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
      "variants": {
        "adaptive_alpha": {
          "summary": {
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
          "fidelity": {
            "matched_end_sample_windows": 3997,
            "reference_only": 0,
            "transformed_only": 0,
            "classifier_mae": 0.0,
            "reconstruction_mae": 0.0,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        }
      }
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
      "variants": {
        "adaptive_alpha": {
          "summary": {
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
          "fidelity": {
            "matched_end_sample_windows": 5585,
            "reference_only": 0,
            "transformed_only": 0,
            "classifier_mae": 0.0005105752014324083,
            "reconstruction_mae": 0.00014065036628538728,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        }
      }
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
      "variants": {
        "adaptive_alpha": {
          "summary": {
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
          "fidelity": {
            "matched_end_sample_windows": 1011,
            "reference_only": 0,
            "transformed_only": 0,
            "classifier_mae": 0.002600302917903066,
            "reconstruction_mae": 0.0015539708376874084,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        }
      }
    }
  ],
  "policy_versions": "60 ms is frozen current deployment; 30 ms historical policy is explicit reference for F1/F2.",
  "class_specific_fidelity": "Not estimable for unlabeled physical recordings; no invented crash-class metric."
}
