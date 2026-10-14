"""Fresh model evidence, using frozen thresholds and session-aligned windows.

No training or replacement of deployment artifacts. Each command logs its
experiment before returning. Test labels are frozen from the reference path.
"""
import argparse
import dataclasses
import json
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS','2')
os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
import numpy as np
import campaign as c

CACHE=c.BASE/'model_cache'
COLS=['ax','ay','az','gx','gy','gz']

def env():
    import crash_monitor as cm
    from src import io_loaders,preprocess,manifest,normalize,units,features
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml')
    norm=normalize.Normalizer.load(c.BASE/'frozen/models/normalizer.npz')
    th=json.loads((c.BASE/'frozen/models/thresholds.json').read_text())
    return cm,io_loaders,preprocess,manifest,units,features,cfg,norm,th

def keras_model():
    import tensorflow as tf
    from src import model as registration
    return tf.keras.models.load_model(c.BASE/'frozen/models/helmx_crash_model.keras',compile=False)

def float_scores(model,norm,seq,aux):
    s,a=norm.transform(seq,aux)
    pred=model.predict({'seq':s.astype('float32'),'aux':a.astype('float32')},batch_size=128,verbose=0)
    return np.column_stack([pred['crash_prob'].ravel(),pred['recon_error'].ravel()])

def int_scores(model,seq,aux):
    return np.asarray([model.predict(s,a) for s,a in zip(seq,aux)])

def decisions(scores,th,key='classifier_prob_balanced'):
    clf=scores[:,0]>th[key]; rec=scores[:,1]>th['recon_error']
    return clf,rec,clf|rec

def metrics(y,p):
    tp=int(np.sum((y==1)&p));fp=int(np.sum((y==0)&p));fn=int(np.sum((y==1)&~p));tn=int(np.sum((y==0)&~p))
    return {'tn':tn,'fp':fp,'fn':fn,'tp':tp,'precision':tp/(tp+fp) if tp+fp else 0.,
            'recall':tp/(tp+fn) if tp+fn else 0.,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.}

def transitions(a,b):
    return {'ref_neg_to_trans_neg':int(sum(~a&~b)),'ref_neg_to_trans_pos':int(sum(~a&b)),
            'ref_pos_to_trans_neg':int(sum(a&~b)),'ref_pos_to_trans_pos':int(sum(a&b)),
            'n':len(a),'agreement':float(np.mean(a==b)) if len(a) else None}

def grouped(a,b,y):
    return {name:transitions(a[m],b[m]) for name,m in [('overall',np.ones(len(y),bool)),('normal',y==0),('crash_like',y==1)]}

def events(scores,sids,th,key='classifier_prob_balanced'):
    import crash_monitor as cm
    result={}
    for sid in dict.fromkeys(sids.tolist()):
        ss=scores[sids==sid]; policy=cm.TriggerPolicy(th[key],th['recon_error'],3,60)
        triggers=[];triple=[];positive=decisions(ss,th,key)[2]
        for i,(p,r) in enumerate(ss):
            _,fired=policy.update(float(p),float(r),now=1.18+.3*i)
            if fired:triggers.append(i)
            if i>=2 and positive[i-2:i+1].all():triple.append(i)
        result[sid]={'trigger_indices':triggers,'trigger_times_s':[1.18+.3*i for i in triggers],
                     'overlapping_three_positive_positions':triple,
                     'event_detected':bool(triggers)}
    return result

def compare(a,b,y,sids,th,key='classifier_prob_balanced'):
    da=decisions(a,th,key);db=decisions(b,th,key)
    return {'classifier':grouped(da[0],db[0],y),'reconstruction':grouped(da[1],db[1],y),
            'or':grouped(da[2],db[2],y),'reference_metrics':metrics(y,da[2]),'transformed_metrics':metrics(y,db[2]),
            'score_mae':{'classifier':float(np.mean(abs(a[:,0]-b[:,0]))),'reconstruction':float(np.mean(abs(a[:,1]-b[:,1])))},
            'reference_events':events(a,sids,th,key),'transformed_events':events(b,sids,th,key)}

