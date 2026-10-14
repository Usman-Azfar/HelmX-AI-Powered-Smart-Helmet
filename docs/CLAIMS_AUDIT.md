# Claims audit

The supplied report is contextual material, not a verified experimental record. The current
repository does not support its claimed 94–96% drowsiness accuracy, MobileNetV2 implementation,
500/500 image test, cross-lighting accuracy, Raspberry Pi deployment, or mobile/LED/vibration
integration.

Conflicts found in the supplied artifacts include:

- the old code alerts after 0.5 seconds, while the report specifies 2 seconds;
- the old code uses EAR 0.15 after multiplying EAR by 100, while the report specifies EAR 0.25;
- the report labels HelmX as MediaPipe + MobileNetV2, but the H5 architecture is undocumented in
  the report and the repository provides no training source;
- the report says approximately 15 FPS on a laptop but contains no benchmark output;
- the requirements document marks all error handling and cross-platform functionality complete,
  while the old script imports Windows-only `winsound` unconditionally;
- image-level eye-state results, if later measured, cannot be presented as temporal drowsiness
  detection results.

The completed D2-D5 study supports this wording: "HelmX implements and development-evaluates a
quality-aware causal temporal drowsiness architecture under subject-disjoint UTA-RLDD rotations."
It does not support state-of-the-art, cross-domain, motorcycle-deployment, external-validation, or
safety-certification claims. Use the exact metrics and limitations in `FINAL_RESULTS_SUMMARY.md`.

## Self-audit: the auxiliary multi-task heads (found and fixed 2026-08-28)

The README described "masked multi-task loss for heterogeneous datasets" as implemented, and the
model exposes eye-closure, yawn, head-pose, and quality heads. In review it was found that no
dataset this repository preprocesses ever writes `eye_closure`, `yawn`, `head_pose`, or
`quality_target` into a training NPZ, so every mask was always false and those four heads received
exactly zero gradient in every run to date - the "no auxiliary heads" ablation in
`docs/RESEARCH_PROTOCOL.md` was accidentally the only configuration ever exercised, not a
deliberate baseline. Fixed by making the auxiliary loss weights an explicit config field
(`training.loss_weights`), set to zero in both shipped configs, with a test
(`tests/test_config.py::test_auxiliary_loss_weights_stay_zero_until_a_dataset_supplies_those_labels`)
that fails if a nonzero weight is committed before a dataset actually supplies that target. See
`ARCHITECTURE.md` for the current model contract.
