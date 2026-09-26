"""Conditional cross-stack intervention. Every coupling is a teaching assumption."""
from pathlib import Path
import json, csv, math
from statistics import NormalDist

OUT=Path(__file__).resolve().parent/'results'
arrays=list(csv.DictReader((OUT/'array-sweep.csv').open()))
base=json.loads((OUT/'workload.json').read_text())['chosen']
coupling=.4/.13 # V per (C/m^2); assumed effective read-window coupling.
rows=[]
for polarization in [.08,.10,.13,.16]:
    for sigma_factor in [.8,1.0,1.2]:
        for mode in ['fixed architecture','reselected array']:
            options=[]
            for raw in arrays:
                a={k:float(v) for k,v in raw.items() if k!='feasible'}
                if mode=='fixed architecture' and (a['banks']!=32 or a['width_bits']!=256):continue
                sigma=(.05+.00005*a['local_rows'])*sigma_factor
                window=coupling*polarization
                ber=.5*math.erfc(window/(2*math.sqrt(2)*sigma))
                energy=a['access_energy_pJ']+.02*a['width_bits']*((polarization/.13)**2-1)
                if a['latency_ns']>15 or a['area_mm2']>30 or ber>1e-3:continue
                options.append(dict(a,window_V=window,BER=ber,energy_pJ_per_byte=energy/(a['width_bits']/8)))
            row={'Pr_C_m2':polarization,'sigma_factor':sigma_factor,'mode':mode,'feasible':bool(options)}
            if options:
                a=min(options,key=lambda x:x['energy_pJ_per_byte'])
                # Fix workload B=16,S=128, numerical quality, 64MiB capacity and compute.
                bandwidth=min(a['bandwidth_B_s'],80e9)
                traffic=16e6+2*16*4*64*2*16*128
                ops=2*16e6*16+4*16*4*64*16*128
                step=max(ops/1e12,traffic/bandwidth)+20e-6
                rate=.7*16/step
                dyn=(traffic*a['energy_pJ_per_byte']*1e-12+ops*2e-12)/16
                facility=1.2*(45+rate*dyn)
                row.update(banks=int(a['banks']),width_bits=int(a['width_bits']),window_V=a['window_V'],
                           BER=a['BER'],memory_pJ_byte=a['energy_pJ_per_byte'],
                           step_s=step,tokens_s=rate,facility_J_token=facility/rate)
            rows.append(row)
baseline=next(r for r in rows if r['Pr_C_m2']==.13 and r['sigma_factor']==1 and r['mode']=='fixed architecture')
assert abs(baseline['step_s']-base['latency_s'])<1e-15
assert any(not r['feasible'] for r in rows)
z=NormalDist().inv_cdf(1-1e-3)
required_window=2*z*.0532
required_p=required_window/coupling
result={'evidence':'T: conditional sensitivity model, not a measured material-to-system forecast',
 'fixed_conditions':'64MiB, B16, S128, quality assumed fixed, 1TFLOP/s, interface80GB/s, utilization0.7, idle45W, PUE1.2',
 'coupling_V_per_C_m2':coupling,'downward_window_for_BER_1e_3_V':required_window,
 'downward_Pr_C_m2_under_assumed_coupling':required_p,
 'rows':rows,'checks':'PASS: baseline matches cumulative model; infeasible interventions retained'}
(OUT/'capstone.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
