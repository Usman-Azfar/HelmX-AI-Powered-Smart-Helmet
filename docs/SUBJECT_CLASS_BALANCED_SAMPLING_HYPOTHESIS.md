# Frozen hypothesis: subject-class-balanced window sampling

Status: **formally rejected after D2-D5 screening; failure audit complete** on 2026-09-21.

This is the next candidate governed by `MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`. It changes
one training-data factor: the probability with which existing training windows are sampled. The
cached windows, labels, preprocessing, augmentation, architecture, quality gate, categorical
objective, MRL initialization, optimizer, learning rates, stopping, video pooling, calibration,
and inference remain unchanged. Fold 1 and DROZY are excluded and prohibited.

## Development-only rationale

The rationale uses only the completed seed-13 categorical D2-D5 predictions and development
manifests. The reproducible baseline audit is
`runs/uta-multifold-screen/categorical_baseline_failure_audit/baseline_failure_audit.json`, SHA-256
`0D548FADB229512B26345316845201A1686394023049323A464543AF569D8CC2`.

Across 146 out-of-fold videos from 48 subjects, categorical macro-F1 is 0.64212. Low-vigilance
recall is the weakest at 0.54167, compared with 0.75000 for alert and 0.64000 for drowsy. The 22
low-vigilance errors split in both directions: 13 are predicted alert and 9 drowsy. Eight of the 13
errors made with confidence at least 0.60 are low-vigilance videos. This is not a simple low-quality
tail: incorrect videos have mean monitoring quality 0.86132 versus 0.85026 for correct videos, and
error rate is non-monotonic across quality quartiles. Two subjects have no correctly classified
videos, while 13 have every video correct; subject accuracy has standard deviation 0.28297.

The current window loader uses uniform random shuffling. Consequently, a subject-class recording
with more cached windows contributes more expected gradient updates. In the four development
rotations, training recordings contain 6-39 windows and subject totals contain 58-92 windows.
Although pooled class counts are close to balanced, uniform window sampling does not give equal
training influence to subjects or to each subject's alertness stages. This is misaligned with the
subject-disjoint protocol and its provider-video primary endpoint.

The pure ordinal, categorical-plus-ordinal, quality-concat, and fully frozen-backbone candidates
are already rejected. Their outcomes do not support another ordered-loss, fusion, or complete
backbone-freezing change. The new hypothesis is that equal expected training mass for every
subject-class cell will reduce recording-duration dominance and improve unseen-subject class
boundaries, especially the heterogeneous middle stage, without changing the model or labels.

## Exact one-factor intervention

Add one validated training option:

```yaml
training:
  window_sampling: subject_class_balanced
```

The historical default is:

```yaml
training:
  window_sampling: uniform_shuffle
```

For the candidate's training split only, group manifest rows by `(dataset, subject_id, label)`. If
cell `c` contains `n_c` windows, assign every window in that cell raw sampling weight:

```text
w_i = 1 / n_c
```

Draw exactly `N` indices with replacement per epoch, where `N` is the unchanged number of training
manifest rows. The sampler must use an explicit generator seeded deterministically from the run
seed and epoch, so a resumed epoch boundary produces the same next-epoch index stream as an
uninterrupted run. Every subject-class cell must therefore have equal expected mass; split provider
recordings such as `10_1` and `10_2` collectively remain one subject-class cell.

Validation remains exhaustive, deterministic, and unsampled. No class weights, weighted loss,
balanced batch constraint, hard-example mining, curriculum, extra augmentation, altered epoch
length, or tuning coefficient is allowed. The only candidate difference is `window_sampling`.

## Matched evaluation

Reuse the completed categorical seed-13 D2-D5 runs as frozen matched baselines. After the
implementation gate passes, train only the subject-class-balanced candidate once per D2-D5
rotation. Candidate configs must be mechanically identical to their categorical counterparts
except for `training.window_sampling`.

The candidate advances only if every existing screening gate passes:

1. Improve video macro-F1 over categorical in at least three of four folds.
2. Improve pooled out-of-fold video macro-F1 by at least 0.020.
3. Be no worse than -0.020 on every fold.
4. Have a paired 2,000-resample subject-clustered 95% lower bound above zero.

