#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
: > runs/stage1_batch_status.tsv
while read -r case; do
  mkdir -p "runs/$case"
  if spectre "netlists/$case.scs" +log "runs/$case/spectre.log" -format psfascii -raw "runs/$case/psf" > "runs/$case/stdout.log" 2>&1; then
    printf '%s\tPASS\n' "$case" >> runs/stage1_batch_status.tsv
  else
    printf '%s\tFAIL\n' "$case" >> runs/stage1_batch_status.tsv
    tail -25 "runs/$case/stdout.log"
    exit 1
  fi
done < <(python -c 'import json; print("\n".join(x["name"] for x in json.load(open("docs/cases.json"))))')
cat runs/stage1_batch_status.tsv
