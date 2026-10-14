
 — Boot 1 early/warm comparison review
Status: CAPTURE VERIFIED; STATIONARITY USER-ATTESTED; ORIENTATION CONFOUND
UTC: 2026-10-04T18:55:43.207409+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_warm_review
{
  "status": "CAPTURE VERIFIED; STATIONARITY USER-ATTESTED; ORIENTATION CONFOUND",
  "early_first_sample_uptime_s": 98.728620449,
  "warm_first_sample_uptime_s": 3600.89205413,
  "warm_elapsed_s": 600.0073105739998,
  "warm_raw_rows_verified": 30000,
  "warm_score_rows_verified": 1997,
  "warm_sample_rate_hz": 49.999390792922775,
  "warm_i2c_errors": 0,
  "warm_gaps": 0,
  "warm_alert_events": 0,
  "warm_clipping": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 0,
    "gz": 0
  },
  "mean_acceleration_direction_difference_deg": 10.016943938244475,
  "limitations": [
    "Early capture starts about 99 seconds after boot, not at power-on.",
    "Mean acceleration direction differs between early and warm recordings; consistent with changed resting orientation after guided motion. Do not interpret acceleration-axis changes as temperature drift alone.",
    "Three-boot series remains incomplete."
  ],
  "operator_confirmation": "User confirmed helmet remained untouched throughout 23:28\u201323:38 PKT warm capture.",
  "operator_confirmation_utc": "2026-10-04T18:55:43.205107+00:00"
}
