# Frozen hypothesis: quality-weighted concatenation fusion

Status: **screening complete and rejected** on 2026-09-10.

This is the next candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes
one architectural factor: the operation that fuses the already projected visual and physiology
representations. Data, full-face input, feature definitions, quality inputs, temporal network,
categorical objective, MRL initialization, optimizer, learning rates, augmentation, seed, stopping,
video pooling, calibration, and inference labels remain unchanged. Fold 1 and DROZY are excluded
from selection and remain prohibited.

## Development-only rationale

The rationale uses only prior fold-2 development diagnostics and the completed D2-D5 development
artifacts. In the retained fold-2 pilot, the learned convex gate assigned only 0.0815 mean weight
to vision. Training visual-only and equal-weight variants did not generalize, and training-time
modality dropout did not pass its fold-2 gate. Thus neither discarding physiology nor forcing equal
contribution is supported. The existing fusion still has a structural bottleneck: visual and
physiology vectors share coordinates and are reduced to one elementwise weighted average before
the temporal network, so information suppressed by the competitive two-way softmax cannot be
recovered downstream.

The pure ordinal and categorical-plus-ordinal candidates are also rejected. The hybrid changes
only 7 of 146 pooled video correctness outcomes relative to categorical (3 categorical-only and 4
hybrid-only), agrees on 93.84% of predictions, improves pooled macro-F1 by only 0.00934, and gives
no pooled drowsy-recall gain. This does not support another classification-loss adjustment.

The hypothesis is that retaining both modality vectors in distinct channels, while still scaling
them by measured input quality, will let a small learned projection use complementary cues without
requiring a globally competitive modality weight at every timestep.

## Exact one-factor intervention

Let `v` and `p` be the unchanged 192-dimensional projected visual and physiology vectors, and let
`q = [q_v, q_p]` be the unchanged measured-quality input. Define:

```text
q_safe = clamp(q, min=1e-4)
w = q_safe / sum(q_safe)
x = concat(w_v * v, w_p * p, q)
h = GELU(LayerNorm(Linear(x)))
```

`h` has the unchanged 192-dimensional hidden size and enters the unchanged causal temporal
network. The new linear layer maps `2 * hidden_size + 2` inputs to `hidden_size`. No attention,
residual bypass, coefficient, auxiliary loss, modality dropout, or tuning grid is added. Returned
`modality_weights` are the normalized measured-quality weights `w`; they describe the actual
pre-projection scaling but are not claimed to measure post-projection feature importance.

Add one validated fusion mode:

```yaml
model:
  fusion_mode: quality_concat
```

Historical `quality_gated`, `equal`, `visual_only`, and `physiology_only` behavior must remain
unchanged. Candidate configs must differ from their matched categorical configs only in
`model.fusion_mode`. The candidate returns to the retained categorical cross-entropy objective;
rejected ordinal objectives cannot be combined with this architecture.

## Matched evaluation

Reuse the completed seed-13 D2-D5 categorical runs as frozen matched baselines. Train only the
quality-concat candidate once per D2-D5 rotation. It advances only if every existing gate passes:

1. Improve video macro-F1 over categorical in at least three of four folds.
2. Improve pooled OOF video macro-F1 by at least 0.020.
3. Be no worse than -0.020 on every fold.
4. Have a paired 2,000-resample subject-clustered 95% lower bound above zero.

Failure archives the candidate and prohibits five-seed confirmation. Passing all four gates would
authorize the existing five-seed stage, not immediate DROZY access. No result from a rejected
candidate, fold 1, or an external dataset can rescue a failed gate.

## Implementation gate

Before D2 training:

- tests must prove the exact normalized-quality scaling and concatenated tensor contract;
- gradients must be finite and reach both modality projections and the new fusion projection;
- zero measured quality must remain finite through the `1e-4` floor;
- historical fusion-mode outputs must remain unchanged under fixed seeds and state dictionaries;
- ONNX export parity and the public output contract must still pass;
- D2-D5 candidate configs must validate and become identical to categorical after resetting only
  `fusion_mode`;
- the complete tests, Ruff lint/format, strict MyPy, and dependency checks must pass;
- README must record config/document hashes and the exact resumable D2 command.

No candidate training is authorized until this implementation gate is complete and documented.

## Implementation checkpoint (2026-09-08)

The implementation gate passes. `ModelConfig` accepts the exact `quality_concat` mode. The model
normalizes measured quality with the frozen finite floor, scales each projected modality without
mixing their coordinates, concatenates both scaled vectors plus raw quality, and applies the frozen
projection before the unchanged temporal network. Historical fusion modes keep their prior
weighted-sum paths and state-dictionary keys.

Tests prove the exact concatenated tensor, finite zero-quality behavior, finite gradients through
both modality projections and the new fusion projection, unchanged historical quality-gated
weighted-sum behavior, candidate config equality after resetting only fusion mode, and PyTorch/ONNX
numerical parity. All four configs validate. The complete repository passes 123 tests, Ruff across
`src` and `tests`, strict MyPy across 51 source files, `pip check`, and `git diff --check`. The six
warnings are upstream PyTorch/ONNX-export warnings covered by passing numerical parity tests.

This checkpoint authorizes only seed-13 D2-D5 quality-concat screening, beginning with D2 and
reusing the existing categorical baselines. It does not authorize fold 1, five-seed confirmation,
or DROZY.

## Screening outcome (2026-09-10)

All four seed-13 rotations completed with test evaluation disabled. Candidate-minus-categorical
video macro-F1 differences were D2 -0.12355, D3 -0.10089, D4 -0.11432, and D5 -0.06951: zero wins
and a regression beyond 0.020 in every fold. Across all 146 OOF development videos, categorical
macro-F1 was 0.64212 and quality-concat macro-F1 was 0.54436, a -0.09776 difference. The frozen
2,000-resample paired subject-bootstrap 95% interval was [-0.16422, -0.02620]. All four screening
gates failed.

The quality-concat candidate is rejected. Five-seed confirmation and DROZY access remain
unauthorized. Completed categorical and candidate runs must not be repeated. Any future candidate
requires a new development-only failure audit and a separately frozen one-factor hypothesis.

## Development-only failure audit (2026-09-10)

The paired audit confirms a broad failure rather than a single-subject anomaly. Categorical and
quality-concat predictions agree on 69.18% of the 146 videos. Both are correct on 69 and both wrong
on 41; categorical alone is correct on 25, while quality-concat alone is correct on 11. Relative
to categorical, pooled recall changes by -0.22917 for alert, -0.10417 for low vigilance, and
+0.04000 for drowsy. Drowsy F1 nevertheless falls from 0.68085 to 0.64151 because precision falls.

The largest absolute leave-one-subject-out contribution to the pooled macro-F1 difference is only
0.01147, far smaller than the full -0.09776 regression. Thus no subject exclusion or fold-specific
adjustment is supported. The failure rejects the premise that replacing competitive learned fusion
with direct quality-weighted concatenation improves robust class separation. Future hypotheses
must retain the categorical baseline and cannot tune this failed fusion using these outcomes.
