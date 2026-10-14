# HelmX drowsiness research protocol

## Research question

Does personalized, quality-aware causal fusion of facial appearance and interpretable temporal
physiology improve subject-independent and cross-dataset driver drowsiness detection while
remaining deployable on low-power hardware?

This is a hypothesis, not a current performance claim.

## Model families and ablations

All models use identical frozen splits, preprocessing, seeds, and selection criteria.

1. Geometry baseline: EAR/MAR/PERCLOS plus calibrated classical classifier.
2. Frame baseline: lightweight RGB CNN without temporal context.
3. Temporal visual baseline: MobileNetV3 plus causal TCN.
4. Ungated fusion: temporal visual and physiological features with equal weights.
5. Proposed fusion: learned reliability gates conditioned on measured modality quality.
6. Ablations: no personal baseline, no quality measurements, no auxiliary heads, no hard-negative
   training, and no cross-dataset training.

The proposed model is accepted as better only when improvement is consistent across subjects and
seeds, uncertainty intervals exclude a practically negligible effect, and deployment cost remains
within the target budget.

### Post-pilot fusion-collapse diagnostic

The first quality-gated pilot assigned a median of only about 6.7% visual weight on fold-2
validation windows (mean 8.2%), despite a valid MRL Eye checkpoint. Its physiology-only inference
ablation retained macro-F1 0.452 versus 0.463 configured, while post-hoc equal and visual-only
inference were worse because their downstream layers had not been trained for those representations.
This is evidence of training-time modality collapse, not evidence that post-hoc gate overriding is
a solution.

Before adding gate regularizers or changing capacity, run one controlled diagnostic pilot with
`fusion_mode: equal`; retain the same split, seed, initialization, data, augmentation, optimizer,
loss, and stopping rule. This forces both branches to receive training signal and changes exactly
one experimental factor. Compare its validation macro-F1, loss trajectory, and subject-level
dispersion with the original pilot. Do not advance it because of test performance alone. Preserve
both runs regardless of outcome.

Equal-fusion retraining underperformed the original validation macro-F1 (0.44683 versus 0.46337),
so it is retained as a negative result. The next single-factor pilot keeps quality-gated inference
and introduces training-only modality dropout with total probability 0.25: 12.5% of training
samples are forced visual-only, 12.5% physiology-only, and 75% retain learned quality gating. The
choice is constant across every timestep in a sample, is disabled in evaluation/export, and leaves
all other pilot settings unchanged. It advances only if fold-2 validation macro-F1 exceeds 0.46337
and the learned visual weight is materially above the original mean 0.0815 without a pathological
loss curve. Fold-1 results cannot rescue a validation failure.

Training-only modality dropout also failed its validation gate (best macro-F1 0.45610). Before
redesigning crops or adding another fusion mechanism, train the protocol's visual-only baseline
from the same MRL-pretrained initialization with every non-fusion setting held fixed. The earlier
post-hoc visual-only inference result is not a trained visual baseline because its classifier and
temporal layers learned under a physiology-dominated representation. If the properly trained
visual-only fold-2 macro-F1 exceeds 0.46337, treat the visual stream as viable and investigate
staged fusion training. Otherwise, treat the current full-face/MRL-eye transfer interface as the
next failure point and redesign it before another fusion experiment. Fold-1 results remain
reporting-only and cannot decide the branch.

The trained full-face visual baseline then failed (fold-2 macro-F1 0.38777), activating the visual
input redesign. The first redesign is deliberately deterministic and recoverable from the frozen
NPZ cache: crop normalized face coordinates `x=[0.05, 0.95]`, `y=[0.18, 0.55]`, resize to the
configured square input, convert to grayscale, and replicate to three channels. The source face
crop was already derived from MediaPipe landmarks with fixed padding, and a balanced 12-frame
train/validation montage confirmed both eyes remained inside this band across the inspected pose,
lighting, glasses, and occlusion examples. Physiology, quality, labels, splits, timestamps, and
window identities remain byte-for-byte/logically unchanged. This brings the visual tensor closer
to MRL's grayscale eye-crop domain without using labels to choose per-sample crops.

Train visual-only on the derived cache before restoring fusion. It establishes a viable transfer
interface only if fold-2 validation macro-F1 exceeds both the full-face visual baseline 0.38777 and
the selected quality-gated pilot 0.46337. Test performance cannot activate fusion work.

