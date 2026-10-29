"""Reconcile saved evidence and record prerequisites without inventing trials."""
import argparse
import datetime
import json
from pathlib import Path
import campaign as c

def reconcile():
    initial=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    checks={name:c.sha(c.ROOT/name)==value for name,value in initial.items()}
    if not all(checks.values()):
        raise RuntimeError('Frozen deployment/source/protocol artifact changed: '+str(checks))
    sanity=json.loads((c.BASE/'03_fifo_stationary_sanity/summary.json').read_text())
    equivalence=json.loads((c.BASE/'04_polling_fifo_equivalence/summary.json').read_text())
    if not sanity['stationary_physical_plausibility_gate'] or not equivalence['gate_passed']:
        raise RuntimeError('FIFO gates do not pass')
    c.finish(['B1'],'FIFO audit hardware-gate reconciliation','COMPLETE (CONFIGURATION QUALIFIED)',
             {'original_audit':'piResults/results/final-closure/02_fifo_parser_audit',
              'sanity_gate':'piResults/results/final-closure/03_fifo_stationary_sanity',
              'equivalence_gate':'piResults/results/final-closure/04_polling_fifo_equivalence',
              'artifact_hash_checks':checks,
              'interpretation':'Later B2/B3 evidence resolves the old hardware-gate-pending status. This is reconciliation, not a new physical trial. Physical silicon identity and mounting remain qualified. Historical faulty FIFO results remain debugging provenance, not evidence of FIFO inferiority.'},
             c.BASE/'02_fifo_gate_reconciliation')

def thermal():
    path=c.ROOT/'piResults/results/final-validation/long_soak/long_soak_summary.json'
    d=json.loads(path.read_text())
    if d['config']['actual_duration_min']<180 or d['n_exceptions']:
        raise RuntimeError('Historical soak not complete')
    keys=['config','n_input_samples','n_windows_generated','n_triggers','n_sensor_read_failures',
          'n_reconnects','n_exceptions','deadline_miss_count_gt_stride_budget','resources',
          'memory_leak_check','throttling_status']
    c.finish(['I1'],'Retain existing three-hour thermal evidence','SATISFIED (HISTORICAL SCOPE; NO NEW RUN)',
             {'source':str(path.relative_to(c.ROOT)),'sha256':c.sha(path),
              'basis':'last_test.txt I1 explicitly says no new run is required; section R preserves the existing 90-minute and three-hour soaks.',
              'recorded_evidence':{k:d[k] for k in keys},
              'limits':'No fresh three-hour measurement. Historical resource series supports CPU/RSS/temperature observations, but not missing per-axis bias drift or sensor-temperature records. Positive RSS drift is retained; the old stable-plateau label is not proof of zero memory drift.'},
             c.BASE/'thermal_I1_retained')

