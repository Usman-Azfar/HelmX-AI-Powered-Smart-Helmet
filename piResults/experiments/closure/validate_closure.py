"""Verify completed evidence and the local archive without rerunning experiments."""
import csv
import json
from pathlib import Path
import campaign as c

def read(path):return json.loads(path.read_text())

def main():
    checks={}
    checklist=read(c.BASE/'metadata/checklist.json')
    checks['all_recorded_evidence_exists']=all(
        (c.ROOT/i['evidence']/'summary.json').exists() for i in checklist if i['evidence'])
    for folder,filename,count_key,duration in [
            ('06_high_range_register_check','raw.csv','samples',10),
            ('06_high_range_stationary','raw.csv','samples',600),
            ('08_high_range_20min','raw_sensor.csv','n_samples',1200)]:
        directory=c.BASE/folder;summary=read(directory/'summary.json')
        with (directory/filename).open() as f:rows=sum(1 for _ in csv.reader(f))-1
        checks[folder+'_rows_match']=rows==summary[count_key]
        checks[folder+'_full_duration']=summary['elapsed_s']>=duration
        checks[folder+'_no_exception']=summary['exception'] is None
    directory=c.BASE/'08_high_range_20min'
    with (directory/'window_scores.csv').open() as f:rows=sum(1 for _ in csv.reader(f))-1
    checks['C4_window_rows_match']=rows==read(directory/'summary.json')['n_windows']
    motion=read(c.BASE/'motion_C3_completed/summary.json')
    plan=read(c.BASE/'07_high_range_benign_motion/guided_plan.json')
    checks['C3_all_eleven_phases']=([r['phase'] for r in motion['phases']]==plan['phases']
                                   and motion['phase_count']==11)
    checks['C3_source_hashes_match']=all(
        c.sha(c.BASE/'07_high_range_benign_motion'/phase/name)==digest
        for phase,files in motion['source_hashes'].items() for name,digest in files.items())
    checks['C3_all_replays_exact']=all(
        all(read(c.BASE/'07_high_range_benign_motion'/(phase+'_resume_verification')/'summary.json')['checks'].values())
        for phase in plan['phases'])
    checks['C3_totals_match']=all(motion['totals'][key]==sum(r[key] for r in motion['phases'])
                                 for key in motion['totals'])
    table=c.BASE/'presentation_N5_high_range'
    checks['N5_table_hash_matches']=c.sha(table/'benign_motion.csv')==read(table/'summary.json')['table_sha256']
    checks['O1_fifty_pulses']=len(read(c.BASE/'gpio_O1/pulse_timestamps.json'))==50
    gpio=read(c.BASE/'gpio_G_O2/summary.json')
    checks['G_ten_to_twenty_traces']=10<=gpio['trials']<=20
    checks['G_no_sms_attempts']=all(
        r['cancel_outcome'] is None or
        (r['cancel_outcome']['cancelled'] and not r['cancel_outcome']['sms_attempted'])
        for r in gpio['trace_summary'])
    target=c.ROOT/read(c.BASE/'archive_Q3/summary.json')['directory']
    manifest=read(target/'SHA256_MANIFEST.json')
    mismatches=[name for name,digest in manifest.items()
                if not (target/name).is_file() or c.sha(target/name)!=digest]
    files={str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}
    checks['archive_hashes_match']=not mismatches
    checks['archive_manifest_covers_all_files']=files==set(manifest)|{'SHA256_MANIFEST.json'}
    forbidden=[name for name in files if
               any(p in {'__pycache__','.scratch','.git','execution_logs','last_test.txt','RESUME.txt'} for p in Path(name).parts)
               or Path(name).suffix in {'.pyc','.ipynb','.aux','.log','.out'}]
    checks['archive_excludes_working_and_reviewer_files']=not forbidden
    archived=read(target/'piResults/results/final-closure/metadata/checklist.json')
    checks['archive_checklist_current']=archived==checklist
    checks['archive_evidence_references_resolve']=all(
        (target/i['evidence']/'summary.json').exists() for i in archived if i['evidence'])
    required=['model_cache/test.npz','model_cache/scores.npz','model_cache/raw_test_sessions.npz',
              'model_cache/val.npz','model_cache/train.npz','model_cache/causal_inputs.npz']
    checks['archive_analysis_inputs_present']=all((target/'piResults/results/final-closure'/p).exists() for p in required)
    checks['archive_C3_closure_current']=(read(target/'piResults/results/final-closure/motion_C3_completed/summary.json')==motion)
    checks['deployed_artifacts_unchanged']=all(c.sha(c.ROOT/p)==h for p,h in read(c.BASE/'hashes/initial_artifacts.json').items())
    result={'checks':checks,'archive_files_hashed':len(manifest),'hash_mismatches':mismatches,
            'forbidden_archive_paths':forbidden,'checklist_items':len(checklist),
            'items_with_evidence':sum(bool(i['evidence']) for i in checklist),
            'pending_ids':[i['id'] for i in checklist if i['status']=='PENDING'],
            'scope':'Evidence integrity checks only; no new hardware performance or physical-safety claim.'}
    c.finish([],'Resumed campaign evidence and archive verification',
             'PASS' if all(checks.values()) else 'FAIL — SEE CHECKS',result,c.BASE/'validation_resumed_campaign')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
