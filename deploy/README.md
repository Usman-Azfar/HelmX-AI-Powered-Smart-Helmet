# Raspberry Pi deployment

This directory contains the real-time monitor, hardware configuration,
benchmark utility, systemd template, and the research validation suite.

## Installation

1. Create a virtual environment on the Pi and install
   `deploy/requirements.txt`.
2. Make authorized model, normalizer, and threshold artifacts available at the
   paths configured in `deploy/config.yaml`.
3. Replace the placeholder GSM recipient and verify the serial port, GPIO pin,
   I2C address, and cancellation signal path.
4. Run `python deploy/crash_monitor.py` interactively and validate sensor,
   alarm, cancellation, GPS, and GSM behavior before enabling a service.
5. Install the service template with `sudo bash deploy/install_service.sh`.

The systemd installer resolves the repository and virtual-environment paths at
installation time; the committed unit therefore contains no developer-specific
home directory. Research orchestrators likewise derive the repository root and
accept `HELMX_ROOT` and `HELMX_PYTHON` overrides.

The deployment is a research prototype, not a certified safety device. Review
the limitations in `performance.md` and the complete hardware evidence in
`piResults/results/COMPLETE_RESULTS.md`.
