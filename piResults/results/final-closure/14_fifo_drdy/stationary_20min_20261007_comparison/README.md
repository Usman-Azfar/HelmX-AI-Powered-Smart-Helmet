# J3 acquisition extension comparison

COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED)

Historical comparisons are descriptive, not simultaneous/matched-motion equivalence or causal estimates. Raw binary decoding and model replay are verified independently. FIFO batch timestamps are host availability; IIO timestamps may be driver reconstructed. Do not compare their dt as physical jitter. Kernel I2C error counts are unavailable for IIO. Desktop/IDE and development activity remained active during current extension captures.

| Condition | Samples | Windows | Gaps | C_D | V_T | Events |
|---|---:|---:|---:|---:|---:|---:|
| Current J3 | 60712 | 4040 | 1 | 0.999011 | 0.999753 | 0 |
| Historical FIFO | 60595 | 4029 | 2 | 0.998266 | 0.999504 | 0 |
| Historical DATA_RDY | 60688 | 4042 | 0 | 1.000000 | 1.000000 | 0 |
| Historical filtered polling | 59837 | 3986 | 0 | 1.000000 | 1.000000 | 0 |

Complete timing, resources, axis statistics, score distributions and source hashes are in summary.json.

The single long host interval was 89.143663 ms. FIFO draining retained queued samples: 60,691 single-packet drains, nine two-packet drains, one three-packet drain and eleven empty drains. Shared host timestamps within a batch are intentional. No reconstructed physical timestamps or silent decimation were used.
