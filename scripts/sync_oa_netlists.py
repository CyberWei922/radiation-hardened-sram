"""Validate Virtuoso-exported device connectivity and use that export for simulation."""
from pathlib import Path
import json,re,subprocess

ROOT=Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'design/cell_definitions.json').read_text())
folder=ROOT/'artifacts/netlists';folder.mkdir(parents=True,exist_ok=True)
library=['// Device lines exported by Virtuoso from rh_sram_lib schematics.', 'simulator lang=spectre']
checked=[]
def number(s):
 match=re.fullmatch(r'([-+\d.eE]+)([afpnumkMG]?)',s)
 assert match,s
 return float(match[1])*{'':1,'a':1e-18,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'M':1e6,'G':1e9}[match[2]]
for cell,definition in spec.items():
 target=folder/(cell+'_virtuoso.scs')
 remote=f'ic618:/home/rocky/work/rh_sram/runs/cadence_netlists/{cell}/spectre/schematic/netlist/netlist'
 subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=8',remote,str(target)],check=True)
 text=target.read_text().replace('\\\n',' ')
 found={}
 for line in text.splitlines():
  match=re.match(r'^([PN]\d+)\s+\(([^)]+)\)\s+(nch|pch)\s+(.*)',line)
  if match:found[match[1]]=(match[2].split(),match[3],dict(re.findall(r'(\w+)=([^\s]+)',match[4])))
 assert len(found)==len(definition['transistors']),(cell,len(found))
 for m in definition['transistors']:
  pins,model,params=found[m['name']]
  assert pins==[m[p] for p in ['d','g','s','b']],(cell,m['name'],pins)
  assert model==('nch' if m['kind']=='n' else 'pch')
  for param,expected in {'w':m['w_um']*1e-6,'l':m['l_um']*1e-6,'ad':m['w_um']*.2e-12,'as':m['w_um']*.2e-12,'nrd':.135,'nrs':.135}.items():
   assert abs(number(params[param])-expected)<max(abs(expected)*1e-9,1e-22),(cell,m['name'],param)
 library += [f'subckt {cell} ({" ".join(definition["ports"])})', text, f'ends {cell}\n']
 checked.append({'cell':cell,'transistors':len(found),'all_DGSB_and_geometry_matched':True})
(ROOT/'design/netlists/bitcells.scs').write_text('\n'.join(library)+'\n',encoding='ascii')
(folder/'consistency_check.json').write_text(json.dumps(checked,indent=2),encoding='ascii')
print(json.dumps(checked))
