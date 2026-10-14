# Raspberry Pi Hardware Validation

This document consolidates every distinct Raspberry Pi test campaign preserved in the project's
local `piResults2/` research archive. It replaces the archive's overlapping chronological notes
with one review-oriented account of what was tested, what was measured, what was superseded, and
what remains untested.

The report covers physical-device experiments, replay experiments executed on the Pi, offline
analyses created to interpret Pi measurements, failed or discarded attempts that affect the
evidence, and explicitly unperformed tests. It is not a claim that HelmX is certified for
safety-critical use.

## Executive summary

The deployed crash-detection pipeline was exercised on a Raspberry Pi 4 Model B Rev 1.5 with a
physically connected six-axis I2C IMU. The principal results are:

| Area | Result |
|---|---|
| Isolated INT8 inference | Typical latency was sub-millisecond; a 50,000-call run had 0 calls above the 300 ms decision-stride budget, although rare scheduler outliers reached 256.73 ms. |
| Live end-to-end latency | A 12-minute physical-sensor run scored 1,975 windows at 1.70 ms median, 3.19 ms p99, and 8.72 ms maximum, with 0 deadline misses. |
| Long-duration stability | The longest live polling run lasted 180 minutes, processed 539,981 samples and 33,734 windows, and recorded 0 triggers, sensor failures, reconnects, exceptions, or deadline misses. |
| Thermal behavior | The 180-minute run reached 55.0 C with no reported throttling. A separate 30-minute sustained-inference test reached 61.3 C with `get_throttled=0x0`. |
| Memory behavior | Fifteen-, 20-, 90-, and 180-minute runs were classified as stable plateaus. The 180-minute research harness rose by 5.46 MB in total; its retained buffers mean this is not a production-process leak estimate. |
| Replay fidelity | Offline-versus-causal streaming agreement was 99.61% per window and 100% per test session in the original replay study. Later composed-chain analysis showed that disagreement is concentrated in crash-like windows. |
| Quantization | INT8-versus-Keras agreement was 99.89% at the deployed classifier threshold. A large reconstruction-score outlier was retained and investigated rather than hidden. |
| Trigger path | Controlled crash-trace injections exercised the real policy and GPIO call path. Five of ten held-out session traces triggered; median injection-onset-to-GPIO-call time among triggered traces was 2.382 s. |
| Benign movement | Low-range tests exposed gyro clipping and classifier-driven false triggers during some non-crash handling. High-range follow-up removed rail hits in the recorded phases but was not an amplitude-matched crash validation. |
| Acquisition methods | Corrected, configuration-matched polling/FIFO/polling tests produced no positive windows in any arm. Earlier FIFO-trigger claims came from a non-equivalent path and are retained only as debugging history. |
| Scheduler/service load | Reduced background load often improved timing coverage, but randomized and headless comparisons contained reversals. The evidence does not establish a universal SCHED_FIFO or service-reduction advantage. |
| Communications and power | GPS/GSM end-to-end transmission and instrumented electrical power remain untested because the required hardware was absent. |

Machine-readable public artifacts supporting the headline measurements are organized under
[`foundational/`](foundational/), [`final-validation/`](final-validation/), and
[`final-closure/`](final-closure/). The 4.37 GiB local source archive is retained as
`piResults2/` and excluded from Git because it contains duplicated releases, raw scheduler traces,
host diagnostics, intermediate attempts, and research captures.

## Hardware and interpretation boundaries

| Item | Evaluated configuration |
|---|---|
| Computer | Raspberry Pi 4 Model B Rev 1.5, 64-bit ARM, four CPU cores, approximately 8 GB RAM |
| Recorded kernel | Linux `6.12.96+rpt-rpi-v8` in the final closure campaign |
| IMU bus/address | I2C bus 1, address `0x68` |
| IMU identity | `WHO_AM_I=0x70` on 100/100 reads across each of three power-cycle records |
| Model | 83,568-byte INT8 TFLite hybrid classifier/autoencoder |
| Input | 60 samples x 6 channels; nominal 50 Hz; stride 15 samples (300 ms) |
| Policy | Classifier OR reconstruction threshold, three consecutive positive windows, 60-second cooldown |
| Live deployment mode | Host-paced polling, causal gravity filter, one TFLite inference thread |

