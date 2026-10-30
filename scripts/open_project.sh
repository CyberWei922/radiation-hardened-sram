#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
python - <<'PY'
import io
s=io.open('cds.lib',encoding='utf-8').read()
if s.count('DEFINE rh_sram_lib')>1:
    io.open('docs/cds.lib.before_deduplicate','w',encoding='utf-8').write(s)
    io.open('cds.lib','w',encoding='utf-8').write('\n'.join(x for x in s.splitlines() if not x.startswith('DEFINE rh_sram_lib'))+'\nDEFINE rh_sram_lib /home/rocky/work/rh_sram/lib\n')
PY
session_pid=$(pgrep -u rocky -f '^/usr/libexec/gnome-session-binary' | head -1)
while IFS= read -r -d '' entry; do
  case "$entry" in DISPLAY=*|XAUTHORITY=*|DBUS_SESSION_BUS_ADDRESS=*|XDG_RUNTIME_DIR=*) export "$entry";; esac
done < "/proc/$session_pid/environ"
nohup virtuoso -nocdsinit -replay scripts/open_project.il -log runs/virtuoso_gui.log > runs/virtuoso_gui.stdout 2>&1 </dev/null &
echo "Virtuoso GUI PID=$!"