def prepare():
    cm,io,pre,manifest,units,features,cfg,norm,th=env()
    CACHE.mkdir(exist_ok=True)
    c.save(CACHE/'metadata.json',c.metadata())
    raw=io.load_all_sessions();split=manifest.assign_splits(raw)
    canonical=pre.canonicalize_all(raw)
    # Preserve all split membership and dataset sizes for independent checks.
    c.save(CACHE/'split.json',split)
    for name in ['train','val','test']:
        ds=manifest.build_dataset(canonical,split,name)
        np.savez_compressed(CACHE/(name+'.npz'),seq=ds.X_seq,aux=ds.X_aux,y=ds.y,sids=ds.session_id.astype(str),sources=ds.source.astype(str))
    ds=np.load(CACHE/'test.npz');net=keras_model()
    lite=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
    float_ref=float_scores(net,norm,ds['seq'],ds['aux']);int_ref=int_scores(lite,ds['seq'],ds['aux'])
    causal_seq=[];causal_aux=[];causal_training_aux=[];raw_sequences={};alignment=[]
    for s in raw:
        if split[s.session_id]!='test':continue
        x=units.gyro_to_deg_per_s(s.df,s.gyro_in_deg_per_s)
        raw_sequences[s.session_id]=x[COLS].to_numpy()
        filtered=x.copy();filt=cm.CausalGravityFilter(.3,50)
        vals=np.asarray([filt.apply(row) for row in x[COLS[:3]].to_numpy()])
        filtered[COLS[:3]]=vals
        # Counterfactual causal filter with the same training-side auxiliary formula.
        filtered=features.add_derived_columns(filtered)
        cs=dataclasses.replace(s,df=filtered,gyro_in_deg_per_s=True)
        cd=manifest.build_dataset([cs],{s.session_id:'test'},'test')
        expected=int(sum(ds['sids']==s.session_id))
        assert len(cd.y)==expected, (s.session_id,len(cd.y),expected)
        causal_seq.extend(cd.X_seq)
        causal_aux.extend(cm.compute_aux_features(w) for w in cd.X_seq)
        causal_training_aux.extend(cd.X_aux)
        live_count=1+(len(x)-60)//15 if len(x)>=60 else 0
        alignment.append({'session':s.session_id,'samples':len(x),'reference_windows':expected,
                          'live_windows_if_all_samples_scored':live_count,'unmatched_live_tail_windows':live_count-expected})
    cs=np.asarray(causal_seq,dtype='float32');ca=np.asarray(causal_aux,dtype='float32');cta=np.asarray(causal_training_aux,dtype='float32')
    assert len(cs)==len(ds['y'])
    np.savez_compressed(CACHE/'raw_test_sessions.npz',**raw_sequences)
    np.savez_compressed(CACHE/'causal_inputs.npz',seq=cs,aux=ca,training_aux=cta)
    np.savez_compressed(CACHE/'scores.npz',reference=float_ref,offline_int8=int_ref,
                        causal_float=float_scores(net,norm,cs,cta),
                        causal_runtime_float=float_scores(net,norm,cs,ca),
                        deployed=int_scores(lite,cs,ca))
    c.save(CACHE/'alignment.json',alignment)
    c.save(CACHE/'data_hashes.json',{str(p.relative_to(c.ROOT)):c.sha(p) for src in ['carla','road','fall','near-fall','darus'] for p in (c.ROOT/'data'/src).rglob('*') if p.is_file() and p.suffix in ['.csv','.tab']})

def load():
    d=np.load(CACHE/'test.npz');s=np.load(CACHE/'scores.npz');th=json.loads((c.BASE/'frozen/models/thresholds.json').read_text())
    return d,s,th

def fidelity(which):
    out=c.BASE/('model_'+which);out.mkdir(exist_ok=True)
    c.save(out/'metadata.json',c.metadata())
    if which=='L1':prepare()
    d,s,th=load();a=s['reference'];key={'L1':'deployed','L2':'causal_float','L3':'offline_int8'}[which];b=s[key]
    result=compare(a,b,d['y'],d['sids'],th)
    result['method']={'L1':'offline float with original training preprocessing/features versus exact causal deployment features and INT8',
                      'L2':'Isolated causal EMA vs zero-phase Butterworth; SAME Keras model and training-side feature formula. Not the confounded historical replay.',
                      'L3':'Same offline inputs and auxiliary features: Keras versus deployed INT8.'}[which]
    result['auxiliary_mismatch']='Training jerk is abs(gradient(accel magnitude, seconds)); runtime jerk is max(abs(diff(accel magnitude))) without dt division. L1 includes this implementation difference; L2 isolates filter by holding formula fixed.'
    result['alignment']=json.loads((CACHE/'alignment.json').read_text())
    result['policy_note']='Three consecutive positive scored windows, cooldown 60 s, nominal 50-Hz replay. No SMS/countdown blocking simulated. No hardware deadline claim.'
    # All flips carry session index, reference label and both score margins.
    flips=[];ao=decisions(a,th)[2];bo=decisions(b,th)[2]
    for sid in dict.fromkeys(d['sids'].tolist()):
        inds=np.flatnonzero(d['sids']==sid)
        for local,i in enumerate(inds):
            if ao[i]==bo[i]:continue
            flips.append({'global_index':int(i),'session':sid,'source':str(d['sources'][i]),'window_index':local,'label':int(d['y'][i]),
                          'reference_scores':a[i].tolist(),'transformed_scores':b[i].tolist(),
                          'reference_margin':(a[i]-[th['classifier_prob_balanced'],th['recon_error']]).tolist(),
                          'transformed_margin':(b[i]-[th['classifier_prob_balanced'],th['recon_error']]).tolist(),
                          'in_reference_confirmation_triplet':any(local<=j<=local+2 for j in result['reference_events'][sid]['overlapping_three_positive_positions']),
                          'in_transformed_confirmation_triplet':any(local<=j<=local+2 for j in result['transformed_events'][sid]['overlapping_three_positive_positions'])})
    c.save(out/'flipped_windows.json',flips)
    result['branch_counts']={name:{'classifier_only':int(sum(cl&~rc)),'reconstruction_only':int(sum(~cl&rc)),'both':int(sum(cl&rc)),'neither':int(sum(~cl&~rc))} for name,(cl,rc,_) in [('reference',decisions(a,th)),('transformed',decisions(b,th))]}
    c.finish([which],which+' fidelity','COMPLETE',result,out)

