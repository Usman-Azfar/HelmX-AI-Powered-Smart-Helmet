
L6 — Front-end range and 16-bit emulation
Status: COMPLETE
UTC: 2026-09-29T19:26:06.151113+00:00
Evidence: piResults/final_pi_review_closure/model_L6
{
  "limitations": "Emulation on already-resampled 50-Hz raw sequences, before causal gravity removal. Not a high-frequency anti-alias or physical crash validation. Labels fixed from original reference, not recomputed after clipping. Scales match sensor sensitivity constants; no additional analog noise.",
  "ranges": {
    "current_2g_250dps": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5400,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 34,
          "n": 5437,
          "agreement": 0.9994482251241493
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 3,
          "n": 5294,
          "agreement": 1.0
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 109,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 31,
          "n": 143,
          "agreement": 0.9790209790209791
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5424,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 7,
          "ref_pos_to_trans_pos": 6,
          "n": 5437,
          "agreement": 0.9987125252896818
        },
        "normal": {
          "ref_neg_to_trans_neg": 5293,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 0,
          "n": 5294,
          "agreement": 0.999811106913487
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 131,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 6,
          "ref_pos_to_trans_pos": 6,
          "n": 143,
          "agreement": 0.958041958041958
        }
      },
      "or": {
        "overall": {
          "ref_neg_to_trans_neg": 5398,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 4,
          "ref_pos_to_trans_pos": 35,
          "n": 5437,
          "agreement": 0.9992643001655325
        },
        "normal": {
          "ref_neg_to_trans_neg": 5290,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 3,
          "n": 5294,
          "agreement": 0.999811106913487
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 108,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 32,
          "n": 143,
          "agreement": 0.9790209790209791
        }
      },
      "reference_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 108,
        "tp": 35,
        "precision": 0.8974358974358975,
        "recall": 0.24475524475524477,
        "f1": 0.38461538461538464
      },
      "transformed_metrics": {
        "tn": 5291,
        "fp": 3,
        "fn": 111,
        "tp": 32,
        "precision": 0.9142857142857143,
        "recall": 0.22377622377622378,
        "f1": 0.3595505617977528
      },
      "score_mae": {
        "classifier": 0.0034643990251977193,
        "reconstruction": 0.07007231391899196
      },
      "reference_events": {
        "carla_onder": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2. Aggressive": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2.Bump": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "near_fall_Acceleration On Curve": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            56,
            60,
            61,
            62,
            63,
            64,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            197,
            198,
            199
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_non_crash_Pothole_5_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "darus_non_crash_Randomstate_60_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        }
      },
      "transformed_events": {
        "carla_onder": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2. Aggressive": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2.Bump": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "near_fall_Acceleration On Curve": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            56,
            60,
            61,
            62,
            63,
            64,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            197,
            198,
            199
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            5
          ],
          "trigger_times_s": [
            2.6799999999999997
          ],
          "overlapping_three_positive_positions": [
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            5
          ],
          "trigger_times_s": [
            2.6799999999999997
          ],
          "overlapping_three_positive_positions": [
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            5
          ],
          "trigger_times_s": [
            2.6799999999999997
          ],
          "overlapping_three_positive_positions": [
            5
          ],
          "event_detected": true
        },
        "darus_non_crash_Pothole_5_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "darus_non_crash_Randomstate_60_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        }
      },
      "per_axis_clipped_samples": {
        "ax": 158,
        "ay": 45,
        "az": 151,
        "gx": 3840,
        "gy": 3950,
        "gz": 10042
      },
      "total_samples": 82125,
      "fraction_normal_windows_clipped": 0.26992822062712507,
      "fraction_crash_windows_clipped": 0.08391608391608392,
      "feature_change": {
        "accel_peak": {
          "mean_signed": -0.5239075422286987,
          "mean_absolute": 0.5242065191268921,
          "max_absolute": 299.1426086425781
        },
        "gyro_peak": {
          "mean_signed": -321.444580078125,
          "mean_absolute": 321.4458923339844,
          "max_absolute": 4277.2841796875
        },
        "runtime_jerk_peak": {
          "mean_signed": -0.5037294030189514,
          "mean_absolute": 0.5042412281036377,
          "max_absolute": 282.2527160644531
        }
      }
    },
    "wide_16g_2000dps": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5399,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 36,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 3,
          "n": 5294,
          "agreement": 1.0
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 108,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 33,
          "n": 143,
          "agreement": 0.986013986013986
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5424,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 1.0
        },
        "normal": {
          "ref_neg_to_trans_neg": 5293,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 1.0
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 131,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 12,
          "n": 143,
          "agreement": 1.0
        }
      },
      "or": {
        "overall": {
          "ref_neg_to_trans_neg": 5397,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 39,
          "n": 5437,
          "agreement": 0.9998160750413831
        },
        "normal": {
          "ref_neg_to_trans_neg": 5290,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 4,
          "n": 5294,
          "agreement": 1.0
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 107,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 35,
          "n": 143,
          "agreement": 0.993006993006993
        }
      },
      "reference_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 108,
        "tp": 35,
        "precision": 0.8974358974358975,
        "recall": 0.24475524475524477,
        "f1": 0.38461538461538464
      },
      "transformed_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 107,
        "tp": 36,
        "precision": 0.9,
        "recall": 0.2517482517482518,
        "f1": 0.39344262295081966
      },
      "score_mae": {
        "classifier": 0.002186264254184293,
        "reconstruction": 0.0024561428214689377
      },
      "reference_events": {
        "carla_onder": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2. Aggressive": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2.Bump": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "near_fall_Acceleration On Curve": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            56,
            60,
            61,
            62,
            63,
            64,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            197,
            198,
            199
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_non_crash_Pothole_5_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "darus_non_crash_Randomstate_60_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        }
      },
      "transformed_events": {
        "carla_onder": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2. Aggressive": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "road_2.Bump": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "near_fall_Acceleration On Curve": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            56,
            60,
            61,
            62,
            63,
            64,
            65,
            66
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            197,
            198,
            199
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            4
          ],
          "trigger_times_s": [
            2.38
          ],
          "overlapping_three_positive_positions": [
            4,
            5
          ],
          "event_detected": true
        },
        "darus_non_crash_Pothole_5_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "darus_non_crash_Randomstate_60_Out": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        }
      },
      "per_axis_clipped_samples": {
        "ax": 3,
        "ay": 0,
        "az": 73,
        "gx": 0,
        "gy": 19,
        "gz": 1552
      },
      "total_samples": 82125,
      "fraction_normal_windows_clipped": 0.07064601435587457,
      "fraction_crash_windows_clipped": 0.08391608391608392,
      "feature_change": {
        "accel_peak": {
          "mean_signed": -0.15360626578330994,
          "mean_absolute": 0.15562087297439575,
          "max_absolute": 129.9373779296875
        },
        "gyro_peak": {
          "mean_signed": -66.1971206665039,
          "mean_absolute": 66.21137237548828,
          "max_absolute": 2529.7548828125
        },
        "runtime_jerk_peak": {
          "mean_signed": -0.16591742634773254,
          "mean_absolute": 0.16872072219848633,
          "max_absolute": 146.79969787597656
        }
      }
    }
  }
}