The eye-band visual-only pilot improved over the full-face visual-only baseline but failed the
required multimodal gate: best fold-2 validation macro-F1 was 0.40457 at epoch 6, versus 0.38777
for full face and 0.46337 for the selected quality-gated pilot. Training early-stopped after epoch
14 (eight consecutive non-improvements). Its fold-1 test macro-F1 was 0.32553 and is reporting-only.
Therefore, do not restore fusion, export this checkpoint, or event-evaluate it. The deterministic
eye band is useful evidence that visual input geometry matters, but it has not established a viable
transfer interface. Any next crop/interface revision must be preregistered and selected from
training/fold-2 only; fold-1 outcomes from these failed diagnostics cannot choose it.

The saved fold-2 prediction audit localizes the tradeoff: compared with full face, eye-band input
raised low-vigilance F1 from 0.19027 to 0.45630 but reduced drowsy F1 from 0.46982 to 0.24599; it
changed 477/765 predictions and sent 147/259 drowsy windows to low-vigilance. Before adding a
dual-eye architecture, run one controlled eye-band visual-only diagnostic with the MRL checkpoint
removed and all other settings fixed. This distinguishes harmful cross-domain initialization from
an eye-band representation that is intrinsically insufficient under the current temporal model.
It advances only if fold-2 macro-F1 exceeds 0.46337; fold-1 remains reporting-only.

The dual-single-eye revision is frozen as follows. Starting from the same landmark-derived padded
face cache, crop left x `[0.05, 0.48]` and right x `[0.52, 0.95]`, both at y `[0.18, 0.55]`.
Resize each independently to 160x160, convert each to grayscale replicated across three channels,
and pack left then right along width as a 160x320 tensor. Split the tensor inside the model, pass
both eyes through the same MRL-initialized MobileNet backbone, and take their arithmetic-mean
features before the existing visual projection and causal temporal network. The shared weights and
mean make output invariant to eye order. No mirroring or label-dependent crop selection is used.
A balanced 12-frame training/fold-2 montage was inspected before training and retained at
`runs/uta-rldd-pilot/dual_eye_montage.png`. The experiment otherwise retains the eye-band pilot's
split, seed, augmentation, optimizer, loss, temporal model, and stopping rule. It advances only if
fold-2 validation macro-F1 exceeds 0.46337; fold-1 remains reporting-only.

The no-MRL diagnostic failed decisively: best fold-2 validation macro-F1 was 0.31645, versus
0.40457 with the otherwise identical MRL initialization. Training loss fell from 1.17487 to
0.52606 while validation loss rose from 1.12065 to 1.98256, and calibration reached temperature
19.99990. Thus MRL initialization is beneficial rather than the cause of the remaining failure.
Do not export or event-evaluate the no-MRL checkpoint. The next input experiment, if pursued, must
retain MRL initialization and explicitly match its single-eye domain: extract deterministic left
and right eye inputs, encode them with shared weights, and combine them symmetrically so eye order
cannot become a subject shortcut. Freeze exact crop/orientation/pooling rules from training/fold-2
inspection before training; advancement still requires fold-2 macro-F1 above 0.46337.

The subsequent dual-single-eye pilot also failed its gate. Epoch 1 was best at fold-2 validation
macro-F1 0.40542; eight consecutive non-improvements stopped training after epoch 9. This is
effectively tied with the simpler bilateral eye-band result 0.40457 and below 0.46337. Training
loss fell from 1.16954 to 0.66209 while validation loss rose from 1.13403 to 1.63688.
Reporting-only fold-1 test macro-F1 was 0.33744. Do not export or event-evaluate this checkpoint.
Because full-face, bilateral-band, and dual-single-eye visual pilots all failed, do not launch
another crop variant or restore fusion without a new research-design amendment addressing weak
clip labels, temporal supervision, and subject generalization instead of continuing post-hoc crop
search.

### Development-only temporal-label audit (2026-09-06)

