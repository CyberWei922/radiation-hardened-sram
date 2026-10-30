#!/bin/bash
set -e
cd /home/rocky/work/rh_sram
. ./env.sh
virtuoso -nograph -nocdsinit -replay scripts/shorten_labels.il -log runs/shorten_labels.log > runs/shorten_labels.stdout 2>&1
cat > scripts/start_gui.sh <<'EOF'
#!/bin/bash
cd /home/rocky/work/rh_sram || exit 1
. ./env.sh
exec virtuoso -nocdsinit -replay scripts/open_project.il -log "runs/gui_$(date +%Y%m%d_%H%M%S).log"
EOF
chmod +x scripts/start_gui.sh
cat > /home/rocky/Desktop/SRAM-Project.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=SRAM Project - Virtuoso
Exec=/home/rocky/work/rh_sram/scripts/start_gui.sh
Path=/home/rocky/work/rh_sram
Terminal=false
Icon=applications-engineering
EOF
chmod +x /home/rocky/Desktop/SRAM-Project.desktop
if command -v gio >/dev/null; then gio set /home/rocky/Desktop/SRAM-Project.desktop metadata::trusted true || true; fi
echo 'Project launcher created; labels saved.'
