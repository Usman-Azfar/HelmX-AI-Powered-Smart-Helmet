
L5 — Frozen operating-point sensitivity
Status: COMPLETE
UTC: 2026-09-29T14:53:05.799032+00:00
Evidence: piResults/final_pi_review_closure/model_L5
{
  "classifier_prob_balanced": {
    "causal_float": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5405,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 6,
          "ref_pos_to_trans_pos": 25,
          "n": 5437,
          "agreement": 0.9987125252896818
        },
        "normal": {
          "ref_neg_to_trans_neg": 5292,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 0,
          "n": 5294,
          "agreement": 0.9996222138269739
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 113,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 4,
          "ref_pos_to_trans_pos": 25,
          "n": 143,
          "agreement": 0.965034965034965
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 5404,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 6,
          "ref_pos_to_trans_pos": 26,
          "n": 5437,
          "agreement": 0.9987125252896818
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 113,
          "ref_neg_to_trans_pos": 1,
          "ref_pos_to_trans_neg": 4,
          "ref_pos_to_trans_pos": 25,
          "n": 143,
          "agreement": 0.965034965034965
        }
      },
      "reference_metrics": {
        "tn": 5291,
        "fp": 3,
        "fn": 114,
        "tp": 29,
        "precision": 0.90625,
        "recall": 0.20279720279720279,
        "f1": 0.3314285714285714
      },
      "transformed_metrics": {
        "tn": 5293,
        "fp": 1,
        "fn": 117,
        "tp": 26,
        "precision": 0.9629629629629629,
        "recall": 0.18181818181818182,
        "f1": 0.3058823529411765
      },
      "score_mae": {
        "classifier": 0.024563182145357132,
        "reconstruction": 0.6006314754486084
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
            56
          ],
          "trigger_times_s": [
            17.98
          ],
          "overlapping_three_positive_positions": [
            56,
            61,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
            56
          ],
          "trigger_times_s": [
            17.98
          ],
          "overlapping_three_positive_positions": [
            56,
            61,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
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
      }
    },
    "offline_int8": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5402,
          "ref_neg_to_trans_pos": 4,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 29,
          "n": 5437,
          "agreement": 0.9988964502482987
        },
        "normal": {
          "ref_neg_to_trans_neg": 5292,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 2,
          "n": 5294,
          "agreement": 1.0
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 110,
          "ref_neg_to_trans_pos": 4,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 27,
          "n": 143,
          "agreement": 0.958041958041958
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 15,
          "n": 5437,
          "agreement": 1.0
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
          "ref_neg_to_trans_neg": 5401,
          "ref_neg_to_trans_pos": 4,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 30,
          "n": 5437,
          "agreement": 0.9988964502482987
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
          "ref_neg_to_trans_neg": 110,
          "ref_neg_to_trans_pos": 4,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 27,
          "n": 143,
          "agreement": 0.958041958041958
        }
      },
      "reference_metrics": {
        "tn": 5291,
        "fp": 3,
        "fn": 114,
        "tp": 29,
        "precision": 0.90625,
        "recall": 0.20279720279720279,
        "f1": 0.3314285714285714
      },
      "transformed_metrics": {
        "tn": 5291,
        "fp": 3,
        "fn": 112,
        "tp": 31,
        "precision": 0.9117647058823529,
        "recall": 0.21678321678321677,
        "f1": 0.3502824858757062
      },
      "score_mae": {
        "classifier": 0.0657939640444035,
        "reconstruction": 0.6117278392477276
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
            56
          ],
          "trigger_times_s": [
            17.98
          ],
          "overlapping_three_positive_positions": [
            56,
            61,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
            55
          ],
          "trigger_times_s": [
            17.68
          ],
          "overlapping_three_positive_positions": [
            55,
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
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
      }
    },
    "deployed": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5393,
          "ref_neg_to_trans_pos": 13,
          "ref_pos_to_trans_neg": 7,
          "ref_pos_to_trans_pos": 24,
          "n": 5437,
          "agreement": 0.9963215008276624
        },
        "normal": {
          "ref_neg_to_trans_neg": 5289,
          "ref_neg_to_trans_pos": 3,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 0,
          "n": 5294,
          "agreement": 0.9990555345674348
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 104,
          "ref_neg_to_trans_pos": 10,
          "ref_pos_to_trans_neg": 5,
          "ref_pos_to_trans_pos": 24,
          "n": 143,
          "agreement": 0.8951048951048951
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 5392,
          "ref_neg_to_trans_pos": 13,
          "ref_pos_to_trans_neg": 6,
          "ref_pos_to_trans_pos": 26,
          "n": 5437,
          "agreement": 0.9965054257862792
        },
        "normal": {
          "ref_neg_to_trans_neg": 5288,
          "ref_neg_to_trans_pos": 3,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9990555345674348
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 104,
          "ref_neg_to_trans_pos": 10,
          "ref_pos_to_trans_neg": 4,
          "ref_pos_to_trans_pos": 25,
          "n": 143,
          "agreement": 0.9020979020979021
        }
      },
      "reference_metrics": {
        "tn": 5291,
        "fp": 3,
        "fn": 114,
        "tp": 29,
        "precision": 0.90625,
        "recall": 0.20279720279720279,
        "f1": 0.3314285714285714
      },
      "transformed_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 108,
        "tp": 35,
        "precision": 0.8974358974358975,
        "recall": 0.24475524475524477,
        "f1": 0.38461538461538464
      },
      "score_mae": {
        "classifier": 0.0723699174272159,
        "reconstruction": 0.6273458136270349
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
            56
          ],
          "trigger_times_s": [
            17.98
          ],
          "overlapping_three_positive_positions": [
            56,
            61,
            65
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
      }
    }
  },
  "classifier_prob_moderate_recall": {
    "causal_float": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5386,
          "ref_neg_to_trans_pos": 11,
          "ref_pos_to_trans_neg": 7,
          "ref_pos_to_trans_pos": 33,
          "n": 5437,
          "agreement": 0.9966893507448961
        },
        "normal": {
          "ref_neg_to_trans_neg": 5288,
          "ref_neg_to_trans_pos": 3,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9990555345674348
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 98,
          "ref_neg_to_trans_pos": 8,
          "ref_pos_to_trans_neg": 5,
          "ref_pos_to_trans_pos": 32,
          "n": 143,
          "agreement": 0.9090909090909091
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 5385,
          "ref_neg_to_trans_pos": 11,
          "ref_pos_to_trans_neg": 7,
          "ref_pos_to_trans_pos": 34,
          "n": 5437,
          "agreement": 0.9966893507448961
        },
        "normal": {
          "ref_neg_to_trans_neg": 5287,
          "ref_neg_to_trans_pos": 3,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 2,
          "n": 5294,
          "agreement": 0.9990555345674348
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 98,
          "ref_neg_to_trans_pos": 8,
          "ref_pos_to_trans_neg": 5,
          "ref_pos_to_trans_pos": 32,
          "n": 143,
          "agreement": 0.9090909090909091
        }
      },
      "reference_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 106,
        "tp": 37,
        "precision": 0.9024390243902439,
        "recall": 0.25874125874125875,
        "f1": 0.40217391304347827
      },
      "transformed_metrics": {
        "tn": 5289,
        "fp": 5,
        "fn": 103,
        "tp": 40,
        "precision": 0.8888888888888888,
        "recall": 0.27972027972027974,
        "f1": 0.425531914893617
      },
      "score_mae": {
        "classifier": 0.024563182145357132,
        "reconstruction": 0.6006314754486084
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
            54
          ],
          "trigger_times_s": [
            17.38
          ],
          "overlapping_three_positive_positions": [
            54,
            55,
            56,
            57,
            58,
            59,
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
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112,
            113
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
            55,
            56,
            57,
            58,
            59,
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
            198
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
      }
    },
    "offline_int8": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5366,
          "ref_neg_to_trans_pos": 31,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 39,
          "n": 5437,
          "agreement": 0.9941144013242597
        },
        "normal": {
          "ref_neg_to_trans_neg": 5273,
          "ref_neg_to_trans_pos": 18,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 3,
          "n": 5294,
          "agreement": 0.9965999244427654
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 93,
          "ref_neg_to_trans_pos": 13,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 36,
          "n": 143,
          "agreement": 0.9020979020979021
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 15,
          "n": 5437,
          "agreement": 1.0
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
          "ref_neg_to_trans_neg": 5365,
          "ref_neg_to_trans_pos": 31,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 40,
          "n": 5437,
          "agreement": 0.9941144013242597
        },
        "normal": {
          "ref_neg_to_trans_neg": 5272,
          "ref_neg_to_trans_pos": 18,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 4,
          "n": 5294,
          "agreement": 0.9965999244427654
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 93,
          "ref_neg_to_trans_pos": 13,
          "ref_pos_to_trans_neg": 1,
          "ref_pos_to_trans_pos": 36,
          "n": 143,
          "agreement": 0.9020979020979021
        }
      },
      "reference_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 106,
        "tp": 37,
        "precision": 0.9024390243902439,
        "recall": 0.25874125874125875,
        "f1": 0.40217391304347827
      },
      "transformed_metrics": {
        "tn": 5272,
        "fp": 22,
        "fn": 94,
        "tp": 49,
        "precision": 0.6901408450704225,
        "recall": 0.34265734265734266,
        "f1": 0.45794392523364486
      },
      "score_mae": {
        "classifier": 0.0657939640444035,
        "reconstruction": 0.6117278392477276
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
            54
          ],
          "trigger_times_s": [
            17.38
          ],
          "overlapping_three_positive_positions": [
            54,
            55,
            56,
            57,
            58,
            59,
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
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112,
            113
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
          "trigger_indices": [
            739
          ],
          "trigger_times_s": [
            222.88
          ],
          "overlapping_three_positive_positions": [
            739
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [],
          "trigger_times_s": [],
          "overlapping_three_positive_positions": [],
          "event_detected": false
        },
        "near_fall_Acceleration On Curve": {
          "trigger_indices": [
            54
          ],
          "trigger_times_s": [
            17.38
          ],
          "overlapping_three_positive_positions": [
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            104
          ],
          "trigger_times_s": [
            32.38
          ],
          "overlapping_three_positive_positions": [
            104,
            105,
            111,
            112,
            113,
            114,
            115,
            116,
            117
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
      }
    },
    "deployed": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 5341,
          "ref_neg_to_trans_pos": 56,
          "ref_pos_to_trans_neg": 6,
          "ref_pos_to_trans_pos": 34,
          "n": 5437,
          "agreement": 0.9885966525657531
        },
        "normal": {
          "ref_neg_to_trans_neg": 5253,
          "ref_neg_to_trans_pos": 38,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9924442765394786
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 88,
          "ref_neg_to_trans_pos": 18,
          "ref_pos_to_trans_neg": 4,
          "ref_pos_to_trans_pos": 33,
          "n": 143,
          "agreement": 0.8461538461538461
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 5340,
          "ref_neg_to_trans_pos": 56,
          "ref_pos_to_trans_neg": 5,
          "ref_pos_to_trans_pos": 36,
          "n": 5437,
          "agreement": 0.9887805775243701
        },
        "normal": {
          "ref_neg_to_trans_neg": 5252,
          "ref_neg_to_trans_pos": 38,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 2,
          "n": 5294,
          "agreement": 0.9924442765394786
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 88,
          "ref_neg_to_trans_pos": 18,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 34,
          "n": 143,
          "agreement": 0.8531468531468531
        }
      },
      "reference_metrics": {
        "tn": 5290,
        "fp": 4,
        "fn": 106,
        "tp": 37,
        "precision": 0.9024390243902439,
        "recall": 0.25874125874125875,
        "f1": 0.40217391304347827
      },
      "transformed_metrics": {
        "tn": 5254,
        "fp": 40,
        "fn": 91,
        "tp": 52,
        "precision": 0.5652173913043478,
        "recall": 0.36363636363636365,
        "f1": 0.4425531914893617
      },
      "score_mae": {
        "classifier": 0.0723699174272159,
        "reconstruction": 0.6273458136270349
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
            54
          ],
          "trigger_times_s": [
            17.38
          ],
          "overlapping_three_positive_positions": [
            54,
            55,
            56,
            57,
            58,
            59,
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
            111
          ],
          "trigger_times_s": [
            34.48
          ],
          "overlapping_three_positive_positions": [
            111,
            112,
            113
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
          "trigger_indices": [
            585
          ],
          "trigger_times_s": [
            176.68
          ],
          "overlapping_three_positive_positions": [
            585,
            586
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            8
          ],
          "trigger_times_s": [
            3.58
          ],
          "overlapping_three_positive_positions": [
            8
          ],
          "event_detected": true
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
            3,
            48,
            54,
            55,
            56,
            57,
            58,
            59,
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
            112,
            149,
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
      }
    }
  },
  "classifier_prob_high_recall": {
    "causal_float": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 4648,
          "ref_neg_to_trans_pos": 125,
          "ref_pos_to_trans_neg": 67,
          "ref_pos_to_trans_pos": 597,
          "n": 5437,
          "agreement": 0.9646864079455583
        },
        "normal": {
          "ref_neg_to_trans_neg": 4624,
          "ref_neg_to_trans_pos": 117,
          "ref_pos_to_trans_neg": 64,
          "ref_pos_to_trans_pos": 489,
          "n": 5294,
          "agreement": 0.9658103513411409
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 24,
          "ref_neg_to_trans_pos": 8,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 108,
          "n": 143,
          "agreement": 0.9230769230769231
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 4647,
          "ref_neg_to_trans_pos": 125,
          "ref_pos_to_trans_neg": 67,
          "ref_pos_to_trans_pos": 598,
          "n": 5437,
          "agreement": 0.9646864079455583
        },
        "normal": {
          "ref_neg_to_trans_neg": 4623,
          "ref_neg_to_trans_pos": 117,
          "ref_pos_to_trans_neg": 64,
          "ref_pos_to_trans_pos": 490,
          "n": 5294,
          "agreement": 0.9658103513411409
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 24,
          "ref_neg_to_trans_pos": 8,
          "ref_pos_to_trans_neg": 3,
          "ref_pos_to_trans_pos": 108,
          "n": 143,
          "agreement": 0.9230769230769231
        }
      },
      "reference_metrics": {
        "tn": 4740,
        "fp": 554,
        "fn": 32,
        "tp": 111,
        "precision": 0.16691729323308271,
        "recall": 0.7762237762237763,
        "f1": 0.2747524752475248
      },
      "transformed_metrics": {
        "tn": 4687,
        "fp": 607,
        "fn": 27,
        "tp": 116,
        "precision": 0.16044260027662519,
        "recall": 0.8111888111888111,
        "f1": 0.2678983833718245
      },
      "score_mae": {
        "classifier": 0.024563182145357132,
        "reconstruction": 0.6006314754486084
      },
      "reference_events": {
        "carla_onder": {
          "trigger_indices": [
            921,
            2039,
            2609
          ],
          "trigger_times_s": [
            277.48,
            612.8799999999999,
            783.8799999999999
          ],
          "overlapping_three_positive_positions": [
            921,
            922,
            2039,
            2609,
            2610,
            2611
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            163,
            374,
            583,
            784,
            984,
            1193,
            2205
          ],
          "trigger_times_s": [
            50.08,
            113.38000000000001,
            176.08,
            236.38,
            296.38,
            359.08,
            662.68
          ],
          "overlapping_three_positive_positions": [
            163,
            164,
            165,
            166,
            167,
            172,
            173,
            193,
            194,
            195,
            300,
            301,
            302,
            310,
            311,
            312,
            322,
            323,
            328,
            329,
            340,
            341,
            342,
            374,
            375,
            376,
            377,
            394,
            395,
            396,
            397,
            398,
            441,
            470,
            471,
            472,
            473,
            474,
            488,
            489,
            490,
            491,
            492,
            521,
            522,
            583,
            584,
            585,
            586,
            587,
            613,
            614,
            621,
            622,
            623,
            624,
            630,
            631,
            632,
            633,
            634,
            635,
            645,
            646,
            658,
            659,
            660,
            669,
            670,
            689,
            690,
            691,
            692,
            693,
            694,
            695,
            696,
            697,
            698,
            699,
            710,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            744,
            745,
            746,
            755,
            756,
            757,
            758,
            768,
            769,
            781,
            782,
            783,
            784,
            785,
            786,
            787,
            788,
            789,
            790,
            795,
            796,
            807,
            808,
            812,
            813,
            854,
            855,
            856,
            862,
            863,
            868,
            869,
            908,
            909,
            910,
            911,
            912,
            913,
            946,
            947,
            948,
            962,
            963,
            964,
            975,
            976,
            977,
            978,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1021,
            1022,
            1023,
            1024,
            1025,
            1031,
            1032,
            1073,
            1074,
            1084,
            1092,
            1093,
            1094,
            1095,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1111,
            1112,
            1113,
            1114,
            1115,
            1116,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1133,
            1134,
            1135,
            1136,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1153,
            1165,
            1172,
            1173,
            1174,
            1193,
            1194,
            1195,
            1196,
            1197,
            1223,
            1224,
            1225,
            1232,
            1233,
            1234,
            1238,
            1239,
            2205,
            2224,
            2225,
            2226,
            2227,
            2228,
            2238,
            2239,
            2240,
            2241,
            2261,
            2262,
            2263,
            2264,
            2271,
            2272,
            2307,
            2308,
            2318,
            2319,
            2320,
            2321,
            2322,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            7
          ],
          "trigger_times_s": [
            3.2800000000000002
          ],
          "overlapping_three_positive_positions": [
            7,
            8,
            9,
            10
          ],
          "event_detected": true
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
            3,
            4,
            5,
            22,
            38,
            39,
            40,
            41,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            81,
            82,
            83,
            84,
            85,
            86,
            87,
            88,
            89,
            90,
            91,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            123,
            124
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
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            76,
            77,
            84,
            85,
            86,
            87,
            88,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            125,
            126,
            134,
            135,
            149,
            150,
            195,
            196,
            197,
            198
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
          "trigger_indices": [
            922,
            1559,
            2040,
            2422
          ],
          "trigger_times_s": [
            277.78,
            468.88,
            613.18,
            727.78
          ],
          "overlapping_three_positive_positions": [
            922,
            923,
            1559,
            1578,
            2040,
            2422,
            2586,
            2610,
            2611,
            2612
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            161,
            373,
            583,
            784,
            984,
            1193,
            2206
          ],
          "trigger_times_s": [
            49.48,
            113.08,
            176.08,
            236.38,
            296.38,
            359.08,
            662.9799999999999
          ],
          "overlapping_three_positive_positions": [
            161,
            162,
            163,
            164,
            165,
            166,
            171,
            172,
            173,
            181,
            193,
            194,
            195,
            272,
            307,
            308,
            312,
            322,
            323,
            328,
            329,
            342,
            357,
            373,
            374,
            375,
            376,
            377,
            394,
            395,
            396,
            397,
            398,
            441,
            442,
            470,
            471,
            472,
            473,
            474,
            487,
            488,
            489,
            490,
            491,
            492,
            493,
            521,
            522,
            527,
            528,
            529,
            530,
            531,
            532,
            533,
            534,
            535,
            536,
            560,
            561,
            583,
            584,
            585,
            586,
            587,
            588,
            613,
            614,
            621,
            622,
            623,
            624,
            630,
            631,
            632,
            633,
            634,
            639,
            640,
            641,
            645,
            646,
            656,
            657,
            658,
            659,
            660,
            670,
            688,
            694,
            695,
            696,
            697,
            698,
            699,
            710,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            755,
            756,
            757,
            758,
            767,
            768,
            769,
            781,
            782,
            783,
            784,
            785,
            786,
            787,
            788,
            789,
            790,
            805,
            806,
            807,
            808,
            812,
            813,
            814,
            846,
            854,
            855,
            856,
            861,
            862,
            863,
            869,
            884,
            885,
            900,
            906,
            907,
            908,
            909,
            910,
            911,
            912,
            913,
            927,
            941,
            942,
            943,
            944,
            945,
            946,
            947,
            948,
            963,
            964,
            965,
            966,
            967,
            975,
            976,
            980,
            981,
            982,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1021,
            1022,
            1029,
            1030,
            1031,
            1032,
            1033,
            1059,
            1060,
            1061,
            1073,
            1074,
            1093,
            1094,
            1095,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1111,
            1112,
            1113,
            1114,
            1115,
            1116,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1130,
            1131,
            1132,
            1133,
            1134,
            1135,
            1136,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1156,
            1157,
            1158,
            1165,
            1166,
            1172,
            1173,
            1174,
            1193,
            1194,
            1195,
            1221,
            1222,
            1223,
            1224,
            1225,
            1233,
            1234,
            1238,
            1239,
            2206,
            2219,
            2225,
            2226,
            2227,
            2228,
            2262,
            2263,
            2264,
            2265,
            2266,
            2267,
            2268,
            2269,
            2270,
            2271,
            2272,
            2273,
            2274,
            2289,
            2298,
            2299,
            2308,
            2309,
            2317,
            2318,
            2319,
            2320,
            2321,
            2322,
            2323,
            2324,
            2325,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332,
            2337
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            7
          ],
          "trigger_times_s": [
            3.2800000000000002
          ],
          "overlapping_three_positive_positions": [
            7,
            8,
            9,
            10
          ],
          "event_detected": true
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
            3,
            4,
            22,
            23,
            31,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            86,
            87,
            88,
            89,
            90,
            91,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            123
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2,
            203
          ],
          "trigger_times_s": [
            1.7799999999999998,
            62.08
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            77,
            86,
            87,
            88,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            125,
            126,
            134,
            135,
            136,
            137,
            138,
            139,
            140,
            141,
            149,
            150,
            195,
            196,
            197,
            198,
            199,
            200,
            201,
            202,
            203,
            204
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
      }
    },
    "offline_int8": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 4300,
          "ref_neg_to_trans_pos": 473,
          "ref_pos_to_trans_neg": 69,
          "ref_pos_to_trans_pos": 595,
          "n": 5437,
          "agreement": 0.9003126724296487
        },
        "normal": {
          "ref_neg_to_trans_neg": 4284,
          "ref_neg_to_trans_pos": 457,
          "ref_pos_to_trans_neg": 55,
          "ref_pos_to_trans_pos": 498,
          "n": 5294,
          "agreement": 0.9032867397053268
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 16,
          "ref_neg_to_trans_pos": 16,
          "ref_pos_to_trans_neg": 14,
          "ref_pos_to_trans_pos": 97,
          "n": 143,
          "agreement": 0.7902097902097902
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 0,
          "ref_pos_to_trans_pos": 15,
          "n": 5437,
          "agreement": 1.0
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
          "ref_neg_to_trans_neg": 4299,
          "ref_neg_to_trans_pos": 473,
          "ref_pos_to_trans_neg": 69,
          "ref_pos_to_trans_pos": 596,
          "n": 5437,
          "agreement": 0.9003126724296487
        },
        "normal": {
          "ref_neg_to_trans_neg": 4283,
          "ref_neg_to_trans_pos": 457,
          "ref_pos_to_trans_neg": 55,
          "ref_pos_to_trans_pos": 499,
          "n": 5294,
          "agreement": 0.9032867397053268
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 16,
          "ref_neg_to_trans_pos": 16,
          "ref_pos_to_trans_neg": 14,
          "ref_pos_to_trans_pos": 97,
          "n": 143,
          "agreement": 0.7902097902097902
        }
      },
      "reference_metrics": {
        "tn": 4740,
        "fp": 554,
        "fn": 32,
        "tp": 111,
        "precision": 0.16691729323308271,
        "recall": 0.7762237762237763,
        "f1": 0.2747524752475248
      },
      "transformed_metrics": {
        "tn": 4338,
        "fp": 956,
        "fn": 30,
        "tp": 113,
        "precision": 0.10570626753975679,
        "recall": 0.7902097902097902,
        "f1": 0.18646864686468648
      },
      "score_mae": {
        "classifier": 0.0657939640444035,
        "reconstruction": 0.6117278392477276
      },
      "reference_events": {
        "carla_onder": {
          "trigger_indices": [
            921,
            2039,
            2609
          ],
          "trigger_times_s": [
            277.48,
            612.8799999999999,
            783.8799999999999
          ],
          "overlapping_three_positive_positions": [
            921,
            922,
            2039,
            2609,
            2610,
            2611
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            163,
            374,
            583,
            784,
            984,
            1193,
            2205
          ],
          "trigger_times_s": [
            50.08,
            113.38000000000001,
            176.08,
            236.38,
            296.38,
            359.08,
            662.68
          ],
          "overlapping_three_positive_positions": [
            163,
            164,
            165,
            166,
            167,
            172,
            173,
            193,
            194,
            195,
            300,
            301,
            302,
            310,
            311,
            312,
            322,
            323,
            328,
            329,
            340,
            341,
            342,
            374,
            375,
            376,
            377,
            394,
            395,
            396,
            397,
            398,
            441,
            470,
            471,
            472,
            473,
            474,
            488,
            489,
            490,
            491,
            492,
            521,
            522,
            583,
            584,
            585,
            586,
            587,
            613,
            614,
            621,
            622,
            623,
            624,
            630,
            631,
            632,
            633,
            634,
            635,
            645,
            646,
            658,
            659,
            660,
            669,
            670,
            689,
            690,
            691,
            692,
            693,
            694,
            695,
            696,
            697,
            698,
            699,
            710,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            744,
            745,
            746,
            755,
            756,
            757,
            758,
            768,
            769,
            781,
            782,
            783,
            784,
            785,
            786,
            787,
            788,
            789,
            790,
            795,
            796,
            807,
            808,
            812,
            813,
            854,
            855,
            856,
            862,
            863,
            868,
            869,
            908,
            909,
            910,
            911,
            912,
            913,
            946,
            947,
            948,
            962,
            963,
            964,
            975,
            976,
            977,
            978,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1021,
            1022,
            1023,
            1024,
            1025,
            1031,
            1032,
            1073,
            1074,
            1084,
            1092,
            1093,
            1094,
            1095,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1111,
            1112,
            1113,
            1114,
            1115,
            1116,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1133,
            1134,
            1135,
            1136,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1153,
            1165,
            1172,
            1173,
            1174,
            1193,
            1194,
            1195,
            1196,
            1197,
            1223,
            1224,
            1225,
            1232,
            1233,
            1234,
            1238,
            1239,
            2205,
            2224,
            2225,
            2226,
            2227,
            2228,
            2238,
            2239,
            2240,
            2241,
            2261,
            2262,
            2263,
            2264,
            2271,
            2272,
            2307,
            2308,
            2318,
            2319,
            2320,
            2321,
            2322,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            7
          ],
          "trigger_times_s": [
            3.2800000000000002
          ],
          "overlapping_three_positive_positions": [
            7,
            8,
            9,
            10
          ],
          "event_detected": true
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
            3,
            4,
            5,
            22,
            38,
            39,
            40,
            41,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            81,
            82,
            83,
            84,
            85,
            86,
            87,
            88,
            89,
            90,
            91,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            123,
            124
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
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            76,
            77,
            84,
            85,
            86,
            87,
            88,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            125,
            126,
            134,
            135,
            149,
            150,
            195,
            196,
            197,
            198
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
          "trigger_indices": [
            921,
            2609
          ],
          "trigger_times_s": [
            277.48,
            783.8799999999999
          ],
          "overlapping_three_positive_positions": [
            921,
            922,
            2609,
            2610,
            2611
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            161,
            361,
            581,
            781,
            982,
            1182,
            2205
          ],
          "trigger_times_s": [
            49.48,
            109.48,
            175.48,
            235.48,
            295.78,
            355.78,
            662.68
          ],
          "overlapping_three_positive_positions": [
            161,
            162,
            163,
            164,
            165,
            166,
            167,
            172,
            173,
            174,
            175,
            176,
            177,
            178,
            179,
            180,
            181,
            182,
            183,
            193,
            194,
            195,
            196,
            207,
            211,
            223,
            224,
            225,
            235,
            246,
            247,
            248,
            256,
            257,
            265,
            266,
            267,
            268,
            269,
            270,
            271,
            272,
            273,
            274,
            291,
            292,
            293,
            294,
            295,
            301,
            310,
            311,
            312,
            317,
            318,
            322,
            323,
            324,
            325,
            326,
            327,
            328,
            329,
            334,
            335,
            336,
            343,
            344,
            345,
            346,
            347,
            354,
            355,
            356,
            357,
            358,
            359,
            360,
            361,
            362,
            363,
            364,
            373,
            374,
            375,
            376,
            377,
            378,
            379,
            380,
            381,
            391,
            392,
            393,
            394,
            395,
            396,
            397,
            398,
            399,
            400,
            419,
            431,
            440,
            441,
            442,
            446,
            462,
            463,
            464,
            465,
            472,
            473,
            474,
            475,
            476,
            477,
            478,
            479,
            480,
            481,
            482,
            488,
            489,
            490,
            491,
            492,
            493,
            504,
            505,
            506,
            507,
            511,
            520,
            521,
            522,
            526,
            527,
            528,
            529,
            530,
            531,
            532,
            536,
            537,
            544,
            545,
            550,
            558,
            559,
            581,
            582,
            583,
            584,
            585,
            586,
            587,
            588,
            589,
            590,
            591,
            599,
            607,
            608,
            609,
            613,
            614,
            621,
            622,
            623,
            624,
            630,
            631,
            632,
            633,
            634,
            635,
            636,
            637,
            638,
            639,
            640,
            641,
            642,
            643,
            644,
            645,
            654,
            655,
            656,
            657,
            658,
            659,
            660,
            668,
            669,
            670,
            674,
            675,
            676,
            677,
            678,
            679,
            685,
            686,
            687,
            688,
            694,
            695,
            696,
            697,
            698,
            699,
            707,
            711,
            712,
            713,
            717,
            718,
            719,
            720,
            721,
            728,
            729,
            730,
            731,
            732,
            733,
            734,
            735,
            736,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            744,
            745,
            746,
            755,
            756,
            757,
            758,
            759,
            760,
            761,
            762,
            763,
            764,
            765,
            766,
            767,
            768,
            769,
            776,
            777,
            778,
            779,
            780,
            781,
            782,
            783,
            787,
            788,
            789,
            790,
            791,
            792,
            793,
            794,
            795,
            796,
            797,
            803,
            804,
            805,
            806,
            807,
            808,
            809,
            810,
            811,
            812,
            813,
            814,
            815,
            816,
            817,
            818,
            819,
            825,
            829,
            830,
            831,
            832,
            833,
            834,
            835,
            836,
            837,
            838,
            839,
            840,
            841,
            842,
            843,
            844,
            845,
            846,
            847,
            848,
            849,
            850,
            851,
            852,
            853,
            854,
            855,
            856,
            860,
            861,
            862,
            863,
            864,
            865,
            866,
            867,
            868,
            869,
            870,
            871,
            872,
            873,
            874,
            875,
            876,
            877,
            878,
            884,
            888,
            889,
            890,
            905,
            906,
            907,
            908,
            909,
            910,
            911,
            912,
            913,
            914,
            915,
            916,
            917,
            918,
            919,
            920,
            921,
            922,
            923,
            943,
            944,
            945,
            946,
            947,
            948,
            949,
            950,
            951,
            952,
            953,
            957,
            958,
            959,
            960,
            961,
            962,
            963,
            964,
            975,
            976,
            982,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1000,
            1007,
            1021,
            1022,
            1023,
            1024,
            1025,
            1026,
            1027,
            1028,
            1029,
            1030,
            1031,
            1032,
            1033,
            1034,
            1035,
            1036,
            1037,
            1038,
            1039,
            1044,
            1045,
            1046,
            1059,
            1060,
            1061,
            1062,
            1063,
            1072,
            1073,
            1074,
            1075,
            1076,
            1081,
            1082,
            1083,
            1084,
            1085,
            1086,
            1087,
            1088,
            1089,
            1090,
            1091,
            1092,
            1093,
            1094,
            1095,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1108,
            1109,
            1110,
            1111,
            1112,
            1113,
            1114,
            1115,
            1116,
            1117,
            1118,
            1119,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1130,
            1131,
            1132,
            1133,
            1134,
            1135,
            1136,
            1137,
            1138,
            1139,
            1140,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1153,
            1154,
            1155,
            1156,
            1157,
            1158,
            1164,
            1165,
            1166,
            1167,
            1168,
            1172,
            1173,
            1174,
            1175,
            1176,
            1177,
            1178,
            1179,
            1180,
            1181,
            1182,
            1183,
            1184,
            1188,
            1192,
            1193,
            1194,
            1195,
            1196,
            1197,
            1198,
            1199,
            1200,
            1201,
            1202,
            1203,
            1204,
            1205,
            1206,
            1217,
            1218,
            1219,
            1220,
            1221,
            1222,
            1223,
            1224,
            1225,
            1226,
            1227,
            1232,
            1233,
            1234,
            1235,
            1236,
            1237,
            1238,
            1239,
            2205,
            2206,
            2207,
            2208,
            2209,
            2210,
            2211,
            2212,
            2213,
            2214,
            2215,
            2216,
            2217,
            2221,
            2222,
            2223,
            2224,
            2225,
            2226,
            2227,
            2228,
            2237,
            2238,
            2239,
            2240,
            2241,
            2256,
            2257,
            2258,
            2262,
            2263,
            2264,
            2271,
            2272,
            2273,
            2274,
            2275,
            2286,
            2287,
            2288,
            2289,
            2296,
            2297,
            2298,
            2299,
            2300,
            2301,
            2306,
            2307,
            2308,
            2309,
            2318,
            2319,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332,
            2333,
            2334,
            2335,
            2336,
            2337,
            2338,
            2354
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            7
          ],
          "trigger_times_s": [
            3.2800000000000002
          ],
          "overlapping_three_positive_positions": [
            7,
            8,
            9,
            10,
            11,
            12
          ],
          "event_detected": true
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
            3,
            4,
            5,
            6,
            39,
            40,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            86,
            87,
            88,
            89,
            90,
            91,
            101,
            102,
            103,
            109
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            58
          ],
          "trigger_times_s": [
            18.58
          ],
          "overlapping_three_positive_positions": [
            58,
            59,
            85,
            86,
            87,
            88,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            119,
            120,
            121,
            122,
            123,
            124,
            125,
            126,
            127,
            128,
            129,
            133,
            134,
            135,
            136,
            137,
            141,
            142,
            195,
            196,
            197,
            198
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            3
          ],
          "trigger_times_s": [
            2.08
          ],
          "overlapping_three_positive_positions": [
            3,
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
      }
    },
    "deployed": {
      "classifier": {
        "overall": {
          "ref_neg_to_trans_neg": 4282,
          "ref_neg_to_trans_pos": 491,
          "ref_pos_to_trans_neg": 93,
          "ref_pos_to_trans_pos": 571,
          "n": 5437,
          "agreement": 0.8925878241677395
        },
        "normal": {
          "ref_neg_to_trans_neg": 4271,
          "ref_neg_to_trans_pos": 470,
          "ref_pos_to_trans_neg": 79,
          "ref_pos_to_trans_pos": 474,
          "n": 5294,
          "agreement": 0.8962976955043446
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 11,
          "ref_neg_to_trans_pos": 21,
          "ref_pos_to_trans_neg": 14,
          "ref_pos_to_trans_pos": 97,
          "n": 143,
          "agreement": 0.7552447552447552
        }
      },
      "reconstruction": {
        "overall": {
          "ref_neg_to_trans_neg": 5422,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 13,
          "n": 5437,
          "agreement": 0.9996321500827662
        },
        "normal": {
          "ref_neg_to_trans_neg": 5291,
          "ref_neg_to_trans_pos": 0,
          "ref_pos_to_trans_neg": 2,
          "ref_pos_to_trans_pos": 1,
          "n": 5294,
          "agreement": 0.9996222138269739
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
          "ref_neg_to_trans_neg": 4281,
          "ref_neg_to_trans_pos": 491,
          "ref_pos_to_trans_neg": 92,
          "ref_pos_to_trans_pos": 573,
          "n": 5437,
          "agreement": 0.8927717491263565
        },
        "normal": {
          "ref_neg_to_trans_neg": 4270,
          "ref_neg_to_trans_pos": 470,
          "ref_pos_to_trans_neg": 79,
          "ref_pos_to_trans_pos": 475,
          "n": 5294,
          "agreement": 0.8962976955043446
        },
        "crash_like": {
          "ref_neg_to_trans_neg": 11,
          "ref_neg_to_trans_pos": 21,
          "ref_pos_to_trans_neg": 13,
          "ref_pos_to_trans_pos": 98,
          "n": 143,
          "agreement": 0.7622377622377622
        }
      },
      "reference_metrics": {
        "tn": 4740,
        "fp": 554,
        "fn": 32,
        "tp": 111,
        "precision": 0.16691729323308271,
        "recall": 0.7762237762237763,
        "f1": 0.2747524752475248
      },
      "transformed_metrics": {
        "tn": 4349,
        "fp": 945,
        "fn": 24,
        "tp": 119,
        "precision": 0.1118421052631579,
        "recall": 0.8321678321678322,
        "f1": 0.19718309859154928
      },
      "score_mae": {
        "classifier": 0.0723699174272159,
        "reconstruction": 0.6273458136270349
      },
      "reference_events": {
        "carla_onder": {
          "trigger_indices": [
            921,
            2039,
            2609
          ],
          "trigger_times_s": [
            277.48,
            612.8799999999999,
            783.8799999999999
          ],
          "overlapping_three_positive_positions": [
            921,
            922,
            2039,
            2609,
            2610,
            2611
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            163,
            374,
            583,
            784,
            984,
            1193,
            2205
          ],
          "trigger_times_s": [
            50.08,
            113.38000000000001,
            176.08,
            236.38,
            296.38,
            359.08,
            662.68
          ],
          "overlapping_three_positive_positions": [
            163,
            164,
            165,
            166,
            167,
            172,
            173,
            193,
            194,
            195,
            300,
            301,
            302,
            310,
            311,
            312,
            322,
            323,
            328,
            329,
            340,
            341,
            342,
            374,
            375,
            376,
            377,
            394,
            395,
            396,
            397,
            398,
            441,
            470,
            471,
            472,
            473,
            474,
            488,
            489,
            490,
            491,
            492,
            521,
            522,
            583,
            584,
            585,
            586,
            587,
            613,
            614,
            621,
            622,
            623,
            624,
            630,
            631,
            632,
            633,
            634,
            635,
            645,
            646,
            658,
            659,
            660,
            669,
            670,
            689,
            690,
            691,
            692,
            693,
            694,
            695,
            696,
            697,
            698,
            699,
            710,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            744,
            745,
            746,
            755,
            756,
            757,
            758,
            768,
            769,
            781,
            782,
            783,
            784,
            785,
            786,
            787,
            788,
            789,
            790,
            795,
            796,
            807,
            808,
            812,
            813,
            854,
            855,
            856,
            862,
            863,
            868,
            869,
            908,
            909,
            910,
            911,
            912,
            913,
            946,
            947,
            948,
            962,
            963,
            964,
            975,
            976,
            977,
            978,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1021,
            1022,
            1023,
            1024,
            1025,
            1031,
            1032,
            1073,
            1074,
            1084,
            1092,
            1093,
            1094,
            1095,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1111,
            1112,
            1113,
            1114,
            1115,
            1116,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1133,
            1134,
            1135,
            1136,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1153,
            1165,
            1172,
            1173,
            1174,
            1193,
            1194,
            1195,
            1196,
            1197,
            1223,
            1224,
            1225,
            1232,
            1233,
            1234,
            1238,
            1239,
            2205,
            2224,
            2225,
            2226,
            2227,
            2228,
            2238,
            2239,
            2240,
            2241,
            2261,
            2262,
            2263,
            2264,
            2271,
            2272,
            2307,
            2308,
            2318,
            2319,
            2320,
            2321,
            2322,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            7
          ],
          "trigger_times_s": [
            3.2800000000000002
          ],
          "overlapping_three_positive_positions": [
            7,
            8,
            9,
            10
          ],
          "event_detected": true
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
            3,
            4,
            5,
            22,
            38,
            39,
            40,
            41,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            81,
            82,
            83,
            84,
            85,
            86,
            87,
            88,
            89,
            90,
            91,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            123,
            124
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
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            76,
            77,
            84,
            85,
            86,
            87,
            88,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            125,
            126,
            134,
            135,
            149,
            150,
            195,
            196,
            197,
            198
          ],
          "event_detected": true
        },
        "darus_crash_Iso_115_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_312_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            4,
            5
          ],
          "event_detected": true
        },
        "darus_crash_Iso_513_2_Out": {
          "trigger_indices": [
            2
          ],
          "trigger_times_s": [
            1.7799999999999998
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
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
          "trigger_indices": [
            922,
            1578,
            2423
          ],
          "trigger_times_s": [
            277.78,
            474.58,
            728.0799999999999
          ],
          "overlapping_three_positive_positions": [
            922,
            923,
            924,
            1578,
            2423,
            2586,
            2610,
            2611,
            2612
          ],
          "event_detected": true
        },
        "road_2. Aggressive": {
          "trigger_indices": [
            160,
            360,
            560,
            760,
            960,
            1164,
            2207
          ],
          "trigger_times_s": [
            49.18,
            109.18,
            169.18,
            229.18,
            289.18,
            350.38,
            663.28
          ],
          "overlapping_three_positive_positions": [
            160,
            161,
            162,
            163,
            164,
            165,
            166,
            167,
            171,
            172,
            173,
            174,
            175,
            176,
            180,
            181,
            182,
            183,
            184,
            185,
            193,
            194,
            195,
            196,
            202,
            203,
            207,
            211,
            212,
            213,
            223,
            224,
            225,
            226,
            234,
            235,
            248,
            256,
            257,
            258,
            271,
            272,
            273,
            274,
            275,
            276,
            290,
            291,
            292,
            309,
            310,
            311,
            312,
            322,
            323,
            324,
            325,
            326,
            327,
            328,
            329,
            335,
            336,
            337,
            338,
            339,
            340,
            341,
            342,
            343,
            344,
            345,
            346,
            347,
            348,
            349,
            350,
            354,
            355,
            356,
            357,
            358,
            359,
            360,
            365,
            366,
            367,
            368,
            369,
            370,
            371,
            372,
            373,
            374,
            375,
            376,
            377,
            378,
            379,
            393,
            394,
            395,
            396,
            397,
            398,
            399,
            400,
            401,
            440,
            441,
            442,
            446,
            447,
            461,
            462,
            463,
            464,
            471,
            472,
            473,
            474,
            475,
            476,
            477,
            478,
            479,
            480,
            488,
            489,
            490,
            491,
            492,
            493,
            499,
            500,
            504,
            505,
            526,
            527,
            528,
            529,
            530,
            531,
            532,
            533,
            534,
            535,
            536,
            537,
            538,
            544,
            545,
            558,
            559,
            560,
            561,
            570,
            575,
            576,
            577,
            578,
            579,
            580,
            581,
            582,
            583,
            584,
            585,
            586,
            587,
            588,
            589,
            590,
            591,
            592,
            593,
            594,
            599,
            621,
            622,
            632,
            633,
            634,
            635,
            636,
            637,
            638,
            639,
            640,
            644,
            645,
            646,
            647,
            654,
            655,
            656,
            657,
            658,
            659,
            660,
            668,
            669,
            670,
            671,
            672,
            676,
            677,
            678,
            679,
            687,
            688,
            696,
            697,
            698,
            699,
            705,
            706,
            707,
            708,
            709,
            710,
            716,
            717,
            718,
            719,
            728,
            729,
            730,
            731,
            732,
            733,
            734,
            735,
            736,
            737,
            738,
            739,
            740,
            741,
            742,
            743,
            744,
            745,
            746,
            747,
            748,
            753,
            754,
            755,
            756,
            757,
            758,
            759,
            760,
            766,
            767,
            768,
            769,
            777,
            778,
            779,
            780,
            781,
            782,
            783,
            787,
            788,
            789,
            790,
            791,
            792,
            793,
            794,
            795,
            796,
            797,
            798,
            799,
            800,
            801,
            802,
            803,
            804,
            805,
            806,
            807,
            808,
            809,
            810,
            811,
            812,
            813,
            814,
            815,
            816,
            817,
            833,
            834,
            840,
            841,
            842,
            843,
            844,
            845,
            846,
            847,
            852,
            853,
            854,
            855,
            856,
            857,
            858,
            859,
            860,
            861,
            862,
            863,
            864,
            865,
            866,
            867,
            868,
            869,
            870,
            882,
            883,
            884,
            885,
            886,
            887,
            888,
            889,
            890,
            901,
            902,
            903,
            904,
            905,
            906,
            907,
            908,
            909,
            910,
            911,
            912,
            913,
            914,
            919,
            920,
            921,
            922,
            927,
            928,
            935,
            936,
            937,
            938,
            939,
            940,
            941,
            942,
            943,
            944,
            945,
            946,
            947,
            948,
            949,
            950,
            951,
            952,
            953,
            954,
            955,
            956,
            957,
            958,
            959,
            960,
            961,
            962,
            963,
            964,
            965,
            966,
            967,
            968,
            969,
            970,
            971,
            972,
            973,
            974,
            975,
            976,
            980,
            981,
            982,
            983,
            984,
            985,
            986,
            987,
            988,
            989,
            990,
            991,
            992,
            993,
            994,
            995,
            996,
            997,
            998,
            999,
            1000,
            1004,
            1005,
            1006,
            1007,
            1008,
            1009,
            1010,
            1011,
            1012,
            1016,
            1017,
            1018,
            1019,
            1020,
            1021,
            1022,
            1023,
            1029,
            1030,
            1031,
            1032,
            1033,
            1034,
            1035,
            1036,
            1037,
            1038,
            1039,
            1040,
            1053,
            1059,
            1060,
            1061,
            1062,
            1063,
            1064,
            1065,
            1066,
            1067,
            1068,
            1069,
            1070,
            1071,
            1072,
            1073,
            1074,
            1075,
            1076,
            1077,
            1078,
            1079,
            1080,
            1081,
            1082,
            1092,
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            1102,
            1103,
            1104,
            1105,
            1106,
            1107,
            1111,
            1112,
            1113,
            1114,
            1115,
            1120,
            1121,
            1122,
            1123,
            1124,
            1125,
            1126,
            1127,
            1128,
            1129,
            1130,
            1131,
            1132,
            1133,
            1134,
            1135,
            1136,
            1137,
            1138,
            1139,
            1140,
            1141,
            1142,
            1143,
            1144,
            1145,
            1146,
            1147,
            1148,
            1149,
            1150,
            1151,
            1152,
            1153,
            1154,
            1155,
            1156,
            1157,
            1158,
            1164,
            1165,
            1166,
            1172,
            1173,
            1174,
            1175,
            1176,
            1177,
            1178,
            1179,
            1180,
            1192,
            1193,
            1194,
            1195,
            1196,
            1197,
            1198,
            1199,
            1200,
            1219,
            1220,
            1221,
            1222,
            1223,
            1224,
            1225,
            1226,
            1227,
            1228,
            1232,
            1233,
            1234,
            1235,
            1236,
            1237,
            1238,
            1239,
            2207,
            2208,
            2214,
            2218,
            2219,
            2223,
            2224,
            2225,
            2226,
            2227,
            2228,
            2229,
            2230,
            2237,
            2262,
            2263,
            2264,
            2265,
            2266,
            2267,
            2268,
            2269,
            2270,
            2271,
            2272,
            2273,
            2274,
            2275,
            2286,
            2287,
            2288,
            2289,
            2290,
            2298,
            2299,
            2300,
            2305,
            2306,
            2307,
            2308,
            2309,
            2317,
            2318,
            2319,
            2320,
            2321,
            2322,
            2323,
            2324,
            2325,
            2326,
            2327,
            2328,
            2329,
            2330,
            2331,
            2332,
            2333,
            2344,
            2345
          ],
          "event_detected": true
        },
        "road_2.Bump": {
          "trigger_indices": [
            6
          ],
          "trigger_times_s": [
            2.9799999999999995
          ],
          "overlapping_three_positive_positions": [
            6,
            7,
            8,
            9,
            10
          ],
          "event_detected": true
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
            3,
            4,
            31,
            32,
            33,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            81,
            93,
            103,
            109
          ],
          "event_detected": true
        },
        "fall_fall-in-a-leaning": {
          "trigger_indices": [
            2,
            203
          ],
          "trigger_times_s": [
            1.7799999999999998,
            62.08
          ],
          "overlapping_three_positive_positions": [
            2,
            3,
            58,
            59,
            63,
            87,
            88,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            119,
            120,
            121,
            122,
            123,
            124,
            125,
            126,
            127,
            128,
            129,
            130,
            131,
            132,
            133,
            134,
            135,
            136,
            137,
            138,
            139,
            140,
            141,
            142,
            148,
            149,
            196,
            197,
            198,
            199,
            200,
            201,
            202,
            203,
            204,
            205
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
      }
    }
  }
}