Early notes called the device an MPU6050 because it was connected at the usual `0x68` address and
used through an MPU6050-compatible library. The later identity campaign consistently read
`WHO_AM_I=0x70`, so this report uses "compatible IMU" unless describing the historical test name.
The final register interpretation used the compatible MPU6500 map, but silicon provenance was not
independently established.

Two sensor configurations appear in the archive and must not be conflated:

- The deployed/early low-range path used approximately +/-2 g and +/-250 degrees/s.
- The closure campaign also evaluated a filtered 50 Hz, +/-16 g and +/-2000 degrees/s path to
  reduce clipping. Results from that path do not retroactively change the deployed model or prove
  crash performance at the wider range.

## Evidence hierarchy and superseded findings

When records conflict, this report applies the following order:

1. Final verified closure evidence dated through 11 October 2026.
2. Corrected configuration-matched reruns.
3. Completed live-sensor and replay campaigns.
4. Historical, blocked, interrupted, or discarded attempts.

The most important supersession concerns FIFO acquisition. An early A-B-A campaign reported zero
reconstruction error under polling and non-zero errors under FIFO, including 33 confirmed FIFO
triggers. Later review found that historical FIFO work was not a valid like-for-like basis for an
acquisition-method claim. The corrected filtered A-B-A used matched range, filtering, divider,
scorer, guard, model, and thresholds:

| Corrected arm | Samples | Windows | Timing gaps | Positive windows | Confirmed alerts |
|---|---:|---:|---:|---:|---:|
| A1 polling | 59,837 | 3,986 | 0 | 0 | 0 |
| B FIFO | 60,595 | 4,029 | 2 | 0 | 0 |
| A2 polling | 59,956 | 3,994 | 0 | 0 | 0 |

Replaying each corrected arm from its saved raw samples reproduced both model outputs exactly and
gave 100% OR-decision agreement. The defensible conclusion is therefore that the corrected tested
methods were decision-equivalent for these stationary recordings; the earlier result is debugging
provenance, not evidence that FIFO is intrinsically inferior.

## Test catalogue

### 1. Foundational Pi and replay tests

These tests established compute feasibility before and alongside the live-sensor campaign.

