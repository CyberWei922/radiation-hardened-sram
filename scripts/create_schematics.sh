#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
grep -q 'DEFINE rh_sram_lib' cds.lib || printf '\nDEFINE rh_sram_lib ./lib\n' >> cds.lib
virtuoso -nograph -nocdsinit -replay scripts/create_schematics.il -log runs/create_schematics.log > runs/create_schematics.stdout 2>&1
cat docs/schematics_done.txt
cat docs/schematic_connectivity.tsv
grep -E '\*Error\*|SCH-.*(warning|error)|Check completed' runs/create_schematics.log | tail -20 || true
