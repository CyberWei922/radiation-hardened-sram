#!/bin/bash
set -e
project=/home/rocky/work/rh_sram
mkdir -p "$project"/{netlists,scripts,runs,docs}
cat > "$project/env.sh" <<'EOF'
export CADHOME=/opt/cadence
export CDS_INST_DIR=/opt/cadence/IC618
export CDSDIR=$CDS_INST_DIR
export CDSHOME=$CDS_INST_DIR
export CDS_LIC_FILE=$CDS_INST_DIR/share/license/license.dat
export LM_LICENSE_FILE=$CDS_LIC_FILE
export CDS_LIC_ONLY=1
export CDS_AUTO_64BIT=ALL
export CDS_Netlisting_Mode=Analog
export CDS_LOAD_ENV=CWD
export LANG=C
export PATH=/opt/cadence/IC618/tools/dfII/bin:/opt/cadence/SPECTRE231/tools/bin:/opt/cadence/SPECTRE231/bin:$PATH
EOF
cat > "$project/cds.lib" <<'EOF'
INCLUDE /opt/cadence/IC618/share/cdssetup/cds.lib
DEFINE tsmc18rf /home/rocky/work/iclab018um/tsmc18rf
EOF
cp -n /home/rocky/work/iclab018um/display.drf "$project/" || true
cat > "$project/netlists/inverter_smoke.scs" <<'EOF'
// Environment check: 180 nm core CMOS inverter, TT, 1.8 V, 27 C.
simulator lang=spectre
global 0
parameters vdd=1.8
include "/home/rocky/work/iclab018um/models/spectre/rf018.scs" section=tt
VDD (vdd 0) vsource dc=vdd
VIN (in 0) vsource type=pulse val0=0 val1=vdd delay=1n rise=50p fall=50p width=4n period=10n
MN (out in 0 0) nch w=500n l=180n ad=100f as=100f pd=1.4u ps=1.4u
MP (out in vdd vdd) pch w=1u l=180n ad=200f as=200f pd=2.4u ps=2.4u
CL (out 0) capacitor c=10f
simOptions options temp=27 tnom=25 reltol=1e-4 vabstol=1e-6 iabstol=1e-12
tran tran stop=20n maxstep=10p errpreset=conservative
save in out VDD:p
EOF
. "$project/env.sh"
cd "$project"
mkdir -p runs/inverter_smoke
spectre netlists/inverter_smoke.scs +log runs/inverter_smoke/spectre.log -format psfascii -raw runs/inverter_smoke/psf > runs/inverter_smoke/stdout.log 2>&1
tail -30 runs/inverter_smoke/spectre.log