| Test | Description | Result |
|---|---|---|
| A1 isolated inference | Five repeats of 100 warmups plus 1,000 measured INT8 calls. | Median 0.553 ms, p95 0.942 ms, p99 1.682 ms; original maximum 21.76 ms. Model load was 4.73 ms. |
| A1 repeat | Repeated the same protocol to test tail stability. | Typical percentiles reproduced, but one call reached 286.84 ms, showing that maxima were scheduler-sensitive. |
| Long-tail inference | Recorded 50,000 individual calls. | Median 0.771 ms, p99 3.940 ms, p99.9 7.232 ms, maximum 256.73 ms; 0 calls exceeded 300 ms. |
| Headless/reduced-load long tail | Repeated 50,000 calls after stopping most nonessential services. | Maximum fell to 6.4 ms in that run, supporting scheduler contention as a cause of earlier outliers; VS Code remained active, so it was not a fully headless appliance test. |
| A2 initial resource run | Launched the real monitor before the sensor was connected. | The process remained in its sensor-retry loop; approximately 46 MB RSS and near-zero process CPU characterize the blocked state, not active inference. |
| A3 thermal load | Ran the deployed INT8 model every 300 ms for 30 minutes while sampling temperature. | Mean 55.4 C, maximum 61.3 C, no throttling. |
| C offline-versus-causal replay | Ran all held-out sessions through offline preprocessing and the deployed causal Pi path. | 99.61% window decision agreement and 100% session event agreement. |
| A5 replay trigger latency | Replayed 36 crash-like sessions through the Pi scorer/policy and pulsed real GPIO18 once. | 35/36 sessions detected; median first-positive-to-confirmation delay 0.6 s; real GPIO call completed without error. This older latency origin differs from later injection-onset timing. |
| B power/CPU contention | Queried power support and benchmarked with a competing busy loop. | Electrical power was `null` because no meter/fuel gauge existed. One competing worker raised mean latency about 11%. |
| D quantization | Compared Keras, FP16, and INT8 on 5,437 held-out windows. | INT8 was 83,568 bytes, about 9.5x smaller than Keras, and agreed 99.89% at the deployed classifier threshold. |
| 15-minute replay-paced pipeline | Paced 44,830 recorded samples at 50 Hz through the complete Pi scorer and policy. | 2,985 windows; 2.04 ms median, 9.61 ms p99, 87.21 ms maximum; 0 deadline misses. |
| Thread-count sensitivity | Compared one, two, and four TFLite threads over 2,000 calls each. | One thread gave the best tail: 7.52 ms maximum versus 24.83 ms and 55.39 ms. |
| Cold-start/restart proxy | Started ten fresh monitor processes and timed them to threshold loading. | Median 0.712 s, range 0.636-0.830 s, 0 failures; this did not include an active sensor-loop restart. |
| Concurrent-worker sweep | Benchmarked zero through three busy-loop workers. | Three workers raised mean inference from 0.554 to 1.224 ms; still far inside budget, but the workers were only a contention proxy. |
| Logging overhead | Compared suppressed, warning-level, and real per-window INFO logging. | Deployed-style INFO logging raised mean measured call cost to 1.400 ms from roughly 0.6 ms. |
| Logic robustness batch 1 | Exercised thresholds, consecutive-window policy, cooldowns, NaN/Inf handling, and boundary behavior. | Deterministic policy checks completed; unsafe/non-finite conditions were recorded rather than used as performance evidence. |
| Logic robustness batch 2 | Tested jitter, dropped samples, filter resets, and startup grace behavior. | Scores are sample-count-driven; pre-guard dropped samples were invisible, motivating `SampleStreamGuard`. First decision occurs after 60 samples. |
| Extended model/decision ablation | Examined threshold margins, quantization, OR-branch contribution, causal disagreement, and operator behavior. | Only 0.09% of windows were within +/-0.001 of the classifier threshold. INT8 reconstruction had one 702.55 absolute-error outlier, but no threshold flip in that run. |
| Thermal recovery | Compared 12 minutes idle with the earlier sustained-inference thermal run. | Idle and loaded means were effectively equal (55.5 versus 55.4 C); ambient conditions dominated model heat. |
| Service/log inspection | Captured service policy, process state, journal, kernel, model hashes, clock, storage, threads, and file descriptors. | No kernel under-voltage/thermal/throttling matches were found. The crash-monitor service template did not match that Pi's actual user/path and was not installed. |
| Weakness 1 revalidation | Changed the suspected-crash handler to return a structured result and reran policy tests. | Result propagation and cancellation/SMS decision reporting were verified in software. |
| Weakness 2 revalidation | Added acquisition-layer delayed/dropped-sample detection and reran replay/policy tests. | Gap detection, buffer invalidation, and corrected pipeline behavior were verified; this became the live guard used later. |

The initial A6 sensor soak was not performed while the IMU was unavailable. It was superseded by
the completed 90-minute and 180-minute live soaks described below.

### 2. Physical live-sensor tests

