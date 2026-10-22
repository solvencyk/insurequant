# -*- coding: utf-8 -*-
"""build_cands: candidate PL + CSM cell lists for a scenario (list of buckets) and the candidate masters (scratchpad only).
usage: build_cands.py <scenario_name> <spec csv>     spec = CODE:Q[:provider[:csm]]   provider in life_is|kb|lotte|meritz|keep   ; ':csm' adopts the CSM latest vector
Outputs (measure dir): cands_<name>.json / .txt ; candidate masters (scratchpad cand/<name>_PL_breakdown.json, <name>_CSM_waterfall.json).  READ-ONLY for the repo."""
import copy
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import cand as K  # noqa: E402  (imports build_pl_breakdown.assemble, chdir)
import csmvec as CV  # noqa: E402
import fsapi as F  # noqa: E402
import lotte_lib as L  # noqa: E402
import mlib as M  # noqa: E402
import plan_lib as PL  # noqa: E402
import prod as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/cand")
SCR.mkdir(parents=True, exist_ok=True)

name = sys.argv[1]
specs = []
for s in sys.argv[2].split(","):
    p = s.split(":")
    specs.append({"code": p[0], "q": p[1], "prov": p[2] if len(p) > 2 and p[2] else "life_is", "csm": (len(p) > 3 and p[3] == "csm")})

pl, names, inames = M.load_pl()
gold = M.jload(M.SNAP / "user_pl_cells.json")
gold_pl = {(c["원보험사코드"], c["공시분기"], c["항목번호"]): c for c in gold["set"]}
gold_c = M.jload(M.SNAP / "user_csm_cells.json")
gold_csm = {(c["원보험사코드"], c["공시분기"], c["항목번호"]): c for c in gold_c["set"]}
csm_m = M.load_csm()


def kb_t2(code, q, t1p):
    tabs = P.tables_for(code, M.later_fy(q))
    t2 = P.C.extract_tier2_kb(tabs, item1=t1p.get(1))
    del tabs
    return t2


def lotte_t2(code, q):
    tabs = P.tables_for(code, M.later_fy(q))
    nm, out, lines = L.run(tabs, True)
    del tabs
    return out


def meritz_t2(code, q):
    import p_meritz_lib as ML
    tabs = P.tables_for(code, M.later_fy(q))
    out, ln = ML.structured(tabs, 1)
    del tabs
    return out