The preregistered audit used all 2,362 training and 765 fold-2 validation windows and excluded
fold 1. Windows were assigned to early/middle/late thirds by midpoint divided by final window end
within each subject/session. Fold-2 macro-F1 increased from 0.36634 to 0.40005 to 0.44763. Within
drowsy clips, late-minus-early means moved toward drowsiness for model probability (+0.01631),
relative EAR (-0.05015), PERCLOS (+0.06209), mean blink duration (+0.66038 seconds), and current
closure (+0.88625 seconds). The expected paired direction occurred in 8/12, 9/12, 7/12, 10/12,
and 5/12 drowsy videos respectively. Drowsy-versus-alert separation strengthened for the same
signals. This supports temporal dilution from assigning one clip label to every 3-second window;
it does not identify physiological onset or justify relabeling individual windows.

Do not select an arbitrary late-window cutoff or report late-only performance as whole-clip
performance. The next experiment requires a separate amendment that freezes a video-level
weak-supervision/multiple-instance objective before implementation. It must sample causal windows
across each training video, aggregate instance logits into a video-level loss without fabricating
window onsets, preserve per-window outputs for deployment, select on fold 2, and leave fold 1
untouched. Bag sampling, pooling, loss, validation unit, and advancement gate must be specified in
advance.

### Frozen video-level weak-supervision pilot (2026-09-06)

The first MIL pilot changes supervision granularity only and retains the MRL-initialized dual-eye
model, subject folds, seed 13, optimizer, learning rates, augmentation, 40-epoch maximum, and
patience 8. A video is exactly one `(subject_id, session_id)` group and must have one clip label.
For each training epoch, form a three-instance bag by selecting one window from each normalized
early/middle/late third. Selection rotates deterministically with seed, epoch, subject, session,
and bin; it never uses predictions, physiology values, or labels within a video. Each selected
window receives the existing temporally consistent augmentation independently.

Run the unchanged causal model on all three instances, then take the arithmetic mean of their
uncalibrated class logits. Apply the existing label-smoothed cross-entropy once to that video logit
and its provider clip label. Do not add instance losses, pseudo-labels, monotonic constraints,
attention parameters, top-k selection, or inferred onset labels. Per-window logits remain the
deployment output; bag pooling exists only for weakly supervised training and video evaluation.

Validation is deterministic: run every available window in each fold-2 video and mean its logits,
then select checkpoints on macro-F1 across the 36 videos. Under this exact aggregation, the
existing dual-eye visual checkpoint scores 0.44444 and the selected quality-gated checkpoint scores
0.48629. The MIL pilot advances only if fold-2 video macro-F1 exceeds 0.48629. Window-level fold-2
metrics are secondary diagnostics. Fold 1 remains untouched until the gate passes and cannot rescue
a validation failure.

### Video-level weak-supervision outcome and failure audit (2026-09-06)

The pilot early-stopped after 36 epochs and selected epoch 28 at fold-2 video macro-F1 0.51736,
strictly passing the frozen 0.48629 gate. The subsequently authorized fold-1 result was only
0.33232 video macro-F1, versus 0.56481 for the retained quality-gated model under the same video
aggregation. MIL's test-minus-validation shift was -0.18503, while the selected model's was
+0.07853. Test data did not select or modify either checkpoint.

The descriptive influence audit found no single fold-2 video sufficient to explain the MIL gate
pass (maximum absolute leave-one-video contribution 0.02222). It did find subject sensitivity:
removing `fold2_20` lowers MIL macro-F1 to 0.47046, below the frozen selected-model baseline, and
the maximum absolute leave-one-subject contribution is 0.04690. MIL confidence is nearly uniform
at about 0.349 on both folds; validation errors are slightly more confident than correct results.
Retain the quality-gated checkpoint and reject MIL promotion. Any new hypothesis must demonstrate
multi-fold development robustness without using fold 1 for tuning.

## Selection and reporting

- Select checkpoints on validation macro-F1, with PR-AUC and calibration as secondary criteria.
- Fit robust physiology scaling and temperature calibration on training/validation data only;
  serialize both inside the checkpoint so test and runtime transformations are identical.
- Tune operating thresholds and temperature scaling on validation subjects only.
- For the post-pilot event-threshold correction, preserve the preregistered probability gaps
  between release/caution/warning/critical and search warning thresholds from 0.40 through 0.72
  in 0.02 increments on the continuous fold-2 validation videos. Select the highest event
  sensitivity among candidates with zero observed false-alert events on validation alert clips;
  break sensitivity ties with the higher, more conservative warning threshold. Fold 1 may be used
  to diagnose the original failure but must not select the corrected operating point.
