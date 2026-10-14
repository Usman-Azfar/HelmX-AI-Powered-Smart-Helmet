"""Create a local reviewable research archive; does not upload or invent a DOI."""
import json
import shutil
import time
from pathlib import Path
import campaign as c

def main():
    target=c.BASE/('release_candidate_'+time.strftime('%Y%m%dT%H%M%S'))
    target.mkdir(exist_ok=False)
    excluded={'__pycache__','.scratch','.git','.pi_research_venv','execution_logs','archive','metadata','last_test.txt'}
    for name in ['src','scripts','deploy','models','datasets_used']:
        shutil.copytree(c.ROOT/name,target/name,ignore=lambda directory,names:[n for n in names if n in excluded or n.endswith(('.pyc','.log','.out'))])
    shutil.copy2(c.ROOT/'requirements.txt',target/'requirements.txt')
    for name in ['README.md','LICENSE','CITATION.cff','DATA_LICENSES.md']:
        if (c.ROOT/name).exists():shutil.copy2(c.ROOT/name,target/name)
    shutil.copy2(c.BASE/'DEPLOYED_POLICY_THRESHOLDS.json',target/'DEPLOYED_POLICY_THRESHOLDS.json')
    legacy=target/'legacy_not_used_in_paper';legacy.mkdir()
    shutil.copy2(c.ROOT/'crash-gpt/models/thresholds.json',legacy/'crash_gpt_thresholds.json')
    (legacy/'README.txt').write_text('Historical threshold file, not used by the current deployment or new evidence campaign. Retained only to explain archive provenance.\n')
    evidence=target/'piResults/results/final-closure';evidence.mkdir(parents=True)
    for path in c.BASE.iterdir():
        if path.name in excluded or path.name.startswith('release_candidate_') or path.name in ['RESUME.txt','archive_Q3']:continue
        if path.is_dir():shutil.copytree(path,evidence/path.name,ignore=lambda directory,names:[n for n in names if n in excluded or n.endswith(('.pyc','.log','.out'))])
        elif path.suffix in ['.json','.csv','.npz','.npy','.service']:shutil.copy2(path,evidence/path.name)
    shutil.copytree(c.BASE/'scripts',evidence/'scripts',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (evidence/'metadata').mkdir(exist_ok=True)
    for name in ['checklist.json','environment_packages.txt']:
        if (c.BASE/'metadata'/name).exists():shutil.copy2(c.BASE/'metadata'/name,evidence/'metadata'/name)
    (evidence/'model_cache/README.txt').write_text('Frozen derived analysis inputs and predictions, retained because the analysis scripts load them directly. Regenerate with model_analysis.py L1 after restoring the training data layout. These are reproducibility inputs, not disposable interpreter caches.\n')
    # Historical raw inputs remain explicitly historical, but must be included
    # for the newly computed stream/presentation tables to be reproducible.
    historical=c.ROOT/'piResults/results/final-validation'
    required=[historical/'final_aba_acquisition_test/A1_polling/raw_sensor.csv',
              historical/'clipping/motion_session_raw.csv',historical/'clipping/motion_session_raw_part2.csv']
    required+=sorted((historical/'scheduler_repeats').glob('run*_dt.csv'))
    required+=sorted((historical/'scheduler_repeats').glob('run*_detector.json'))
    required+=[historical/'long_soak/long_soak_summary.json']
    for source in required:
        destination=target/source.relative_to(c.ROOT)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
    for name in ['final_aba_acquisition_test','mpu_config']:
        shutil.copytree(historical/name,target/'piResults/results/final-validation'/name,dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.log','__pycache__'))
    # Models/inputs are byte-exact. Human-readable metadata gets portable paths.
    converted=[]
    empty_metadata=[]
    for path in target.rglob('*'):
        if path.is_file() and path.name=='metadata.json':
            raw_metadata=path.read_text()
            if not raw_metadata.strip():
                empty_metadata.append(str(path.relative_to(target)))
                continue  # Retain interrupted-run files byte-for-byte, never invent metadata.
            metadata=json.loads(raw_metadata)
            if isinstance(metadata,dict):
                metadata.pop('processes',None)
                c.save(path,metadata)
        if path.is_file() and path.suffix in ['.txt','.json','.md','.csv','.yaml']:
            try:old=path.read_text()
            except UnicodeError:continue
            new=old.replace(str(c.ROOT)+'/','').replace('/home/helmx/Crash Detection/','')
            if new!=old:path.write_text(new);converted.append(str(path.relative_to(target)))
    (target/'README_REVIEW.txt').write_text('LOCAL REVIEW CANDIDATE — not deposited or publicly published.\nModel/data binaries retained byte-for-byte; readable paths normalized to portable relative paths.\nNo reviewer correspondence, notebooks, virtual environments, agent checkpoint metadata, process lists, temporary execution logs, or existing manuscript PDFs included.\nDataset license/source-owner confirmation and author/deposit metadata are required before any public upload.\nUnperformed tests remain unperformed; see included evidence summaries.\nReproducibility: copy datasets_used/{carla,road,fall,near-fall,darus} to data/ before using the source loaders.\nThe closure model_cache contains frozen derived inputs needed by L2–L10 and GPIO trace replay. L1 regenerates it.\nHistorical faulty FIFO evidence is retained only as debugging provenance; use the corrected closure evidence for scientific interpretation.\nHost service/process metadata collected in a sandbox is not proof of a headless environment.\n')
    c.save(target/'INCOMPLETE_METADATA.json', {'empty_metadata_preserved':empty_metadata,
           'scope':'Empty metadata belongs to interrupted/incomplete records, not completed trials. Consult resume interruption audit.'})
    manifest={str(p.relative_to(target)):c.sha(p) for p in target.rglob('*') if p.is_file()}
    c.save(target/'SHA256_MANIFEST.json',manifest)
    result={'directory':str(target.relative_to(c.ROOT)),'files_hashed_before_completion_snapshot':len(manifest),'portable_text_files':converted,
            'status':'Local curated candidate only; not uploaded. License/author/deposit review outstanding.',
            'original_project':'Untouched. Legacy threshold is segregated in this candidate rather than breaking the historical crash-gpt project.'}
    c.finish(['Q3'],'Clean local research archive','COMPLETE (REVIEW CANDIDATE; NOT PUBLISHED)',result,c.BASE/'archive_Q3')
    # Capture Q3 completion in the archived checklist, then recompute its hash.
    shutil.copy2(c.BASE/'metadata/checklist.json',evidence/'metadata/checklist.json')
    (evidence/'archive_Q3').mkdir(exist_ok=True)
    for name in ['summary.json','README.txt']:
        shutil.copy2(c.BASE/'archive_Q3'/name,evidence/'archive_Q3'/name)
    manifest={str(p.relative_to(target)):c.sha(p) for p in target.rglob('*') if p.is_file() and p.name!='SHA256_MANIFEST.json'}
    c.save(target/'SHA256_MANIFEST.json',manifest)

if __name__=='__main__':main()