pl_cells, csm_cells, log = [], [], []
bucket_info = {}
for sp in specs:
    code, q, prov = sp["code"], sp["q"], sp["prov"]
    m = pl.get((code, q), {})
    t1p, _ = (F.same(code, q) if prov == "same" else F.prior(code, q))
    if t1p is None:
        log.append(f"{code} {q}: no FS-API prior -> skipped")
        continue
    t2 = {k: m[k] for k in (4, 5, 6, 9, 10, 11) if m.get(k) is not None}
    is_life = (m.get(13) == 0.0 and m.get(14) == 0.0)
    if prov == "kb":
        t2 = kb_t2(code, q, t1p)
        is_life = False
    elif prov == "lotte":
        t2 = lotte_t2(code, q)
        is_life = False
    elif prov == "meritz":
        t2 = meritz_t2(code, q)
        is_life = False
    elif prov == "keep_nonlife":
        is_life = False
        t2 = {k: m[k] for k in (4, 5, 6, 9, 10, 11) if m.get(k) is not None}
        for k in ("_jang_net",):
            pass
        # legs unchanged: feed the master legs back (item 2 via _jang_net, 13, 14)
        t2["_jang_net"] = m.get(2)
        t2[13], t2[14] = m.get(13), m.get(14)
        if os.environ.get("IR_LEGS"):   # decision-table variant: LOB legs 2/13/14 of the restated quarter from the IR factsheet prior-year columns (hd_ir_legs.json)
            _ov = json.loads(Path(os.environ["IR_LEGS"]).read_text(encoding="utf-8")).get(f"{code}|{q}")
            if _ov:
                t2["_jang_net"], t2[13], t2[14] = _ov["2"], _ov["13"], _ov["14"]
    csm_p = CV.prior(code, q) if sp["csm"] else None
    if csm_p is not None and prov in ("life_is", "keep_nonlife"):
        # PL4 follows the restated CSM amortisation (verified equal to the note prior column on KB라이프/KDB/한화/메리츠/롯데/미래에셋; see p_*.txt)
        t2[4] = float(abs(round(csm_p[4] * 100)))
    zf = None if m.get(6) is not None else frozenset()
    v = P.__dict__  # noqa
    from build_pl_breakdown import assemble  # noqa: E402
    vv = assemble(dict(t1p), dict(t2), is_life, zero_fill_ok=zf)
    if vv.get("_reconciled") is False:
        log.append(f"{code} {q}: WARNING assemble RC gate suppressed Tier-2 (legs do not reconcile)")
    # OCI name-fallback repair: when the prior column leaves an OCI leaf (26..30) untagged the FS-API catch-all (32) absorbs it; the XML statement prints the leaf by label
    # (verified KR0099 2023.3Q: 재보험계약자산부채순금융손익 427 @FY2024_Q3 L25661).  Keep the master value of that leaf and take it out of item 32 when that restores 25 = sum.
    for _it in (26, 27, 28, 29, 30):
        if vv.get(_it) is None and m.get(_it) is not None and vv.get(32) is not None and vv.get(25) is not None:
            _c32 = vv[32] - m[_it]
            _s = sum((vv.get(k) if vv.get(k) is not None else m.get(k) or 0.0) for k in (26, 27, 28, 29, 30)) + m[_it] * 0 + _c32
            if abs(_s - vv[25]) < 0.5:
                vv[_it], vv[32] = m[_it], _c32
                log.append(f"{code} {q}: OCI item {_it} untagged in the prior column -> label fallback keeps {m[_it]} and item 32 {vv[32] + m[_it]} -> {_c32}")
    # sign preservation for 기타사업비용 (item 16): master convention wins when the magnitudes agree within 50%
    old16, new16 = m.get(16), vv.get(16)
    if old16 is not None and new16 is not None and old16 * new16 < 0 and abs(abs(old16) - abs(new16)) < 0.5 * max(abs(old16), 1.0):
        vv[16] = -new16
    ch = PL.changed(code, q, vv, pl)
    clo = PL.closure(vv, nonlife=not is_life)
    for it, old, new in ch:
        g = gold_pl.get((code, q, it))
        pl_cells.append({"code": code, "q": q, "item": it, "old": old, "new": new, "gold": (g.get("값") if g else None), "gold_was": (g.get("was") if g else None), "gold_note": ((g.get("note") or "")[:80] if g else None)})
    csm_n = 0
    if csm_p is not None:
        cur = csm_m.get((code, q), {})
        for i in range(1, 7):
            old = cur.get(i)
            new = csm_p[i - 1]
            if new is None:
                continue
            if old is None or abs(old - new) > 0.05:
                g = gold_csm.get((code, q, i))
                csm_cells.append({"code": code, "q": q, "item": i, "old": old, "new": new, "gold": (g.get("값") if g else None), "gold_was": (g.get("was") if g else None)})
                csm_n += 1
    log.append(f"{code} {q} [{prov}{'+csm' if sp['csm'] else ''}] PL cells={len(ch)} CSM cells={csm_n} closure={ {k: (round(x, 3) if x is not None else None) for k, x in clo.items()} }")
    bucket_info[f"{code}|{q}"] = {"prov": prov, "csm": sp["csm"], "n_pl": len(ch), "n_csm": csm_n, "closure": {k: (round(x, 4) if x is not None else None) for k, x in clo.items()}, "screen_eok": PL.screen_eok(code, q, vv, pl), "reconciled": vv.get("_reconciled")}

# ---- optional restriction of the PL cells (decision-table variants, e.g. 현대 CSM + PL4 only): env PL_ONLY_ITEMS="4" ----
import os  # noqa: E402
if os.environ.get("PL_ONLY_ITEMS"):
    _keep = {int(x) for x in os.environ["PL_ONLY_ITEMS"].split(",")}
    _n0 = len(pl_cells)
    pl_cells = [c for c in pl_cells if c["item"] in _keep]
    log.append(f"PL_ONLY_ITEMS={sorted(_keep)}: PL cells {_n0} -> {len(pl_cells)}")
# ---- candidate masters (scratchpad) ----
plm = M.jload(M.SNAP / "PL_breakdown.json")
idx = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in plm}


