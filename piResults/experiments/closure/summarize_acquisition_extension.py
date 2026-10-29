"""Record verified J2/J3 metrics with explicitly historical comparators."""
import argparse
import json
import campaign as c

def main():
    p=argparse.ArgumentParser();p.add_argument('--id',choices=['J2','J3'],required=True);p.add_argument('--label',required=True);p.add_argument('--attest',action='store_true');a=p.parse_args()
    review=json.loads((c.BASE/(a.label+'_verification')/'summary.json').read_text())
    if not all(review['checks'].values()):raise RuntimeError('Verification failed')
    records=[]
    for name,label in [('Current '+a.id,a.label),('Historical FIFO','05_corrected_aba/B_fifo'),('Historical DATA_RDY','13_optional_drdy/stationary_20min_20261006'),('Historical filtered polling','05_corrected_aba/A1_polling')]:
        s=json.loads((c.BASE/label/'summary.json').read_text())
        resources=json.loads((c.BASE/label/'resources.json').read_text())
        records.append({'condition':name,'source':label,'n_samples':s['n_samples'],'n_windows':s['n_windows'],'duration_s':s['elapsed_s'],'sample_rate_hz':s['sample_rate_hz'],'gaps':s['gap_count'],
                        'gaps_per_min':s['gap_count']*60/s['elapsed_s'],'C_D':s['C_D'],'V_T':s['V_T_scored_over_scored_plus_resets'],'survival_90':s['p_valid_90_sample_position'],
                        'dt_p99_ms':s['timing']['p99_ms'],'dt_max_ms':s['timing']['max_ms'],'processing_p99_ms':s['processing_ms']['99'],'i2c_failures':s['i2c_failures'],
                        'events':s['confirmed_alert_events'],'cpu_mean_pct':sum(r['cpu_pct'] for r in resources)/len(resources),'rss_max_bytes':max(r['rss_bytes'] for r in resources),
                        'cpu_temp_max_c':max(r['cpu_temp_c'] for r in resources),'score_distributions':s['score_distributions'],'physical_axes':s['physical_axes'],'summary_sha256':c.sha(c.BASE/label/'summary.json')})
    result={'id':a.id,'verification':a.label+'_verification','checks':review['checks'],'comparisons':records,
            'operator_attestation':'Untouched throughout confirmed after capture' if a.attest else 'Readiness/stationary condition confirmed before capture; post-capture confirmation pending',
            'limits':'Historical comparisons are descriptive, not simultaneous/matched-motion equivalence or causal estimates. Raw binary decoding and model replay are verified independently. FIFO batch timestamps are host availability; IIO timestamps may be driver reconstructed. Do not compare their dt as physical jitter. Kernel I2C error counts are unavailable for IIO. Reported process CPU excludes separate kernel interrupt work. IIO manages sensor clock/filter configuration and uses sysfs scale values; its physical means and rate are not an acquisition-only matched comparison with the older userspace configuration. Desktop/IDE and development activity remained active during current extension captures.'}
    status='COMPLETE (VERIFIED; HISTORICAL COMPARATORS; OPERATOR-ATTESTED)' if a.attest else 'PARTIAL (VERIFIED; POST-CAPTURE ATTESTATION PENDING)'
    out=c.BASE/(a.label+'_comparison')
    c.finish([a.id],a.id+' acquisition extension comparison',status,result,out)
    lines=['# '+a.id+' acquisition extension comparison','',status,'',result['limits'],'','| Condition | Samples | Windows | Gaps | C_D | V_T | Events |','|---|---:|---:|---:|---:|---:|---:|']
    for r in records:lines.append(f'| {r["condition"]} | {r["n_samples"]} | {r["n_windows"]} | {r["gaps"]} | {r["C_D"]:.6f} | {r["V_T"]:.6f} | {r["events"]} |')
    lines+=['','Complete timing, resources, axis statistics, score distributions and source hashes are in summary.json.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
