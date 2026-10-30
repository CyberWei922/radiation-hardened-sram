from pathlib import Path
import csv,json,re
import numpy as np
from analyze_stage1 import read_psf,at,ROOT,RESULTS

cases=json.loads((ROOT/'design/cases.json').read_text())
rows=[]
for case in cases:
 data=read_psf(RESULTS/case['name']/'psf/tran.tran.tran')
 row={**case}
 if case['kind']=='functional':
  state_ok=[]
  for time,state in [(9,1),(15,1),(24,0),(30,0)]:
   q,qb=at(data,'Xcell.Q',time),at(data,'Xcell.QN',time)
   state_ok.append(q>1.44 and qb<.36 if state else q<.36 and qb>1.44)
  deltas=[at(data,'BL',t)-at(data,'BLB',t) for t in [12.9,27.9]]
  row.update(passed=all(state_ok) and deltas[0]>.1 and deltas[1]<-.1,
             read1_delta_V=deltas[0],read0_delta_V=deltas[1])
 else:
  state=case['state']
  before_q,before_qn=at(data,'Xcell.Q',9.9),at(data,'Xcell.QN',9.9)
  after_q,after_qn=at(data,'Xcell.Q',18),at(data,'Xcell.QN',18)
  before=before_q>1.44 and before_qn<.36 if state else before_q<.36 and before_qn>1.44
  recovered=after_q>1.44 and after_qn<.36 if state else after_q<.36 and after_qn>1.44
  charge=abs(float(np.trapezoid(data['VSEUMON:p'],data['time'])*1e15))
  charge_ok=abs(charge-case['charge_fc'])<max(.1,case['charge_fc']*.001)
  deviation=np.maximum(abs(data['Xcell.Q']-1.8*state),abs(data['Xcell.QN']-1.8*(1-state)))
  bad=(data['time']>=10e-9)&(deviation>.36)
  last_bad=float(data['time'][bad][-1]*1e9-10) if bad.any() else 0.0
  row.update(passed=bool(before and recovered and charge_ok),before_state_ok=bool(before),recovered=bool(recovered),
             q_after_V=after_q,qn_after_V=after_qn,actual_charge_fC=charge,
             restore_20pct_ns=last_bad)
 rows.append(row)
out=RESULTS/'stage1_checks.json'
out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
fields=sorted(set().union(*(r.keys() for r in rows)))
with (RESULTS/'stage1_checks.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
print('CHECKED',len(rows),'PASSED',sum(bool(r['passed']) for r in rows))
for row in rows:
 print(row['name'],row['passed'], ('recovered='+str(row['recovered'])+' charge='+str(round(row['actual_charge_fC'],4))) if row['kind']=='seu' else '')