| Test | Description | Result |
|---|---|---|
| 4.1 I2C detection | Probed the physical bus and opened the sensor through the runtime library. | Device present at bus 1/address `0x68`; later identity reads qualified it as `WHO_AM_I=0x70`. |
| 4.2 / W2-LIVE-1 raw read characterization | Read back-to-back for 12 minutes without 50 Hz pacing. | 108,892 reads, 151.24 Hz achieved, 0 I2C failures; p99 interval 12.41 ms and maximum 130.53 ms. |
| 4.3 active CPU/RAM | Ran the real monitor with the connected IMU for 15 minutes. | Mean process CPU 2.72%, RSS about 47.9 MB, maximum CPU temperature 51.1 C, stable memory, 0 I2C failures. |
| 4.4 / W2-LIVE-2 end-to-end pipeline | Physical IMU through guard, filter, windowing, features, INT8 model, and trigger policy for 12 minutes. | 35,800 samples and 1,975 windows; median/p99/max 1.70/3.19/8.72 ms; 0 failures, reconnects, exceptions, or deadline misses. |
| 4.5 90-minute soak | Same live pipeline with five-minute checkpoints and normal background services. | 267,891 samples, 14,461 windows, p99 3.25 ms, max 82.86 ms; 0 triggers and 0 deadline misses; max 53.0 C. |
| Reduced-background 20-minute comparison | Repeated the live soak after stopping nonessential services. | Gaps fell from 11.96 to 4.20 per minute and maximum sample interval from 287.0 to 52.3 ms; both conditions still had 0 I2C failures and deadline misses. |
| Loaded/reduced matched 20-minute pair | Added process/system `perf` and scheduler tracing. | Reduced load scored more windows and lowered gaps/min by 56.6%, but the active development environment remained a confound. |
| Three matched loaded/reduced pairs | Repeated the service-profile comparison three times. | Reduced load improved mean coverage and p99 latency, but pair-level reversals existed; single-run maximum scheduler delay was not stable enough to lead with. |
| 180-minute long soak | Longest deployed-polling live run. | 539,981 samples, 33,734 windows, p99/max 3.031/11.040 ms, 0 alerts/failures/reconnects/exceptions/deadline misses, max 55.0 C, no throttling. |
| 4.6 physical movement smoke test | Guided stationary, rotation, tilt, shake, and non-crash bump phases. | Valid rerun had 0 I2C errors across 3,547 reads and physically plausible changes. A no-movement attempt was discarded and retained. |
| Low-range benign-motion battery | Guided 11 non-crash handling phases under the deployed range. | Reconstruction crossed threshold zero times; classifier-driven confirmed alerts occurred in repeated tilts, moderate rotation, helmet donning, and soft placement. Gyro clipping occurred in vigorous benign handling. |
| High-range stationary test | Ten minutes at +/-16 g, +/-2000 degrees/s with 20 Hz filtering and nominal 50 Hz output. | 30,000 samples at 49.999 Hz, 0 I2C errors/overflows/rail hits; mean acceleration magnitude 9.789 m/s^2. |
| High-range benign-motion battery | Repeated guided handling at the wider range. | No rail hits in the saved phases. Donning-onset coverage was incomplete and the trials were not amplitude-matched to low-range captures. |
| High-range 20-minute live run | Wider-range filtered polling through the model/policy. | 59,913 samples, 3,988 windows, one guard gap, 0 positive windows/alerts/deadline misses, processing p99 9.77 ms. |
| Reboot repeatability | Compared identity and stationary/gentle-motion captures across boots. | Identity was stable. One boot's manually performed rotation was more vigorous and triggered once, so exact motion repeatability was not claimed. |
| 4.7 live trigger path | Established a live sensor baseline, injected a saved crash trace into the same scorer/policy, and used GPIO. | Baseline stayed negative; the injected `darus_crash_Iso_312_2_Out` trace triggered with classifier score 0.9961. |
| 4.8 background services | Observed the 90-minute run with BLE, MQTT, Rhasspy, and assistant services active. | 0/14,461 deadline misses despite service activity; this was not a controlled isolation study. |

The public summary of the longest run is
[`w2_live3_soak_summary.json`](foundational/current/w2_live3_soak_summary.json).

### 3. Acquisition, timing, and operating-system closure tests

Before the final 55-item closure checklist, the project ran an A-R validation campaign. Its items
map to the evidence above and below as follows:

| ID | Test | Result |
|---|---|---|
| A1 | Freeze authoritative artifacts | Model, normalizer, thresholds, configuration, scripts, and hashes were frozen for the campaign. |
| A2 | Experiment-condition inventory | Populated across live, motion, reboot, acquisition, scheduler, and soak runs; later closure work retained the inventory as provenance. |
| B1 | Low-range register readback | Recorded `WHO_AM_I=0x70`, low-range settings, filter/divider state, FIFO/interrupt state, and bus configuration. |
| B2 | Acquisition-method documentation | Documented host-paced polling at nominal 50 Hz and distinguished host timestamps from physical sensor timestamps. |
| C1 | Mounted stationary noise | Ten minutes, 247,151 unpaced reads, 0 I2C failures; exposed gyro bias and non-Z-aligned mounting. |
| C2 | Benign-motion clipping | Accelerometer clipping was rare; low-range gyro clipping was measurable during vigorous but non-crash handling. |
| D1 | Three timing-load conditions | Minimal, normal HelmX, and stress-loaded captures had 0 I2C failures and no >30 ms gaps in those unpaced runs; jitter increased under stress. |
| D2-D3 | Valid-time/coverage and contiguous-run analysis | Computed coverage and 90-sample opportunity metrics, then refined them using paced raw-dt captures. |
| E1 | Polling baseline | Reused the established live polling run rather than manufacturing a duplicate capture. |
| E2 | FIFO acquisition | Historical 20-minute FIFO capture completed with no hardware errors but produced reconstruction-only positives; later B2-B5 review superseded its acquisition-method interpretation. |
| E3 | FIFO plus SCHED_FIFO/affinity | Historical 20-minute variant completed with no deadline misses and repeated the E2 score behavior; later corrected comparison superseded the causal claim. |
| E4 | Reduced-interactive polling | Twenty minutes, 0 triggers/failures/reconnects/exceptions/deadline misses, stable memory, and no throttling. |
| F1 | Three loaded/reduced matched pairs | Six 20-minute runs. Reduced service load improved average coverage/p99 metrics, with pair-level reversals retained. |
| G1 | Live processing latency | Satisfied by the preserved 12-minute physical-sensor pipeline run. |
| G2 | Guard overhead | Measured within the same live run; guard cost was small relative to the 300 ms stride. |
| G3 | TFLite thread sensitivity | One thread provided the best latency tail and remained the deployment choice. |
| H1 | Preserve 90-minute soak | Existing completed soak retained without an unnecessary rerun. |
| H2 | Optional three-hour soak | Completed: 539,981 samples, 33,734 windows, and zero alerts, hardware failures, exceptions, or deadline misses. |
| I | Eleven-phase benign-motion stress test | Reconstruction produced no threshold crossings; classifier positives caused confirmed policy events in four phases. |
| J | Reboot repeatability | Identity remained stable; differences in manually performed rotation amplitude prevented an exact motion-equivalence claim. |
| K | INT8 reconstruction-outlier diagnostic | Located the 702.55-score-difference case at held-out window 5,410; both Keras and INT8 decisions remained positive. |
| L | Representative-dataset audit | Counted crash-like calibration examples and documented the limits of reconstructing a conversion-time selection after the fact. |
| M1 | EMA cutoff sensitivity | Evaluated five cutoffs over the ten held-out sessions. |
| M2 | Causal Butterworth comparison | Compared causal filter identity/frequency response without presenting it as a new physical trial. |
| N1 | Causal preprocessing fidelity | Demonstrated that offline-versus-causal disagreement was concentrated in crash-like windows. |
| N2 | INT8 class-stratified fidelity | Normal-window agreement was higher than crash-like-window agreement; later L3 formalized the 2x2 table. |
| O | Frozen detector context | Recomputed classifier-only, reconstruction-only, both, and neither branch contributions. |
| P | Controlled live trigger path | Physical baseline, crash-trace injection, GPIO actuation, and clean resume completed. |
| Q | GPS/GSM dispatch | Blocked because no module/serial device was connected; no SMS was sent. |
| R | Standalone runtime/GC campaign | Originally skipped as optional; later K2 added GC overlap logging during a selected closure run. |

The campaign also ran a three-arm 20-minute polling-FIFO-polling test that appeared to isolate a
FIFO effect. As explained in the supersession section, the later corrected configuration-matched
campaign is authoritative.