def prev_q(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


def flow(ytd, q):
    cur = ytd.get(q)
    if cur is None:
        return None
    p = prev_q(q)
    if p is None:
        return cur
    prev = ytd.get(p)
    return None if prev is None else round(cur - prev, 6)


touched = set()
for c in pl_cells:
    r = idx.get((c["code"], str(c["item"]), c["q"]))
    if r is None:
        log.append(f"PL row absent {c['code']} {c['q']} item {c['item']} (skipped in candidate master)")
        continue
    r["값"] = round(c["new"], 6)
    touched.add((c["code"], str(c["item"])))
ytd = defaultdict(dict)
for r in plm:
    k = (r["원보험사코드"], str(r["항목번호"]))
    if k in touched:
        ytd[k][r["공시분기"]] = r["값"]
nd = 0
for r in plm:
    k = (r["원보험사코드"], str(r["항목번호"]))
    if k in touched:
        nv = flow(ytd[k], r["공시분기"]) if r["값"] is not None else None
        if nv != r.get("값_당분기"):
            r["값_당분기"] = nv
            nd += 1
(SCR / f"{name}_PL_breakdown.json").write_text(json.dumps(plm, ensure_ascii=False, indent=2), encoding="utf-8")

csm = M.jload(M.SNAP / "CSM_waterfall.json")
cidx = {(r["원보험사코드"], int(r["항목번호"]), r["공시분기"]): r for r in csm}
ctouched = set()
for c in csm_cells:
    r = cidx.get((c["code"], c["item"], c["q"]))
    if r is None:
        continue
    r["값"] = c["new"]
    ctouched.add((c["code"], c["item"]))
    for i in (1, 2, 3, 4, 5, 6):
        ctouched.add((c["code"], i))
cy = defaultdict(dict)
for r in csm:
    k = (r["원보험사코드"], int(r["항목번호"]))
    if k in ctouched:
        cy[k][r["공시분기"]] = r["값"]
cnd = 0
for r in csm:
    k = (r["원보험사코드"], int(r["항목번호"]))
    if k not in ctouched:
        continue
    it, q, v = int(r["항목번호"]), r["공시분기"], r["값"]
    if v is None:
        nv = None
    elif it == 6:
        nv = v
    elif it == 1:
        p = prev_q(q)
        nv = v if p is None else cy[(k[0], 6)].get(p)
    else:
        nv = flow(cy[k], q)
    if nv is not None:
        nv = round(nv, 6)
    if nv != r.get("값_당분기"):
        r["값_당분기"] = nv
        cnd += 1
(SCR / f"{name}_CSM_waterfall.json").write_text(json.dumps(csm, ensure_ascii=False, indent=2), encoding="utf-8")
log.append(f"candidate masters written: PL cells {len(pl_cells)} (+{nd} single-quarter recomputed), CSM cells {len(csm_cells)} (+{cnd} single-quarter recomputed) -> scratchpad cand/{name}_*")
out = {"name": name, "specs": specs, "pl_cells": pl_cells, "csm_cells": csm_cells, "buckets": bucket_info, "log": log}
M.MEASURE.joinpath(f"cands_{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath(f"cands_{name}.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))

# ---- candidate provenance: DISCLOSURE-lineage income_statement blocks of adopted buckets become OWNER_GOLD (as the e19 apply does via the sandbox emit_pl_provenance) ----
prov = M.jload(M.SNAP / "PL_breakdown_provenance.json")
byb = defaultdict(list)
for c in pl_cells:
    byb[(c["code"], c["q"])].append(c["item"])
GOLD_T1 = {1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31}
nprov = 0
CN_ITEMS = {4, 5, 6, 9, 10, 11, 13, 14}
pubcnt = defaultdict(lambda: [0, 0])  # (code, q, block) -> [published, schema] in the candidate master
for r in plm:
    try:
        it_ = int(r["항목번호"])
    except (TypeError, ValueError):
        continue
    k3 = (r["원보험사코드"], r["공시분기"], "contract_notes" if it_ in CN_ITEMS else "income_statement")
    pubcnt[k3][1] += 1
    if r["값"] is not None:
        pubcnt[k3][0] += 1
for cell in prov["cells"]:
    k = (cell["company_code"], cell["quarter"])
    blk = cell["item_block"]
    if k not in byb:
        continue
    disc = blk == "income_statement" and cell.get("source_id") == "DISCLOSURE"
    # blocks the master had no source for (0 published values) that the adoption now fills (e.g. 롯데 2023.1Q contract_notes) are re-emitted too
    unres = (not cell.get("source_file")) and any((("contract_notes" if i in CN_ITEMS else "income_statement") == blk) for i in byb[k])
    if disc:
        items = set(byb[k])
        gi = sorted(i for i in items if i in GOLD_T1)
        ri = sorted(i for i in items if i in (2, 3, 7, 8, 12))
        fi = sorted(i for i in items if i in (15, 32))
        sfs = [{"file": "data/_gold/user_pl_cells.json", "how": "owner_gold_overlay", "items": gi}]
        if ri:
            sfs.append({"file": f"data/dart/{M.fy_of(k[1])}/raw/{cell['company_code']}", "how": "raw_filing_derived", "items": ri})
        if fi:
            sfs.append({"file": f"data/dart/_fs_api_cache/{F.corp(cell['company_code'])}_{int(k[1][:4]) + 1}_{F.fdf.REPRT[k[1][5:]]}_OFS.json", "how": "fs_api_tier1", "items": fi})
        cell.update({"source_id": "OWNER_GOLD", "source_file": "data/_gold/user_pl_cells.json", "source_files": sfs, "resolution": "owner_gold_overlay",
                     "published_items": 24, "schema_items": 24, "owner_override": True})
        nprov += 1
    elif unres:
        its = sorted(i for i in byb[k] if (("contract_notes" if i in CN_ITEMS else "income_statement") == blk))
        pc = pubcnt[(k[0], k[1], blk)]
        cell.pop("unresolved_reason", None)
        cell.update({"source_id": "OWNER_GOLD", "source_file": "data/_gold/user_pl_cells.json",
                     "source_files": [{"file": "data/_gold/user_pl_cells.json", "how": "owner_gold_overlay", "items": its}], "resolution": "owner_gold_overlay",
                     "published_items": pc[0], "schema_items": pc[1], "owner_override": True})
        nprov += 1
(SCR / f"{name}_PL_breakdown_provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"candidate provenance: {nprov} DISCLOSURE blocks -> OWNER_GOLD (scratchpad cand/{name}_PL_breakdown_provenance.json)")
