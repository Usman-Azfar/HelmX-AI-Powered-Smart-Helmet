# Experiment Scripts

These are the scripts associated with the published Raspberry Pi results. They are retained for
method review and reproducibility; many require Raspberry Pi hardware, the project environment,
models, or datasets and are not expected to run on a generic workstation without configuration.

| Directory | Scope |
|---|---|
| `core/` | Main Pi research suite and device benchmark: inference, live sensor, soak, replay, quantization, policy, and diagnostics |
| `final-validation/` | A-R validation scripts plus the frozen deployment/export source used by that campaign |
| `closure/` | Final B-Q closure scripts, including corrected A-B-A, scheduler, high-range, IIO/DRDY, model, provenance, and presentation analyses |
| `scheduler-study/` | Matched scheduler/service-profile collection and analysis utilities |

Closure test L11 (jerk-formula isolation and benign-motion replay, 2026-10-28) runs offline on
a workstation. Its script is `scripts/jerk_feature_study.py`, kept with the other repository-root
analysis scripts because it imports `src/` and `deploy/crash_monitor.py` directly.

Scripts are published as research artifacts, not as a single automated test runner. The exact
reported outcome and limitations for each campaign are in
[the complete results report](../results/COMPLETE_RESULTS.md).