def bootstrap():
    d,s,th=load();y=d['y'];sid=d['sids'];unique=list(dict.fromkeys(sid.tolist()));rng=np.random.default_rng(20260929)
    ref=decisions(s['reference'],th)[2];trans={k:decisions(s[k],th)[2] for k in ['causal_float','offline_int8','deployed']}
    stats={k:[] for k in ['causal_crash_agreement','int8_crash_agreement','composed_overall_agreement','precision','recall','f1']}
    for _ in range(2000):
        idx=np.concatenate([np.flatnonzero(sid==u) for u in rng.choice(unique,len(unique),replace=True)])
        crash=idx[y[idx]==1]
        stats['causal_crash_agreement'].append(float(np.mean(ref[crash]==trans['causal_float'][crash])) if len(crash) else None)
        stats['int8_crash_agreement'].append(float(np.mean(ref[crash]==trans['offline_int8'][crash])) if len(crash) else None)
        stats['composed_overall_agreement'].append(float(np.mean(ref[idx]==trans['deployed'][idx])))
        m=metrics(y[idx],trans['deployed'][idx])
        for k in ['precision','recall','f1']:stats[k].append(m[k] if np.any(y[idx]==1) else None)
    result={'n_sessions':len(unique),'replicates':2000,'seed':20260929,'method':'Whole-session percentile bootstrap, with replacement. Undefined crash-free draws excluded and counted. Window metrics, NOT real-road rates.',
            'intervals':{k:{'p2_5':float(np.percentile([v for v in vs if v is not None],2.5)),'p97_5':float(np.percentile([v for v in vs if v is not None],97.5)),'undefined_draws':sum(v is None for v in vs)} for k,vs in stats.items()}}
    out=c.BASE/'model_L4';c.save(out/'bootstrap_draws.json',stats);c.finish(['L4'],'Session-clustered uncertainty','COMPLETE',result,out)

def sensitivity():
    d,s,th=load();result={}
    for k in ['classifier_prob_balanced','classifier_prob_moderate_recall','classifier_prob_high_recall']:
        result[k]={v:compare(s['reference'],s[v],d['y'],d['sids'],th,k) for v in ['causal_float','offline_int8','deployed']}
    c.finish(['L5'],'Frozen operating-point sensitivity','COMPLETE',result,c.BASE/'model_L5')

