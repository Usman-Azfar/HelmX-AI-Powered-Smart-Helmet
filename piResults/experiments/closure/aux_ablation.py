"""L10 inference-time auxiliary-feature ablation; no training claim."""
import numpy as np
from sklearn.metrics import average_precision_score
import campaign as c
from model_analysis import load,env,keras_model,float_scores,compare,decisions,metrics

d,s,th=load();*_,norm,_=env();net=keras_model()
neutral=np.broadcast_to(norm.aux_mean,d['aux'].shape).copy()
scores=float_scores(net,norm,d['seq'],neutral)
result=compare(s['reference'],scores,d['y'],d['sids'],th)
result['method']='Replay fixed model with the seven normalized auxiliary inputs set to zero (training-normal means in physical feature space), versus original full inputs. Temporal tensor and all weights unchanged.'
result['classifier_average_precision']={'full_inputs':float(average_precision_score(d['y'],s['reference'][:,0])),
                                       'neutralized_aux':float(average_precision_score(d['y'],scores[:,0]))}
result['limitation']='Inference-time feature ablation only. This is NOT an independently trained temporal-only architecture; out-of-distribution feature neutralization can affect predictions. It does not establish the incremental benefit of training with auxiliary scalars.'
out=c.BASE/'model_L10';out.mkdir(exist_ok=True);np.save(out/'neutralized_aux_scores.npy',scores)
c.finish(['L10'],'Auxiliary-feature replay ablation','COMPLETE (INFERENCE-TIME DIAGNOSTIC)',result,out)
