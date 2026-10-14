# Frozen hypothesis: categorical objective with ordinal regularization

Status: **formally rejected after D2-D5 screening** on 2026-09-21.

This is the next candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes
one experimental factor: the classification objective. It retains the existing data, labels,
sampling, model, fusion, MRL initialization, optimizer, learning rates, augmentation, seed,
stopping, video pooling, calibration, and inference behavior. Fold 1 and DROZY are excluded from
hypothesis selection and remain prohibited.

## Development-only rationale

The rationale uses only the completed D2-D5 seed-13 development predictions preserved in
`runs/uta-multifold-screen/failure_audit`. The pure cumulative-ordinal replacement won three of
four rotations but failed the pooled, worst-fold, and paired-bootstrap gates. Across all 146 OOF
videos, its macro-F1 gain was only +0.00970 with 95% subject-clustered interval
[-0.04556, +0.06517]. Prediction agreement with categorical cross-entropy was 80.8%; categorical
alone was correct on 10 videos and ordinal alone on 11, so the two objectives contain complementary
rather than uniformly superior decisions.

Pure ordinal supervision improved pooled drowsy recall from 0.6400 to 0.7000, but reduced alert
recall from 0.7500 to 0.7083. Low-vigilance recall stayed 0.5417 while its F1 fell from 0.5532 to
0.5253 because precision declined. The decisive D3 regression was concentrated in the middle
stage: low-vigilance recall fell from 0.4167 to 0.2500 and F1 from 0.5000 to 0.3158, even while
drowsy recall improved from 0.7692 to 0.8462. No single subject explains the pooled result; the
largest absolute leave-one-subject-out contribution to the objective difference is below 0.009.

The rejected pure replacement therefore appears to add useful ordered-boundary information while
discarding useful mutually exclusive class discrimination. The follow-up hypothesis is that
retaining categorical cross-entropy as the primary term and adding a fixed, subordinate ordinal
regularizer can preserve alert/middle-stage separation while retaining some drowsy-stage benefit.

## Exact one-factor intervention

For the unchanged three logits `z = [z0, z1, z2]`, compute the existing smoothed categorical loss
and the already verified cumulative-ordinal loss using smoothing `s = 0.05`:

```text
L_ce = CrossEntropy(z, y, label_smoothing=0.05)
L_ord = mean(BCEWithLogits(a0, t'_0), BCEWithLogits(a1, t'_1))
L_hybrid = L_ce + 0.5 * L_ord
```

The boundary logits and targets remain exactly those frozen for the first ordinal candidate:

```text
a0 = logsumexp(z1, z2) - z0
a1 = z2 - logsumexp(z0, z1)
t0 = 1[y > 0]
t1 = 1[y > 1]
t'_k = 0.95 * t_k + 0.025
```

The coefficient is fixed at 0.5 before any hybrid run. Categorical cross-entropy remains at unit
weight; ordinal supervision is explicitly subordinate. There is no coefficient search, fold-wise
choice, class weighting, threshold adjustment, architecture change, or second hybrid formulation.
Inference remains the unchanged `softmax(z)` followed by `argmax(z)`.

Add one validated objective value:

```yaml
training:
  classification_objective: categorical_with_ordinal_regularization
```

Historical categorical and cumulative-ordinal behavior must remain bit-for-bit unchanged at the
loss-function level.

## Matched evaluation

Reuse the already completed seed-13 D2-D5 categorical runs as frozen matched baselines; rerunning
them would add no information and could introduce accidental selection. Train only the hybrid
candidate once on each existing D2-D5 rotation, with configs mechanically identical to the
categorical configs except for `classification_objective`.

The candidate advances only if every existing screening gate passes:

1. Improve video macro-F1 over categorical in at least three of four folds.
2. Improve pooled OOF video macro-F1 by at least 0.020.
3. Be no worse than -0.020 on every fold.
4. Have a paired 2,000-resample subject-clustered 95% lower bound above zero.