def frontend():
    cm,io,pre,manifest,units,features,cfg,norm,th=env();d,s,_=load()
    raw=np.load(CACHE/'raw_test_sessions.npz');base_inputs=np.load(CACHE/'causal_inputs.npz')
    lite=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
    out=c.BASE/'model_L6';out.mkdir(exist_ok=True);c.save(out/'metadata.json',c.metadata())
    result={'limitations':'Emulation on already-resampled 50-Hz raw sequences, before causal gravity removal. Not a high-frequency anti-alias or physical crash validation. Labels fixed from original reference, not recomputed after clipping. Scales match sensor sensitivity constants; no additional analog noise.', 'ranges':{}}
    for name,asens,gsens in [('current_2g_250dps',16384.,131.),('wide_16g_2000dps',2048.,16.4)]:
        scale=np.array([9.80665/asens]*3+[1/gsens]*3);seq=[];aux=[];clipmask=[];axiscounts=np.zeros(6,dtype=int);nsamples=0
        for sid in dict.fromkeys(d['sids'].tolist()):
            values=raw[sid];counts=values/scale;clipped=(counts < -32768)|(counts>32767)
            quant=np.clip(np.rint(counts),-32768,32767)*scale
            axiscounts+=clipped.sum(axis=0);nsamples+=len(values)
            f=cm.CausalGravityFilter(.3,50);filtered=quant.copy()
            filtered[:,:3]=np.asarray([f.apply(v) for v in quant[:,:3]])
            for start in range(0,len(values)-60,15):
                w=filtered[start:start+60].astype('float32');seq.append(w);aux.append(cm.compute_aux_features(w));clipmask.append(bool(clipped[start:start+60].any()))
        aux=np.asarray(aux);scores=int_scores(lite,seq,aux);clipmask=np.asarray(clipmask)
        np.savez_compressed(out/(name+'.npz'),scores=scores,aux=aux,window_clipped=clipmask)
        r=compare(s['deployed'],scores,d['y'],d['sids'],th)
        r.update(per_axis_clipped_samples=dict(zip(COLS,axiscounts.tolist())),total_samples=nsamples,
                 fraction_normal_windows_clipped=float(np.mean(clipmask[d['y']==0])),fraction_crash_windows_clipped=float(np.mean(clipmask[d['y']==1])),
                 feature_change={name2:{'mean_signed':float(np.mean(aux[:,i]-base_inputs['aux'][:,i])),'mean_absolute':float(np.mean(abs(aux[:,i]-base_inputs['aux'][:,i]))),'max_absolute':float(np.max(abs(aux[:,i]-base_inputs['aux'][:,i])))} for name2,i in [('accel_peak',2),('gyro_peak',5),('runtime_jerk_peak',6)]})
        result['ranges'][name]=r
    c.finish(['L6'],'Front-end range and 16-bit emulation','COMPLETE',result,out)

def calibration():
    *_,norm,th=env();val=np.load(CACHE/'val.npz');test=np.load(CACHE/'test.npz')
    vs,va=norm.transform(val['seq'],val['aux']);ts,ta=norm.transform(test['seq'],test['aux'])
    idx=np.random.default_rng(42).choice(len(vs),min(200,len(vs)),replace=False);ci=idx[val['y'][idx]==1]
    groups={'all_200_representative':vs[idx],'crash_representative':vs[ci],'all_crash_test':ts[test['y']==1],'outlier_5410':ts[5410:5411]}
    def describe(x,lo,hi):
        return {'n_windows':len(x),'channels':{col:{'normalized_min':float(x[:,:,i].min()),'normalized_max':float(x[:,:,i].max()),
                'physical_filtered_min':float(x[:,:,i].min()*norm.seq_std[i]+norm.seq_mean[i]),'physical_filtered_max':float(x[:,:,i].max()*norm.seq_std[i]+norm.seq_mean[i]),
                'percent_values_outside_all_representative_range':float(np.mean((x[:,:,i]<lo[i])|(x[:,:,i]>hi[i]))*100)} for i,col in enumerate(COLS)}}
    lo=vs[idx].min(axis=(0,1));hi=vs[idx].max(axis=(0,1))
    result={'method':'Reconstructed export representative selection: 200 validation windows sampled with default_rng(42), no test windows used for calibration.',
            'representative_crash_count':len(ci),'test_crash_count':int(sum(test['y']==1)),
            'representative_indices':idx.tolist(),'crash_representative_indices':ci.tolist(),
            'outlier_session':str(test['sids'][5410]),'outlier_label':int(test['y'][5410]),
            'groups':{k:describe(x,lo,hi) for k,x in groups.items()},
            'aux_normalized_range':{'representative_min':va[idx].min(axis=0).tolist(),'representative_max':va[idx].max(axis=0).tolist(),'outlier':ta[5410].tolist()},
            'caveat':'Reconstruction from current frozen exporter and unchanged data, not a previously saved conversion-time selection log. Physical values here are gravity-removed training inputs, not raw sensor register ranges.'}
    c.finish(['L7'],'Representative range audit','COMPLETE',result,c.BASE/'model_L7')