Low-vigilance recall, per-subject accuracy, calibration, and confidence are mandatory secondary
diagnostics but cannot rescue a primary-gate failure. There is no sampler-weight adjustment,
without-replacement variant, subject-only variant, class-only variant, or second sampling attempt
after results are known. Failure archives the candidate and prohibits five-seed confirmation.
Passing all four gates authorizes only the existing five-seed stage, not DROZY access.

## Implementation gate

Before D2 candidate training, tests must prove:

- historical configurations default to uniform shuffled loading with unchanged behavior;
- candidate weights equal exactly `1 / n_c` for each `(dataset, subject_id, label)` cell;
- every subject-class cell has equal total raw weight, including a cell split across two sessions;
- the candidate draws exactly `N` samples with replacement per epoch;
- identical seed and epoch values reproduce identical indices, different epochs use different
  deterministic streams, and resume at an epoch boundary reproduces the uninterrupted stream;
- validation loading remains exhaustive, ordered, and unaffected;
- D2-D5 candidate configs validate and become identical to categorical after resetting only
  `window_sampling`;
- training provenance records the sampling policy and atomic resume rejects a mismatched policy;
- the complete tests, Ruff lint, strict MyPy, dependency checks, and `git diff --check` pass;
- README records the hypothesis/config hashes and exact resumable D2 command.

No candidate training is authorized until this implementation gate passes and the checkpoint is
documented. Fold 1, rejected candidates, and all external data remain inaccessible.

## Implementation checkpoint (2026-09-20)

The implementation gate passes. `TrainingConfig` now has a strict `window_sampling` field whose
historical default is `uniform_shuffle`; `subject_class_balanced` is accepted only with window
supervision. `SubjectClassBalancedSampler` computes exact inverse cell counts over
`(dataset, subject_id, label)`, draws exactly the manifest row count with replacement, and uses an
explicit PyTorch generator seeded by run seed plus the 1-indexed epoch. Training sets the sampler's
epoch before iteration, so a recovery checkpoint resumes with the same next-epoch stream without
depending on mutable sampler RNG state. Validation loading remains sequential and exhaustive.

Provenance records `window_sampling` as a top-level recovery contract in addition to the resolved
configuration. A changed sampling policy is rejected before an incomplete run can load its atomic
recovery checkpoint. Tests cover exact per-window weights, equal total cell mass across split
sessions, unchanged sample count, deterministic same-epoch streams, distinct epoch streams,
epoch-boundary resume equivalence, the historical random sampler, candidate-only training
sampling, unchanged validation loading, video-bag rejection, config equality, and provenance
mismatch rejection.

The four candidate configs validate and become identical to their categorical counterparts after
resetting only `training.window_sampling`:

- D2 `configs/uta-multifold-d2-subject-class-balanced.yaml` SHA-256
  `E8F5C48F74A486BB637831283E78C3D838244EBF20B9BA9D4A482E7EC30600F3`
- D3 `configs/uta-multifold-d3-subject-class-balanced.yaml` SHA-256
  `E42DB59729A10B1FD3A13633B940BD675F389CC2B7208D0B91CECC84873FD355`
- D4 `configs/uta-multifold-d4-subject-class-balanced.yaml` SHA-256
  `85A6BC5FF44FE139DABEDEFEC6A10EC37960DCA0CC314E27EF12D70CA8BABA88`
- D5 `configs/uta-multifold-d5-subject-class-balanced.yaml` SHA-256
  `8780829FC7DA715EEB9449B13ACBEC59EAC0A2D1E9C4C2FC9763513C24BB4227`

The complete repository passes 141 tests, Ruff lint across `src` and `tests`, strict MyPy across 53
source files, `pip check`, and `git diff --check`. The six warnings are upstream PyTorch/ONNX-export
warnings already covered by numerical parity tests. This checkpoint authorizes only seed-13 D2-D5
candidate screening, beginning with D2 and reusing the completed categorical baselines. It does not
authorize fold 1, five-seed confirmation, or DROZY.

## D2 screening checkpoint (2026-09-20)

The seed-13 D2 candidate completed normally under
`runs/uta-multifold-screen/d2/subject_class_balanced/seed-13`. Early stopping selected epoch 5
after epoch 13 exhausted patience 8. Training loss fell from 1.04524 to 0.41130 while validation
loss rose from 0.95927 to 1.53657. All auxiliary loss components remained exactly zero.

