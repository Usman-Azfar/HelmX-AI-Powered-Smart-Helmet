"""Experiment 3 (deadline-miss statistical bound): independently verifies the
protocol document's numbers rather than trusting them -- both the underlying
20,175-window count (cross-checked against the actual JSON files that
produced it) and the rule-of-three vs. exact Clopper-Pearson bounds."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PI_RESEARCH = ROOT / "results" / "pi_research"

RUNS = {
    "4.4 (12-min live pipeline)": "w2_live2_pipeline.json",
    "4.5 loaded (90-min soak)": "w2_live3_soak_90min.json",
    "4.5 reduced-background (20-min soak)": "w2_live3_soak_20min.json",
}

total = 0
for label, fname in RUNS.items():
    d = json.loads((PI_RESEARCH / fname).read_text())
    n = d["n_windows_generated"]
    misses = d["deadline_miss_count_gt_stride_budget"]
    print(f"{label}: n_windows={n}, deadline_misses_gt_300ms={misses}")
    assert misses == 0, f"{label} has nonzero deadline misses -- protocol's zero-event assumption would be wrong"
    total += n

print(f"\nTotal combined windows: {total} (manuscript/protocol claims 20,175)")
assert total == 20175, f"MISMATCH: computed {total}, expected 20175"

for n in (total, 14461):
    rule_of_three = 3.0 / n
    exact_cp = 1 - 0.05 ** (1.0 / n)
    print(f"\nn={n}:")
    print(f"  rule-of-three approx  = {rule_of_three:.7f} ({rule_of_three*100:.4f}%)")
    print(f"  exact Clopper-Pearson = {exact_cp:.7f} ({exact_cp*100:.4f}%)")