def configuration():
    directory=c.BASE/'06_high_range_register_check'
    regs=json.loads((directory/'registers_during.json').read_text())
    expected={'WHO_AM_I':0x70,'GYRO_CONFIG':0x18,'ACCEL_CONFIG':0x18,
              'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19}
    if any(regs[k]!=v for k,v in expected.items()):raise RuntimeError('Unexpected high-range readback')
    c.finish(['C1'],'High-range register-map interpretation','COMPLETE (MAP-QUALIFIED READBACK)',
             {'physical_test':'piResults/results/final-closure/06_high_range_register_check',
              'registers':regs,'AFS_SEL':3,'FS_SEL':3,'accel_full_scale_g':16,'gyro_full_scale_deg_s':2000,
              'accel_counts_per_g':2048,'gyro_counts_per_deg_s':16.4,
              'gyro_DLPF_CFG':4,'gyro_FCHOICE_B':0,'accel_A_DLPF_CFG':4,'accel_FCHOICE_B':0,
              'map_gyro_bandwidth_hz':20,'map_accel_bandwidth_hz':20,
              'map_internal_rate_hz':1000,'divider':19,'nominal_output_rate_hz':50,'host_target_hz':50,
              'source':'InvenSense RM-MPU-6500A-00 revision 2.1, sections 4.4–4.8, pages 12–15.',
              'official_source_url':'https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6500-Register-Map2.pdf',
              'manufacturer_document_mirror_read':'https://www.ic-components.jp/files/5b/MPU-6500.pdf',
              'limits':'Interpretation assumes the compatible MPU6500 register map. Silicon provenance is unproven. Nominal bandwidth and ODR are register-derived, not independent anti-alias or physical-clock measurements.'},
             c.BASE/'06_high_range_configuration')

def deferred():
    groups=[
        (['A1','H1','I2'],'USER POWER CYCLES / GUIDED MOTION',
         'Three full Pi+sensor power cycles, at least ten seconds powered off, with identity capture, five-minute stationary baseline and guided motion on each boot. Warm-start comparison requires a genuinely fresh cold baseline and >=60-minute warm measurement.'),
        (['C3'],'USER GUIDED MOTION',
         'Present operator performs all eleven safe high-range helmet scenarios. Do not substitute historical motion or simulated data.'),
        (['D1','D2','D3','D4','K1'],'USER SESSION HANDOFF',
         'True headless tests require the interactive IDE/desktop session to exit. Prepare detached capture and restore services afterward; do not label this active session headless. Optional randomized repeats require preregistered pair order.'),
        (['J1','J2','J3'],'WIRING / DRIVER PREREQUISITE',
         'Confirm actual IMU INT wiring and GPIO assignment; kernel-buffered acquisition also needs supported device configuration. No pin guessing or unverified device-tree changes.'),
        (['P'],'MODEM HARDWARE / RECEIPT',
         'Host check on resumption found no /dev/ttyUSB* modem. Requires existing modem connection/configuration and any manual receipt verification. No SMS has been sent by this campaign.'),
        (['Q4'],'AUTHOR / DEPOSIT INPUT',
         'Requires legally shareable dataset/license confirmation, author metadata, destination account and review of the local archive. No deposit or DOI claimed.')]
    items=json.loads((c.BASE/'metadata/checklist.json').read_text())
    grouped=[]
    for ids,reason,description in groups:
        pending=[x['id'] for x in items if x['id'] in ids and x['status']=='PENDING']
        if pending:grouped.append({'ids':pending,'reason':reason,'next_step':description})
    result={'groups':grouped,'count_deferred_items':sum(len(g['ids']) for g in grouped),
            'rule':'These remain PENDING in the checklist. Prerequisite documentation does not count as a completed experiment.'}
    c.finish([],'User-dependent tests reserved for the final phase','DEFERRED — NOT PERFORMED',result,c.BASE/'manual_phase_remaining')
    (c.BASE/'MANUAL_PHASE.md').write_text('# Remaining user-dependent phase\n\n'+
        '\n\n'.join('**'+', '.join(g['ids'])+' — '+g['reason']+'**\n\n'+g['next_step'] for g in grouped)+'\n')

def status():
    items=json.loads((c.BASE/'metadata/checklist.json').read_text())
    motion=json.loads((c.BASE/'motion_C3_completed/summary.json').read_text())
    archive=json.loads((c.BASE/'archive_Q3/summary.json').read_text())
    validation=json.loads((c.BASE/'validation_resumed_campaign/summary.json').read_text())
    pending=[i['id'] for i in items if i['status']=='PENDING']
    count=sum(bool(i['evidence']) for i in items)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report=(f'# Current campaign status\n\nUpdated UTC: {now}\n\n'
            f'{count} of {len(items)} items have evidence; {len(pending)} remain pending. '
            'Evidence qualifications below are part of the result, not a claim that all requested physical experiments passed.\n\n'
            'C3 now contains all 11 saved high-range guided phases. The previous partial label was hard-coded '
            'despite an empty remaining-phase list. Fresh replay verification matched the saved scores and policy decisions exactly. '
            'The first tilt attempt remains excluded. Donning onset coverage remains unproven.\n\n'
            f'Motion totals: {motion["totals"]["samples"]:,} samples, {motion["totals"]["windows"]:,} scored windows, '
            f'{motion["totals"]["confirmed_alerts"]} confirmed policy events; zero recorded acceleration/gyro rail hits. '
            'These are separate benign-motion trials, not crash sensitivity or a road false-alert rate.\n\n'
            'All currently executable autonomous checklist experiments have evidence. Remaining work needs physical power cycles, '
            'a true headless session, wiring/driver confirmation, modem hardware, or deposit metadata. '
            'See `USER_PHASE_HANDOFF.md` for the next steps.\n\n'
            f'Latest local archive: `{archive["directory"]}`. Not published.\n\n'
            f'Integrity: {sum(validation["checks"].values())}/{len(validation["checks"])} checks passed; '
            f'{validation["archive_files_hashed"]} archived files hashed; '
            f'{len(validation["hash_mismatches"])} mismatches.\n\n'
            '| ID | Requirement | Status |\n|---|---|---|\n'+
            '\n'.join(f'| {i["id"]} | {i["title"]} | {i["status"]} |' for i in items)+'\n')
    (c.BASE/'summaries/STATUS.md').write_text(report)
    c.finish([], 'Campaign status reconciliation', 'AUTONOMOUS WORK COMPLETE; USER PHASE PENDING',
             {'items_with_evidence':count,'checklist_items':len(items),'pending_ids':pending,
              'motion_totals':motion['totals'],'archive':archive['directory'],
              'integrity_checks_passed':all(validation['checks'].values()),
              'scope':'Status reconciliation and saved-data verification; no new power cycle, headless capture, interrupt capture, or modem trial claimed.'},
             c.BASE/'status_reconciliation')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['reconcile','thermal','deferred','configuration','status']);a=p.parse_args()
    {'reconcile':reconcile,'thermal':thermal,'deferred':deferred,'configuration':configuration,'status':status}[a.action]()
