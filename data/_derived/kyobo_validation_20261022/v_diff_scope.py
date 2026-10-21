# -*- coding: utf-8 -*-
"""HEAD~1 vs HEAD: any cell outside KR0073 that moved? masters + provenance + gold + ledgers. Read-only (git show)."""
import json, subprocess
from collections import Counter, defaultdict
def show(rev, f):
    return json.loads(subprocess.run(["git", "show", f"{rev}:{f}"], capture_output=True, check=True).stdout.decode("utf-8"))
out = []
def P(*a): print(*a); out.append(" ".join(str(x) for x in a))

for f, keyf in [("CSM_waterfall.json", None), ("PL_breakdown.json", None)]:
    a, b = show("3e53aef8~1", f), show("3e53aef8", f)
    ka = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in a}
    kb = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in b}
    P(f"== {f}: rows HEAD~1={len(a)} HEAD={len(b)} keys added={len(set(kb)-set(ka))} removed={len(set(ka)-set(kb))} dup-key rows HEAD~1={len(a)-len(ka)} HEAD={len(b)-len(kb)}")
    chg = Counter(); cells = set(); fields = Counter(); other_fields = set()
    for k in ka.keys() & kb.keys():
        ra, rb = ka[k], kb[k]
        for fld in set(ra) | set(rb):
            if ra.get(fld) != rb.get(fld):
                chg[k[0]] += 1; cells.add(k); fields[fld] += 1
    P("   changed fields by company code:", dict(chg), " distinct cells:", len(cells), " by field:", dict(fields))
    P("   cells by quarter (KR0073):", dict(sorted(Counter(k[1] for k in cells if k[0] == "KR0073").items())))
    # added keys detail
    for k in sorted(set(kb) - set(ka))[:10]: P("   ADDED", k)
    for k in sorted(set(ka) - set(kb))[:10]: P("   REMOVED", k)
    if f == "PL_breakdown.json":
        newfill = [k for k in cells if ka[k].get("값") is None and kb[k].get("값") is not None]
        P("   first-time fills (값 None->value):", len(newfill), dict(Counter(k[1] for k in newfill)))
        P("   cells with 값 changed:", len([k for k in cells if ka[k].get("값") != kb[k].get("값")]))

# provenance
for f in ["CSM_waterfall_provenance.json", "PL_breakdown_provenance.json"]:
    a, b = show("3e53aef8~1", f), show("3e53aef8", f)
    def flat(d, pre=""):
        if isinstance(d, dict):
            for k, v in d.items(): yield from flat(v, pre + "/" + str(k))
        elif isinstance(d, list):
            for i, v in enumerate(d): yield from flat(v, pre + f"[{i}]")
        else: yield pre, d
    fa, fb = dict(flat(a)), dict(flat(b))
    ch = [k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)]
    P(f"== {f}: changed leaf paths={len(ch)}")
    top = Counter("/".join(p.split("/")[:3]) for p in ch)
    P("   top-level path groups (first 3 comps):", dict(list(top.most_common(25))))
    nonk = [p for p in ch if "KR0073" not in p and "교보" not in p]
    P("   leaf paths NOT mentioning KR0073/교보:", len(nonk), nonk[:15])

# gold / ledgers: entries touching other companies
a, b = show("3e53aef8~1", "data/_gold/user_csm_cells.json"), show("3e53aef8", "data/_gold/user_csm_cells.json")
def key(e): return (e["원보험사코드"], e["항목번호"], e["공시분기"])
da = {key(e): e for e in a["set"]}; db = {key(e): e for e in b["set"]}
chg = [k for k in set(da) | set(db) if da.get(k) != db.get(k)]
P(f"== user_csm_cells.set: HEAD~1={len(a['set'])} HEAD={len(b['set'])} changed/added/removed keys={len(chg)} companies={dict(Counter(k[0] for k in chg))}  other top-level keys equal: {({k:v for k,v in a.items() if k!='set'}=={k:v for k,v in b.items() if k!='set'})}")
a, b = show("3e53aef8~1", "data/_gold/user_pl_cells.json"), show("3e53aef8", "data/_gold/user_pl_cells.json")
da = {key(e): e for e in a["set"]}; db = {key(e): e for e in b["set"]}
chg = [k for k in set(da) | set(db) if da.get(k) != db.get(k)]
P(f"== user_pl_cells.set: HEAD~1={len(a['set'])} HEAD={len(b['set'])} changed keys={len(chg)} companies={dict(Counter(k[0] for k in chg))} removed={len(set(da)-set(db))} other top-level equal: {({k:v for k,v in a.items() if k!='set'}=={k:v for k,v in b.items() if k!='set'})}")
a, b = show("3e53aef8~1", "data/_gold/gold_overlay_ledger.json"), show("3e53aef8", "data/_gold/gold_overlay_ledger.json")
P("== gold_overlay_ledger: top keys", list(b.keys()))
ea, eb = a["entries"], b["entries"]
def ek(e): return json.dumps({k: e[k] for k in e if k in ("axis","overlay","code","item","quarter","원보험사코드","항목번호","공시분기")}, sort_keys=True, ensure_ascii=False)
P("   entries type", type(ea).__name__, len(ea), len(eb))
ia = ea if isinstance(ea, list) else list(ea.values()); ib = eb if isinstance(eb, list) else list(eb.values())
sa = {json.dumps(e, sort_keys=True, ensure_ascii=False) for e in ia}; sb = {json.dumps(e, sort_keys=True, ensure_ascii=False) for e in ib}
rem = [json.loads(x) for x in sa - sb]; add = [json.loads(x) for x in sb - sa]
def co(e): return e.get("code") or e.get("원보험사코드") or e.get("kr") or "?"
P("   removed", len(rem), dict(Counter(co(e) for e in rem)), " added", len(add), dict(Counter(co(e) for e in add)))
P("   meta keys changed:", [k for k in b if k != "entries" and a.get(k) != b.get(k)])
a, b = show("3e53aef8~1", "data/_gold/csm_amort_identity_ledger.json"), show("3e53aef8", "data/_gold/csm_amort_identity_ledger.json")
ea, eb = a["entries"], b["entries"]
P("== csm_amort_identity_ledger: entries", len(ea), "->", len(eb), "removed:", [x for x in (ea if isinstance(ea, list) else ea.keys()) if x not in (eb if isinstance(eb, list) else eb.keys())][:5], "meta changed:", [k for k in b if k != "entries" and a.get(k) != b.get(k)])
open("data/_derived/kyobo_validation_20261022/v_diff_scope.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
