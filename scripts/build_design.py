"""Generate the shared transistor specification and stage-one Spectre experiments."""
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design"
NET = OUT / "netlists"
NET.mkdir(parents=True, exist_ok=True)
VDD = 1.8


def mos(name, kind, d, g, s, b, width):
    return dict(name=name, kind=kind, d=d, g=g, s=s, b=b, w_um=width, l_um=0.18)


cells = {
    "sram6t": dict(
        ports=["BL", "BLB", "WL", "VDD", "VSS"], nodes=["Q", "QN"],
        transistors=[
            mos("P1", "p", "Q", "QN", "VDD", "VDD", 0.30),
            mos("P2", "p", "QN", "Q", "VDD", "VDD", 0.30),
            mos("N1", "n", "Q", "QN", "VSS", "VSS", 0.80),
            mos("N2", "n", "QN", "Q", "VSS", "VSS", 0.80),
            mos("N3", "n", "Q", "WL", "BL", "VSS", 0.40),
            mos("N4", "n", "QN", "WL", "BLB", "VSS", 0.40),
        ],
    ),
    "hphs12t": dict(
        ports=["BL", "BLB", "WL", "VDD", "VSS"], nodes=["Q", "QN", "S0", "S1"],
        transistors=[
            mos("P1", "p", "Q", "QN", "VDD", "VDD", 0.30),
            mos("P2", "p", "QN", "Q", "VDD", "VDD", 0.30),
            mos("N1", "n", "S0", "S1", "VSS", "VSS", 2.40),
            mos("N2", "n", "S1", "S0", "VSS", "VSS", 2.40),
            mos("N3", "n", "Q", "S1", "S0", "VSS", 0.80),
            mos("N4", "n", "QN", "S0", "S1", "VSS", 0.80),
            mos("N5", "n", "VDD", "Q", "S0", "VSS", 0.22),
            mos("N6", "n", "VDD", "QN", "S1", "VSS", 0.22),
            mos("N7", "n", "S0", "WL", "BL", "VSS", 0.40),
            mos("N8", "n", "S1", "WL", "BLB", "VSS", 0.40),
            mos("N9", "n", "Q", "WL", "BL", "VSS", 0.40),
            mos("N10", "n", "QN", "WL", "BLB", "VSS", 0.40),
        ],
    ),
}
(OUT / "cell_definitions.json").write_text(json.dumps(cells, indent=2), encoding="utf-8")

lib = ["// Canonical bitcells. D G S B order. Geometry: metres; diffusion extension 0.20 um.", "simulator lang=spectre"]
for name, cell in cells.items():
    lib.append(f"subckt {name} ({' '.join(cell['ports'])})")
    for m in cell["transistors"]:
        w = m["w_um"]
        lib.append(
            f"{m['name']} ({m['d']} {m['g']} {m['s']} {m['b']}) {'nch' if m['kind']=='n' else 'pch'} "
            f"w={w:g}u l=180n ad={w*0.2:g}p as={w*0.2:g}p pd={2*(w+0.2):g}u ps={2*(w+0.2):g}u nrd=0.135 nrs=0.135"
        )
    lib.append(f"ends {name}\n")
(NET / "bitcells.scs").write_text("\n".join(lib) + "\n", encoding="ascii")


def wave(initial, events):
    points = [(0.0, initial)]
    previous = initial
    for t_ns, value in events:
        points += [(t_ns * 1e-9, previous), (t_ns * 1e-9 + 50e-12, value)]
        previous = value
    return " ".join(f"{t:.12g} {v:.12g}" for t, v in points)


def source(name, node, initial, events):
    return f"{name} ({node} 0) vsource type=pwl wave=[ {wave(initial, events)} ]"


def header(title, corner="tt"):
    return [f"// {title}", "simulator lang=spectre", "global 0", "parameters vdd=1.8",
            f'include "/home/rocky/work/iclab018um/models/spectre/rf018.scs" section={corner}',
            'include "bitcells.scs"', "VDD (VDD 0) vsource dc=vdd"]


def bench(cell, wl, we, pc, data, datab):
    return [wl, we, pc, data, datab,
            "WBL (BL DATA WE 0) relay ropen=1e12 rclosed=1 vt1=0.8 vt2=1.0",
            "WBLB (BLB DATAB WE 0) relay ropen=1e12 rclosed=1 vt1=0.8 vt2=1.0",
            "PRE1 (BL PC VDD VDD) pch w=2u l=180n",
            "PRE2 (BLB PC VDD VDD) pch w=2u l=180n",
            "CBL (BL 0) capacitor c=100f", "CBLB (BLB 0) capacitor c=100f",
            f"Xcell (BL BLB WL VDD 0) {cell}"]


