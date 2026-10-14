"""One-shot delayed warm capture for the current boot; no reboot or alerts."""
import json
import subprocess
import sys
import time
from pathlib import Path

import campaign as c


def main():
    out = c.BASE / 'boot_capture_execution/boot1_warm'
    out.mkdir(exist_ok=False)
    expected_boot = json.loads((c.BASE / '01_identity_three_boots/boot1/summary.json').read_text())['boot_id']
    state = {'status': 'WAITING', 'expected_boot_id': expected_boot,
             'minimum_uptime_s': 3600, 'duration_s': 600,
             'limitation': 'Operator instructed to maintain original resting position; full warm-run stationarity requires subsequent confirmation.'}
    def save():
        c.save(out / 'state.json', state)
    def current_boot():
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    def uptime():
        return float(Path('/proc/uptime').read_text().split()[0])
    save()
    try:
        while uptime() < 3600:
            if current_boot() != expected_boot:
                raise RuntimeError('Boot changed; warm comparison invalid')
            time.sleep(min(30, 3600 - uptime()))
        if current_boot() != expected_boot:
            raise RuntimeError('Wrong boot')
        for service in ['helmx-crash-monitor.service', 'helmx-research-boot-capture.service']:
            check = c.command(['systemctl', 'is-active', service])
            if check.get('stdout', '').strip() != 'inactive':
                raise RuntimeError('Service not confirmed inactive: ' + service)
        check = c.command(['fuser', '/dev/i2c-1'])
        if check.get('returncode') != 1 or check.get('stdout', '').strip():
            raise RuntimeError('Sensor ownership check failed')
        hashes = json.loads((c.BASE / 'hashes/initial_artifacts.json').read_text())
        if not all(c.sha(c.ROOT / name) == digest for name, digest in hashes.items()):
            raise RuntimeError('Frozen artifacts changed')
        label = 'boot_repeatability/boot1_warm_stationary'
        state.update(status='RECORDING', requested_start_uptime_s=uptime(), label=label)
        save()
        with (out / 'capture.log').open('w') as log:
            subprocess.run([sys.executable, str(c.BASE / 'scripts/live.py'),
                            '--seconds', '600', '--label', label],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        summary = json.loads((c.BASE / label / 'summary.json').read_text())
        if summary['exception'] or summary['elapsed_s'] < 600:
            raise RuntimeError('Incomplete capture')
        state.update(status='CAPTURED; COMPARISON AND OPERATOR CONFIRMATION PENDING',
                     finished_uptime_s=uptime())
        save()
    except Exception as error:
        state.update(status='FAILED; DO NOT RETRY AUTOMATICALLY', error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
