
L10 — Auxiliary-feature replay ablation
Status: COMPLETE (INFERENCE-TIME DIAGNOSTIC)
UTC: 2026-10-02T15:03:50.881082+00:00
Evidence: piResults/final_pi_review_closure/model_L10
{
  "classifier": {
    "overall": {
      "ref_neg_to_trans_neg": 5406,
      "ref_neg_to_trans_pos": 0,
      "ref_pos_to_trans_neg": 8,
      "ref_pos_to_trans_pos": 23,
      "n": 5437,
      "agreement": 0.9985286003310649
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
      "ref_neg_to_trans_neg": 114,
      "ref_neg_to_trans_pos": 0,
      "ref_pos_to_trans_neg": 8,
      "ref_pos_to_trans_pos": 21,
      "n": 143,
      "agreement": 0.9440559440559441
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
      "ref_neg_to_trans_neg": 5405,
      "ref_neg_to_trans_pos": 0,
      "ref_pos_to_trans_neg": 7,
      "ref_pos_to_trans_pos": 25,
      "n": 5437,
      "agreement": 0.9987125252896818
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
      "ref_neg_to_trans_neg": 114,
      "ref_neg_to_trans_pos": 0,
      "ref_pos_to_trans_neg": 7,
      "ref_pos_to_trans_pos": 22,
      "n": 143,
      "agreement": 0.951048951048951
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
    "fn": 121,
    "tp": 22,
    "precision": 0.88,
    "recall": 0.15384615384615385,
    "f1": 0.2619047619047619
  },
  "score_mae": {
    "classifier": 0.04330364242196083,
    "reconstruction": 0.0
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
        65
      ],
      "trigger_times_s": [
        20.68
      ],
      "overlapping_three_positive_positions": [
        65
      ],
      "event_detected": true
    },
    "fall_fall-in-a-leaning": {
      "trigger_indices": [
        112
      ],
      "trigger_times_s": [
        34.78
      ],
      "overlapping_three_positive_positions": [
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
  "method": "Replay fixed model with the seven normalized auxiliary inputs set to zero (training-normal means in physical feature space), versus original full inputs. Temporal tensor and all weights unchanged.",
  "classifier_average_precision": {
    "full_inputs": 0.5401924816430507,
    "neutralized_aux": 0.5608853428372305
  },
  "limitation": "Inference-time feature ablation only. This is NOT an independently trained temporal-only architecture; out-of-distribution feature neutralization can affect predictions. It does not establish the incremental benefit of training with auxiliary scalars."
}
