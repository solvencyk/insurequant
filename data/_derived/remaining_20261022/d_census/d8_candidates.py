# -*- coding: utf-8 -*-
"""d8: build CANDIDATE masters in memory and write them to the SCRATCHPAD (never into the repo).  Read-only for the repo.
Usage: d8_candidates.py <name> <selector>
  <selector> = 'pl_closing'  : PL Tier-1 latest vector for every bucket the census calls 'closing' (A51 + ADDL siblings/OCI-only that close the same way)
               'csm_a51'     : CSM latest vector (2026-10-12 dry-run, trusted) for the A51 buckets whose CSM differs, WITHOUT the PL4 companion
               'csm_chain'   : same + the ADDL sibling buckets of the same companies (complete FY chain), still WITHOUT the PL4 companion
Writes <scratch>/<name>_PL_breakdown.json or <name>_CSM_waterfall.json and prints the cell list."""
import json, sys, os
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/d_census")
SCR.mkdir(parents=True, exist_ok=True)
name, sel = sys.argv[1], sys.argv[2]
rows6 = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))
disp = json.loads((OUT / "d9_disposition.json").read_text(encoding="utf-8")) if (OUT / "d9_disposition.json").exists() else {}

def qkey(q): return (int(q[:4]), int(q[5]))
def prev_q(q): return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
def flow_dangi(ytd, q):
    cur = ytd.get(q)
    if cur is None: return None
    p = prev_q(q)
    if p is None: return cur
    prev = ytd.get(p)
    return None if prev is None else round(cur - prev, 6)

if sel in ("pl_closing", "pl_bridgebreak"):
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    idx = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in pl}
    changed = []
    for b in rows6:
        d = disp.get(f"{b['code']}|{b['q']}")
        if sel == "pl_closing" and (not d or not d.get("pl_adoptable")): continue
        if sel == "pl_bridgebreak" and not (b["kind"] == "RESTATEMENT" and b["bridge_note"].startswith("BREAKS")): continue
        its = {int(i): v for i, v in b["its"].items()}
        new = {}
        for i in b["real"]:
            if its[i]["prior"] is not None: new[i] = its[i]["prior"]
        g = lambda i: new.get(i, its.get(i, {}).get("master") if i in its else None)
        if 17 in new or 19 in new:
            if g(17) is not None and g(19) is not None: new[18] = round(g(17) - g(19), 6)
        if 22 in new or 20 in new:
            if g(22) is not None and g(20) is not None: new[21] = round(g(22) - g(20), 6)
        if 22 in new or 24 in new:
            if g(22) is not None and g(24) is not None: new[23] = round(g(22) - g(24), 6)
        for i, v in sorted(new.items()):
            r = idx.get((b["code"], str(i), b["q"]))
            if r is None: continue
            if r.get("값") is None or abs(r["값"] - v) > 1e-9:
                changed.append((b["code"], b["q"], i, r.get("값"), v))
                r["값"] = v
    # recompute 값_당분기 for every touched (code,item) series
    touched = {(c, str(i)) for c, q, i, a, b2 in changed}
    ytd = defaultdict(dict)
    for r in pl:
        k = (r["원보험사코드"], str(r["항목번호"]))
        if k in touched: ytd[k][r["공시분기"]] = r["값"]
    nd = 0
    for r in pl:
        k = (r["원보험사코드"], str(r["항목번호"]))
        if k in touched:
            v = flow_dangi(ytd[k], r["공시분기"]) if r["값"] is not None else None
            if v != r.get("값_당분기"):
                nd += 1; r["값_당분기"] = v
    (SCR / f"{name}_PL_breakdown.json").write_text(json.dumps(pl, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / f"{name}_cells.json").write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    print(name, "PL cells changed:", len(changed), "single-quarter cells recomputed:", nd, "buckets:", len({(c, q) for c, q, *_ in changed}))
else:
    cs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    idx = {(r["원보험사코드"], int(r["항목번호"]), r["공시분기"]): r for r in cs}
    changed = []
    for b in rows6:
        if b["csm_state"] != "DIFF" or not b["csm_latest"]: continue
        if sel == "csm_a51" and b["scope"] != "A51": continue
        if sel in ("csm_chain", "csm_chain_full") and b["scope"] == "ADDL_OCI_ONLY": continue      # its own FY-boundary does not close in the filings themselves
        d = disp.get(f"{b['code']}|{b['q']}") or {}
        if d.get("csm_gold_conflict") and sel != "csm_chain_full": continue
        for i, v in enumerate(b["csm_latest"], start=1):
            r = idx.get((b["code"], i, b["q"]))
            if r is None or v is None: continue
            if r.get("값") is None or abs(r["값"] - v) > 1e-9:
                changed.append((b["code"], b["q"], i, r.get("값"), v)); r["값"] = v
    touched = {(c, i) for c, q, i, a, b2 in changed} | {(c, i) for c, q, i, a, b2 in changed for i in (1, 2, 3, 4, 5, 6)}
    ytd = defaultdict(dict)
    for r in cs:
        k = (r["원보험사코드"], int(r["항목번호"]))
        if k in touched: ytd[k][r["공시분기"]] = r["값"]
    nd = 0
    for r in cs:
        k = (r["원보험사코드"], int(r["항목번호"]))
        if k not in touched: continue
        it = int(r["항목번호"]); q = r["공시분기"]; v = r["값"]
        if v is None: nv = None
        elif it == 6: nv = v
        elif it == 1:
            p = prev_q(q); nv = v if p is None else ytd[(k[0], 6)].get(p)
        else: nv = flow_dangi(ytd[k], q)
        if nv is not None: nv = round(nv, 6)
        if nv != r.get("값_당분기"):
            nd += 1; r["값_당분기"] = nv
    (SCR / f"{name}_CSM_waterfall.json").write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / f"{name}_cells.json").write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    print(name, "CSM cells changed:", len(changed), "single-quarter cells recomputed:", nd, "buckets:", len({(c, q) for c, q, *_ in changed}))
