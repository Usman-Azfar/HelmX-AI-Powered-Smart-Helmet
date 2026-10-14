
F1 — F1 sensor-stream analysis
Status: COMPLETE (HISTORICAL INPUTS)
UTC: 2026-09-29T19:33:07.481232+00:00
Evidence: piResults/final_pi_review_closure/stream_F1
{
  "recordings": [
    {
      "file": "piResults/final_pi_results/final_aba_acquisition_test/A1_polling/raw_sensor.csv",
      "sha256": "71709da0ebc32cb36a70db682b3d99247556c16507622a4633a5d30c2b58a498",
      "origin": "HISTORICAL recording; fresh analysis, not a fresh hardware trial",
      "invalid_rows_removed": 0,
      "reference": {
        "scored": 3993,
        "nominal_received_sample_positions": 3997,
        "nominal_elapsed_time_positions": 3997,
        "invalidations": 1,
        "V_T_scored_over_scored_plus_resets": 0.9997496244366549,
        "C_D_received_sample_denominator": 0.9989992494370779,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 0.9985144631202951,
        "confirmed_alert_events": 0,
        "trigger_timestamps": [],
        "guard_threshold_s": 0.03,
        "run_lengths_samples": [
          25303,
          34697
        ]
      },
      "variants": {
        "linear_one_sample": {
          "summary": {
            "scored": 3997,
            "nominal_received_sample_positions": 3997,
            "nominal_elapsed_time_positions": 3997,
            "invalidations": 0,
            "V_T_scored_over_scored_plus_resets": 1.0,
            "C_D_received_sample_denominator": 1.0,
            "inserted_samples": 1,
            "p_valid_90_sample_position": 1.0,
            "confirmed_alert_events": 0,
            "trigger_timestamps": [],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              60001
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 1683,
            "reference_only": 2310,
            "transformed_only": 2314,
            "classifier_mae": 0.0,
            "reconstruction_mae": 0.0,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        },
        "hold_one_sample": {
          "summary": {
            "scored": 3997,
            "nominal_received_sample_positions": 3997,
            "nominal_elapsed_time_positions": 3997,
            "invalidations": 0,
            "V_T_scored_over_scored_plus_resets": 1.0,
            "C_D_received_sample_denominator": 1.0,
            "inserted_samples": 1,
            "p_valid_90_sample_position": 1.0,
            "confirmed_alert_events": 0,
            "trigger_timestamps": [],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              60001
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 1683,
            "reference_only": 2310,
            "transformed_only": 2314,
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
        "scored": 5571,
        "nominal_received_sample_positions": 5603,
        "nominal_elapsed_time_positions": 5604,
        "invalidations": 9,
        "V_T_scored_over_scored_plus_resets": 0.9983870967741936,
        "C_D_received_sample_denominator": 0.9942887738711405,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 0.9904654207832401,
        "confirmed_alert_events": 2,
        "trigger_timestamps": [
          527.213259593,
          594.002590444
        ],
        "guard_threshold_s": 0.03,
        "run_lengths_samples": [
          3280,
          2374,
          5921,
          97,
          3756,
          2831,
          3070,
          3034,
          5288,
          54448
        ]
      },
      "variants": {
        "linear_one_sample": {
          "summary": {
            "scored": 5587,
            "nominal_received_sample_positions": 5603,
            "nominal_elapsed_time_positions": 5604,
            "invalidations": 5,
            "V_T_scored_over_scored_plus_resets": 0.9991058655221745,
            "C_D_received_sample_denominator": 0.9971443869355703,
            "inserted_samples": 4,
            "p_valid_90_sample_position": 0.9947032637417573,
            "confirmed_alert_events": 2,
            "trigger_timestamps": [
              527.213259593,
              594.002590444
            ],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              5655,
              6019,
              3756,
              2831,
              6105,
              59737
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 1588,
            "reference_only": 3983,
            "transformed_only": 3999,
            "classifier_mae": 0.0,
            "reconstruction_mae": 0.0,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        },
        "hold_one_sample": {
          "summary": {
            "scored": 5587,
            "nominal_received_sample_positions": 5603,
            "nominal_elapsed_time_positions": 5604,
            "invalidations": 5,
            "V_T_scored_over_scored_plus_resets": 0.9991058655221745,
            "C_D_received_sample_denominator": 0.9971443869355703,
            "inserted_samples": 4,
            "p_valid_90_sample_position": 0.9947032637417573,
            "confirmed_alert_events": 2,
            "trigger_timestamps": [
              527.213259593,
              594.002590444
            ],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              5655,
              6019,
              3756,
              2831,
              6105,
              59737
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 1588,
            "reference_only": 3983,
            "transformed_only": 3999,
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
      "file": "piResults/final_pi_results/clipping/motion_session_raw_part2.csv",
      "sha256": "ad69611ad17fefab595b08824d3039f51696d2fdefdecb9b19856efd2642307f",
      "origin": "HISTORICAL recording; fresh analysis, not a fresh hardware trial",
      "invalid_rows_removed": 0,
      "reference": {
        "scored": 991,
        "nominal_received_sample_positions": 1014,
        "nominal_elapsed_time_positions": 1014,
        "invalidations": 7,
        "V_T_scored_over_scored_plus_resets": 0.9929859719438878,
        "C_D_received_sample_denominator": 0.9773175542406312,
        "inserted_samples": 0,
        "p_valid_90_sample_position": 0.9589429286938184,
        "confirmed_alert_events": 2,
        "trigger_timestamps": [
          773.39463977,
          907.195115199
        ],
        "guard_threshold_s": 0.03,
        "run_lengths_samples": [
          5131,
          127,
          1831,
          1593,
          3145,
          114,
          395,
          2927
        ]
      },
      "variants": {
        "linear_one_sample": {
          "summary": {
            "scored": 1011,
            "nominal_received_sample_positions": 1014,
            "nominal_elapsed_time_positions": 1014,
            "invalidations": 1,
            "V_T_scored_over_scored_plus_resets": 0.9990118577075099,
            "C_D_received_sample_denominator": 0.9970414201183432,
            "inserted_samples": 6,
            "p_valid_90_sample_position": 0.9941370223978919,
            "confirmed_alert_events": 2,
            "trigger_timestamps": [
              773.494959853,
              907.374938594
            ],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              11946,
              3323
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 362,
            "reference_only": 629,
            "transformed_only": 649,
            "classifier_mae": 0.0,
            "reconstruction_mae": 0.0,
            "or_flips": 0,
            "or_agreement": 1.0,
            "caveat": "Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures."
          }
        },
        "hold_one_sample": {
          "summary": {
            "scored": 1011,
            "nominal_received_sample_positions": 1014,
            "nominal_elapsed_time_positions": 1014,
            "invalidations": 1,
            "V_T_scored_over_scored_plus_resets": 0.9990118577075099,
            "C_D_received_sample_denominator": 0.9970414201183432,
            "inserted_samples": 6,
            "p_valid_90_sample_position": 0.9941370223978919,
            "confirmed_alert_events": 2,
            "trigger_timestamps": [
              773.494959853,
              907.374938594
            ],
            "guard_threshold_s": 0.03,
            "run_lengths_samples": [
              11946,
              3323
            ]
          },
          "fidelity": {
            "matched_end_sample_windows": 362,
            "reference_only": 629,
            "transformed_only": 649,
            "classifier_mae": 0.0,
            "reconstruction_mae": 0.0,
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