Validation-only calibration selected temperature 2.81557 and reduced NLL from 1.17999 to 1.00745.
The selected 36-video macro-F1 is 0.55756 versus the frozen categorical D2 baseline 0.58385, a
-0.02629 difference. Candidate recalls are 0.58333 alert, 0.58333 low vigilance, and 0.50000
drowsy, compared with baseline recalls 0.50000, 0.66667, and 0.58333. The candidate therefore loses
D2 and already violates the frozen no-fold-worse-than-0.020 gate. This cannot be rescued by later
folds, secondary metrics, fold 1, or external data; formal four-fold screening remains incomplete.

The terminal marker confirms `test_evaluation: disabled` and `test_split_accessed: false`.
Selected `best.pt` SHA-256 is
`5B1E65FAA5E7B9F5EA2DE01136F0D4CC1F78ACA9111D0537591792898A8C16BB`; validation-video
predictions SHA-256 is `DA9920FB64364FC444B2D9FE511D8A47F9BAD51581D440404C33494F93A58CA3`;
and `development_complete.json` SHA-256 is
`FC334BCE60FD317AF4F7C889637375D15CC32913B997786E0A698CAF7709EE3E`. D2 is terminal and must
not be repeated. At this checkpoint D3 had not yet been launched. Fold 1, confirmatory seeds, and
DROZY remained locked.

## D3 screening checkpoint (2026-09-20)

The seed-13 D3 candidate completed normally under
`runs/uta-multifold-screen/d3/subject_class_balanced/seed-13`. Early stopping selected epoch 3
after epoch 11 exhausted patience 8. Training loss fell from 1.01722 to 0.42013 while validation
loss rose from 1.01117 to 1.11927. All auxiliary loss components remained exactly zero.

Validation-only calibration selected temperature 1.28645 and reduced NLL from 0.92363 to 0.91247.
The selected 37-video macro-F1 is 0.62484 versus the frozen categorical D3 baseline 0.68498, a
-0.06014 difference. Candidate recalls are 0.83333 alert, 0.33333 low vigilance, and 0.76923
drowsy, compared with baseline recalls 0.91667, 0.41667, and 0.76923. Thus the proposed sampling
policy did not improve the targeted low-vigilance weakness and instead reduced both alert and
low-vigilance recall on D3. Together with D2, the candidate has lost both completed rotations and
has already irreversibly failed the worst-fold and three-of-four-wins gates. Formal four-fold
screening remains incomplete.

The terminal marker confirms `test_evaluation: disabled` and `test_split_accessed: false`.
Selected `best.pt` SHA-256 is
`7AC7E3FE00961A3956439D55C9F32C15414F5FA443E438EDB32A73F47218745B`; validation-video
predictions SHA-256 is `6A7660C472AC288F05F99DD5CF5FFF674FB3085D80C866986AE389B8B228B3EA`;
and `development_complete.json` SHA-256 is
`1046C3DDAE8650FC545B1239FC88457885E6EAFF3AFEB71097FF96D62B38332D`. D3 is terminal and must
not be repeated. At that checkpoint D4 had not been launched. Fold 1, confirmatory seeds, and
DROZY remained locked.

## D4 screening checkpoint (2026-09-20)

The seed-13 D4 candidate completed normally under
`runs/uta-multifold-screen/d4/subject_class_balanced/seed-13`. Early stopping selected epoch 2
after epoch 10 exhausted patience 8. Training loss fell from 1.05135 to 0.44823 while validation
loss rose from 0.84793 to 0.97572. All auxiliary loss components remained exactly zero.

Validation-only calibration selected temperature 0.50928 and reduced NLL from 0.75541 to 0.69896.
The selected 36-video macro-F1 is 0.72302 versus the frozen categorical D4 baseline 0.66325, a
+0.05977 difference. Candidate recalls are 0.91667 alert, 0.58333 low vigilance, and 0.66667
drowsy, compared with baseline recalls 0.66667, 0.50000, and 0.83333. D4 is therefore a candidate
win and improves the targeted low-vigilance recall on this rotation, although drowsy recall falls.
This result cannot reverse the already-failed three-of-four-wins and worst-fold gates from D2-D3;
D5 remains required to complete the frozen characterization.

