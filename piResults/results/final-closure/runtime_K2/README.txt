
K2 — GC/runtime overlap analysis
Status: COMPLETE
UTC: 2026-10-02T15:01:49.159047+00:00
Evidence: piResults/final_pi_review_closure/runtime_K2
{
  "runs": [
    {
      "run": "08_high_range_20min",
      "gc_intervals": 9,
      "gc_duration_max_ms": 6.329348000008395,
      "dt_above_30ms": 194,
      "long_dt_overlapping_gc": 1,
      "processing_above_p99": 40,
      "processing_tails_overlapping_gc": 0,
      "context_switches_delta": {
        "ctx_voluntary": 899317,
        "ctx_involuntary": 17981,
        "minor_faults": 596,
        "major_faults": 0
      }
    }
  ],
  "limitation": "Temporal overlap is descriptive association, not proof that GC caused a gap. Context switches/faults sampled at approximately 1 Hz; cannot localize all pauses to individual reads."
}
