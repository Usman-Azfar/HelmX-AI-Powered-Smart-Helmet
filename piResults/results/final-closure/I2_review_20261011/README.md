# I2 historical-result review — 11 October 2026

I2 is complete for the qualified early/warm comparison using the existing 7 October recordings. The user requested reuse without a repeat, and confirmed both physical conditions: both Pi and sensor were unpowered for at least 10 seconds before boot; the helmet remained untouched in the same position and orientation throughout the early and warm recordings. See operator_attestation.json for the verbatim response and scope.

All 10 offline verification checks passed. Each phase contains 30,000 samples and 1,997 replayed scoring windows. Sensor configurations match and registers were restored. The first available recording covers uptime 97.843–697.821 seconds; the later recording covers 3600.057–4200.037 seconds. The first 97.84 seconds after boot are absent. This is not literal coverage of the first ten minutes from power-on, and no samples were synthesized to fill that interval.

Accelerometer and gyroscope per-axis means/noise and classifier/reconstruction baseline distributions are in summary.json. Scores are offline replay, not an online-latency benchmark. The warm label denotes >=60-minute uptime, not proof of a higher sensor temperature or thermal equilibrium.

The source pair is ../cold_warm_20261007T141614Z; its raw recordings remain unchanged. Newly generated offline scores and analysis accompany the preserved captures. No repeat, rearming, shutdown, or reboot was performed. This local review postdates GitHub commit e0d5f6e and the existing release archives.