- The initial one-dimensional scan was infeasible because even 0.72 produced one validation
  false-alert event. The sole permitted second-stage correction jointly scans warning persistence
  values `[2, 3, 5, 7.5, 10]` seconds with the same probability grid and zero-false-event
  constraint. Ten seconds is a deployment-facing upper bound so tuning cannot manufacture a low
  false-alert rate by delaying warnings indefinitely. Critical persistence is raised to the
  warning persistence when required by severity ordering. Among equally sensitive feasible
  candidates, prefer shorter persistence, then the higher warning threshold. This amendment was
  made after the one-dimensional validation scan failed and must be reported as such.
- Report accuracy, balanced accuracy, macro/weighted F1, macro precision/recall, MCC, quadratic
  kappa, one-vs-rest ROC-AUC, PR-AUC, negative log likelihood, Brier score, and ECE.
- For deployment, report false alarms per hour, missed drowsiness events, event-level sensitivity,
  unavailable time, FPS, p50/p95 latency, peak RAM, model size, and energy/power on the actual
  Raspberry Pi target. Report onset-based detection delay only when ground truth includes a
  defensible drowsiness-onset timestamp; otherwise use the clip-level terminology defined below.
- Aggregate first by subject/session, then across subjects. Frame counts must not create artificial
  confidence intervals.
- Run at least five fixed seeds and provide mean, standard deviation, and subject-clustered 95%
  bootstrap confidence intervals.
- Compare paired models on the same subjects/sessions and report effect sizes, not only p-values.

## Leakage controls

- A subject cannot occur in more than one split within a dataset.
- Overlapping temporal windows from one video/session cannot cross splits.
- Near-duplicate frames are never randomly divided across train and test.
- Pretrained auxiliary datasets are disclosed; their subjects are checked against evaluation data
  when identities are available.
- External datasets remain untouched until the architecture and calibration procedure are frozen.
- For UTA-RLDD, use nested folds: one official fold is untouched test, one of the remaining folds is
  validation, and the other three are training. Rotate the outer test fold for the final study.

## Event-level evaluation

Window-level classification metrics (`evaluation.metrics`) score independent 3-second snippets and
cannot report false alarms/hour, clip-start time-to-first-alert, onset-based detection delay, or
unavailable time - the quantities the alert system is actually judged on.
`evaluation.causal_harness` (CLI: `evaluate-events`) causally replays full raw test videos through
the same calibration/temporal-buffer/`AlertController` path as the live app and pools per-video
`EventMetrics`.

UTA-RLDD labels a whole video, not a frame-level drowsy event, so the harness documents an explicit
mapping rather than assuming one: an alert-class video is a pure negative (used only for
false-alarm rate), a drowsy-class video is treated as one continuous positive clip, and a
low-vigilance video is reported separately as the fraction that ever reaches CAUTION or above, not
mixed into the binary event statistics. See the module docstring in
`src/helmx_drowsiness/evaluation/causal_harness.py` before changing this mapping, and revisit it if a
future dataset instead provides frame-level drowsy-event annotations.

### Required timing terminology for clip-level labels

UTA-RLDD's clip label does not establish when the driver physiologically became drowsy. Therefore,
elapsed time from video start to the first alert must be reported as:

> **time-to-first-alert within drowsy-labelled clips**

It must not be shortened to "drowsiness detection delay" or described as time from physiological
drowsiness onset. Even if the current harness or an output field uses `detection_delay`, the paper,
tables, plots, and captions must use the clip-start terminology and disclose the clip-level ground
truth assumption. A true onset-based detection-delay result requires a dataset with independently
annotated onset timestamps. If such annotations later become available, preserve the clip-start
metric separately rather than silently changing its definition.

## Five-second blink-rate floor: empirical validation

The five-second minimum elapsed-duration floor prevents the known early-session failure in which a
single blink can imply roughly 300 blinks/minute. Five seconds is an engineering choice, not a
validated physiological constant. Do not tune it to 4, 5, or 10 seconds by intuition before
examining official data, and do not tune it on an untouched test fold.

For the first official UTA-RLDD pilot manifest, preserve the `data-quality-report` output and
inspect at minimum:

- early-window maximum and p99 `blink_rate_per_minute`;
- later-window maximum and p99 `blink_rate_per_minute`;
- timestamp-binned values around the first few seconds, looking for a sharp discontinuity near the
  five-second boundary;
- NaN and Inf fractions, which must both be zero.

