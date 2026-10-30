#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
virtuoso -nograph -nocdsinit -replay scripts/polish_schematics.il -log runs/polish_schematics.log > runs/polish_schematics.stdout 2>&1
cat docs/presentation_checks.txt
