# Current campaign status — D4/K1 updated 2026-10-11

**D4/K1 completion — 2026-10-11:** both full six-pair studies passed all 12 recording verifications and restored services without errors. Operator confirmed the helmet remained untouched in the same position and orientation throughout both successful studies. D4: 359,970 samples, eight timing gaps (all FIFO), zero I2C errors/alerts. K1: 359,999 samples, zero gaps/I2C errors/alerts. Both are COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED). Earlier failed K1 attempts remain preserved and excluded. See [completion review](../../results/final-closure/randomized_review_20261011/README.md). Existing release archives predate this update; other dated statements below describe the earlier checkpoint.

53/55 requirements have completed or qualified-complete evidence; 2 remain pending (Q4, P). Counts are recomputed from the checklist and supersede stale hand-maintained totals.

D1/D2/D3: latest headless pair verified and operator-attested untouched. J3: 60,712 samples, 4,040 windows, one 89.144 ms long host interval, no I2C errors/overflows/timeouts/alerts; 21/21 checks passed and operator confirmed untouched throughout. Evidence: 14_fifo_drdy/stationary_20min_20261007_comparison.

J2: full 20-minute IIO capture COMPLETE, 60,043 samples, 3,999 windows, zero timing-guard resets and alerts. All 19 verification checks passed; operator confirmed untouched throughout. Temporary overlay removed, recorded sensor settings restored and bus free. Kernel I2C error count is unavailable, not zero. Evidence: 15_iio/stationary_20min_20261007_comparison. No capture is active.

D4 and K1: full studies complete; evidence and operator attestation are in randomized_review_20261011. See the completion checkpoint above.

I2: COMPLETE for the qualified early/warm comparison using cold_warm_20261007T141614Z. All 10 verification checks passed; 30,000 samples and 1,997 offline scoring windows per phase. Operator confirmed >=10 seconds with both Pi/IMU unpowered and unchanged untouched placement. First capture begins 97.843 seconds after boot; literal startup coverage remains unavailable. User selected reuse without repeat. See [I2 review](../../results/final-closure/I2_review_20261011/README.md). Boot recorder is unarmed; no new capture was started.

Q4: original software MIT license and CITATION.cff prepared for Usman Azfar, PUCIT, University of the Punjab, at the existing GitHub repository. GitHub fetch returned 404; no Zenodo connection or DOI exists. Dataset rights remain separate (DATA_LICENSES.md). P: user reconfirmed GPS/GSM disconnected; no SMS trial attempted.

Final local archive piResults/final_pi_review_closure/release_candidate_20261007T095628 passed 27/27 integrity checks over 1427 hashes. Includes J2/J3 results, operator attestations, prepared console/boot runners, MIT license and citation metadata. Historical archive checkpoint; current cold/warm arm has been consumed and is false. Frozen deployment files remain unchanged.

