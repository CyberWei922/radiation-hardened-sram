"""Add readable device annotations and conductive core paths, without changing nets."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lines=[(ROOT/'design/create_schematics.il').read_text().split("simulator('spectre)",1)[0],"simulator('spectre)",
       'fp=outfile("/home/rocky/work/rh_sram/docs/presentation_checks.txt")']
for cell in ['sram6t','hphs12t']:
 for viewcell in [cell,f'tb_{cell}_seu',f'tb_{cell}_functional']:
  lines += [f'cv=dbOpenCellViewByType("rh_sram_lib" "{viewcell}" "schematic" "schematic" "a")',
            'foreach(inst cv~>instances',
            '  when(equal(inst~>libName "tsmc18rf")',
            '    xy=inst~>xy',
            '    dbCreateLabel(cv list("text" "drawing") list(xCoord(xy)-.55 yCoord(xy)+.8) sprintf(nil "%s W=%s" inst~>name inst~>w) "lowerLeft" "R0" "stick" .12)',
            '  )',')']
  if not viewcell.endswith('_functional'):
   if cell=='hphs12t':
    paths=[('Q',[(-2.25,5.3125),(-2.25,3.1875)]),('QN',[(2.75,5.3125),(2.75,3.1875)]),
           ('S0',[(-2.25,1.8125),(-2.25,.6875)]),('S1',[(2.75,1.8125),(2.75,.6875)]),
           ('S0',[(-.65,3.6125),(-.65,1.25),(-2.25,1.25)]),
           ('S1',[(1.15,3.6125),(1.15,1.25),(2.75,1.25)]),
           ('VDD',[(-2.25,6.6875),(-2.25,7.2),(2.75,7.2),(2.75,6.6875)]),
           ('VSS',[(-2.25,-.6875),(-2.25,-1.2),(2.75,-1.2),(2.75,-.6875)])]
   else:
    py=3.5 if viewcell==cell else 4
    ny=.5 if viewcell==cell else 1
    paths=[('Q',[(-2.25,py-.6875),(-2.25,ny+.6875)]),
           ('QN',[(2.75,py-.6875),(2.75,ny+.6875)]),
           ('VDD',[(-2.25,py+.6875),(-2.25,py+1.25),(2.75,py+1.25),(2.75,py+.6875)]),
           ('VSS',[(-2.25,ny-.6875),(-2.25,ny-1.25),(2.75,ny-1.25),(2.75,ny-.6875)])]
   for net,points in paths:
    ps=' '.join(f'list({x} {y})' for x,y in points)
    lines.append(f'rhWireLabel(cv list({ps}) "{net}")')
  lines += ['schCheck(cv)','dbSave(cv)',f'fprintf(fp "{viewcell} markers=%d\\n" length(cv~>markers))','dbClose(cv)',
            'envSetVal("asimenv.startup" "projectDir" \'string "/home/rocky/work/rh_sram/runs/cadence_netlists")',
            f'design("rh_sram_lib" "{viewcell}" "schematic" "r")','createNetlist(?recreateAll t)']
lines += ['close(fp)','exit()']
(ROOT/'design/polish_schematics.il').write_text('\n'.join(lines)+'\n',encoding='ascii')
