# I²C connection check — 11 October 2026

The failed K1 run recorded one sensor read returning Errno 5. Its sensor registers were restored. No competing capture service or I²C bus owner was present before this diagnostic. Current identity was 0x70, matching the audited device; I²C clock was 100 kHz. Pi undervoltage/throttling flags were zero both at the failed run and at the diagnostic. The failed recording CPU temperature ranged from 38.459 to 42.355 °C. No kernel entries were returned for the failure interval; later display-driver warnings do not establish the cause of the earlier read error.

A fresh 120-second capture using the same deployed sensor-read path completed with 5,969 samples, 394 scored windows, zero I²C failures, zero timing-guard gaps, and zero alert events. All 14 saved-capture verification checks passed, including exact replay and register restoration. Desktop/IDE remained active; this is a diagnostic, not K1 research evidence.

The failure was not reproduced. This does not establish the cause or prove two-hour reliability. Physical jumper tightness, continuity, and brief sensor-side power disturbances cannot be checked remotely. Inspect/reseat SDA, SCL, ground, and sensor power connections with power off before another long attempt. No bus settings, production source, or retry policy were changed; K1 was not restarted.
