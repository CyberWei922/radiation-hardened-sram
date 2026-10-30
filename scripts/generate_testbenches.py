"""Create functional and SEU Virtuoso testbenches, with file-backed stimuli."""
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
cells=json.loads((ROOT/'design/cell_definitions.json').read_text())
stim=ROOT/'design/stimuli';stim.mkdir(exist_ok=True)
remote='/home/rocky/work/rh_sram'
helpers=(ROOT/'design/create_schematics.il').read_text().split("simulator('spectre)",1)[0]
lines=[helpers,r'''
simulator('spectre)
procedure(rhAnalog(cv cell name xy nets props)
  let((master inst point finish dx dy)
    master=dbOpenCellViewByType("analogLib" cell "symbol" nil "r")
    inst=dbCreateInst(cv master name xy "R0")
    foreach(prop props dbReplaceProp(inst car(prop) "string" cadr(prop)))
    foreach(term master~>terminals
      point=centerBox(car(term~>pins)~>fig~>bBox)
      if(equal(cell "switch") then
        dx=if(xCoord(point)>0.1 then 0.625 else -0.625)
        dy=0
      else
        dx=0
        dy=if(yCoord(point)>-0.1 then 0.625 else -0.625)
      )
      finish=list(xCoord(point)+dx yCoord(point)+dy)
      rhWireLabel(cv list(dbTransformPoint(point inst~>transform) dbTransformPoint(finish inst~>transform)) cadr(assoc(term~>name nets)))
    )
    inst
  )
)
procedure(rhBlock(cv cell)
  let((master inst point finish)
    master=dbOpenCellViewByType("rh_sram_lib" cell "symbol" nil "r")
    inst=dbCreateInst(cv master "Xcell" list(0 0) "R0")
    foreach(term master~>terminals
      point=centerBox(car(term~>pins)~>fig~>bBox)
      finish=cond(
        (equal(term~>name "VDD") list(xCoord(point) yCoord(point)+0.75))
        (equal(term~>name "VSS") list(xCoord(point) yCoord(point)-0.75))
        (t list(xCoord(point)-0.75 yCoord(point)))
      )
      rhWireLabel(cv list(point finish) term~>name)
    )
  )
)
rhTBReport=outfile("/home/rocky/work/rh_sram/docs/testbench_checks.txt")
''']
def analog(cell,name,x,y,nets,props):
 nets={p:('gnd!' if n=='0' else n) for p,n in nets.items()}
 ns=' '.join(f'list("{p}" "{n}")' for p,n in nets.items())
 ps=' '.join(f'list("{p}" "{v}")' for p,v in props.items())
 return f'rhAnalog(cv "{cell}" "{name}" list({x} {y}) list({ns}) list({ps}))'
positions={'P1':(-2.5,6),'P2':(2.5,6),'N1':(-2.5,0),'N2':(2.5,0),
           'N3':(-2.5,2.5),'N4':(2.5,2.5),'N5':(-.9,4.3),'N6':(.9,4.3),
           'N7':(-6,1),'N8':(6,1),'N9':(-6,4.5),'N10':(6,4.5)}
