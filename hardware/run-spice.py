"""Run real ngspice and verify static equations and assumed-state transients."""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'projects'))
from polarization import displacement

def run(name):
    r=subprocess.run(['ngspice','-b',name],cwd=H,capture_output=True,text=True)
    (H/(Path(name).stem+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr+r.stdout)

run('static-branches.cir');run('teaching-cell.cir')
d=np.loadtxt(H/'static-branches.dat',skiprows=1)
# wr_singlescale stores sweep value once, then the named vectors.
err=max(np.max(abs(d[:,2]-displacement(d[:,1]/1e-8,1))),
        np.max(abs(d[:,3]-displacement(d[:,1]/1e-8,-1))))
assert err<1e-8
w=np.loadtxt(H/'cell-waveform.dat',skiprows=1)
assert np.isfinite(w).all()
interp=lambda ns,col:float(np.interp(ns*1e-9,w[:,0],w[:,col]))
ion=-interp(200,5);ioff=-interp(500,5)
assert interp(200,3)>.99 and interp(500,3)<-.99
assert ion>9e-6 and abs(ioff)<1e-12
# Repeat with half maximum timestep, preserving the first output for comparison.
original=(H/'teaching-cell.cir').read_text()
(H/'teaching-cell-fine.cir').write_text(original.replace('tran .2n 650n 0 .2n','tran .1n 650n 0 .1n').replace('cell-waveform.dat','cell-waveform-fine.dat'))
run('teaching-cell-fine.cir')
fine=np.loadtxt(H/'cell-waveform-fine.dat',skiprows=1)
delta=float(np.max(abs(w[:,3]-np.interp(w[:,0],fine[:,0],fine[:,3]))))
assert delta<.002
# Independently integrate the identical forcing law in Python for a cross-solver check.
from scipy.integrate import solve_ivp
times=np.array([0,10,11,110,111,310,311,410,411,650])*1e-9
volts=np.array([0,0,1.2,1.2,0,0,-1.2,-1.2,0,0])
s=solve_ivp(lambda t,y:[(y[0]-y[0]**3+np.interp(t,times,volts))/20e-9],(0,650e-9),[-1],max_step=.1e-9,rtol=1e-9,atol=1e-11,dense_output=True)
cross=float(np.max(abs(s.sol(w[:,0])[0]-w[:,3])))
assert cross<.002
fig,axs=plt.subplots(3,1,figsize=(9,7),sharex=True)
axs[0].plot(w[:,0]*1e9,w[:,1],label='Write forcing');axs[0].plot(w[:,0]*1e9,w[:,2],label='Read gate');axs[0].set_ylabel('Voltage (V)');axs[0].legend()
axs[1].plot(w[:,0]*1e9,w[:,3],label='State x');axs[1].plot(w[:,0]*1e9,w[:,4],label='Threshold (V)');axs[1].legend()
axs[2].plot(w[:,0]*1e9,-w[:,5]*1e6);axs[2].set(xlabel='Time (ns)',ylabel='Read current (µA)')
axs[2].annotate('Programmed read',xy=(200,ion*1e6),xytext=(230,7),arrowprops={'arrowstyle':'->'})
axs[2].annotate('Erased read',xy=(500,0),xytext=(440,4),arrowprops={'arrowstyle':'->'})
fig.suptitle('Executed ngspice teaching model: assumed kinetics and ideal isolation')
fig.tight_layout();fig.savefig(H/'cell-waveform.svg');plt.close(fig)
result={'classification':'illustrative teaching model; static published equation check; no measured-device calibration',
        'static_max_error_C_m2':float(err),'on_current_A':ion,'off_current_A':ioff,
        'max_state_delta_half_timestep':delta,'max_state_delta_python_solver':cross,
        'checks':'PASS: finite outputs, initialized states, read distinction, timestep and cross-solver agreement'}
(H/'spice-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