| ID | Test | Result |
|---|---|---|
| A1 | Three power-cycle identity records | Complete. Three distinct boot IDs; each boot returned `0x70` in 100/100 identity reads. Power removal was operator-attested. |
| B1 | Exact FIFO packet/configuration audit | Complete after reconciliation. Packet/configuration interpretation was qualified against the compatible register map. |
| B2 | Static FIFO sanity, no model | 600 s, 30,022 samples at 50.036 Hz, 0 I2C errors/overflows; physical plausibility gate passed. |
| B3 | Matched polling-versus-FIFO raw equivalence | Both approximately 50 Hz; conservative per-axis equivalence/plausibility gate passed with 0 errors or rail hits. This was not a formal statistical-equivalence test. |
| B4 | Corrected polling-FIFO-polling A-B-A | Three 20-minute arms produced 3,986/4,029/3,994 windows; 0 positive windows and alerts in every arm. FIFO had two guard gaps. |
| B5 | Saved-raw replay diagnostic | Every arm reproduced both saved model outputs exactly; OR agreement 100%. |
| C1 | High-range configuration readback | Verified +/-16 g, +/-2000 degrees/s, 20 Hz filter map, divider 19, nominal 50 Hz under the compatible register map. |
| C2 | High-range stationary noise | 30,000 samples, no rail hits/errors; physically plausible stationary magnitudes. |
| C3 | High-range benign-motion battery | Guided captures complete with noted donning-onset limitation; no claim of independent observation or amplitude matching. |
| C4 | High-range 20-minute polling | 59,913 samples, 3,988 windows, 0 alerts/deadline misses, one timing gap. |
| D1-D3 | Headless normal, SCHED_FIFO+affinity, and normal-scheduler control | Verified 20-minute normal and FIFO-scheduled runs. Normal had 0 gaps; FIFO had 4 and a 156.65 ms maximum interval. Neither alerted. This pair did not prove a scheduling advantage. |
| D4 | Six randomized scheduler pairs | 359,970 samples; 8 gaps, all in FIFO-scheduled conditions; 0 I2C errors/alerts. FIFO improved some paired p99 metrics but not timing gaps, so no general advantage is claimed. |
| E1 | Complete observed-delta-time distributions | Historical raw captures reanalyzed with explicit interval bins and no invented FIFO timestamps. |
| E2 | Sub-30-ms jitter analysis | Quantified coverage and score/jitter relationships. Correlations are descriptive because windows overlap and physical captures lack crash labels. |
| E3 | EMA versus real-dt diagnostic | Adaptive-alpha variants were compared on matched endpoints; one reported run had 100% OR agreement with small score changes. |
| F1 | Interpolation sensitivity | Hold/linear one-sample interpolation changed which windows existed; matched-window decisions remained aligned in the cited stationary records. |
| F2 | Gap-threshold sensitivity | Replayed 25, 30, 35, 40, and 60 ms guard thresholds plus reference behavior. Results characterize coverage-policy sensitivity, not crash-class accuracy. |
| H1 | Three-boot repeatability | Complete with operator attestation; manual motions were not amplitude-matched, so qualitative rather than exact repeatability is claimed. |
| H2 | EMA state and long-pause behavior | Software replay confirmed that unexpected long gaps reset EMA, while a known alarm/cancel pause clears the window and preserves EMA. Tested trace scores remained zero. |
| I1 | Long stationary thermal evidence | Satisfied using the retained long-run evidence; no new physical run was invented. |
| I2 | Early-versus-warm comparison | 30,000 samples and 1,997 replay windows per phase; all ten checks passed. First capture began 97.843 s after boot, so literal startup coverage is absent. |
| J1 | DATA_RDY interrupt acquisition | 20-minute run: 60,688 samples, 4,042 windows, 0 gaps/alerts; historical polling comparison was descriptive, not paired. |
| J2 | Linux IIO buffered acquisition | 60,043 samples, 3,999 windows, 0 gaps/alerts; all 19 checks passed. Kernel I2C-error count was unavailable, not assumed zero. |
| J3 | FIFO plus DATA_RDY | 60,712 samples, 4,040 windows, one 89.14 ms interval, no I2C errors/overflows/timeouts/alerts; all 21 checks passed. |
| K1 | Six randomized service-profile pairs | 359,999 samples, 0 gaps/I2C errors/alerts. Earlier interrupted attempts were excluded, not pooled. The successful study did not establish a universal service-profile effect. |
| K2 | GC and Python-pause logging | Nine GC intervals; maximum GC duration 6.33 ms. One long interval overlapped GC, but no causal attribution is made. |

### 4. Model, fidelity, provenance, and presentation closure tests

