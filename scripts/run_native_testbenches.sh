#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
mkdir -p netlists/native
for cell in sram6t hphs12t; do
  for kind in functional seu; do
    tb=tb_${cell}_${kind}
    out=netlists/native/${tb}.scs
    {
      printf 'simulator lang=spectre\nglobal 0\n'
      printf 'include "/home/rocky/work/iclab018um/models/spectre/rf018.scs" section=tt\n'
      cat "runs/cadence_netlists/$tb/spectre/schematic/netlist/netlist"
      if [ "$kind" = functional ]; then
        prefix=Xcell.
        stop=32n
      else
        prefix=
        stop=20n
      fi
      printf '\nic %sQ=0 %sQN=1.8' "$prefix" "$prefix"
      if [ "$cell" = hphs12t ]; then printf ' %sS0=0 %sS1=1.2' "$prefix" "$prefix"; fi
      printf '\nsimOptions options temp=27 tnom=25 reltol=1e-5 vabstol=1e-6 iabstol=1e-12\n'
      printf 'tran tran stop=%s maxstep=10p errpreset=conservative\n' "$stop"
      printf 'save WL WE PC BL BLB VSUPPLY:p %sQ %sQN' "$prefix" "$prefix"
      if [ "$cell" = hphs12t ]; then printf ' %sS0 %sS1' "$prefix" "$prefix"; fi
      if [ "$kind" = seu ]; then printf ' VSEUMON:p'; fi
      printf '\n'
    } > "$out"
    mkdir -p "runs/native/$tb"
    spectre "$out" +log "runs/native/$tb/spectre.log" -format psfascii -raw "runs/native/$tb/psf" > "runs/native/$tb/stdout.log" 2>&1
    grep 'completes with' "runs/native/$tb/spectre.log"
  done
done
