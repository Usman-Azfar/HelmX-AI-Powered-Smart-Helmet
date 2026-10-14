HelmX Final Pi Acquisition A-B-A Test
========================================
Source protocol: piResults/HelmX_FINAL_Pi_ABA_Acquisition_Test.txt
Run: 2026-09-20, three 20-minute conditions in one session, no Pi restart.

Purpose: isolate whether switching ONLY the acquisition method (deployed
polling vs. the FIFO/decimated path) changes the reconstruction-error
distribution -- the explicit follow-up called for by the E2/E3/E4/H2 round's
own writeup (acquisition_compare/acquisition_comparison.txt).

Structure:
  A1_polling/   -- deployed polling baseline, 20 min
  B_fifo/       -- FIFO/decimated acquisition, 20 min
  A2_polling/   -- deployed polling repeat, 20 min
  aba_comparison.csv          -- one row per metric, one column per condition
  aba_comparison_summary.txt  -- full write-up, interpretation, and claim limits

Each condition folder contains: raw_sensor.csv (every raw sample),
window_scores.csv (every scored window, not just triggers), timing.csv (one
row of timing/stream/latency metrics), system_metrics.csv (periodic
CPU/RSS/temperature), summary.json (everything, machine-readable), and
summary.txt (human-readable).

HEADLINE RESULT: reconstruction_error was exactly 0.0 for 100% of windows in
BOTH polling runs (A1: 3993/3993, A2: 3986/3986) and NEVER zero in the FIFO
run (0/3925, range 3.53-15.12, 220 threshold crossings, 33 confirmed
triggers). Classifier probability was exactly 0.0 in all three conditions
throughout. See aba_comparison_summary.txt for the full interpretation
(Scenario 1 per the source doc's own framework), a disclosed but unproven
hypothesis for the mechanism, and explicit claim limits.

Per the source doc's own stopping rule, this is the final targeted Pi
experiment recommended for the current paper.