| ID | Test | Result |
|---|---|---|
| L1 | Full composed deployed-chain fidelity | Overall OR agreement 99.65%; normal 99.91%; crash-like 90.21%. All five crash-like test sessions remained event-detected and all five normal sessions remained event-negative. |
| L2 | Causal preprocessing crash-class 2x2 | OR agreement 99.87% overall and 96.50% on crash-like windows; reconstruction agreement was 100% on crash-like windows. |
| L3 | INT8 class-stratified 2x2 | OR agreement 99.89% overall and 95.80% on crash-like windows; normal OR agreement was 100%. |
| L4 | Session-clustered bootstrap | 2,000 whole-session resamples. Composed overall-agreement interval was 95.77%-99.97%; broad metric intervals reflect only ten sessions. |
| L5 | Operating-point sensitivity | Repeated fidelity analysis for balanced, moderate-recall, and high-recall classifier thresholds. Conclusion: agreement and event behavior depend on the operating point and must not be represented by one threshold-free number. |
| L6 | Physical front-end emulation | Emulated low-range and wide-range clipping on 50 Hz data. Wide range preserved decisions better and reduced clipping, but this was not a high-frequency physical crash experiment. |
| L7 | INT8 calibration-range audit | The representative set contained 8 crash-like windows versus 143 in the held-out test; the known reconstruction outlier was identified as `darus_crash_Iso_115_Out`. |
| L8 | Crash-enriched diagnostic conversions | Compared original-selection, 100-positive-window, and amplitude-stratified calibration variants. They were diagnostic conversions and were not byte-identical replacements for the deployed model. |
| L9 | Operator-level INT8 outlier trace | At window 5,410, Keras reconstruction error was 751.84 and INT8 was 49.29; both remained decisively positive. Tensor saturation was documented but not asserted as proven root cause. |
| L10 | Auxiliary-feature ablation | Inference-time neutralization gave 99.87% OR agreement and 95.10% crash-like agreement. It was not a separately trained temporal-only model, so it cannot isolate training-time feature value. |
| M1 | Per-source provenance table | Documented physical/simulated origin, placement, and native-rate knowledge; unknown metadata remained explicitly unknown. |
| M2 | Weak-label disclosure | Froze the top-fraction severity labeling rule and its limitations. |
| M3 | Test-session composition | Enumerated all ten test sessions, 5,437 windows, label types, positive counts, and reference trigger indices. |
| M4 | Source-stratified fidelity | Reported causal, quantization, and composed agreement separately for CARLA, road, fall, near-fall, and DaRUS. The largest composed disagreement was concentrated in fall/crash-like windows. |
| N1 | Raw A-B-A signal figure | Generated the corrected acquisition comparison figure from preserved inputs. |
| N2 | Class-fidelity figure | Generated the class-stratified causal/INT8/composed fidelity figure. |
| N3 | Scheduler-pair figure | Rebuilt three historical loaded/reduced pairs using corrected coverage counting; reversals were retained. |
| N4 | Delta-time distribution figure | Plotted available loaded/reduced distributions and explicitly counted out-of-range observations; no headless curve was fabricated before headless data existed. |
| N5 | Benign-motion table | Produced the high-range guided-motion table with discarded attempt, incomplete donning onset, and non-continuous-trial limitations preserved. |
| O1 | GPIO actuation repeatability | 50 software-timed GPIO calls: median high interval 50.13 ms, maximum 53.19 ms. No oscilloscope measured the electrical edge. |
| O2/G | Multiple trace injection and onset-to-GPIO timing | Ten held-out session traces; five triggered. Median onset-to-confirmation 2.382 s and confirmation-to-GPIO-call 0.511 ms. Inputs were controlled trace segments, not physical crash onset. |
| Q1 | Threshold-file conflict review | Completed; authoritative deployed thresholds were reconciled and frozen. |
| Q2 | Training-configuration review | Completed; the configuration used for model generation was documented. |
| Q3 | Clean public archive verification | Review candidate passed integrity checks at its checkpoint; it was not claimed as an external publication. |
| Q4 | DOI-backed deposit | Not performed. No reachable GitHub release/Zenodo DOI existed at review time. |
| P | GPS/GSM smoke trial | Not performed. Module/serial device was absent and no SMS was attempted. |

### 5. Protocol-specific follow-up tests

| Test | Result |
|---|---|
| Deadline-miss statistical bound | Recomputed from 20,175 live windows with 0 observed misses. Rule-of-three upper bound was 0.0149% per window; this is an empirical bound, not a real-time guarantee. |
| Physical/mounting validation rerun | A first run with no actual movement was discarded after operator confirmation. The valid guided run recorded 3,570 reads over 522 s with 0 I2C errors and clear phase-dependent motion. |
| Stationary-noise characterization | Ten-minute low-range capture showed approximately 9.91 m/s^2 acceleration magnitude and about 2.37 degrees/s static gyro magnitude, exposing real gyro bias and non-Z-aligned mounting. |
| Clipping characterization | Accelerometer rarely clipped in benign handling, while +/-250 degrees/s gyro clipping was measurable during stronger shaking and helmet removal. |
| EMA cutoff sensitivity | Five cutoffs across ten sessions were evaluated; undefined correlations for zero-variance windows were retained as NaN rather than imputed. |
| Causal Butterworth comparison | Compared the deployed causal preprocessing with another causal-filter family and saved frequency-response data; it was an analysis, not a new road trial. |
| Class-stratified causal fidelity | Original analysis found much lower agreement on crash-like than normal windows, motivating the later L1-L4 closure work. |
| Trigger-path rerun | Clean baseline, crash-trace injection, real GPIO pulse, and clean resume completed without sensor errors. |
| Frozen detector context | Verified the recorded OR-branch counts against the source result rather than copying them without recomputation. |

