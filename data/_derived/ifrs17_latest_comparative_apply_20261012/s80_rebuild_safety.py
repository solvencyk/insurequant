"""Rebuild-safety proof (combo-diff) for PL_breakdown.json / CSM_waterfall.json, run on TEMPORARY COPIES only.

build_root_masters.build_pl() / build_csm() are called in-process with their module paths pointed at temp files (the repo files are never touched; main() is never run):
  A) LIVE inputs      : temp PL_OUT/CSM_OUT = copy of the LIVE masters, real gold files            -> drift_live  = cells where the rebuild output differs from the live master
  B) CANDIDATE inputs : temp PL_OUT/CSM_OUT = copy of the CANDIDATE masters, candidate gold files   -> drift_cand  = same for the candidate
  Rebuild safety: drift_cand must equal drift_live (my cells survive the rebuild and the rebuild changes nothing else because of them) and every plan cell of
  the candidate equals its rebuild output.
usage: s80_rebuild_safety.py <simdir>
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_root_masters as BR  # noqa: E402

sim = Path(sys.argv[1])
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
plan_pl = {(c["code"], c["item"], c["quarter"]): c for c in plan["cells"] if c["master"] == "PL_breakdown"}
plan_csm = {(c["code"], c["item"], c["quarter"]): c for c in plan["cells"] if c["master"] == "CSM_waterfall"}


def run(tag, pl_master, csm_master, gold_pl, gold_csm):
    tmp = Path(tempfile.mkdtemp(prefix=f"rb_{tag}_"))
    pl_out, csm_out = tmp / "PL_breakdown.json", tmp / "CSM_waterfall.json"
    shutil.copyfile(pl_master, pl_out)
    shutil.copyfile(csm_master, csm_out)
    BR.PL_OUT, BR.CSM_OUT, BR.PL_OVR, BR.CSM_OVR = pl_out, csm_out, Path(gold_pl), Path(gold_csm)
    n_pl = BR.build_pl()
    n_csm = BR.build_csm()
    return json.loads(pl_out.read_text(encoding="utf-8")), json.loads(csm_out.read_text(encoding="utf-8")), tmp


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def drift(master_rows, rebuilt_rows):
    mi = {key(r): r for r in master_rows}
    ri = {key(r): r for r in rebuilt_rows}
    out = {}
    for k in set(mi) | set(ri):
        a, b = mi.get(k), ri.get(k)
        if a != b:
            out[k] = (None if a is None else (a.get("값"), a.get("값_당분기")), None if b is None else (b.get("값"), b.get("값_당분기")))
    return out


live_pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
live_csm = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
cand_pl = json.loads((sim / "PL_breakdown.json").read_text(encoding="utf-8"))
cand_csm = json.loads((sim / "CSM_waterfall.json").read_text(encoding="utf-8"))

rb_pl_live, rb_csm_live, t1 = run("live", ROOT / "PL_breakdown.json", ROOT / "CSM_waterfall.json", ROOT / "data/_gold/user_pl_cells.json", ROOT / "data/_gold/user_csm_cells.json")
d_pl_live, d_csm_live = drift(live_pl, rb_pl_live), drift(live_csm, rb_csm_live)
rb_pl_c, rb_csm_c, t2 = run("cand", sim / "PL_breakdown.json", sim / "CSM_waterfall.json", sim / "data/_gold/user_pl_cells.json", sim / "data/_gold/user_csm_cells.json")
d_pl_c, d_csm_c = drift(cand_pl, rb_pl_c), drift(cand_csm, rb_csm_c)

print(f"PL : drift live {len(d_pl_live)} cells ; drift candidate {len(d_pl_c)} cells")
print(f"CSM: drift live {len(d_csm_live)} cells ; drift candidate {len(d_csm_c)} cells")
same_pl = d_pl_live == d_pl_c
same_csm = d_csm_live == d_csm_c
print("PL  drift identical live vs candidate:", same_pl)
print("CSM drift identical live vs candidate:", same_csm)
if not same_pl:
    only = set(d_pl_c) ^ set(d_pl_live)
    print("   PL differing keys", len(only), sorted(only, key=str)[:12])
if not same_csm:
    only = set(d_csm_c) ^ set(d_csm_live)
    print("   CSM differing keys", len(only), sorted(only, key=str)[:12])
# plan cells survive
ri = {key(r): r for r in rb_pl_c}
bad = [k for k, c in plan_pl.items() if abs((ri[k]["값"] or 0) - c["new"]) > 1e-6]
print("PL plan cells equal to their rebuild output:", len(plan_pl) - len(bad), "/", len(plan_pl), bad[:5])
ri = {key(r): r for r in rb_csm_c}
bad2 = [k for k, c in plan_csm.items() if abs((ri[k]["값"] or 0) - c["new"]) > 1e-6]
print("CSM plan cells equal to their rebuild output:", len(plan_csm) - len(bad2), "/", len(plan_csm), bad2[:5])
# and what the rebuild would have done to them WITHOUT the gold lines (live inputs): proves the gold lines are what protect them
rl = {key(r): r for r in rb_pl_live}
rev = [k for k, c in plan_pl.items() if abs((rl[k]["값"] or 0) - c["new"]) > 1e-6]
print("without the new gold lines the rebuild would revert", len(rev), "of", len(plan_pl), "PL plan cells (expected: all)"); print("   NOT reverted:", [ (k, plan_pl[k]["old"], plan_pl[k]["new"], rl[k]["값"]) for k in plan_pl if k not in rev])
rlc = {key(r): r for r in rb_csm_live}
rev2 = [k for k, c in plan_csm.items() if abs((rlc[k]["값"] or 0) - c["new"]) > 1e-6]
print("without the new gold lines the rebuild would revert", len(rev2), "of", len(plan_csm), "CSM plan cells (expected: all)")
shutil.rmtree(t1, ignore_errors=True)
shutil.rmtree(t2, ignore_errors=True)
