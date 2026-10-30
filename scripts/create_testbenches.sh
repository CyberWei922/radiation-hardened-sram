#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
virtuoso -nograph -nocdsinit -replay scripts/create_testbenches.il -log runs/create_testbenches.log > runs/create_testbenches.stdout 2>&1
cat docs/testbench_checks.txt
grep -E '\*Error\*|ERROR|WARNING' runs/create_testbenches.log | tail -20 || true
