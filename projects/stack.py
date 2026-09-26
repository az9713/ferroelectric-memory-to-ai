"""Cumulative, explicitly synthetic materials-to-system studies. No device forecast."""
from pathlib import Path
import argparse
import csv
import json
import math
import numpy as np
from scipy.special import erfc
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from polarization import EPS0

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent/'results'
OUT.mkdir(exist_ok=True)

def save(name,data):
    (OUT/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    return data

def foundations():
    # Teaching constants at 300 K, not parameter extraction for a Khan sample.
    q=1.602176634e-19;k=1.380649e-23;temp=300
    vt=k*temp/q
    cf=EPS0*33/10e-9;ci=EPS0*3.9/1e-9
    ps=.13
    # V=0; D continuity across FE + linear interface. Polarization held fixed.
    depol=-ps/(EPS0*33+EPS0*3.9*10e-9/1e-9)
    ef_no_interface=0.0
    subthreshold=math.log(10)*vt
    assert abs(subthreshold-.059526)<1e-5
    assert abs(depol*10e-9+(EPS0*33*depol+ps)*1e-9/(EPS0*3.9))<1e-12
    rows=[]
    for ti in [.25,.5,1,2]:
        ef=-ps/(EPS0*33+EPS0*3.9*10/ti)
        rows.append({'interface_nm':ti,'depolarization_MV_cm':ef/1e8,
                     'FE_voltage_fraction_without_P':(EPS0*3.9/(ti*1e-9))/(cf+EPS0*3.9/(ti*1e-9))})
    return save('foundations',{'evidence':'T: assumed fixed polarization electrostatics at 300 K',
               'thermal_voltage_V':vt,'ideal_swing_V_dec':subthreshold,'CF_F_m2':cf,'CI_F_m2':ci,
               'depolarization_V_m':depol,'interface_sweep':rows,'checks':'PASS'})

def switching():
    # Dimensionless double-well gradient descent: tau dx/dt = x - x^3 + v.
    tau=20e-9
    def voltage(t):return 1.2 if t<100e-9 else 0.0
    sol=solve_ivp(lambda t,y:[(y[0]-y[0]**3+voltage(t))/tau],(0,300e-9),[-1],
                  rtol=1e-9,atol=1e-11,max_step=.2e-9,dense_output=True)
    t=np.linspace(0,300e-9,1501);x=sol.sol(t)[0]
    assert sol.success and x[-1]>.99
    # Merz-law parameter sweep is separate from the illustrative Landau dynamics.
    e=np.linspace(.5,3,101);tau0=1e-9;activation=2.0
    duration=tau0*np.exp(activation/e)
    pfail=np.exp(-100e-9/duration)
    viable=e[pfail<=1e-6]
    arrhenius=math.exp(.7/8.617333262e-5*(1/300-1/358))
    fig,ax=plt.subplots(1,2,figsize=(10,4))
    ax[0].plot(t*1e9,x);ax[0].set(xlabel='Time (ns)',ylabel='Normalized state x',title='Assumed double-well dynamics')
    ax[1].semilogy(e,pfail);ax[1].axhline(1e-6,color='black',ls='--');ax[1].set(xlabel='Field (MV/cm)',ylabel='Illustrative failure probability',title='100 ns pulse; assumed Merz law')
    fig.tight_layout();fig.savefig(OUT/'switching.svg');plt.close(fig)
    return save('switching',{'evidence':'T: all kinetic/barrier parameters assumed; no measured lifetime forecast',
              'tau_s':tau,'final_state':float(x[-1]),'min_grid_field_MV_cm':float(viable.min()),
              'grid_step_MV_cm':float(e[1]-e[0]),'temperature_acceleration_300_to_358K':arrhenius,
              'retention_seconds_at_300K_for_tau0_1ns_barrier_0_7eV':1e-9*math.exp(.7/(8.617333262e-5*300)),
              'checks':'PASS: ODE convergence, stable switched state, finite constrained sweep'})

def reliability():
    n=72;p=1e-5
    # Stable binomial tail via sum avoids cancellation in 1-P0-P1.
    fail=sum(math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(2,n+1))
    approx=math.comb(n,2)*p*p
    endurance=1e6;logical_rate=100;cells=1024;amplification=2
    life=endurance*cells/(logical_rate*amplification)
    ber=float(.5*erfc(.4/(2*math.sqrt(2)*.05)))
    assert abs(fail/approx-1)<.001
    return save('reliability',{'evidence':'T: independent bit errors, Gaussian thresholds, ideal wear spreading',
           'raw_bit_error_probability':p,'SEC_word_uncorrectable_probability':fail,'leading_order':approx,
           'gaussian_error_for_window_0_4V_sigma_0_05V':ber,
           'ideal_wear_lifetime_s':life,'hotspot_lifetime_s':endurance/(logical_rate*amplification),
           'checks':'PASS: exact binomial tail vs small-error limit'})

def arrays():
    # Fixed 64 MiB synthetic capacity. A row is word-wide; W is bits/word.
    bits=64*2**20*8
    rows=[]
    for banks in [1,2,4,8,16,32]:
        for width in [32,64,128,256]:
            # Distributed RC grows quadratically with rows per local subarray.
            local_rows=bits/(banks*width*1024)  # 1024 tiled subarrays per bank, assumed.
            wire_ns=.002*local_rows+.00002*local_rows**2
            latency=2+wire_ns+width*.002
            energy_pj=.02*width+.004*local_rows*width+3*banks
            area_mm2=bits*.04/1e6+.04*banks+.0002*banks*width
            bw=banks*width/8/(latency*1e-9)
            sigma=.05+.00005*local_rows
            ber=float(.5*erfc(.4/(2*math.sqrt(2)*sigma)))
            feasible=latency<=15 and area_mm2<=30 and ber<=1e-3
            rows.append(dict(banks=banks,width_bits=width,local_rows=local_rows,latency_ns=latency,
                             access_energy_pJ=energy_pj,area_mm2=area_mm2,bandwidth_B_s=bw,
                             error_probability=ber,feasible=feasible))
    feasible=[r for r in rows if r['feasible']]
    assert feasible and any(not r['feasible'] for r in rows)
    # Global non-dominated set of this finite enumerated design space; no continuum claim.
    dims=['access_energy_pJ','latency_ns','area_mm2']
    pareto=[r for r in feasible if not any(all(s[k]<=r[k] for k in dims) and any(s[k]<r[k] for k in dims) for s in feasible)]
    with (OUT/'array-sweep.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
    fig,ax=plt.subplots(figsize=(7,4.8))
    ax.scatter([r['latency_ns'] for r in rows],[r['access_energy_pJ'] for r in rows],c=['#157d83' if r['feasible'] else '#b8b8b8' for r in rows],label='Feasible teal; infeasible gray')
    ax.scatter([r['latency_ns'] for r in pareto],[r['access_energy_pJ'] for r in pareto],facecolors='none',edgecolors='black',s=90,label='3-objective Pareto set')
    ax.set(xlabel='Read latency (ns)',ylabel='Read access energy (pJ)',title='Synthetic array sweep at fixed 64 MiB');ax.legend(fontsize=9)
    fig.tight_layout();fig.savefig(OUT/'array-pareto.svg');plt.close(fig)
    chosen=min(feasible,key=lambda r:r['access_energy_pJ']/(r['width_bits']/8))
    # Budgeting at system level uses an energy per byte, not energy per word.
    chosen=dict(chosen);chosen['energy_pJ_per_byte']=chosen['access_energy_pJ']/(chosen['width_bits']/8)
    return save('arrays',{'evidence':'T: phenomenological educational cost model, no PDK characterization',
              'capacity_bytes':bits//8,'candidate_count':len(rows),'feasible_count':len(feasible),
              'pareto_count':len(pareto),'pareto':pareto,'chosen_min_energy_per_byte':chosen,
              'constraints':'latency <=15ns; area <=30mm2; raw BER <=1e-3',
              'checks':'PASS: feasible/infeasible cases and exhaustive finite dominance'})

def placement():
    # Grid search for macro location minimizing weighted Manhattan wiring, with keepout.
    pins=np.array([[0,2],[0,8],[10,5]],float);weights=np.array([1,1,2],float)
    candidates=[]
    for x in np.arange(1,10,.25):
        for y in np.arange(1,10,.25):
            if 4<=x<=6 and 4<=y<=6:continue
            cost=float((np.abs(pins-[x,y]).sum(axis=1)*weights).sum())
            candidates.append((cost,float(x),float(y)))
    best=min(candidates)
    # Cumulative DRC/LVS is impossible without a process; this checks only abstract geometry.
    return save('placement',{'evidence':'T: point macro, arbitrary mm floorplan; weighted wirelength proxy',
                'grid_best_weighted_mm':best[0],'x_mm':best[1],'y_mm':best[2],
                'candidate_count':len(candidates),'global_scope':'enumerated grid only; ties possible',
                'checks':'PASS: bounding box and keepout; not foundry DRC'})

def workload():
    arr=json.loads((OUT/'arrays.json').read_text());a=arr['chosen_min_energy_per_byte']
    params=16_000_000;weight_bytes=1;layers=16;kvheads=4;head_dim=64;kvbytes=2
    bandwidth=min(a['bandwidth_B_s'],80e9);flops=1e12
    rows=[]
    for batch in [1,2,4,8,16]:
        for context in [128,512,1024,2048]:
            kv=2*layers*kvheads*head_dim*kvbytes*batch*context
            weights=params*weight_bytes
            # Lower-bound dense work plus approximate attention work; no full model quality claim.
            ops=2*params*batch+4*layers*kvheads*head_dim*batch*context
            traffic=weights+kv
            decode=max(ops/flops,traffic/bandwidth)+20e-6
            capacity=weights+kv+8*2**20 # 8 MiB assumed non-KV runtime overhead
            feasible=capacity<=arr['capacity_bytes'] and decode<=.005
            energy=traffic*a['energy_pJ_per_byte']*1e-12+ops*2e-12
            rows.append(dict(batch=batch,context=context,kv_bytes=kv,capacity_bytes=capacity,
                             latency_s=decode,tokens_s=batch/decode,
                             dynamic_J_per_token=energy/batch,feasible=feasible))
    feasible=[r for r in rows if r['feasible']]
    assert feasible and any(not r['feasible'] for r in rows)
    selected=max(feasible,key=lambda r:r['tokens_s'])
    with (OUT/'workload-sweep.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
    return save('workload',{'evidence':'T: hypothetical 16M-parameter workload; fixed assumed numerical quality',
            'memory_bandwidth_B_s':bandwidth,'compute_FLOP_s':flops,'chosen':selected,
            'rows':rows,'checks':'PASS: capacity rejects otherwise attractive batches; latency constraint enforced'})

def system():
    w=json.loads((OUT/'workload.json').read_text());choice=w['chosen'];peak=choice['tokens_s']
    rows=[]
    for utilization in [.1,.3,.5,.7,.9,.98]:
        # M/M/1 teaching model of batch arrivals: service time s, batch tokens B.
        rate=utilization*peak;s=choice['latency_s'];response=s/(1-utilization)
        power=45+rate*choice['dynamic_J_per_token']
        pue=1.2;facility=power*pue
        rows.append({'utilization':utilization,'tokens_s':rate,'batch_response_s':response,
                     'IT_power_W':power,'facility_W':facility,'facility_J_token':facility/rate,
                     'feasible':response<=.005 and power<=100})
    viable=[r for r in rows if r['feasible']]
    selected=min(viable,key=lambda r:r['facility_J_token'])
    amdahl=1/(.95+.05/10)
    # Fixed workload energy fractions; device-only gain, no second throughput multiplier.
    fraction=.05;local_gain=10;fixed_work_ratio=(1-fraction)+fraction/local_gain
    optimistic=.7*.1+.3
    assert 1<amdahl<1.06 and abs(fixed_work_ratio-.955)<1e-12
    # Lower memory energy cannot remove modeled idle power or queueing.
    robustness=[]
    for pue in [1.1,1.2,1.5]:
        for idle in [25,45,80]:
            r=selected['tokens_s'];e=pue*(idle+r*choice['dynamic_J_per_token'])/r
            robustness.append({'PUE':pue,'idle_W':idle,'J_token':e})
    fig,ax=plt.subplots(1,2,figsize=(10,4))
    ax[0].plot([r['utilization'] for r in rows],[r['facility_J_token'] for r in rows],marker='o');ax[0].set(xlabel='Utilization',ylabel='Facility joules / token',title='Idle power amortization')
    ax[1].plot([r['utilization'] for r in rows],[r['batch_response_s']*1e3 for r in rows],marker='o');ax[1].axhline(5,color='black',ls='--');ax[1].set(xlabel='Utilization',ylabel='Mean batch response (ms)',title='Queueing penalty')
    fig.tight_layout();fig.savefig(OUT/'system.svg');plt.close(fig)
    return save('system',{'evidence':'T: M/M/1 assumptions; no measured serving system',
        'rows':rows,'chosen':selected,'device_10x_speedup_at_5pct_time_fraction':amdahl,
        'device_10x_energy_gain_at_5pct_energy_fraction_ratio':fixed_work_ratio,
        'redesigned_70pct_affected_energy_fraction_ratio':optimistic,
        'robustness':robustness,'checks':'PASS: Amdahl bound, feasibility, energy/power separation'})

def precision():
    rng=np.random.default_rng(1989)
    weights=rng.normal(size=(64,64));inputs=rng.normal(size=(64,32))
    reference=weights@inputs;rows=[]
    for bits in [2,3,4,6,8,12,16]:
        levels=2**(bits-1)-1;scale=np.max(np.abs(weights))/levels
        quantized=np.clip(np.rint(weights/scale),-levels,levels)*scale
        err=float(np.linalg.norm(quantized@inputs-reference)/np.linalg.norm(reference))
        rows.append({'bits':bits,'relative_output_error':err,'weight_bytes':weights.size*bits/8,'feasible':err<=.02})
    best=min((r for r in rows if r['feasible']),key=lambda r:r['weight_bytes'])
    assert rows[-1]['relative_output_error']<1e-3 and best['bits']>=6
    # Prefill lower bound for the same hypothetical 16M-parameter, 16-layer, 4-head model.
    tokens=128;ops=2*16e6*tokens+4*16*4*64*tokens*tokens
    bound=ops/1e12
    return save('precision',{'evidence':'T: quantized random linear layer; not language-model accuracy',
         'rows':rows,'chosen':best,'prefill_128_tokens_compute_lower_bound_s':bound,
         'prefill_FLOPs':ops,'checks':'PASS: constrained precision selection and high-precision limit'})

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',nargs='?',default='all',choices=['all','foundations','switching','reliability','arrays','placement','workload','system','precision']);a=p.parse_args()
    stages=[foundations,switching,reliability,arrays,placement,workload,system,precision]
    for f in stages:
        if a.stage in ['all',f.__name__]:
            r=f();print(f.__name__,r['checks'])

if __name__=='__main__':main()
