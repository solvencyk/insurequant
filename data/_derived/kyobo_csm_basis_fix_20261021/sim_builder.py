"""Read-only builder simulation for CSM_waterfall (KR0073 fix, 2026-10-21).

Runs the REAL scripts/build_root_masters.py::build_csm() logic with module globals redirected:
    CSM_SRC  = live data/dart/viz/csm_waterfall_master_diag.json (read only)
    CSM_OVR  = <candidate gold file>                              (read only)
    CSM_OUT  = <temp file seeded with a copy of the live master>   (the only file written)
so nothing in the repo is changed.  The result is spliced back: all rows of the live master stay byte-for-byte
the same objects except the rows of --code, which are taken from the simulated build (値 + 값_당분기).

Usage:
  python sim_builder.py --gold <gold.json> --out <candidate_master.json> [--code KR0073] [--tmp <tmp.json>] [--full-diff]
Prints: number of rows differing from the live master by company (fidelity report), and for --code the cell diff.
"""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")


def load_brm():
    spec = importlib.util.spec_from_file_location("brm_sim", str(ROOT / "scripts" / "build_root_masters.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def simulate(gold_path, tmp_path):
    brm = load_brm()
    shutil.copyfile(ROOT / "CSM_waterfall.json", tmp_path)
    brm.CSM_OVR = Path(gold_path)
    brm.CSM_OUT = Path(tmp_path)
    nrows, nbad = brm.build_csm()
    with open(tmp_path, "r", encoding="utf-8") as f:
        return json.load(f), nrows, nbad


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--code", default="KR0073")
    ap.add_argument("--tmp", default=None)
    ap.add_argument("--full-diff", action="store_true")
    a = ap.parse_args()
    tmp = a.tmp or (str(Path(a.out).with_suffix(".simtmp.json")))
    sim, nrows, nbad = simulate(a.gold, tmp)
    with open(ROOT / "CSM_waterfall.json", "r", encoding="utf-8") as f:
        live = json.load(f)
    live_by = {key(r): r for r in live}
    sim_by = {key(r): r for r in sim}
    # fidelity report: how many rows of each company differ between live and a fresh builder run
    diff_by_co = {}
    only_live, only_sim = 0, 0
    for k, r in live_by.items():
        s = sim_by.get(k)
        if s is None:
            only_live += 1
            continue
        if (r.get("값"), r.get("값_당분기"), r.get("항목명")) != (s.get("값"), s.get("값_당분기"), s.get("항목명")):
            diff_by_co.setdefault(k[0], []).append(k)
    for k in sim_by:
        if k not in live_by:
            only_sim += 1
    print(f"simulated rows={nrows} unit-error c-q nulled={nbad}; live rows={len(live)}; only_in_live={only_live}; only_in_sim={only_sim}")
    print("companies where a fresh builder run != live master (cell count):",
          {c: len(v) for c, v in sorted(diff_by_co.items())} if diff_by_co else "none")
    # splice
    out_rows = []
    for r in live:
        if r["원보험사코드"] == a.code:
            s = sim_by.get(key(r))
            if s is None:
                raise SystemExit(f"ABORT: {key(r)} missing in simulation")
            nr = dict(r)
            nr["값"] = s["값"]
            nr["값_당분기"] = s["값_당분기"]
            out_rows.append(nr)
        else:
            out_rows.append(r)
    extra = [r for k, r in sim_by.items() if k not in live_by and k[0] == a.code]
    if extra:
        raise SystemExit(f"ABORT: simulation adds {len(extra)} new rows for {a.code}: {[key(r) for r in extra][:5]}")
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_rows, f, ensure_ascii=False, indent=2)
    # cell diff for code
    changed = []
    for r, n in zip(live, out_rows):
        if r["원보험사코드"] == a.code and (r["값"], r.get("값_당분기")) != (n["값"], n.get("값_당분기")):
            changed.append((r["공시분기"], r["항목번호"], r["값"], n["값"], r.get("값_당분기"), n.get("값_당분기")))
    print(f"{a.code} cells changed vs live: {len(changed)}")
    for c in changed:
        print("  ", c)


if __name__ == "__main__":
    main()
