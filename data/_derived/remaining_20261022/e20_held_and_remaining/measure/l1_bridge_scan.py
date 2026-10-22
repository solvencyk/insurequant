"""l1: for every d_census bucket (104) compare the master LOB bridge with the FS-API 'same' (original) and 'prior' (latest comparative)
vectors, and test whether the master legs follow the income-statement insurance lines (_is_rev/_is_cost/_is_rerev/_is_recost).
READ-ONLY -> l1_bridge_scan.json/.txt"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F  # noqa: E402  (chdir to repo root, imports fetch_dart_fs)
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
pl, names, inames = M.load_pl()
d6 = M.jload(M.D_CENSUS / "d6_rows.json")
disp = M.jload(M.D_CENSUS / "d9_disposition.json")
rows = []
txt = []


def isl(t):
    """income-statement insurance legs (rev - |cost|) + (rerev - |recost|) from a Tier-1 dict, or None"""
    if not t:
        return None, None, None
    r, c, rr, rc = t.get("_is_rev"), t.get("_is_cost"), t.get("_is_rerev"), t.get("_is_recost")
    a = None if r is None or c is None else r - abs(c)
    b = None if rr is None or rc is None else rr - abs(rc)
    tot = None if a is None else a + (b or 0.0)
    return a, b, tot


for b in d6:
    code, q = b["code"], b["q"]
    m = pl.get((code, q), {})
    life = (m.get(13) == 0.0 and m.get(14) == 0.0) and True
    t_same, dsame = F.same(code, q)
    t_prior, dprior = F.prior(code, q)
    ms = {k: m.get(k) for k in (1, 2, 3, 8, 13, 14, 15, 16)}
    legs_master = (ms[2] or 0.0) + (ms[13] or 0.0) + (ms[14] or 0.0)
    res_master = None if ms[1] is None else legs_master + (ms[15] or 0.0) - (ms[16] or 0.0) - ms[1]
    rec = {"code": code, "name": b["name"], "q": q, "scope": b["scope"], "disp": (disp.get(f"{code}|{q}") or {}).get("disposition"),
           "master": ms, "res_master": res_master, "div_same": dsame, "div_prior": dprior}
    for tag, t in (("same", t_same), ("prior", t_prior)):
        if t:
            a, bb, tot = isl(t)
            rec[tag] = {"1": t.get(1), "15": t.get(15), "16": t.get(16), "IS3": a, "IS8": bb, "IStot": tot}
            if t.get(1) is not None:
                rec[tag]["target_legs"] = t[1] - (t.get(15) or 0.0) + abs(t.get(16) or 0.0)
                rec[tag]["res_IS"] = None if tot is None else tot - rec[tag]["target_legs"]
        else:
            rec[tag] = None
    # does the master follow the IS lines of the ORIGINAL filing?
    if rec["same"] and rec["same"]["IStot"] is not None and ms[2] is not None:
        rec["master_item2_minus_IS_orig"] = ms[2] - rec["same"]["IStot"]
        rec["master_item3_minus_IS3_orig"] = None if (ms[3] is None or rec["same"]["IS3"] is None) else ms[3] - rec["same"]["IS3"]
    rows.append(rec)
    def f(x):
        return "None" if x is None else f"{x:,.1f}"
    s = rec["same"] or {}
    p = rec["prior"] or {}
    txt.append(f"{code} {b['name'][:8]:<8} {q} {rec['disp'] or '':<14} master[1={f(ms[1])} 2={f(ms[2])} 13={f(ms[13])} 14={f(ms[14])} 15={f(ms[15])} 16={f(ms[16])}] resM={f(res_master)} | "
               f"orig[1={f(s.get('1'))} IStot={f(s.get('IStot'))} resIS={f(s.get('res_IS'))}] | later[1={f(p.get('1'))} 16={f(p.get('16'))} IStot={f(p.get('IStot'))} resIS={f(p.get('res_IS'))} target={f(p.get('target_legs'))}] "
               f"| m2-ISorig={f(rec.get('master_item2_minus_IS_orig'))}")
M.MEASURE.joinpath("l1_bridge_scan.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("l1_bridge_scan.txt").write_text("\n".join(txt), encoding="utf-8")
print(len(rows))
