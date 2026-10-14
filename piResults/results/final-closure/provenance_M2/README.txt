
M2 — Weak-label disclosure
Status: COMPLETE
UTC: 2026-09-29T19:28:34.125128+00:00
Evidence: piResults/final_pi_review_closure/provenance_M2
{
  "ANOMALY_TOP_FRACTION": 0.3,
  "severity_metric": "Maximum acceleration magnitude within each 60-sample window after canonical gravity removal, before normalizer scaling.",
  "rule": "For each fall/near_fall file, positive iff severity >= session 70th percentile. Ties can make the positive fraction exceed 30%. Other windows become label 0, although they belong to a crash-like recording.",
  "label_caveat": "Weak positives are not independently annotated crash onsets. DaRUS uses interpolated per-timestep simulation labels and any-positive window assignment. Accuracy against these labels is not physical crash sensitivity.",
  "window_loop": "range(0, len(df)-60, 15), exclusive stop; runtime may score one extra terminal window, excluded explicitly from aligned comparisons."
}
