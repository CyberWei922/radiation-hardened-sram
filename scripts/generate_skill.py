"""Build genuine Virtuoso schematic/symbol views from the shared MOS definition."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
cells=json.loads((ROOT/'design/cell_definitions.json').read_text())
out=ROOT/'design/create_schematics.il'
prelude=r'''
procedure(rhWireLabel(cv points name)
  let((w)
    w=schCreateWire(cv "draw" "full" points 0.0625 0.0625 0)
    schCreateWireLabel(cv car(w) car(last(points)) name "lowerLeft" "R0" "stick" 0.09 nil)
  )
)
procedure(rhDevice(cv kind name origin orient width length nets)
  let((master inst point offset finish net term value)
    master=dbOpenCellViewByType("tsmc18rf" if(equal(kind "n") then "nmos2v" else "pmos2v") "symbol" nil "r")
    inst=dbCreateInst(cv master name origin orient)
    dbReplaceProp(inst "w" "string" sprintf(nil "%gu" width))
    dbReplaceProp(inst "l" "string" sprintf(nil "%gu" length))
    dbReplaceProp(inst "m" "string" "1")
    foreach(prop list("ad" "as") dbReplaceProp(inst prop "string" sprintf(nil "%g" width*0.2e-12)))
    foreach(prop list("pd" "ps") dbReplaceProp(inst prop "string" sprintf(nil "%gu" 2*(width+0.2))))
    foreach(term master~>terminals
      net=cadr(assoc(term~>name nets))
      unless(net error("No net supplied for %s.%s" name term~>name))
      point=centerBox(car(term~>pins)~>fig~>bBox)
      offset=cond(
        (equal(term~>name "G") list(-0.625 0.0))
        (equal(term~>name "B") list(0.625 0.0))
        (yCoord(point)>0 list(0.0 0.50))
        (t list(0.0 -0.50))
      )
      finish=list(xCoord(point)+xCoord(offset) yCoord(point)+yCoord(offset))
      point=dbTransformPoint(point inst~>transform)
      finish=dbTransformPoint(finish inst~>transform)
      rhWireLabel(cv list(point finish) net)
    )
    inst
  )
)
procedure(rhPort(cv name direction xy)
  let((master endpoint)
    master=dbOpenCellViewByType("basic" if(equal(direction "input") then "ipin" else "iopin") "symbol" nil "r")
    schCreatePin(cv master name direction nil xy "R0")
    endpoint=list(xCoord(xy)+0.75 yCoord(xy))
    rhWireLabel(cv list(xy endpoint) name)
  )
)
simulator('spectre)
unless(ddGetObj("rh_sram_lib") ddCreateLib("rh_sram_lib" "/home/rocky/work/rh_sram/lib"))
techBindTechFile(ddGetObj("rh_sram_lib") "tsmc18rf")
rhReport=outfile("/home/rocky/work/rh_sram/docs/schematic_connectivity.tsv")
'''
positions={
 'sram6t':{'P1':(-2.5,3.5),'P2':(2.5,3.5),'N1':(-2.5,0.5),'N2':(2.5,0.5),'N3':(-6,2),'N4':(6,2)},
 'hphs12t':{'P1':(-2.5,6),'P2':(2.5,6),'N1':(-2.5,0),'N2':(2.5,0),
             'N3':(-2.5,2.5),'N4':(2.5,2.5),'N5':(-.9,4.3),'N6':(.9,4.3),
             'N7':(-6,1),'N8':(6,1),'N9':(-6,4.5),'N10':(6,4.5)}}
lines=[prelude]
for name,cell in cells.items():
 lines += [f'cv=dbOpenCellViewByType("rh_sram_lib" "{name}" "schematic" "schematic" "w")',
           'foreach(inst cv~>instances dbDeleteObject(inst))',
           'foreach(shape cv~>shapes dbDeleteObject(shape))',
           'foreach(term cv~>terminals dbDeleteObject(term))',
           'foreach(net cv~>nets dbDeleteObject(net))']
 for m in cell['transistors']:
  x,y=positions[name][m['name']]
  access=m['g']=='WL'
  orient='R90' if access else 'R0'
  nets=' '.join(f'list("{p.upper()}" "{m[p]}")' for p in ['d','g','s','b'])
  lines.append(f'rhDevice(cv "{m["kind"]}" "{m["name"]}" list({x} {y}) "{orient}" {m["w_um"]} {m["l_um"]} list({nets}))')
 top=8 if name=='hphs12t' else 6
 for pin,direction,x,y in [('VDD','inputOutput',-8,top),('WL','input',-8,top-1),('BL','inputOutput',-8,top-2),('BLB','inputOutput',8,top-2),('VSS','inputOutput',-8,-2)]:
  lines.append(f'rhPort(cv "{pin}" "{direction}" list({x} {y}))')
 lines += [f'dbCreateLabel(cv list("text" "drawing") list(-3 {top}) "{name.upper()}  |  180 nm  |  1.8 V" "lowerLeft" "R0" "stick" 0.22)',
           'schCheck(cv)', 'dbSave(cv)',
           f'fprintf(rhReport "CELL\t{name}\t%d\tMARKERS\t%d\\n" length(cv~>instances) length(cv~>markers))',
           r'''foreach(inst cv~>instances
  when(equal(inst~>libName "tsmc18rf")
    foreach(it inst~>instTerms fprintf(rhReport "%s\t%s\t%s\t%s\n" cv~>cellName inst~>name it~>name it~>net~>name))
  )
)''', 'dbClose(cv)',
           f'sym=dbOpenCellViewByType("rh_sram_lib" "{name}" "symbol" "schematicSymbol" "w")',
           'foreach(inst sym~>instances dbDeleteObject(inst))',
           'foreach(shape sym~>shapes dbDeleteObject(shape))',
           'foreach(term sym~>terminals dbDeleteObject(term))',
           'foreach(net sym~>nets dbDeleteObject(net))',
           'dbCreateRect(sym list("device" "drawing") list(list(-1 -1) list(1 1)))',
           f'dbCreateLabel(sym list("device" "drawing") list(0 0) "{name.upper()}" "centerCenter" "R0" "stick" 0.22)',
           'pinMaster=dbOpenCellViewByType("basic" "sympin" "symbolNN" nil "r")']
 for pin,direction,x,y,orient in [('BL','inputOutput',-1,.5,'R0'),('WL','input',-1,0,'R0'),('BLB','inputOutput',-1,-.5,'R0'),('VDD','inputOutput',0,1,'R270'),('VSS','inputOutput',0,-1,'R90')]:
  lines.append(f'schCreateSymbolPin(sym pinMaster "{pin}" "{direction}" list({x} {y}) "{orient}")')
 lines+=['dbSave(sym)','dbClose(sym)']
lines += ['close(rhReport)','fp=outfile("/home/rocky/work/rh_sram/docs/schematics_done.txt")','fprintf(fp "SCHEMATICS_CREATED\\n")','close(fp)']
for name in cells:
 lines += ['envSetVal("asimenv.startup" "projectDir" \'string "/home/rocky/work/rh_sram/runs/cadence_netlists")',
           "simulator('spectre)",f'design("rh_sram_lib" "{name}" "schematic" "r")',
           'netlistPath=createNetlist(?recreateAll t)',
           f'printf("NETLIST {name} %L\\n" netlistPath)']
lines += ['exit()']
out.write_text('\n'.join(lines)+'\n',encoding='ascii')
print(out)
