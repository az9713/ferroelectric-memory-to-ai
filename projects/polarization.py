"""Static major-loop reconstruction and synthetic inverse-problem lab. SI API."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares, brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'results'
OUT.mkdir(exist_ok=True)
EPS0=8.8541878128e-12

def displacement(field, direction, ps=.14, pr=.13, ec=1e8, epsr=33, offset=0):
    """Return D [C/m²] for E [V/m]; direction ±1, Ps > Pr > 0, Ec > 0."""
    if not (ps > pr > 0 and ec > 0 and epsr > 0):
        raise ValueError('Require Ps > Pr > 0, Ec > 0, relative permittivity > 0')
    if not np.all(np.isin(direction,[-1,1])):
        raise ValueError('Branch direction must be +1 or -1')
    slope=np.log((ps+pr)/(ps-pr))/(2*ec)
    return ps*np.tanh(slope*(np.asarray(field)-np.asarray(direction)*ec))+offset+EPS0*epsr*np.asarray(field)

def scaled_model(x, direction, p):
    ps, ratio, ec, epsr, offset=p
    return displacement(x*1e8,direction,ps*.01,ps*ratio*.01,ec*1e8,epsr,offset*.01)*100

def run():
    # Published synthetic Fig. 2 parameters; these are not measurements of a device.
    x=np.linspace(-4,4,401)
    up=displacement(x*1e8,1)
    down=displacement(x*1e8,-1)
    slope=np.log(27)/(2e8)
    crossing=brentq(lambda f:displacement(f,1),0,1e8)
    linear_crossing=1e8/(1+EPS0*33/(.14*slope))
    loss_per_volume=np.trapezoid(down-up,x*1e8)
    loss_j=loss_per_volume*1e-8*1e-12
    np.savetxt(OUT/'major-loop.csv',np.c_[x*1e8,up,down],delimiter=',',header='E_V_per_m,D_up_C_per_m2,D_down_C_per_m2',comments='')
    fig,axs=plt.subplots(1,2,figsize=(11,4.4))
    axs[0].plot(x,up*100,label='Increasing field');axs[0].plot(x,down*100,label='Decreasing field')
    axs[0].set(xlabel='Field (MV/cm)',ylabel='Displacement D (µC/cm²)',title='Published synthetic major-loop parameters')
    axs[0].legend();axs[0].grid(alpha=.25)
    rng=np.random.default_rng(1989)
    xx=np.r_[x,x];direction=np.r_[np.ones(len(x)),-np.ones(len(x))]
    truth=np.array([14,13/14,1,33,0])
    y=scaled_model(xx,direction,truth)+rng.normal(0,.10,len(xx))
    train=np.arange(len(xx))%3!=0
    bounds=([1,.1,.1,1,-5],[40,.995,3,100,5])
    fit=least_squares(lambda p:scaled_model(xx[train],direction[train],p)-y[train],
                      [12,.8,.8,25,.2],bounds=bounds,xtol=1e-12,gtol=1e-12,ftol=1e-12)
    test_rmse=float(np.sqrt(np.mean((scaled_model(xx[~train],direction[~train],fit.x)-y[~train])**2)))
    sparse=xx>3.5
    sparse_fits=[]
    for guess in [[10,.5,.3,30,0],[20,.98,2.5,40,0]]:
        f=least_squares(lambda p:scaled_model(xx[sparse],direction[sparse],p)-y[sparse],guess,bounds=bounds,max_nfev=3000)
        sparse_fits.append({'parameters':f.x.tolist(),'rmse_uC_cm2':float(np.sqrt(np.mean(f.fun**2)))})
    svals=np.linalg.svd(fit.jac,compute_uv=False)
    axs[1].scatter(xx[~train],y[~train],s=7,alpha=.35,label='Held-out synthetic samples')
    axs[1].plot(x,scaled_model(x,1,fit.x),color='black',label='Fitted increasing branch')
    axs[1].plot(x,scaled_model(x,-1,fit.x),color='black')
    axs[1].set(xlabel='Field (MV/cm)',ylabel='D (µC/cm²)',title='Synthetic fit; not experimental calibration')
    axs[1].legend(fontsize=8);axs[1].grid(alpha=.25)
    fig.tight_layout();fig.savefig(OUT/'polarization.svg');plt.close(fig)
    # Independent formula and invariants, not a second call to the same formula.
    assert abs(displacement(0,1)+.13)<1e-12
    assert abs(displacement(0,-1)-.13)<1e-12
    assert np.allclose(up,-down[::-1])
    assert .8e8<crossing<1e8 and loss_j>0
    assert abs(loss_per_volume-4*.14*1e8)/(4*.14*1e8)<.001
    assert test_rmse<.13 and abs(fit.x[0]-14)<.15
    try:displacement(0,1,ps=.1,pr=.2)
    except ValueError:pass
    else:raise AssertionError('Invalid polarization accepted')
    out={'provenance':'Wang et al. 2021 Fig.2 synthetic parameters; seeded synthetic noisy data',
         'Ps_C_m2':.14,'Pr_C_m2':.13,'Ec_V_m':1e8,'epsr':33,'tFE_m':1e-8,
         'charge_zero_field_MV_cm':crossing/1e8,'linearized_crossing_MV_cm':linear_crossing/1e8,
         'crossing_underestimate_percent':100*(1-crossing/1e8),
         'loop_loss_J_m3':loss_per_volume,'loop_loss_J_for_1um2_10nm':loss_j,
         'fit_parameters_Ps_uC_ratio_Ec_MV_epsr_offset_uC':fit.x.tolist(),
         'heldout_RMSE_uC_cm2':test_rmse,'scaled_jacobian_singular_values':svals.tolist(),
         'saturated_only_fits':sparse_fits,'checks':'PASS: units, remanence, symmetry, analytic loop area, held-out synthetic fit, input boundary'}
    (OUT/'polarization.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
