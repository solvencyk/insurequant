# -*- coding: utf-8 -*-
"""KR0099 evidence (read-only): the 61 PL + 15 CSM candidate cells of the e20 measure phase (scenario N2_KBlife_B) vs git HEAD master (old) vs the loaded plan (60 PL + 15 CSM).  Writes candidate_vs_plan.txt"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
MEAS = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"
sys.stdout.reconfigure(encoding="utf-8")
cand = json.loads((MEAS / "cands_N2_KBlife_B.json").read_text(encoding="utf-8"))
plan = json.loads((HERE / "e23_plan_kblife.json").read_text(encoding="utf-8"))


def head(rel):
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


HM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in head("PL_breakdown.json")}
CM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in head("CSM_waterfall.json")}
pl_plan = {(c["code"], c["item"], c["quarter"]): c["new"] for b in plan["buckets"] for c in b["cells"]}
dropped = {(b["code"], d["item"], b["quarter"]): d for b in plan["buckets"] for d in b["dropped"]}
cs_plan = {(c["code"], c["item"], c["quarter"]): c["new"] for cb in plan["csm_buckets"] for c in cb["cells"]}
out = []
n_same = n_diff = n_drop = n_oldbad = 0
out.append("PL candidates (e20 N2_KBlife_B): old vs HEAD master, new vs loaded value")
for c in cand["pl_cells"]:
    k = (c["code"], c["item"], c["q"])
    ho = HM.get(k)
    old_ok = (ho is None and c["old"] is None) or (ho is not None and c["old"] is not None and abs(ho - c["old"]) < 5e-7)
    if not old_ok:
        n_oldbad += 1
    if k in pl_plan:
        d = pl_plan[k] - c["new"]
        if abs(d) < 5e-7:
            n_same += 1
            tag = "same"
        else:
            n_diff += 1
            tag = f"DIFFERENT by {d:+g}"
        out.append(f"  {k[2]} i{k[1]:>2}: candidate old {c['old']} / HEAD {ho} {'ok' if old_ok else 'OLD MISMATCH'} | candidate new {c['new']} -> loaded {pl_plan[k]} ({tag})")
    else:
        n_drop += 1
        d = dropped.get(k)
        out.append(f"  {k[2]} i{k[1]:>2}: candidate old {c['old']} / HEAD {ho} {'ok' if old_ok else 'OLD MISMATCH'} | candidate new {c['new']} -> NOT LOADED ({d['cls'] if d else '?'}: {d['reason'] if d else ''})")
extra = sorted(k for k in pl_plan if k not in {(c["code"], c["item"], c["q"]) for c in cand["pl_cells"]})
out.append(f"PL: candidates {len(cand['pl_cells'])}: loaded identical {n_same}, loaded with a different value {n_diff}, not loaded {n_drop}, candidate old != HEAD {n_oldbad}; loaded cells that are not candidates: {extra}")
out.append("")
out.append("CSM candidates (e20 N2_KBlife_B)")
n_same = n_diff = n_oldbad = 0
for c in cand["csm_cells"]:
    k = (c["code"], c["item"], c["q"])
    ho = CM.get(k)
    old_ok = ho is not None and abs(ho - c["old"]) < 1e-9
    n_oldbad += 0 if old_ok else 1
    if k in cs_plan and abs(cs_plan[k] - c["new"]) < 1e-9:
        n_same += 1
    else:
        n_diff += 1
    out.append(f"  {k[2]} i{k[1]}: candidate old {c['old']} / HEAD {ho} {'ok' if old_ok else 'OLD MISMATCH'} | candidate new {c['new']} -> loaded {cs_plan.get(k)}")
out.append(f"CSM: candidates {len(cand['csm_cells'])}: loaded identical {n_same}, different/not loaded {n_diff}, candidate old != HEAD {n_oldbad}; loaded cells that are not candidates: {sorted(k for k in cs_plan if k not in {(c['code'], c['item'], c['q']) for c in cand['csm_cells']})}")
(HERE / "candidate_vs_plan.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out[-1:]))
print(out[-len(cand["csm_cells"]) - 2 - 1] if False else "")
