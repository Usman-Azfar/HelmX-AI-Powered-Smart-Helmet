# Frozen hypothesis: cumulative ordinal classification objective

Status: **formally rejected after D2-D5 screening** on 2026-09-21.

This is the first candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes
one experimental factor: the classification objective. It does not change data, labels, sampling,
architecture, fusion, MRL initialization, optimizer, learning rates, augmentation, stopping
patience, output logits, video pooling, calibration, or inference.

## Development-only rationale

The rationale uses UTA-RLDD fold 2 and training evidence only. Fold 1 and DROZY are excluded from
hypothesis selection.

The retained quality-gated checkpoint's fold-2 video confusion matrix is:

```text
                 predicted
true             alert  low  drowsy
alert                5    7       0
low vigilance        2    6       4
drowsy               0    6       6
```

All 19 incorrect video decisions are adjacent-stage errors; none jumps directly between alert and
drowsy. At window level, 378/416 errors (90.9%) are adjacent and only 38 are two-stage errors. The
fold-2 per-class window F1 values are 0.49180 alert, 0.36577 low vigilance, and 0.53254 drowsy;
video F1 values are 0.52632, 0.38710, and 0.54545. The middle stage is the consistent bottleneck.
The temporal-label audit independently found ordered late-session movement in model probability,
EAR, PERCLOS, blink duration, and current closure within drowsy clips.

Ordinary three-class cross-entropy treats the stages as unrelated categories and charges one wrong
class decision regardless of whether it crosses one or two alertness boundaries. The hypothesis is
that supervising the two ordered boundaries will improve low-vigilance separation and reduce
subject-specific categorical decision instability without fabricating window onset labels.

## Exact intervention

Retain three output logits `z = [z0, z1, z2]` and their existing softmax probabilities. Replace
only the classification term of `MultiTaskLoss` with a cumulative ordinal loss over two events:

```text
a0 = logsumexp(z1, z2) - z0       # logit for P(y > 0)
a1 = z2 - logsumexp(z0, z1)       # logit for P(y > 1)
t0 = 1[y > 0]
t1 = 1[y > 1]
```

Apply the existing smoothing value `s = 0.05` independently to each binary target:

```text
t'_k = (1 - s) * t_k + s / 2
L_ordinal = mean(BCEWithLogits(a0, t'_0), BCEWithLogits(a1, t'_1))
```

There is no categorical cross-entropy mixture, coefficient, class weight, distance weight, learned
threshold, monotonic penalty, pseudo-label, or tuning grid. An extreme alert-to-drowsy error crosses
both supervised boundaries; an adjacent error crosses one. At inference, continue to emit
`softmax(z)` and choose `argmax(z)`, so runtime/export interfaces remain unchanged.

Add a validated configuration field:

```yaml
training:
  classification_objective: cumulative_ordinal
```

Its default is `categorical_cross_entropy`, preserving every historical configuration. The
candidate config copies the retained quality-gated settings, uses window supervision rather than
MIL, and changes only this field. Auxiliary loss weights stay zero because no real auxiliary
targets exist.

## Matched evaluation

Implement generic video-level checkpoint selection for both candidate and freshly retrained
baseline: mean uncalibrated logits across every validation video, followed by video macro-F1.
This common protocol setting is applied identically to both arms and is not a candidate factor.
Temperature remains fitted after checkpoint selection on the relevant validation fold only.

Run the four frozen development rotations D2-D5 using seed 13. The matched baseline uses
`categorical_cross_entropy`; the candidate uses `cumulative_ordinal`. Neither fold 1 nor DROZY may
be loaded. The candidate advances only under all Stage-A screening gates already frozen in
`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`:

1. Win at least three of four validation folds on video macro-F1.
2. Improve pooled out-of-fold video macro-F1 by at least 0.020.
3. Lose by no more than 0.020 on every individual fold.
4. Achieve a paired subject-clustered 2,000-resample 95% lower bound above zero.

Low-vigilance recall, quadratic kappa, window macro-F1, confidence, and calibration are secondary
diagnostics and cannot rescue a primary-gate failure. There is no coefficient adjustment or second
ordinal formulation after D2-D5 results. Only a complete screening pass authorizes the five-seed
stage; only the controlling protocol's five-seed pass authorizes downloading DROZY.

## Implementation gate

Before any run, tests must prove:

- the two cumulative logits match probabilities computed from softmax logits;
- labels 0, 1, and 2 produce boundary targets `[0,0]`, `[1,0]`, and `[1,1]`;
- smoothed targets use exactly 0.025 and 0.975;
- gradients are finite and extreme ordered mistakes incur both boundary penalties;
- historical configs resolve to categorical cross-entropy unchanged;
- candidate and baseline resolved configs differ only in `classification_objective`;
- video-level selection reads no fold-1 path.

After tests pass, update README before launching any baseline or candidate rotation.

## Implementation checkpoint (2026-09-06)

The implementation gate passes. `TrainingConfig` now defaults historical runs to
`categorical_cross_entropy`, while the new `cumulative_ordinal` option implements the exact two
boundary logits and 0.05-smoothed targets above. Window-supervised training can select checkpoints
on deterministic all-window video macro-F1, fit validation-video temperature, write calibrated
per-video predictions, and terminate with `development_complete.json` while test evaluation is
disabled.

The matched D2 configs are `configs/uta-multifold-d2-categorical.yaml` and
`configs/uta-multifold-d2-ordinal.yaml`. Replacing the candidate's objective value with categorical
makes their fully resolved configurations equal. An end-to-end synthetic test includes nonexistent
test NPZ paths and proves the development run completes without probing them. Mathematical tests
cover boundary odds, target patterns, exact smoothing, finite gradients, and the greater penalty
for an extreme ordered error. The complete repository passes 104 tests, Ruff lint/format, strict
MyPy across 48 source files, and `pip check`.

This checkpoint authorizes preparing the four rotation manifests and launching the matched D2
baseline/candidate sequence only after README records exact file hashes. It does not authorize
DROZY access or a shortcut directly to the five-seed stage.

## Formal screening decision (2026-09-21)

The report is `runs/uta-multifold-screen/screening_gate_report.json`. It pairs all 146 development
videos from 48 subjects. The candidate won D2 (+0.00537), lost D3 (-0.06416), won D4 (+0.06046), and
won D5 (+0.02786): three wins out of four. Pooled categorical macro-F1 is 0.64212 and pooled
candidate macro-F1 is 0.65182, a +0.00970 difference. The paired 2,000-resample subject-bootstrap
95% interval is [-0.04556, +0.06517].

| Gate | Value | Threshold | Passed |
|---|---|---|---|
| Wins at least 3 of 4 folds | 3 | >=3 | yes |
| Pooled macro-F1 improvement | +0.00970 | >=0.020 | no |
| No fold worse than -0.020 | -0.06416 (D3) | >=-0.020 | no |
| Paired subject-bootstrap 95% lower bound > 0 | -0.04556 | >0 | no |

The win-count gate passes, but the pooled-improvement, worst-fold, and bootstrap gates all fail:
D3's loss is more than three times the allowed worst-fold margin, and the pooled improvement is half
the required threshold despite winning three of four folds. `screening_passed` and
`confirmatory_five_seed_stage_authorized` are false. The candidate is archived. Fold 1, five-seed
confirmation, and DROZY remain locked; further training requires a new development-only one-factor
hypothesis documented and frozen before implementation.
