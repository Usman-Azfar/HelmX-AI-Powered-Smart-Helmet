
N3 — Individual scheduler-pair figure
Status: COMPLETE (HISTORICAL INPUTS)
UTC: 2026-10-02T15:04:28.424862+00:00
Evidence: piResults/final_pi_review_closure/presentation_N3
{
  "pairs": [
    {
      "pair": 1,
      "condition": "loaded",
      "raw_dt_sha256": "0ac21ae414a82ffaa449a0ef83d13820de0d6f719618c77ccc76be38b39586d5",
      "gap_count": 176,
      "gaps_per_min_actual_interval_time": 8.800100484959394,
      "corrected_count_replay_scored": 3425,
      "C_D": 0.8573216520650814,
      "V_T": 0.9511246875867815,
      "historically_recorded_scored": 3425,
      "processing_p99_ms": 4.581358559662471
    },
    {
      "pair": 1,
      "condition": "reduced",
      "raw_dt_sha256": "f96f023c4afaac1b0b869fc833aa1a3b7b144301255519637c288840be37e35f",
      "gap_count": 75,
      "gaps_per_min_actual_interval_time": 3.750003139340128,
      "corrected_count_replay_scored": 3742,
      "C_D": 0.9364364364364365,
      "V_T": 0.9803510610427036,
      "historically_recorded_scored": 3742,
      "processing_p99_ms": 3.340581450411287
    },
    {
      "pair": 2,
      "condition": "loaded",
      "raw_dt_sha256": "3945e6afd4f17915f8781c535cba461a9e0ea91d31bf9eecb60804bcc8bb2975",
      "gap_count": 134,
      "gaps_per_min_actual_interval_time": 6.700038578582054,
      "corrected_count_replay_scored": 3545,
      "C_D": 0.8871371371371372,
      "V_T": 0.9635770589834194,
      "historically_recorded_scored": 3545,
      "processing_p99_ms": 3.7833513599980506
    },
    {
      "pair": 2,
      "condition": "reduced",
      "raw_dt_sha256": "04df9e43a9e957d8a221d66312b992415125178bbf7a0da65d69b19e05fe240f",
      "gap_count": 71,
      "gaps_per_min_actual_interval_time": 3.550039081847746,
      "corrected_count_replay_scored": 3754,
      "C_D": 0.9394394394394394,
      "V_T": 0.9814379084967321,
      "historically_recorded_scored": 3754,
      "processing_p99_ms": 3.4072264302994864
    },
    {
      "pair": 3,
      "condition": "loaded",
      "raw_dt_sha256": "6c4da770e5ff3aa33d0884e3162c8683427ad27379ac38af3b14619cdd85b0e4",
      "gap_count": 113,
      "gaps_per_min_actual_interval_time": 5.650044289708426,
      "corrected_count_replay_scored": 3609,
      "C_D": 0.9031531531531531,
      "V_T": 0.9696399785061794,
      "historically_recorded_scored": 3609,
      "processing_p99_ms": 4.197090760935681
    },
    {
      "pair": 3,
      "condition": "reduced",
      "raw_dt_sha256": "f30b0585ddc30201b8ee91014b957b843f24aa01c9712feb9f850c114107ac1e",
      "gap_count": 131,
      "gaps_per_min_actual_interval_time": 6.550078714179053,
      "corrected_count_replay_scored": 3576,
      "C_D": 0.8951188986232791,
      "V_T": 0.9646614513083356,
      "historically_recorded_scored": 3576,
      "processing_p99_ms": 4.312287998800457
    }
  ],
  "method": "Current sample appended after gap, matching deployed main(); old coverage helper incorrectly skipped that sample. 30-ms historical guard explicit. Actual dt sum used for exposure.",
  "limitation": "These are the three archived pairs, not new randomized/headless repetitions. Reversals are retained."
}
