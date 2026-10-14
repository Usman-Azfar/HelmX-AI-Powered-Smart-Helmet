
L4 — Session-clustered uncertainty
Status: COMPLETE
UTC: 2026-09-29T14:53:01.593313+00:00
Evidence: piResults/final_pi_review_closure/model_L4
{
  "n_sessions": 10,
  "replicates": 2000,
  "seed": 20260929,
  "method": "Whole-session percentile bootstrap, with replacement. Undefined crash-free draws excluded and counted. Window metrics, NOT real-road rates.",
  "intervals": {
    "causal_crash_agreement": {
      "p2_5": 0.9402390438247012,
      "p97_5": 1.0,
      "undefined_draws": 4
    },
    "int8_crash_agreement": {
      "p2_5": 0.9056603773584906,
      "p97_5": 1.0,
      "undefined_draws": 4
    },
    "composed_overall_agreement": {
      "p2_5": 0.9577167019027484,
      "p97_5": 0.9997284822155851,
      "undefined_draws": 0
    },
    "precision": {
      "p2_5": 0.7272727272727273,
      "p97_5": 0.9615384615384616,
      "undefined_draws": 4
    },
    "recall": {
      "p2_5": 0.1394422310756972,
      "p97_5": 1.0,
      "undefined_draws": 4
    },
    "f1": {
      "p2_5": 0.2404692082111437,
      "p97_5": 0.96,
      "undefined_draws": 4
    }
  }
}
