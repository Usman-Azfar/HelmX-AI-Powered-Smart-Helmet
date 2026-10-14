
O1 — GPIO actuation repeatability
Status: COMPLETE (SOFTWARE TIMING)
UTC: 2026-10-02T15:13:04.272171+00:00
Evidence: piResults/final_pi_review_closure/gpio_O1
{
  "trials": 50,
  "software_call_high_interval_s": {
    "50": 0.050128696499996295,
    "95": 0.051278806149912266,
    "100": 0.0531919510001444
  },
  "limitation": "Actual GPIO API used on BCM18, with timestamps surrounding calls. No oscilloscope/loopback: electrical edge timing and physical alarm perception are unmeasured."
}
