"""Derive provenance and presentation data from code and new prediction files."""
import argparse
import csv
import json
import zipfile
import numpy as np
import campaign as c
from model_analysis import CACHE,load,decisions,events,grouped

def table(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def sources():
    from src import io_loaders,manifest
    raw=io_loaders.load_all_sessions();split=json.loads((CACHE/'split.json').read_text());rows=[]
    for source in sorted(set(s.source for s in raw)):
        ss=[s for s in raw if s.source==source]
        row={'source':source,'physical_or_simulated':'simulated' if source in ['carla','darus'] else 'physical',
             'placement':'simulated motorcycle body' if source=='darus' else 'not available (not inferred from model inputs)',
             'native_rate':'CARLA 20 Hz assumed, not measured' if source=='carla' else 'not available in frozen provenance; resampled loader output must not be called native rate',
             'original_accel_units':'m/s^2 (pipeline assumption)','original_gyro_units':'deg/s' if ss[0].gyro_in_deg_per_s else 'rad/s',
             'original_full_scale':'not available','original_anti_alias':'not available',
             'session_count':len(ss),'resampling':'linear np.interp to 50 Hz; no explicit anti-alias low-pass before downsampling',
             'padding':'edge-repeat to at least 150 samples, labels padded zero' if source=='darus' else 'none',
             'labeling':'per-timestep simulation label, interpolated then >0.5' if source=='darus' else ('weak peak-severity heuristic' if source in ['fall','near_fall'] else 'normal recording-level')}
        for sp in ['train','val','test']:
            ds=np.load(CACHE/(sp+'.npz'));mask=ds['sources']==source
            row[sp+'_sessions']=sum(split[s.session_id]==sp for s in ss)
            row[sp+'_normal_windows']=int(sum(mask&(ds['y']==0)));row[sp+'_positive_windows']=int(sum(mask&(ds['y']==1)))
        rows.append(row)
    out=c.BASE/'provenance_M1';table(out/'per_source.csv',rows)
    c.finish(['M1'],'Per-source provenance','COMPLETE WITH EXPLICIT UNKNOWNS',{'sources':rows,'note':'Archive prose contains conflicting road-data origin descriptions. This table does not certify an in-house origin or source license. Original sensor metadata needs source-owner records.'},out)

def weak():
    result={'ANOMALY_TOP_FRACTION':.3,'severity_metric':'Maximum acceleration magnitude within each 60-sample window after canonical gravity removal, before normalizer scaling.',
            'rule':'For each fall/near_fall file, positive iff severity >= session 70th percentile. Ties can make the positive fraction exceed 30%. Other windows become label 0, although they belong to a crash-like recording.',
            'label_caveat':'Weak positives are not independently annotated crash onsets. DaRUS uses interpolated per-timestep simulation labels and any-positive window assignment. Accuracy against these labels is not physical crash sensitivity.',
            'window_loop':'range(0, len(df)-60, 15), exclusive stop; runtime may score one extra terminal window, excluded explicitly from aligned comparisons.'}
    c.finish(['M2'],'Weak-label disclosure','COMPLETE',result,c.BASE/'provenance_M2')

def sessions():
    d,s,th=load();rows=[];ev={k:events(s[k],d['sids'],th) for k in s.files}
    for sid in dict.fromkeys(d['sids'].tolist()):
        mask=d['sids']==sid;source=str(d['sources'][mask][0]);row={'session':sid,'source':source,'windows':int(sum(mask)),'positive_labels':int(sum(d['y'][mask])),
             'label_type':'simulation timestep' if source=='darus' else ('weak severity' if source in ['fall','near_fall'] else 'normal recording')}
        for key in ['reference','causal_float','offline_int8','deployed']:
            row[key+'_trigger']=ev[key][sid]['event_detected'];row[key+'_indices']=json.dumps(ev[key][sid]['trigger_indices'])
        rows.append(row)
    out=c.BASE/'provenance_M3';table(out/'test_sessions.csv',rows);c.finish(['M3'],'Held-out session composition','COMPLETE',{'sessions':rows,'note':'All use exactly the same session-aligned labeled windows. Extra runtime tail windows disclosed separately.'},out)

def domains():
    d,s,th=load();ref=decisions(s['reference'],th)[2];result={}
    for source in sorted(set(d['sources'])):
        mask=d['sources']==source
        result[source]={k:grouped(ref[mask],decisions(s[k],th)[2][mask],d['y'][mask]) for k in ['causal_float','offline_int8','deployed']}
    c.finish(['M4'],'Source-stratified fidelity','COMPLETE',{'by_source':result,'limitation':'Small source/session strata are descriptive only; source absence from test is not inferred as perfect agreement.'},c.BASE/'provenance_M4')

def thresholds():
    th=json.loads((c.BASE/'frozen/models/thresholds.json').read_text());cfg=(c.BASE/'frozen/deploy/config.yaml')
    legacy=c.ROOT/'crash-gpt/models/thresholds.json'
    if not legacy.exists():legacy=c.ROOT/'legacy_not_used_in_paper/crash_gpt_thresholds.json'
    result={'classifier_prob':th['classifier_prob_balanced'],'recon_error':th['recon_error'],'operator':'strict >; classifier OR reconstruction',
            'consecutive_windows':3,'cooldown_seconds':60,'current_timing_guard_max_dt_s':.06,'historical_timing_guard_max_dt_s':.03,
            'threshold_sha256':c.sha(c.BASE/'frozen/models/thresholds.json'),'config_sha256':c.sha(cfg),
            'legacy_thresholds':json.loads(legacy.read_text()),
            'archive_policy':'Legacy thresholds segregated in the clean archive; original historical project retained intact for provenance.'}
    c.save(c.BASE/'DEPLOYED_POLICY_THRESHOLDS.json',result)
    c.finish(['Q1'],'Authoritative deployment policy','COMPLETE',result,c.BASE/'archive_Q1')

def training():
    with zipfile.ZipFile(c.BASE/'frozen/models/helmx_crash_model.keras') as z:
        conf=json.loads(z.read('config.json'));meta=json.loads(z.read('metadata.json'))
    history=json.loads((c.ROOT/'models/training_history.json').read_text())
    result={'artifact_compile_config':conf.get('compile_config'),'keras_metadata':meta,'batch_size_from_train_py':128,
            'max_epochs_from_train_py':60,'early_stopping':{'monitor':'val_crash_prob_auc','mode':'max','patience':8,'restore_best_weights':True},
            'completed_history_epochs':len(next(iter(history.values()))),'best_val_auc_epoch_1_based':int(np.argmax(history['val_crash_prob_auc']))+1,
            'split_seed':42,'training_entrypoint_seed':42,'multi_seed_experiment_seeds':[42,43,44,45,46],
            'selection_criterion':'Maximum validation classifier AUC in train.py. Thresholds separately calibrated on validation data.',
            'limitation':'The .keras artifact records optimizer/loss configuration, not the random seed. Seed 42 is the source entrypoint, not independently embedded execution provenance.'}
    c.finish(['Q2'],'Training configuration audit','COMPLETE',result,c.BASE/'archive_Q2')

def figures():
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d,s,th=load();ref=decisions(s['reference'],th)[2];out=c.BASE/'presentation_N2';out.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(7,4));names=['causal_float','offline_int8','deployed'];pos=np.arange(3)
    for off,label,mask in [(-.18,'Normal',d['y']==0),(.18,'Crash-like',d['y']==1)]:
        vals=[np.mean(ref[mask]==decisions(s[k],th)[2][mask])*100 for k in names]
        bars=ax.bar(pos+off,vals,.36,label=label)
        ax.bar_label(bars,fmt='%.2f%%',fontsize=8)
    ax.set(xticks=pos,xticklabels=['Causal filter only','INT8 only','Composed deployment'],ylabel='OR decision agreement (%)',ylim=(0,110));ax.legend();fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(out/('class_fidelity.'+ext),dpi=180)
    plt.close(fig)
    c.finish(['N2'],'Class-fidelity figure','COMPLETE',{'inputs':'New L1/L2/L3 aligned predictions; full 2x2 tables in respective summaries.','files':['class_fidelity.png','class_fidelity.pdf']},out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['M1','M2','M3','M4','Q1','Q2','N2']);a=p.parse_args()
    {'M1':sources,'M2':weak,'M3':sessions,'M4':domains,'Q1':thresholds,'Q2':training,'N2':figures}[a.experiment]()
