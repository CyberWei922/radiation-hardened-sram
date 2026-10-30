#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
tar --exclude='*.cdslck*' --exclude='__pycache__' --exclude='*.pyc' \
  -czf /home/rocky/work/rh_sram_stage1.tgz \
  cds.lib display.drf env.sh lib scripts stimuli docs netlists runs/cadence_netlists runs/native
tar -tzf /home/rocky/work/rh_sram_stage1.tgz > docs/backup_file_list.txt
sha256sum /home/rocky/work/rh_sram_stage1.tgz