Also retain the early/later bucket definitions and sample counts so the percentiles are auditable.
If the distributions are finite and physiologically plausible, and no boundary artifact is
visible, keep the five-second floor unchanged. Any later change becomes a validation-selected
hyperparameter, must use training/validation data only, and must be recorded with before/after
distribution evidence.

## Historical gate before the originally planned 5-fold x 5-seed study

This section records the original plan. Fold 1 has since been consumed by the preregistered MIL
confirmation and the 25-run design is no longer authorized. The controlling forward protocol is
`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`: four-fold development over folds 2-5, followed only
after all gates pass by one locked external DROZY confirmation.

### Pre-pilot input-contract amendment (2026-09-02)

The first official fold-1-test/fold-2-validation data-quality gate found finite but pathological
robust-standardized physiology tails before any official training was run: `relative_mar` reached
about 629 robust-scale units because one training subject's neutral MAR baseline was near zero;
`mean_blink_seconds` and `valid_fraction` also had extreme standardized tails. The model input
contract therefore clamps every training-only standardized physiology feature to `[-10, 10]`
before the physiology projection. Raw NPZ values remain unchanged and auditable. This correction
was selected without test-subject data, is covered by PyTorch/ONNX parity tests, and must remain
frozen throughout the one-seed pilot and official study. It is a documented pre-pilot amendment,
not a result-driven architecture change during the study.

Do not make another architecture change before this pilot. Once one complete usable official fold
is available, execute this sequence in order:

1. Preprocess the fold using the provider mapping.
2. Run `helmx-drowsiness data-quality-report <manifest>`.
3. Inspect class/window balance and every physiology distribution, including the blink-rate checks
   above.
4. Run one fold with one seed only.
5. Inspect the complete training log rather than only its selected score.
6. Verify all auxiliary losses remain exactly zero by design while their real targets are absent.
7. Verify the visual-backbone learning rate is approximately 0.1 times the main learning rate.
8. Verify both learning-rate groups follow the intended schedule and the training/validation curves
   are sane.
9. Export the selected pilot checkpoint.
10. Run `helmx-drowsiness evaluate-events` on the real raw videos for that fold.
11. Manually inspect a small, documented set of causal predictions and alert transitions.
12. Start the expensive full study only if every pilot gate below passes.

### Pilot pass/fail gate

| Check | Pass condition |
|---|---|
| Subject leakage | 0 leaked identities |
| Train/validation/test mapping | Matches provider folds exactly |
| NaN/Inf physiology | 0 values |
| Blink-rate pathology | No extreme early-session explosion or unexplained boundary discontinuity |
| Class/window imbalance | Measured, documented, and justified |
| Auxiliary losses | Exactly 0, intentionally, while no real auxiliary targets are present |
| Main loss | Decreases sensibly |
| Validation macro-F1 | Learns above the documented trivial baseline |
| Backbone learning rate | Approximately 0.1 times the main learning rate |
| Learning-rate schedule | Both parameter groups decay correctly |
| Calibration | Fitted on validation only |
| Event harness | Processes real raw video end to end |
| Test usage | No threshold, architecture, or hyperparameter tuning on the pilot test fold |
| Predictions | Saved per window and associated with subject/session for later auditing |

If any item fails, stop before the official 5-fold x 5-seed study, diagnose the failure, and rerun
the one-fold/one-seed pilot. If all items pass, freeze preprocessing, architecture, losses,
optimization, calibration, thresholds, and evaluation definitions. No architectural tinkering is
allowed during the official 25-run study; corrections require a documented protocol amendment and
a clean restart rather than selective reruns.

The pilot gates did not all pass, so that official study never began. Do not interpret the
historical conditional language above as authorization to start it.

The controlling replacement and first candidate amendment are
`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md` and `ORDINAL_OBJECTIVE_HYPOTHESIS.md`. The latter
freezes a cumulative two-boundary ordinal objective based only on fold-2 adjacent-error evidence;
implementation verification must complete before any four-fold screening run begins.

## Reproducibility artifacts

Each run must store the resolved configuration, Git commit, environment lock, dataset manifest
hash, split hash, random seed, checkpoint hash, per-sample predictions, calibration parameters,
metrics JSON, confusion matrix, and latency benchmark. Failed runs are retained and identified;
cherry-picked successful seeds are not acceptable.
