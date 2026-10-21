"""Read-only PL builder simulation (KR0073 PL refresh dry run).

Runs the REAL scripts/build_root_masters.py::build_pl() with module globals redirected:
    PL_SRC  = live data/dart/viz/pl_breakdown_master.json (builder output, read only)
    PL_OVR  = <candidate gold file>                         (read only)
    PL_OUT  = <temp file seeded with a copy of the live PL master> (the only file written)
Then splices the KR0073 rows of the result into a copy of the live master (every other row stays the live object).

Usage: python sim_pl_builder.py --gold <gold.json> --out <candidate_PL_breakdown.json> [--tmp <tmp.json>]
"""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0073"


def load_brm():
    spec = importlib.util.spec_from_file_location("brm_sim_pl", str(ROOT / "scripts" / "build_root_masters.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def simulate(gold_path, tmp_path):
    brm = load_brm()
    shutil.copyfile(ROOT / "PL_breakdown.json", tmp_path)
    brm.PL_OVR = Path(gold_path)
    brm.PL_OUT = Path(tmp_path)
    n = brm.build_pl()
    return json.loads(Path(tmp_path).read_text(encoding="utf-8")), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()
    tmp = a.tmp or str(Path(a.out).with_suffix(".simtmp.json"))
    sim, n = simulate(a.gold, tmp)
    live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    lb, sb = {key(r): r for r in live}, {key(r): r for r in sim}
    drift = {}
    for k, r in lb.items():
        s = sb.get(k)
        if s is None:
            drift.setdefault("__missing__", []).append(k)
            continue
        if (r.get("값"), r.get("값_당분기")) != (s.get("값"), s.get("값_당분기")):
            drift.setdefault(k[0], []).append(k)
    print(f"simulated rows={len(sim)} live rows={len(live)} only_in_sim={len(set(sb) - set(lb))}")
    print("companies where a fresh build != live master (cell count):", {c: len(v) for c, v in sorted(drift.items())} or "none")
    out_rows = []
    for r in live:
        if r["원보험사코드"] == CODE:
            s = sb[key(r)]
            nr = dict(r)
            nr["값"], nr["값_당분기"] = s["값"], s["값_당분기"]
            out_rows.append(nr)
        else:
            out_rows.append(r)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_rows, f, ensure_ascii=False, indent=2)
    changed = [(r["공시분기"], r["항목번호"], r["값"], n_["값"], r.get("값_당분기"), n_.get("값_당분기"))
               for r, n_ in zip(live, out_rows) if r["원보험사코드"] == CODE and (r["값"], r.get("값_당분기")) != (n_["값"], n_.get("값_당분기"))]
    print(f"{CODE} cells changed vs live (값 or 값_당분기): {len(changed)}")
    for c in changed[:3]:
        print("  ", c)
    try:
        Path(tmp).unlink()
    except OSError:
        pass


if __name__ == "__main__":
    main()