## Failed, interrupted, and diagnostic attempts

The archive intentionally retains unsuccessful attempts. They are not pooled with successful runs:

- The first 90-minute soak was interrupted before producing a result file; the completed restarted
  90-minute run is the evidence.
- One movement-smoke attempt contained no actual movement. It is marked discarded; the guided rerun
  is used instead.
- Earlier FIFO/decimation runs produced reconstruction-only triggers, and an early A-B-A appeared
  to reproduce them. Configuration-equivalence review and the corrected B2-B5 campaign supersede
  that causal interpretation.
- Several early headless, console, smoke, cold/warm, CLI-path, and release-candidate directories
  are preparation, verification, or historical checkpoints rather than independent headline tests.
- Earlier K1 randomized attempts were interrupted or failed verification. Only the successful
  six-pair study with all checks passed and operator attestation is summarized as K1 evidence.
- The first repeated-tilt high-range motion attempt was discarded and replaced; both remain in the
  private archive.
- Diagnostic I2C, IIO-overlay, interrupt-wiring, boot-capture, and service-restoration runs are
  represented under their final verified J/A/D/K outcomes rather than counted as extra successful
  experiments.

This treatment prevents the number of archive directories from being mistaken for the number of
independent experiments or for repeated evidence of the same claim.

## What was not tested

- No naturally occurring, unstaged motorcycle crash was executed on the device.
- No dangerous physical crash/drop test was performed.
- No complete GPS acquisition, GSM modem dispatch, carrier delivery, or emergency-contact SMS was
  executed because the module was disconnected/absent.
- No instrumented input-power or energy measurement was made; CPU utilization is not used as a
  substitute for electrical power.
- GPIO timing is based on software timestamps around API calls, not oscilloscope measurements.
- No hard real-time guarantee can be inferred from general-purpose Linux timing distributions.
- The benign-motion captures are guided demonstrations, not a statistically representative road
  false-alert exposure study.
- The high-range configuration was not retrained and physically validated on real crashes.
- Dataset/model accuracy claims remain separate from the Pi execution tests and are documented in
  [the repository results guide](../../results/README.md).

## Publication-safe conclusions

The evidence supports saying that the evaluated Raspberry Pi 4 had ample typical compute headroom,
completed multi-hour live polling without deadline misses or hardware read failures, reproduced the
intended policy and GPIO call path, and exposed several real limitations through negative testing.

It does not support saying that HelmX is fail-safe, that latency is always below a fixed value, that
FIFO or SCHED_FIFO is universally better or worse, that physical crash sensitivity has been proven,
or that emergency communications have been validated end to end.

## Public supporting artifacts

- [Result package index](README.md)
- [Curated foundational artifact guide](foundational/README.md)
- [180-minute soak summary](foundational/current/w2_live3_soak_summary.json)
- [Replay-validation result](foundational/current/c_replay_validation.json)
- [Quantization comparison](foundational/current/d_quantization_comparison.json)
- [Isolated-inference benchmark](foundational/current/a1_isolated_inference.json)
- [Historical and corrected controls](foundational/historical/)
- [Selected detailed telemetry](foundational/raw/)

## Provenance

This consolidation was prepared from 9,488 files (approximately 4.37 GB) in the local `piResults2/`
archive. The primary sources were the chronological Pi reports, the final validation progress
tracker, the final review closure status, and the per-test `summary.json`/`README` records. Public
numbers were cross-checked where corresponding artifacts exist under `results/foundational/`.

The source archive was not modified. Its raw captures remain available locally for audit, while
this report is the maintained public narrative. Selection and privacy transformations are documented
in [`provenance/SELECTION_AND_EXCLUSIONS.md`](../provenance/SELECTION_AND_EXCLUSIONS.md).