sixpos={'P1':(-2.5,4),'P2':(2.5,4),'N1':(-2.5,1),'N2':(2.5,1),'N3':(-6,2.5),'N4':(6,2.5)}
for cell in cells:
 for kind in ['functional','seu']:
  tb=f'tb_{cell}_{kind}'
  base=ROOT/'design/netlists'/f'{cell}_{"functional_tt" if kind=="functional" else "seu_s0_QN_30fC"}.scs'
  text=base.read_text()
  for name,node in [('VWL','WL'),('VWE','WE'),('VPC','PC'),('VD','DATA'),('VDB','DATAB')]:
   m=re.search(rf'^{name} .*wave=\[ (.*) \]$',text,re.M)
   vals=m[1].split();pairs=list(zip(vals[::2],vals[1::2]))
   (stim/f'{kind}_{node}.pwl').write_text('\n'.join(' '.join(p) for p in pairs)+'\n',encoding='ascii')
  if kind=='seu':
   m=re.search(r'^ISEU .*wave=\[ (.*) \]$',text,re.M);vals=m[1].split()
   (stim/'seu_30fC.pwl').write_text('\n'.join(' '.join(p) for p in zip(vals[::2],vals[1::2]))+'\n',encoding='ascii')
  lines += [f'cv=dbOpenCellViewByType("rh_sram_lib" "{tb}" "schematic" "schematic" "w")',
            'foreach(inst cv~>instances dbDeleteObject(inst))','foreach(shape cv~>shapes dbDeleteObject(shape))',
            'foreach(term cv~>terminals dbDeleteObject(term))','foreach(net cv~>nets dbDeleteObject(net))']
  if kind=='functional':lines.append(f'rhBlock(cv "{cell}")')
  else:
   for m in cells[cell]['transistors']:
    x,y=(positions if cell=='hphs12t' else sixpos)[m['name']]
    ns=' '.join(f'list("{p.upper()}" "{m[p]}")' for p in ['d','g','s','b'])
    lines.append(f'rhDevice(cv "{m["kind"]}" "{m["name"]}" list({x} {y}) "{"R90" if m["g"]=="WL" else "R0"}" {m["w_um"]} 0.18 list({ns}))')
  lines += ['gndMaster=dbOpenCellViewByType("analogLib" "gnd" "symbol" nil "r")',
            'dbCreateInst(cv gndMaster "GND" list(-12 -7) "R0")',
            'rhWireLabel(cv list(list(-12 -7) list(-12 -6.5)) "gnd!")',
            analog('vdc','VSUPPLY',-12,7,{'PLUS':'VDD','MINUS':'0'},{'vdc':'1.8'}),
            analog('vdc','VSS_REF',-12,4.5,{'PLUS':'VSS','MINUS':'0'},{'vdc':'0'})]
  for node,x,y in [('WL',-12,1.5),('WE',-12,-1.5),('PC',-12,-4.5),('DATA',11,1.5),('DATAB',11,-1.5)]:
   lines.append(analog('vpwlf','V'+node,x,y,{'PLUS':node,'MINUS':'0'},{'fileName':remote+f'/stimuli/{kind}_{node}.pwl'}))
  for name,x,bl,data in [('WBL',-7,'BL','DATA'),('WBLB',6,'BLB','DATAB')]:
   lines.append(analog('switch',name,x,8,{'N+':bl,'N-':data,'NC+':'WE','NC-':'0'},{'vt1':'.8','vt2':'1','ro':'1T','rc':'1'}))
  for name,x,bl in [('PRE1',-5,'BL'),('PRE2',5,'BLB')]:
   lines.append(f'inst=rhDevice(cv "p" "{name}" list({x} -3.5) "R0" 2.0 0.18 list(list("D" "{bl}") list("G" "PC") list("S" "VDD") list("B" "VDD")))')
   for prop in ['ad','as','pd','ps']:lines.append(f'dbReplaceProp(inst "{prop}" "string" "0")')
   for prop in ['nrd','nrs']:lines.append(f'dbReplaceProp(inst "{prop}" "string" "1")')
  lines += [analog('cap','CBL',-3,-6,{'PLUS':'BL','MINUS':'0'},{'c':'100f'}),
            analog('cap','CBLB',3,-6,{'PLUS':'BLB','MINUS':'0'},{'c':'100f'})]
  if kind=='seu':
   lines += [analog('vdc','VSEUMON',11,7,{'PLUS':'QN','MINUS':'INJECT'},{'vdc':'0'}),
             analog('ipwlf','ISEU',11,4.5,{'PLUS':'INJECT','MINUS':'0'},{'fileName':remote+'/stimuli/seu_30fC.pwl'})]
  lines += [f'dbCreateLabel(cv list("text" "drawing") list(-6 10) "{tb.upper()}" "lowerLeft" "R0" "stick" .3)',
            'schCheck(cv)','dbSave(cv)',f'fprintf(rhTBReport "{tb} markers=%d\\n" length(cv~>markers))','dbClose(cv)',
            'envSetVal("asimenv.startup" "projectDir" \'string "/home/rocky/work/rh_sram/runs/cadence_netlists")',
            "simulator('spectre)",f'design("rh_sram_lib" "{tb}" "schematic" "r")',
            'netlistPath=createNetlist(?recreateAll t)',f'fprintf(rhTBReport "NETLIST {tb} %L\\n" netlistPath)']
lines+=['close(rhTBReport)','exit()']
(ROOT/'design/create_testbenches.il').write_text('\n'.join(lines)+'\n',encoding='ascii')
print('Created four native schematic testbenches and stimulus files')