def tail(cell, state, stop_ns):
    init = {"Q": VDD * state, "QN": VDD * (1-state)}
    if cell == "hphs12t":
        init.update(S0=1.2 * state, S1=1.2 * (1-state))
    return ["ic " + " ".join(f"Xcell.{n}={v:g}" for n, v in init.items()),
            "simOptions options temp=27 tnom=25 reltol=1e-5 vabstol=1e-6 iabstol=1e-12",
            f"tran tran stop={stop_ns}n maxstep=10p errpreset=conservative",
            "save WL WE PC BL BLB VDD:p " + " ".join("Xcell."+n for n in cells[cell]["nodes"])]


cases = []
for cell in cells:
    for corner in ["tt", "ff", "ss"]:
        name = f"{cell}_functional_{corner}"
        lines = header("Write 1, hold, read 1, write 0, hold, read 0", corner)
        lines += bench(cell,
            source("VWL", "WL", 0, [(5.2,VDD),(7.2,0),(12,VDD),(13,0),(20.2,VDD),(22.2,0),(27,VDD),(28,0)]),
            source("VWE", "WE", 0, [(5,VDD),(7.4,0),(20,VDD),(22.4,0)]),
            source("VPC", "PC", 0, [(4.8,VDD),(7.6,0),(11.8,VDD),(13.2,0),(19.8,VDD),(22.6,0),(26.8,VDD),(28.2,0)]),
            source("VD", "DATA", VDD, [(19,0)]), source("VDB", "DATAB", 0, [(19,VDD)]))
        lines += tail(cell, 0, 32)
        (NET / (name+".scs")).write_text("\n".join(lines)+"\n", encoding="ascii")
        cases.append(dict(name=name, cell=cell, kind="functional", corner=corner))


def pulse(charge_fc):
    # Normalized difference of exponentials; numerical area is exactly charge_fc.
    tf, tr = 164e-12, 50e-12
    dt = 2e-12
    times = [i*dt for i in range(1641)]
    currents = [math.exp(-t/tf)-math.exp(-t/tr) for t in times]
    area = sum((currents[i]+currents[i+1])*dt/2 for i in range(len(times)-1))
    currents = [x * charge_fc*1e-15/area for x in currents]
    return times, currents


for cell in cells:
    for state in [0,1]:
        # Zero-injection controls and all internal nodes at 90 fC.
        conditions = [("Q", 0)] + [(node,charge) for charge in [10,20,30,45,60,90] for node in cells[cell]["nodes"]]
        for node, charge in conditions:
            name = f"{cell}_seu_s{state}_{node}_{charge}fC"
            lines = header(f"SEU hold-mode test, stored Q={state}, node={node}, charge={charge} fC")
            lines += bench(cell,
                source("VWL", "WL", 0, [(2.2,VDD),(4.2,0)]),
                source("VWE", "WE", 0, [(2,VDD),(4.4,0)]),
                source("VPC", "PC", 0, [(1.8,VDD),(4.6,0)]),
                source("VD", "DATA", VDD*state, []), source("VDB", "DATAB", VDD*(1-state), []))
            times, currents = pulse(charge)
            node_high = state if node in ["Q","S0"] else 1-state
            sign = 1 if node_high else -1
            pairs = [(0,0),(10e-9,0)] + [(10e-9+t,sign*i) for t,i in zip(times[1:],currents[1:])] + [(13.3e-9,0)]
            lines.append(f"VSEUMON (Xcell.{node} INJECT) vsource dc=0")
            lines.append("ISEU (INJECT 0) isource type=pwl wave=[ " + " ".join(f"{t:.12g} {i:.12g}" for t,i in pairs) + " ]")
            lines += tail(cell,state,20)
            lines[-1] += " VSEUMON:p"
            (NET / (name+".scs")).write_text("\n".join(lines)+"\n", encoding="ascii")
            cases.append(dict(name=name,cell=cell,kind="seu",state=state,node=node,charge_fc=charge,tf_ps=164,tr_ps=50))
(OUT / "cases.json").write_text(json.dumps(cases,indent=2),encoding="ascii")
print(f"Generated {len(cases)} experiments and two bitcell definitions in {OUT}")
