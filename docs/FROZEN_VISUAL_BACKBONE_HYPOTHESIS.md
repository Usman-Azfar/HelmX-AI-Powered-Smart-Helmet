# Frozen hypothesis: retain the MRL visual backbone during drowsiness training

Status: **formally rejected after D2-D5 screening** on 2026-09-21.

This is the next candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes
one training-policy factor: after loading the existing MRL Eye checkpoint, the MobileNetV3 visual
backbone is held fixed during drowsiness training. The visual projection, quality-aware fusion,
physiology projection, causal temporal network, and classifier remain trainable. Data, full-face
input, features, categorical objective, initialization, augmentation, seed, stopping, video
pooling, calibration, and inference remain unchanged. Fold 1 and DROZY are excluded and prohibited.

## Development-only rationale

The rationale uses only existing auxiliary and D2-D5 development artifacts. The MRL Eye checkpoint
previously achieved subject-disjoint eye-state macro-F1 0.95468, establishing that it contains a
healthy transferable ocular representation. The retained categorical D2-D5 baselines nevertheless
show the same overfitting pattern in every rotation:

| Fold | Best epoch | Train loss, first to last | Validation loss, first to last |
|---|---:|---:|---:|
| D2 | 4 | 1.02474 to 0.42262 | 0.97681 to 1.53886 |
| D3 | 5 | 1.02062 to 0.39037 | 1.03551 to 1.24814 |
| D4 | 2 | 1.06763 to 0.45002 | 0.80669 to 1.35216 |
| D5 | 1 | 1.03259 to 0.46318 | 0.95392 to 1.42273 |

The backbone already uses a 10x lower learning rate than newly initialized layers, but it still
updates on only 36 training subjects per rotation. Meanwhile the rejected quality-concat candidate
demonstrates that replacing the learned quality gate broadly harms alert and low-vigilance
separation, and the rejected objective candidates do not justify another loss adjustment.

The hypothesis is that preventing drowsiness gradients and BatchNorm running-statistic updates from
drifting the MRL visual representation will reduce subject-specific overfitting while allowing the
new projection, fusion, physiology, temporal, and classification layers to adapt normally.

## Exact one-factor intervention

Add one validated training flag:

```yaml
training:
  freeze_visual_backbone: true
```

Immediately after loading `runs/mrl-eye/best_eye_backbone.pt` and before constructing the optimizer:

1. set `requires_grad = false` for every `model.visual_backbone` parameter;
2. keep `model.visual_backbone` in evaluation mode during every training epoch, preventing
   BatchNorm running-mean and running-variance updates;
3. leave `visual_projection`, `reliability_gate`, `physiology_projection`, `temporal`, and all heads
   in normal training mode;
4. retain the backbone optimizer parameter group and its frozen learning-rate schedule for stable
   checkpoint/provenance structure, while parameters with no gradients remain unchanged.

No gradual unfreezing, warm-up, layer selection, alternate checkpoint, learning-rate change,
dropout change, or added regularizer is allowed. Candidate configs must differ from their matched
categorical configs only in `training.freeze_visual_backbone`. Historical configs default to
`false` and must retain their prior behavior and resolved provenance.

## Matched evaluation

Reuse the completed seed-13 D2-D5 categorical runs as frozen matched baselines. Train only the
frozen-backbone candidate once per D2-D5 rotation. It advances only if every existing gate passes:

1. Improve video macro-F1 over categorical in at least three of four folds.
2. Improve pooled OOF video macro-F1 by at least 0.020.
3. Be no worse than -0.020 on every fold.
4. Have a paired 2,000-resample subject-clustered 95% lower bound above zero.

Failure archives the candidate and prohibits five-seed confirmation. Passing all gates authorizes
only the existing five-seed stage, not DROZY access. Rejected candidates, fold 1, and external data
cannot rescue a failed gate.

## Implementation gate

Before D2 candidate training:

- tests must prove all visual-backbone parameters have `requires_grad = false` after freezing;
- `model.train()` must keep the visual backbone and its BatchNorm modules in evaluation mode while
  the visual projection and downstream layers remain in training mode;
- a training backward pass must leave backbone parameters and BatchNorm buffers unchanged while
  producing finite gradients in the visual projection and downstream classifier;
- false/default mode must preserve historical trainability and state-dictionary keys;
- D2-D5 configs must validate and become identical to categorical after resetting only the flag;
- training provenance and atomic resume must preserve the frozen policy;
- the complete tests, Ruff lint/format, strict MyPy, dependency checks, and ONNX parity must pass;
- README must record document/config hashes and the exact resumable D2 command.

No candidate training is authorized until this implementation gate passes and is documented.

## Implementation checkpoint (2026-09-10)

The implementation gate passes. `TrainingConfig` adds a strict `freeze_visual_backbone` flag that
defaults to false and requires an explicit eye-pretraining checkpoint when enabled. After loading
that checkpoint, training freezes every visual-backbone parameter and a model training-mode guard
keeps the backbone, including BatchNorm modules, in evaluation mode. The visual projection and all
downstream modules remain trainable. The frozen backbone stays in its existing optimizer group so
learning-rate history, checkpoint shape, and atomic resume structure remain stable.

Tests prove fixed parameters and BatchNorm buffers, finite downstream gradients, unchanged
state-dictionary keys, default historical trainability, matched config equality after resetting
only the freeze flag, and an end-to-end train/resume provenance path for both flag states. All four
candidate configs validate. The complete repository passes 130 tests, Ruff across `src` and
`tests`, strict MyPy across 51 source files, `pip check`, and `git diff --check`. The six warnings
are upstream PyTorch/ONNX-export warnings already covered by numerical parity tests.

This checkpoint authorizes only seed-13 D2-D5 frozen-backbone screening, beginning with D2 and
reusing existing categorical baselines. It does not authorize fold 1, five-seed confirmation, or
DROZY.

## Formal screening decision (2026-09-21)

The report is `runs/uta-multifold-screen/frozen_backbone_screening_gate_report.json`. It pairs all
146 development videos from 48 subjects. The candidate lost D2 (-0.03795), lost D3 by a wide margin
(-0.16504), won D4 marginally (+0.00475), and lost D5 (-0.08357): one win out of four. Pooled
categorical macro-F1 is 0.64212 and pooled candidate macro-F1 is 0.57020, a -0.07191 difference. The
paired 2,000-resample subject-bootstrap 95% interval is [-0.16546, +0.02614].

| Gate | Value | Threshold | Passed |
|---|---|---|---|
| Wins at least 3 of 4 folds | 1 | >=3 | no |
| Pooled macro-F1 improvement | -0.07191 | >=0.020 | no |
| No fold worse than -0.020 | -0.16504 (D3) | >=-0.020 | no |
| Paired subject-bootstrap 95% lower bound > 0 | -0.16546 | >0 | no |

All four gates fail decisively; D3's regression alone is more than eight times the allowed
worst-fold margin. Freezing the visual backbone after MRL pretraining is actively harmful relative
to fine-tuning it jointly with the rest of the network on this task, most likely because the
MRL-pretrained representation (eye-openness classification) is not sufficiently aligned with the
three-class drowsiness task to serve as a fixed feature extractor without further adaptation.
`screening_passed` and `confirmatory_five_seed_stage_authorized` are false. The candidate is
archived. Fold 1, five-seed confirmation, and DROZY remain locked; further training requires a new
development-only one-factor hypothesis documented and frozen before implementation.
