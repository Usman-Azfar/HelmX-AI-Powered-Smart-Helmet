"""Preserve interruption evidence and recover attestation from the append-only log."""
import json
from pathlib import Path
import campaign as c


def main():
    out = c.BASE / 'resume_interruption_20261005'
    out.mkdir(exist_ok=False)
    log = c.LOG.read_text()
    marker = ' — Boot 2 operator attestation\n'
    entry = log.split(marker)[-1]
    attestation, _ = json.JSONDecoder().raw_decode(entry[entry.index('{'):])
    c.save(out / 'boot2_attestation_recovered_from_log.json', attestation)
    source = c.BASE / 'boot_repeatability/boot2_guided_motion'
    sizes = {p.name: p.stat().st_size for p in source.iterdir() if p.is_file()}
    current = json.loads((c.BASE / '01_identity_three_boots/boot3/summary.json').read_text())
    previous = json.loads((c.BASE / '01_identity_three_boots/boot2/summary.json').read_text())
    result = {
        'boot2_motion_file_sizes': sizes,
        'boot2_motion_has_usable_data': any(sizes.get(p, 0) for p in ['raw_sensor.csv', 'window_scores.csv']),
        'boot2_id': previous['boot_id'],
        'current_boot_id': current['boot_id'],
        'boot_changed': previous['boot_id'] != current['boot_id'],
        'boot2_attestation_recovery': 'Recovered verbatim from the existing last_results.txt entry; not a new operator statement. Empty original files preserved.',
        'boot2_attestation': attestation,
        'boot3_identity': current['identity_counts'],
        'boot3_capture_scope_correction': 'Identity was collected manually during this resumed session after more than 60 minutes uptime, NOT automatically at startup. The identity script uses a generic startup wording for all unattested captures; that wording does not describe this run.',
        'status': 'Boot 2 motion incomplete. Current boot identity saved; physical power removal and stationary/motion conditions await operator response.',
        'repeatability_limit': 'Cannot fill missing boot 2 motion using a different OS boot. H1 needs another fully documented boot with baseline and motion to replace the incomplete trial.',
        'validation_scope': 'The preceding 27-check PASS covers listed evidence and the older archive. It does not validate these empty boot2 motion/attestation files or establish that the archive includes this new session.',
    }
    c.finish([], 'Resume interruption and boot continuity audit',
             'INCOMPLETE MOTION PRESERVED; OPERATOR INPUT REQUIRED', result, out)
    note = '''# Current resume point — 2026-10-05

No capture is active. Current boot is <redacted-boot-id>.
Boot 3 identity was read 100 times: all 0x70. This was a late manual capture,
not a startup capture. Power removal has not yet been attested.

Boot 2 power-off duration (approximately 10–15 seconds) and baseline stationarity
were already confirmed in last_results.txt. The individual attestation files are
empty; a verbatim recovery is saved in resume_interruption_20261005/. Do not ask
for those old confirmations again. Boot 2 motion files are all empty and have
been preserved. No usable motion capture exists for that boot.

NEXT: obtain power-off duration for the CURRENT boot and current helmet/resting
conditions/readiness. Then capture and document a stationary baseline and the
saved 120-second guided sequence under boot3 labels. Give START only after raw
recording is verified. Never call a current-boot recording boot2 motion.
H1 still needs a replacement fully documented boot for the incomplete boot2
trial. I2 first-ten-minute coverage cannot be recovered on this already warm boot.

The latest integrity check passed 27/27, covering 823 archived hashes. That older
archive does not include this new session. Refresh it after the next completed
physical stage. Thirteen checklist IDs remain pending; see summaries/STATUS.md.
Headless, interrupt/IIO, modem and deposit prerequisites remain in
USER_PHASE_HANDOFF.md. No SMS sent. Frozen deployment artifacts unchanged.
'''
    (c.BASE / 'BOOT_RESUME.md').write_text(note)
    with (c.BASE / 'RESUME.txt').open('a') as f:
        f.write('\n\nSUPERSEDING CHECKPOINT\n' + note)
    handoff = c.BASE / 'USER_PHASE_HANDOFF.md'
    text = handoff.read_text()
    handoff.write_text('> Updated resume point: read BOOT_RESUME.md first. Boot 2 attestation is already recorded; its motion capture is empty. Current boot 3 identity is saved, awaiting power-removal attestation. Earlier boot-status prose below is historical.\n\n' + text)


if __name__ == '__main__':
    main()
