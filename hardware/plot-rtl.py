"""Plot observed top-level signals from the actual Icarus VCD trace."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent
scope=[];signals={};trace={};t=0;active=False
for line in (H/'controller.vcd').read_text().splitlines():
    if line.startswith('$scope'):scope.append(line.split()[2])
    elif line.startswith('$upscope'):scope.pop()
    elif line.startswith('$var') and scope==['tb']:
        parts=line.split();signals[parts[3]]=parts[4];trace[parts[4]]=[]
    elif line.startswith('$enddefinitions'):active=True
    elif active and line.startswith('#'):t=int(line[1:])/1000
    elif active and line and line[0] in '01xz':
        key=line[1:]
        if key in signals:trace[signals[key]].append((t,float(line[0]) if line[0] in '01' else float('nan')))
names=['clk','reset','req_valid','ready','req_write','commit','rsp_valid','rsp_error']
fig,axs=plt.subplots(len(names),1,figsize=(12,8),sharex=True)
for ax,name in zip(axs,names):
    values=trace[name];assert values
    ax.step([v[0] for v in values],[v[1] for v in values],where='post');ax.set_ylim(-.2,1.2);ax.set_yticks([0,1]);ax.set_ylabel(name,rotation=0,ha='right',fontsize=9);ax.grid(alpha=.15)
axs[-1].set_xlabel('Time (ns)')
def before(name,time):
    vals=[v for t,v in trace[name] if t<time]
    return vals[-1] if vals else 0
accepts=[t for t,v in trace['clk'] if v==1 and before('req_valid',t)==1 and before('ready',t)==1]
writes=[t for t in accepts if before('req_write',t)==1]
faultresponses=[t for t,v in trace['rsp_error'] if v==1]
resets=[t for t,v in trace['reset'] if v==1 and t>0]
annotations=[(writes[0],'write accepted'),(writes[0]+40,'write response'),(faultresponses[0],'fault response'),(resets[-1],'reset abort')]
for x,label in annotations:
    axs[0].annotate(label,xy=(x,1),xytext=(x,2.2),rotation=20,fontsize=8,arrowprops={'arrowstyle':'->'})
fig.suptitle('Observed synthesized-controller simulation; no cell/route delay model',y=1.02)
fig.tight_layout();fig.savefig(H/'controller-waveform.svg',bbox_inches='tight');plt.close(fig)
print('PASS: observed VCD digital traces plotted')
