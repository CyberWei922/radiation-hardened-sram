"""Read Spectre PSF ASCII, verify basic results, and save traceable figures."""
from pathlib import Path
import json
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts" / "results"
FIGURES = ROOT / "artifacts" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def read_psf(path):
    body = path.read_text(encoding="utf-8").split("\nVALUE\n", 1)[1]
    values = {}
    for line in body.splitlines():
        match = re.fullmatch(r'"([^"\n]+)"\s+([-+0-9.eE]+)', line.strip())
        if match:
            values.setdefault(match[1], []).append(float(match[2]))
    arrays = {name: np.asarray(data) for name, data in values.items()}
    assert "time" in arrays
    assert all(len(a) == len(arrays["time"]) for a in arrays.values())
    return arrays


def at(data, node, time_ns):
    return float(np.interp(time_ns*1e-9, data["time"], data[node]))


def main():
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150,
                         "axes.grid": True, "grid.alpha": 0.18})
    summary = {}
    for cell in ["sram6t", "hphs12t"]:
        case = cell + "_functional_tt"
        data = read_psf(RESULTS / case / "psf" / "tran.tran.tran")
        q_samples = [at(data,"Xcell.Q",t) for t in [9,15,24,30]]
        qn_samples = [at(data,"Xcell.QN",t) for t in [9,15,24,30]]
        expected = [1,1,0,0]
        functional_pass = all((q > 1.44 and qb < 0.36) if state else
                              (q < 0.36 and qb > 1.44)
                              for q,qb,state in zip(q_samples,qn_samples,expected))
        summary[case] = dict(functional_pass=functional_pass,
            sample_times_ns=[9,15,24,30],q_V=q_samples,qn_V=qn_samples,
            read1_delta_BL_V=at(data,"BL",12.9)-at(data,"BLB",12.9),
            read0_delta_BL_V=at(data,"BL",27.9)-at(data,"BLB",27.9))
        fig, axes = plt.subplots(3,1,figsize=(11,7.2),sharex=True,layout="constrained")
        t=data["time"]*1e9
        axes[0].plot(t,data["WL"],label="WL",color="#6f42c1")
        axes[0].plot(t,data["WE"],label="Write enable",color="#7c8c97",ls="--")
        axes[0].set_ylabel("Control (V)");axes[0].legend(loc="upper right",ncol=2)
        for node,color in [("Q","#0969da"),("QN","#d1242f"),("S0","#198754"),("S1","#d18b00")]:
            if "Xcell."+node in data:
                axes[1].plot(t,data["Xcell."+node],label=node,color=color,ls="--" if node.startswith("S") else "-")
        axes[1].set_ylabel("Storage (V)");axes[1].legend(loc="upper right",ncol=4)
        axes[2].plot(t,data["BL"],label="BL",color="#0969da")
        axes[2].plot(t,data["BLB"],label="BLB",color="#d1242f")
        axes[2].set_ylabel("Bitlines (V)");axes[2].set_xlabel("Time (ns)");axes[2].legend(loc="upper right",ncol=2)
        for ax in axes:
            ax.set_xlim(0,32);ax.set_ylim(-0.1,2.05)
            for a,b in [(5.2,7.2),(12,13),(20.2,22.2),(27,28)]:ax.axvspan(a,b,color="#dce9f4",alpha=0.55)
        fig.suptitle(f"{cell.upper()}: write, hold and read verification\nTSMC 180 nm | TT | VDD = 1.8 V | 27 C | CBL = CBLB = 100 fF",fontsize=12)
        fig.savefig(FIGURES/(case+".png"));plt.close(fig)

    seu_data={}
    for cell in ["sram6t","hphs12t"]:
        case=cell+"_seu_s0_Q_90fC"
        data=read_psf(RESULTS/case/"psf"/"tran.tran.tran")
        seu_data[cell]=data
        stats=dict(q_before_V=at(data,"Xcell.Q",9.9),q_after_V=at(data,"Xcell.Q",18),
                   qn_after_V=at(data,"Xcell.QN",18),q_peak_V=float(data["Xcell.Q"].max()))
        stats["recovered"]=stats["q_after_V"]<0.36 and stats["qn_after_V"]>1.44
        if "VSEUMON:p" in data:
            mask=data["time"]>=9.9e-9
            stats["injected_fC"]=float(-np.trapezoid(data["VSEUMON:p"][mask],data["time"][mask])*1e15)
        summary[case]=stats

    fig,axes=plt.subplots(2,1,figsize=(10.5,6.4),sharex=True,layout="constrained")
    for ax,(cell,data) in zip(axes,seu_data.items()):
        t=data["time"]*1e9
        for node,color in [("Q","#0969da"),("QN","#d1242f"),("S0","#198754"),("S1","#d18b00")]:
            if "Xcell."+node in data:
                ax.plot(t,data["Xcell."+node],label=node,color=color,ls="--" if node.startswith("S") else "-")
        ax.axvline(10,color="#636b74",ls=":");ax.set_ylabel(cell.upper()+" (V)")
        ax.legend(loc="upper right",ncol=4);ax.set_xlim(8,16)
    axes[-1].set_xlabel("Time (ns)")
    fig.suptitle("Same 90 fC injection at Q while storing 0\nDouble exponential: decay 164 ps, rise 50 ps | TT, 1.8 V, 27 C",fontsize=12)
    fig.savefig(FIGURES/"seu_initial_comparison.png");plt.close(fig)
    (RESULTS/"stage1_initial_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
