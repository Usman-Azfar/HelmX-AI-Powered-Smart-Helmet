"""Evidence utilities. Never relabel a failed/incomplete run as a pass."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
LOG = ROOT / 'piResults/last_results.txt'
sys.path[:0] = [str(ROOT), str(ROOT / 'deploy')]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False, default=lambda x: x.item() if hasattr(x, 'item') else str(x))+'\n')

def command(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return {'command':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except Exception as e:
        return {'command':args,'error':repr(e)}

def metadata():
    versions=BASE/'source_versions';versions.mkdir(exist_ok=True)
    for p in (BASE/'scripts').glob('*.py'):
        dst=versions/(sha(p)+'.py')
        if not dst.exists():dst.write_bytes(p.read_bytes())
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'argv':sys.argv,'python':sys.version,'platform':platform.platform(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'affinity':sorted(os.sched_getaffinity(0)), 'scheduler':os.sched_getscheduler(0),
            'priority':os.sched_getparam(0).sched_priority,
            'script_hashes':{p.name:sha(p) for p in (BASE/'scripts').glob('*.py')},
            'artifacts':json.loads((BASE/'hashes/initial_artifacts.json').read_text()),
            'services':command(['systemctl','list-units','--type=service','--state=running','--no-pager']),
            'i2c_openers':command(['fuser','-v','/dev/i2c-1']),
            'processes':command(['ps','-eo','pid,comm,pcpu,pmem,args']),
            'governor':{str(p):p.read_text().strip() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_governor')}}

def finish(ids, title, status, result, directory):
    directory = Path(directory)
    if not (directory/'metadata.json').exists():
        meta = metadata()
        meta['collection_scope'] = 'Collected at analysis finalization, not during the historical source recording. Service/process visibility may be restricted by the execution sandbox.'
        save(directory/'metadata.json', meta)
    save(directory/'summary.json', result)
    rendered = json.dumps(result, indent=2, allow_nan=False, default=str)
    text = f'\n{",".join(ids)} — {title}\nStatus: {status}\nUTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\nEvidence: {directory.relative_to(ROOT)}\n{rendered}\n'
    (directory/'README.txt').write_text(text)
    with LOG.open('a') as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    checklist = json.loads((BASE/'metadata/checklist.json').read_text())
    for item in checklist:
        if item['id'] in ids:
            item.update(status=status,evidence=str(directory.relative_to(ROOT)))
    save(BASE/'metadata/checklist.json',checklist)
    print(text,flush=True)
