
L2 — L2 fidelity
Status: COMPLETE
UTC: 2026-09-29T14:52:41.375515+00:00
Evidence: piResults/final_pi_review_closure/model_L2
{
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
  },
  "method": "Isolated causal EMA vs zero-phase Butterworth; SAME Keras model and training-side feature formula. Not the confounded historical replay.",
  "auxiliary_mismatch": "Training jerk is abs(gradient(accel magnitude, seconds)); runtime jerk is max(abs(diff(accel magnitude))) without dt division. L1 includes this implementation difference; L2 isolates filter by holding formula fixed.",
  "alignment": [
    {
      "session": "carla_onder",
      "samples": 39268,
      "reference_windows": 2614,
      "live_windows_if_all_samples_scored": 2614,
      "unmatched_live_tail_windows": 0
    },
    {
      "session": "road_2. Aggressive",
      "samples": 35375,
      "reference_windows": 2355,
      "live_windows_if_all_samples_scored": 2355,
      "unmatched_live_tail_windows": 0
    },
    {
      "session": "road_2.Bump",
      "samples": 251,
      "reference_windows": 13,
      "live_windows_if_all_samples_scored": 13,
      "unmatched_live_tail_windows": 0
    },
    {
      "session": "near_fall_Acceleration On Curve",
      "samples": 2397,
      "reference_windows": 156,
      "live_windows_if_all_samples_scored": 156,
      "unmatched_live_tail_windows": 0
    },
    {
      "session": "fall_fall-in-a-leaning",
      "samples": 4084,
      "reference_windows": 269,
      "live_windows_if_all_samples_scored": 269,
      "unmatched_live_tail_windows": 0
    },
    {
      "session": "darus_crash_Iso_115_Out",
      "samples": 150,
      "reference_windows": 6,
      "live_windows_if_all_samples_scored": 7,
      "unmatched_live_tail_windows": 1
    },
    {
      "session": "darus_crash_Iso_312_2_Out",
      "samples": 150,
      "reference_windows": 6,
      "live_windows_if_all_samples_scored": 7,
      "unmatched_live_tail_windows": 1
    },
    {
      "session": "darus_crash_Iso_513_2_Out",
      "samples": 150,
      "reference_windows": 6,
      "live_windows_if_all_samples_scored": 7,
      "unmatched_live_tail_windows": 1
    },
    {
      "session": "darus_non_crash_Pothole_5_Out",
      "samples": 150,
      "reference_windows": 6,
      "live_windows_if_all_samples_scored": 7,
      "unmatched_live_tail_windows": 1
    },
    {
      "session": "darus_non_crash_Randomstate_60_Out",
      "samples": 150,
      "reference_windows": 6,
      "live_windows_if_all_samples_scored": 7,
      "unmatched_live_tail_windows": 1
    }
  ],
  "policy_note": "Three consecutive positive scored windows, cooldown 60 s, nominal 50-Hz replay. No SMS/countdown blocking simulated. No hardware deadline claim.",
  "branch_counts": {
    "reference": {
      "classifier_only": 17,
      "reconstruction_only": 1,
      "both": 14,
      "neither": 5405
    },
    "transformed": {
      "classifier_only": 14,
      "reconstruction_only": 1,
      "both": 12,
      "neither": 5410
    }
  }
}
