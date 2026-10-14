
 — Boot 1 guided motion evidence review
Status: CAPTURE VERIFIED; BENIGN-MOTION FALSE TRIGGER OBSERVED
UTC: 2026-10-04T17:48:38.447696+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_review
{
  "operator_confirmation": "Completed as instructed",
  "recorded_utc": "2026-10-04T17:48:38.311864+00:00",
  "raw_rows_verified": 5989,
  "score_rows_verified": 396,
  "configuration_restored": true,
  "i2c_failures": 0,
  "gaps": 0,
  "confirmed_policy_events": 1,
  "positive_windows": 39,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 4,
    "gz": 2
  },
  "assessment": "Capture completed. One false policy trigger during operator-attested benign motion; gyro rails reached. No physical alert or SMS sent. Preserve this adverse result; H1 three-boot comparison remains pending.",
  "early_baseline_first_sample_uptime_s": 98.728620449,
  "early_baseline_limitation": "Early recording began about 99 seconds after boot, not at power-on."
}
