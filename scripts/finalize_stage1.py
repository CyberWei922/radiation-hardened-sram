"""Check native schematic testbenches and plot their real Spectre waveforms."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_stage1 import read_psf, at, ROOT, RESULTS, FIGURES

checks=[]
for cell in ['sram6t','hphs12t']:
    for kind in ['functional','seu']:
        name=f'tb_{cell}_{kind}'
        d=read_psf(RESULTS/'native'/name/'psf/tran.tran.tran')
        prefix='Xcell.' if kind=='functional' else ''
        row={'testbench':name}
        if kind=='functional':
            samples=[(t,state,at(d,prefix+'Q',t),at(d,prefix+'QN',t))
                     for t,state in [(9,1),(15,1),(24,0),(30,0)]]
            row['state_samples']=samples
            row['read1_delta_V']=at(d,'BL',12.9)-at(d,'BLB',12.9)
            row['read0_delta_V']=at(d,'BL',27.9)-at(d,'BLB',27.9)
            row['passed']=all(q>1.44 and qb<.36 if state else q<.36 and qb>1.44
                               for t,state,q,qb in samples) and row['read1_delta_V']>.1 and row['read0_delta_V']<-.1
        else:
            row['q_before_V']=at(d,'Q',9.9)
            row['qn_before_V']=at(d,'QN',9.9)
            row['q_after_V']=at(d,'Q',18)
            row['qn_after_V']=at(d,'QN',18)
            row['charge_fC']=abs(float(np.trapezoid(d['VSEUMON:p'],d['time'])*1e15))
            row['recovered']=row['q_after_V']<.36 and row['qn_after_V']>1.44
            row['expected_behavior_observed']=row['recovered'] == (cell=='hphs12t')
            assert row['q_before_V']<.36 and row['qn_before_V']>1.44
            assert abs(row['charge_fC']-30)<.1
        checks.append(row)
        assert row.get('passed',row.get('expected_behavior_observed'))

(RESULTS/'native_testbench_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.dpi':170,'axes.grid':True,'grid.alpha':.18})
fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained',
                      gridspec_kw={'height_ratios':[.8,1,1]})
for index,cell in enumerate(['sram6t','hphs12t']):
    d=read_psf(RESULTS/'native'/f'tb_{cell}_seu'/'psf/tran.tran.tran')
    t=d['time']*1e9
    if index==0:
        axes[0].plot(t,d['VSEUMON:p']*1e6,color='#8250df')
    ax=axes[index+1]
    for node,color in [('Q','#0969da'),('QN','#d1242f')]:
        ax.plot(t,d[node],label=node,color=color,lw=1.8)
    ax.set_ylabel('Voltage (V)');ax.set_ylim(min(-.2,float(min(d['Q'].min(),d['QN'].min()))-.08),2.05)
    ax.set_title('6T: state flips' if index==0 else 'HPHS12T: original state recovers',loc='left',fontsize=12)
    ax.legend(loc='center right',ncol=2)
    ax.axhline(.36,color='#777',lw=.6,ls=':');ax.axhline(1.44,color='#777',lw=.6,ls=':')
axes[0].set_title('Same 30 fC strike on high QN, stored Q = 0',loc='left',fontsize=12)
axes[0].set_ylabel('Injected (uA)')
axes[-1].set_xlabel('Time (ns)')
for ax in axes:
    ax.set_xlim(9.7,14);ax.axvline(10,color='#666',ls='--',lw=.8)
fig.suptitle('Native Virtuoso schematic simulation | TSMC 180 nm | TT | 1.8 V | 27 C',fontsize=12)
fig.savefig(FIGURES/'seu_30fC_native_comparison.png');plt.close(fig)

for cell in ['sram6t','hphs12t']:
    d=read_psf(RESULTS/'native'/f'tb_{cell}_functional'/'psf/tran.tran.tran')
    fig,axes=plt.subplots(3,1,figsize=(11,7.5),sharex=True,layout='constrained')
    t=d['time']*1e9
    axes[0].plot(t,d['WL'],label='WL',color='#8250df')
    axes[0].plot(t,d['WE'],label='Write enable',color='#777',ls='--')
    axes[0].set_ylabel('Control (V)')
    for node,color in [('Q','#0969da'),('QN','#d1242f'),('S0','#198754'),('S1','#b58200')]:
        if 'Xcell.'+node in d:
            axes[1].plot(t,d['Xcell.'+node],label=node,color=color,ls='--' if node.startswith('S') else '-')
    axes[1].set_ylabel('Storage (V)')
    for node,color in [('BL','#0969da'),('BLB','#d1242f')]:axes[2].plot(t,d[node],label=node,color=color)
    axes[2].set_ylabel('Bitline (V)');axes[2].set_xlabel('Time (ns)')
    for ax in axes:
        ax.set_xlim(0,32);ax.set_ylim(-.1,2.05);ax.legend(loc='lower right' if ax is axes[0] else 'upper right',ncol=4)
        for a,b in [(5.2,7.2),(12,13),(20.2,22.2),(27,28)]:ax.axvspan(a,b,color='#dce9f4',alpha=.45)
    for x,text in [(6.2,'Write 1'),(12.5,'Read 1'),(21.2,'Write 0'),(27.5,'Read 0')]:
        axes[0].text(x,1.96,text,ha='center',va='top',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.85})
    fig.suptitle(f'{cell.upper()}: native schematic read/write/hold\nTT | VDD = 1.8 V | 27 C | CBL = CBLB = 100 fF',fontsize=12)
    fig.savefig(FIGURES/f'{cell}_native_functional.png');plt.close(fig)

rows=json.loads((RESULTS/'stage1_checks.json').read_text())
grid=[]
for cell,nodes in [('sram6t',['Q','QN']),('hphs12t',['Q','QN','S0','S1'])]:
    for charge in [10,20,30,45,60,90]:
        subset=[r for r in rows if r['cell']==cell and r['kind']=='seu' and r['charge_fc']==charge]
        grid.append({'cell':cell,'charge_fC':charge,'recovered':sum(r['recovered'] for r in subset),'total':len(subset)})
(RESULTS/'seu_charge_summary.json').write_text(json.dumps(grid,indent=2),encoding='utf-8')
print(json.dumps({'native_checks':checks,'charge_grid':grid},indent=2))
