
B5 — Fresh acquisition replay diagnostic
Status: COMPLETE
UTC: 2026-09-30T14:02:06.840225+00:00
Evidence: piResults/final_pi_review_closure/05_corrected_aba_replay
{
  "arms": {
    "A1_polling": {
      "windows": 3986,
      "raw_sha256": "69c7813afbc46fb49793cb565373f3fe108c244a4bed5f686fe3ac5a6b4771af",
      "max_abs_score_difference": [
        0.0,
        0.0
      ],
      "mean_abs_score_difference": [
        0.0,
        0.0
      ],
      "exact_float_equal": true,
      "or_agreement": 1.0
    },
    "B_fifo": {
      "windows": 4029,
      "raw_sha256": "2ab88e0f28fe57f3f397b88f5c555a5b969ea3db90431c95bb2a81c6fb58a340",
      "max_abs_score_difference": [
        0.0,
        0.0
      ],
      "mean_abs_score_difference": [
        0.0,
        0.0
      ],
      "exact_float_equal": true,
      "or_agreement": 1.0
    },
    "A2_polling": {
      "windows": 3994,
      "raw_sha256": "035779e40aba2c46009c17a0cfe25ef269bc43c0a8a35ba799bc7616e4e2ab97",
      "max_abs_score_difference": [
        0.0,
        0.0
      ],
      "mean_abs_score_difference": [
        0.0,
        0.0
      ],
      "exact_float_equal": true,
      "or_agreement": 1.0
    }
  },
  "method": "Same raw samples, host availability timestamps, scorer/guard/filter/model; no re-estimated sensor timestamps. Score equivalence checked at identical endpoint sample indices. Policy event timing remains host-execution-dependent."
}
