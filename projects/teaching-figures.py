"""Figures from explicit teaching equations and already computed project results."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets'
x=np.linspace(-2,2,600)
fig,ax=plt.subplots(figsize=(8,4.5))
for v in [0,.25,.5]:ax.plot(x,x**4/4-x**2/2-v*x,label=f'Forcing v={v}')
ax.set(xlabel='Normalized polarization x',ylabel='Normalized energy density',ylim=(-1.2,1.2),title='Assumed quartic energy: field tilts the wells');ax.legend()
fig.tight_layout();fig.savefig(OUT/'landau.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.5))
ax.axvspan(-1,0,alpha=.2,color='gray',label='Oxide');ax.axvspan(0,2,alpha=.1,color='teal',label='Depleted semiconductor')
ax.plot([-1,0],[1,.6],color='black',lw=2)
s=np.linspace(0,2,100);ax.plot(s,.6*(1-s/2)**2,color='black',lw=2)
ax.plot([2,3],[0,0],color='black',lw=2)
ax.set(xlabel='Normalized depth (different region scales; schematic)',ylabel='Electrostatic potential (arbitrary units)',title='MOS voltage drops across oxide and semiconductor')
ax.annotate('Gate',(-1,1),(-.8,.85));ax.annotate('Surface potential',(0,.6),(.4,.8),arrowprops={'arrowstyle':'->'})
ax.annotate('Neutral bulk',(2.6,0),(2.1,.2),arrowprops={'arrowstyle':'->'});ax.legend(loc='upper right')
fig.tight_layout();fig.savefig(OUT/'mos-potential.svg');plt.close(fig)
w=json.loads((ROOT/'projects/results/workload.json').read_text())
fig,ax=plt.subplots(figsize=(8,4.5))
for context in [128,512,1024,2048]:
    rows=[r for r in w['rows'] if r['context']==context]
    ax.plot([r['batch'] for r in rows],[r['capacity_bytes']/2**20 for r in rows],marker='o',label=f'Context {context}')
ax.axhline(64,ls='--',color='black',label='64 MiB capacity');ax.set(yscale='log',xlabel='Batch size',ylabel='Modeled memory requirement (MiB)',title='KV capacity grows with context and batch');ax.legend(fontsize=9)
fig.tight_layout();fig.savefig(OUT/'workload-capacity.svg');plt.close(fig)
c=json.loads((ROOT/'projects/results/capstone.json').read_text())
fig,ax=plt.subplots(figsize=(8,4.5))
for sigma in [.8,1,1.2]:
    rows=[r for r in c['rows'] if r['sigma_factor']==sigma and r['mode']=='fixed architecture' and r['feasible']]
    ax.plot([r['Pr_C_m2'] for r in rows],[r['facility_J_token']*1e3 for r in rows],marker='o',label=f'Variability factor {sigma}')
ax.set(xlabel='Assumed remanent polarization (C/m²)',ylabel='Facility energy (mJ/token)',title='Conditional capstone: only feasible points shown');ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.legend()
fig.tight_layout();fig.savefig(OUT/'capstone.svg');plt.close(fig)
print('Four equation/result-derived teaching figures written')
