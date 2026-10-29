# J2 acquisition extension comparison

COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED)

Historical comparisons are descriptive, not simultaneous/matched-motion equivalence or causal estimates. Raw binary decoding and model replay are verified independently. FIFO batch timestamps are host availability; IIO timestamps may be driver reconstructed. Do not compare their dt as physical jitter. Kernel I2C error counts are unavailable for IIO. Reported process CPU excludes separate kernel interrupt work. IIO manages sensor clock/filter configuration and uses sysfs scale values; its physical means and rate are not an acquisition-only matched comparison with the older userspace configuration. Desktop/IDE and development activity remained active during current extension captures.

| Condition | Samples | Windows | Gaps | C_D | V_T | Events |
|---|---:|---:|---:|---:|---:|---:|
| Current J2 | 60043 | 3999 | 0 | 1.000000 | 1.000000 | 0 |
| Historical FIFO | 60595 | 4029 | 2 | 0.998266 | 0.999504 | 0 |
| Historical DATA_RDY | 60688 | 4042 | 0 | 1.000000 | 1.000000 | 0 |
| Historical filtered polling | 59837 | 3986 | 0 | 1.000000 | 1.000000 | 0 |

Complete timing, resources, axis statistics, score distributions and source hashes are in summary.json.