There is no rescue by the rejected ordinal candidate, secondary metrics, fold 1, or external data.
Failure archives the hybrid candidate and prohibits five-seed confirmation. Passing all four gates
would authorize the existing five-seed stage, not immediate DROZY access.

## Implementation gate

Before D2 hybrid training:

- unit tests must prove the exact `L_ce + 0.5 * L_ord` identity;
- gradients must be finite and reach all three logits;
- historical objective values must produce their prior losses unchanged;
- config validation must accept only the three frozen objective names;
- every D2-D5 hybrid config must differ from its categorical counterpart only by objective;
- the complete tests, Ruff lint/format, strict MyPy, and dependency checks must pass;
- README must record config hashes and the verified recovery command.

No hybrid training is authorized until this implementation gate is complete and documented.

## Implementation checkpoint (2026-09-07)

The implementation gate passes. `TrainingConfig` accepts the exact third objective value while
preserving categorical cross-entropy as the default and prohibiting both non-categorical objectives
with video-bag supervision. `MultiTaskLoss` computes the hybrid classification term as the existing
smoothed categorical loss plus exactly 0.5 times the unchanged cumulative-ordinal loss.

Tests prove the numerical identity, finite gradients through all three logits, rejection under
video-bag supervision, historical default behavior, and resolved D2-D5 config equality after only
the objective is reset to categorical. All four configs also pass CLI validation and text-level
comparison:

- D2 `configs/uta-multifold-d2-hybrid.yaml` SHA-256
  `8CB5D9765364A63F882BB80D2A2FB44C22ADF635613EBE4C10F966DD3211697C`
- D3 `configs/uta-multifold-d3-hybrid.yaml` SHA-256
  `929D066E6A81F6178A00075422C63AA370A07CCE61B78F23524DB18FADDD2E0F`
- D4 `configs/uta-multifold-d4-hybrid.yaml` SHA-256
  `A6DA58F01708E49EA3C967B7AF38AD37CDF561A9CAF36E64A949DAA9D431FEDC`
- D5 `configs/uta-multifold-d5-hybrid.yaml` SHA-256
  `B7E02205045807570D8FC1F218E0F5423E0AC106A3515558F6AF5C4F96A24EE8`

The complete repository passes 114 tests, Ruff lint/format, strict MyPy across 51 source files, and
`pip check`. The four warnings are the existing PyTorch ONNX-export warnings. This checkpoint
authorizes the seed-13 D2-D5 hybrid screening sequence, starting with D2, while retaining the
existing categorical baselines. It does not authorize fold 1, five-seed confirmation, or DROZY.

## Formal screening decision (2026-09-21)

The report is `runs/uta-multifold-screen/hybrid_screening_gate_report.json`. It pairs all 146
development videos from 48 subjects. The candidate tied D2 (0.00000), lost D3 marginally
(-0.00666), won D4 (+0.02290), and won D5 (+0.03229): two wins, one tie, one loss. Pooled
categorical macro-F1 is 0.64212 and pooled candidate macro-F1 is 0.65146, a +0.00934 difference. The
paired 2,000-resample subject-bootstrap 95% interval is [-0.01835, +0.03941].

| Gate | Value | Threshold | Passed |
|---|---|---|---|
| Wins at least 3 of 4 folds | 2 | >=3 | no |
| Pooled macro-F1 improvement | +0.00934 | >=0.020 | no |
| No fold worse than -0.020 | -0.00666 (D3) | >=-0.020 | yes |
| Paired subject-bootstrap 95% lower bound > 0 | -0.01835 | >0 | no |

D3's near-tie (rather than a clear win or loss) means this candidate is the mildest of the two
ordinal-family rejections: it never loses a fold by a meaningful margin, but it also never wins
convincingly enough to clear the win-count, pooled-improvement, or bootstrap gates. `screening_passed`
and `confirmatory_five_seed_stage_authorized` are false. The candidate is archived alongside the
pure-ordinal rejection; fold 1, five-seed confirmation, and DROZY remain locked.