The terminal marker confirms `test_evaluation: disabled` and `test_split_accessed: false`.
Selected `best.pt` SHA-256 is
`F81CEA946A6F5FDAABDD27B2A10BD04DE8D8EBE6FD19896DECC90C2BE576F956`; validation-video
predictions SHA-256 is `183ED6E99254F704C7C757849EC705407D31912DD1A648A5A677172E1479524E`;
and `development_complete.json` SHA-256 is
`3EA02B4DF36226EA184120A0EE8B410F9FCD4A72DD3F96EC794C83EACAB76935`. An idempotent rerun
returned the completed checkpoint without adding history rows. D4 is terminal and must not be
repeated. At that checkpoint D5 had not been launched. Fold 1, confirmatory seeds, and DROZY
remained locked.

## D5 screening checkpoint (2026-09-21)

The seed-13 D5 candidate completed normally under
`runs/uta-multifold-screen/d5/subject_class_balanced/seed-13`. Early stopping selected epoch 10
after epoch 18 exhausted patience 8. Training loss fell from 1.02116 to 0.33025 while validation
loss rose from 0.94838 to 1.60245. Long machine-inactive intervals extended wall-clock time but
did not lose any completed epoch. All auxiliary loss components remained exactly zero.

Validation-only calibration selected temperature 3.53178 and reduced NLL from 1.34540 to 1.02162.
The selected 37-video macro-F1 is 0.56264 versus the frozen categorical D5 baseline 0.61031, a
-0.04767 difference. Candidate recalls are 0.83333 alert, 0.25000 low vigilance, and 0.69231
drowsy, compared with baseline recalls 0.91667, 0.58333, and 0.38462. D5 is therefore a candidate
loss, and the targeted low-vigilance recall deteriorates sharply despite improved drowsy recall.

The terminal marker confirms `test_evaluation: disabled` and `test_split_accessed: false`.
Selected `best.pt` SHA-256 is
`AF4E224BC8F8162EBC6656B7A89B4296B64FD3C94B886223A51C597528467055`; validation-video
predictions SHA-256 is `F73A675A9E054DF57E7C2C1C6D0D7A40F59323A2CCC94D94450F437BB6AD45F7`;
and `development_complete.json` SHA-256 is
`50A07FCCE78CB8ADB629FCDBD1D9170BA5EF3E8DD58A5B39650079C8971CA10B`. An idempotent rerun
returned the completed checkpoint without adding history rows. D5 is terminal and must not be
repeated.

## Formal screening decision and failure audit (2026-09-21)

The formal report is
`runs/uta-multifold-screen/subject_class_balanced_screening_gate_report.json`; SHA-256:
`B5F41FD7634C2AFC7342337C8659835A477662B71C281C163A01D90B8BDB9AED`. It pairs all 146
development videos from 48 subjects and uses the frozen 2,000 paired subject-bootstrap resamples
with seed 2026. The candidate lost D2 by -0.02629, lost D3 by -0.06014, won D4 by +0.05977, and
lost D5 by -0.04767: one win out of four. Pooled categorical macro-F1 is 0.64212 and pooled
candidate macro-F1 is 0.62150, a -0.02062 difference. The paired 95% interval is
[-0.09813, +0.05795]. All four gates failed, so `screening_passed` and
`confirmatory_five_seed_stage_authorized` are false. Fold 1 and DROZY remain locked.

The development-only failure audit is complete under
`runs/uta-multifold-screen/subject_class_balanced_failure_audit`. Candidate and categorical
predictions agree on 73.29% of videos: both are correct on 75, both wrong on 35, categorical alone
is correct on 19, and the candidate alone on 17. Candidate-minus-categorical recall changes are
+0.04167 alert, -0.10417 low vigilance, and +0.02000 drowsy. Maximum absolute leave-one-subject-out
contribution is 0.01512, so no single subject explains the pooled regression. SHA-256 values are
`failure_audit.json` `85ECE82441E54A649D1E6340A614D43B9C570CA54CDDB58278BEDC6D6CCC0D75`,
`paired_video_changes.csv` `8A40F32F32886C086047895CF80AC3775B4889A80268BD3E836A90AC72938129`,
and `subject_influence.csv` `63CE83FE56200742B14F4C3675B8BEDC1FAC80DC958DEAA05E391E37DCA9A58F`.
The candidate is conclusively archived. Further training requires a new development-only
one-factor hypothesis documented and frozen before implementation; five-seed confirmation, fold 1,
and DROZY remain unauthorized.