| ID | Requirement | Status |
|---|---|---|
| A1 | THREE-BOOT IDENTITY TEST | COMPLETE (POWER REMOVAL USER-ATTESTED) |
| B1 | DOCUMENT THE EXACT FIFO PACKET FORMAT | COMPLETE (CONFIGURATION QUALIFIED) |
| B2 | STATIC FIFO SANITY TEST — NO MODEL | PASS (UNATTENDED PHYSICAL CONDITIONS) |
| B3 | POLLING-vs-FIFO RAW EQUIVALENCE TEST | COMPLETE (UNATTENDED) |
| B4 | FINAL CORRECTED A-B-A ACQUISITION TEST | COMPLETE (CONFIGURATION QUALIFIED) |
| B5 | FIFO REPLAY DIAGNOSTIC | COMPLETE |
| C1 | HIGH-RANGE CONFIGURATION | COMPLETE (MAP-QUALIFIED READBACK) |
| C2 | HIGH-RANGE STATIONARY NOISE TEST | PASS (UNATTENDED PHYSICAL CONDITIONS) |
| C3 | HIGH-RANGE BENIGN-MOTION BATTERY | COMPLETE (GUIDED CAPTURES; DONNING ONSET LIMITED) |
| C4 | HIGH-RANGE 20-MIN LIVE POLLING RUN | COMPLETE (UNATTENDED) |
| D1 | HEADLESS / NO-IDE POLLING RUN | COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED) |
| D2 | HEADLESS + SCHED_FIFO + CPU AFFINITY | COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED) |
| D3 | OPTIONAL HEADLESS NORMAL-SCHEDULER CONTROL | COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED) |
| D4 | OPTIONAL RANDOMIZED REPEATS | COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED) |
| E1 | COMPLETE DELTA-T HISTOGRAM | COMPLETE (HISTORICAL INPUTS) |
| E2 | SUB-30-MS JITTER EFFECT | COMPLETE (HISTORICAL INPUTS) |
| E3 | EMA-vs-REAL-DT DIAGNOSTIC | COMPLETE (HISTORICAL INPUTS) |
| F1 | INTERPOLATION SENSITIVITY | COMPLETE (HISTORICAL INPUTS) |
| F2 | GAP-THRESHOLD SENSITIVITY | COMPLETE (HISTORICAL INPUTS) |
| H1 | THREE-BOOT REPEATABILITY | COMPLETE (OPERATOR-ATTESTED; MANUAL MOTION NOT AMPLITUDE-MATCHED) |
| H2 | EMA STATE / LONG-PAUSE BEHAVIOR | COMPLETE (SOFTWARE REPLAY) |
| I1 | LONG STATIONARY THERMAL RUN | SATISFIED (HISTORICAL SCOPE; NO NEW RUN) |
| I2 | OPTIONAL WARM-START COMPARISON | COMPLETE (QUALIFIED EARLY/WARM; 97.84 S STARTUP OMITTED; OPERATOR-ATTESTED) |
| J1 | DATA_RDY INTERRUPT ACQUISITION | COMPLETE (VERIFIED; HISTORICAL COMPARATOR) |
| J2 | LINUX IIO BUFFERED DRIVER | COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED) |
| J3 | FIFO + DATA_RDY | COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED) |
| K1 | 6–8 RANDOMIZED MATCHED PAIRS | COMPLETE (VERIFIED; OPERATOR-ATTESTED UNTOUCHED) |
| K2 | GC / PYTHON PAUSE LOGGING | COMPLETE |
| L1 | FULL COMPOSED DEPLOYED-CHAIN FIDELITY | COMPLETE |
| L2 | CAUSAL PREPROCESSING CRASH-CLASS 2x2 | COMPLETE |
| L3 | INT8 CLASS 2x2 | COMPLETE |
| L4 | SESSION-CLUSTERED BOOTSTRAP | COMPLETE |
| L5 | HIGH-RECALL OPERATING-POINT SENSITIVITY | COMPLETE |
| L6 | PHYSICAL FRONT-END EMULATION | COMPLETE |
| L7 | INT8 CALIBRATION-RANGE AUDIT | COMPLETE |
| L8 | CRASH-ENRICHED INT8 DIAGNOSTIC CONVERSION | COMPLETE |
| L9 | OPERATOR-LEVEL OUTLIER TRACE | COMPLETE |
| L10 | FEATURE ABLATION | COMPLETE (INFERENCE-TIME DIAGNOSTIC) |
| L11 | JERK-FORMULA ISOLATION + BENIGN-MOTION REPLAY | COMPLETE (OFFLINE ANALYSIS/REPLAY, 2026-10-28; NO NEW HARDWARE RUN) |
| M1 | PER-SOURCE TABLE | COMPLETE WITH EXPLICIT UNKNOWNS |
| M2 | WEAK-LABEL DISCLOSURE | COMPLETE |
| M3 | TEST-SESSION COMPOSITION | COMPLETE |
| M4 | SOURCE-STRATIFIED FIDELITY | COMPLETE |
| N1 | RAW A-B-A SIGNAL FIGURE | COMPLETE |
| N2 | CLASS-FIDELITY FIGURE | COMPLETE |
| N3 | SCHEDULER PAIR FIGURE | COMPLETE (HISTORICAL INPUTS) |
| N4 | DT DISTRIBUTION FIGURE | COMPLETE (AVAILABLE HISTORICAL CONDITIONS) |
| N5 | BENIGN-MOTION TABLE | COMPLETE (SAVED GUIDED CAPTURES) |
| O1 | GPIO ACTUATION REPEATABILITY | COMPLETE (SOFTWARE TIMING) |
| O2 | MULTIPLE TRACE INJECTION TEST | COMPLETE (CONTROLLED TRACE SEGMENTS) |
| Q1 | THRESHOLD FILE CONFLICT | COMPLETE |
| Q2 | TRAINING CONFIG | COMPLETE (evidence: `results/final-closure/training_config_Q2/`) |
| Q3 | CLEAN PUBLIC ARCHIVE | COMPLETE (REVIEW CANDIDATE; NOT PUBLISHED) |
| Q4 | DOI-BACKED DEPOSIT | PENDING |
| P | GPS/GSM smoke trials | PENDING |
| G | Controlled injected-trace onset-to-local-GPIO timing | COMPLETE (CONTROLLED TRACE SEGMENTS) |