def outlier():
    import tensorflow as tf
    *_,norm,th=env();d,s,_=load();x,a=norm.transform(d['seq'][5410:5411],d['aux'][5410:5411])
    it=tf.lite.Interpreter(model_path=str(c.BASE/'frozen/models/helmx_crash_model_int8.tflite'),experimental_preserve_all_tensors=True)
    run=it.get_signature_runner();prediction=run(seq=x.astype('float32'),aux=a.astype('float32'))
    rows=[]
    for t in it.get_tensor_details():
        try:v=it.get_tensor(t['index'])
        except ValueError:continue
        if not v.size:continue
        q=t['quantization_parameters'];r={'index':t['index'],'name':t['name'],'shape':list(v.shape),'dtype':str(v.dtype),
            'scale':q['scales'].tolist(),'zero_point':q['zero_points'].tolist(),'min':float(v.min()),'max':float(v.max()),'mean':float(v.mean()),'elements':v.size}
        if np.issubdtype(v.dtype,np.integer):
            limits=np.iinfo(v.dtype);r.update(saturation_min=int(sum((v==limits.min).ravel())),saturation_max=int(sum((v==limits.max).ravel())))
        rows.append(r)
    out=c.BASE/'model_L9';c.save(out/'tensors.json',rows)
    result={'index':5410,'session':str(d['sids'][5410]),'label':int(d['y'][5410]),'reference_scores':s['reference'][5410].tolist(),
            'int8_scores':s['offline_int8'][5410].tolist(),'preserve_tensor_output':{k:np.asarray(v).tolist() for k,v in prediction.items() if k!='reconstruction'},
            'tensors_recorded':len(rows),'mechanism':'Saturation counts are diagnostics, not proof of the first causal divergence. No matched operator-by-operator float execution is asserted.'}
    c.finish(['L9'],'Outlier preserved-tensor trace','COMPLETE',result,out)

def enriched():
    import tensorflow as tf
    cm,*rest=env();norm=rest[-2];th=rest[-1];net=keras_model();d,s,_=load();v=np.load(CACHE/'val.npz')
    vs,va=norm.transform(v['seq'],v['aux']);rng=np.random.default_rng(42)
    original=rng.choice(len(vs),200,replace=False)
    positives=np.flatnonzero(v['y']==1);negatives=np.flatnonzero(v['y']==0)
    pos=rng.choice(positives,min(100,len(positives)),replace=False)
    enriched=np.concatenate([pos,rng.choice(negatives,200-len(pos),replace=False)])
    amp=np.max(abs(vs),axis=(1,2));order=np.argsort(amp,kind='stable')
    amplitude=order[np.linspace(0,len(order)-1,200,dtype=int)]
    out=c.BASE/'model_L8';out.mkdir(exist_ok=True);c.save(out/'metadata.json',c.metadata())
    result={'method':'Three diagnostic exports of the frozen Keras model. Validation data only; same conversion process for all. Deployment model never replaced.', 'variants':{}}
    import tempfile
    for name,indices in [('A_original_selection',original),('B_crash_enriched',enriched),('C_amplitude_stratified',amplitude)]:
        try:
            with tempfile.TemporaryDirectory(prefix='helmx_diag_') as tmp:
                net.export(tmp)
                conv=tf.lite.TFLiteConverter.from_saved_model(tmp);conv.optimizations=[tf.lite.Optimize.DEFAULT]
                conv.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
                # SavedModel keyword input order is not assumed; provide a named dictionary.
                def representative():
                    for i in indices:yield {'seq':vs[i:i+1].astype('float32'),'aux':va[i:i+1].astype('float32')}
                conv.representative_dataset=representative
                path=out/(name+'.tflite');path.write_bytes(conv.convert())
            lite=cm.CrashModel(path,c.BASE/'frozen/models/normalizer.npz');scores=int_scores(lite,d['seq'],d['aux'])
            np.save(out/(name+'_scores.npy'),scores)
            report=compare(s['reference'],scores,d['y'],d['sids'],th)
            report.update(calibration_indices=indices.tolist(),positive_calibration_windows=int(sum(v['y'][indices]==1)),sha256=c.sha(path),outlier_5410=scores[5410].tolist(),
                          byte_identical_to_deployed=path.read_bytes()==(c.BASE/'frozen/models/helmx_crash_model_int8.tflite').read_bytes())
            result['variants'][name]=report
        except Exception as e:
            result['variants'][name]={'error':repr(e)}
            c.save(out/'partial.json',result)
    status='COMPLETE' if all('error' not in r for r in result['variants'].values()) else 'INCOMPLETE — CONVERSION FAILURE'
    c.finish(['L8'],'Diagnostic calibration conversion',status,result,out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['L1','L2','L3','L4','L5','L6','L7','L8','L9']);args=p.parse_args()
    if args.experiment in ['L1','L2','L3']:fidelity(args.experiment)
    elif args.experiment=='L4':bootstrap()
    elif args.experiment=='L5':sensitivity()
    elif args.experiment=='L6':frontend()
    elif args.experiment=='L7':calibration()
    elif args.experiment=='L8':enriched()
    elif args.experiment=='L9':outlier()
