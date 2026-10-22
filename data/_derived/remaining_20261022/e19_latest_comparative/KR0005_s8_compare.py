"""Read-only. Compare per bucket: master 값 (old) / original-filing XML current column / later-filing XML prior column / census value / FS-API second source."""
import sys, os, json, io, copy
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import fetch_dart_fs as fdf
EVD = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
X = json.loads((EVD / "KR0005_s7_xml.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {}
for r in pl:
    if r["원보험사코드"] == "KR0005":
        M[(r["공시분기"], r["항목번호"])] = (r.get("값"), r.get("값_당분기"))
cand = {(c[1], c[2]): (c[3], c[4]) for c in json.loads((ROOT / "data/_derived/remaining_20261022/d_census/cand_pl_cells.json").read_text(encoding="utf-8")) if c[0] == "KR0005"}
CC = "00103176"
def load(year, reprt):
    p = ROOT / f"data/dart/_fs_api_cache/{CC}_{year}_{reprt}_OFS.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
def api(q, which):
    """which: 'ytd' = prior-column cumulative, 'm3' = prior-column 3 months, from the NEXT-year filing's cache"""
    reprt = fdf.REPRT[q[5:]]; annual = q[5:] == "4Q"; nxt = str(int(q[:4]) + 1)
    d = copy.deepcopy(load(nxt, reprt))
    for a in d.get("list", []) or []:
        if annual:
            a["thstrm_amount"], a["thstrm_add_amount"] = a.get("frmtrm_amount"), ""
        elif which == "ytd":
            a["thstrm_amount"] = a.get("frmtrm_q_amount"); a["thstrm_add_amount"] = a.get("frmtrm_add_amount")
        else:
            a["thstrm_amount"] = a.get("frmtrm_q_amount"); a["thstrm_add_amount"] = a.get("frmtrm_q_amount")
    return fdf._parse(d, annual)
def api_same(q):
    d = load(q[:4], fdf.REPRT[q[5:]])
    return fdf._parse(d, q[5:] == "4Q")
ITEMS = [1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
out, res = [], {}
for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"):
    xl, xo = X[f"later|{q}"]["items"], X[f"orig|{q}"]["items"]
    ap, aps = api(q, "ytd"), api_same(q)
    out.append(f"== {q}   later {X['later|'+q]['file']} (col {X['later|'+q]['ytd_col']})   orig {X['orig|'+q]['file']} (col {X['orig|'+q]['ytd_col']})")
    out.append(f"   {'it':>3} {'master':>12} {'origXML':>12} {'laterXML':>12} {'census':>12} {'APIprior':>12} {'APIsame':>12}   flags")
    res[q] = {}
    for k in ITEMS:
        mv = M.get((q, k), (None, None))[0]
        o = xo.get(str(k)) if k != 15 else 0.0
        l = xl.get(str(k)) if k != 15 else 0.0
        cv = cand.get((q, k), (None, None))[1]
        a = (ap or {}).get(k); a_s = (aps or {}).get(k)
        fl = []
        if mv is not None and o is not None and abs(mv - o) > 0.5: fl.append("master!=origXML")
        if mv is None and o is not None: fl.append("master-null,XML-has")
        if l is not None and mv is not None and abs(l - mv) > 0.5: fl.append("DIFF")
        if l is None and mv is not None: fl.append("XML-none,master-has")
        if l is not None and mv is None: fl.append("master-null,laterXML-has")
        if l is not None and a is not None and abs(l - a) > 0.5: fl.append("laterXML!=APIprior")
        if cv is not None and l is not None and abs(cv - l) > 0.5: fl.append("laterXML!=census")
        if (cv is None) != (not ("DIFF" in fl)) and k != 15: fl.append("census-membership?")
        f = lambda v: "None" if v is None else f"{v:,.1f}"
        out.append(f"   {k:>3} {f(mv):>12} {f(o):>12} {f(l):>12} {f(cv):>12} {f(a):>12} {f(a_s):>12}   {','.join(fl)}")
        res[q][k] = {"master": mv, "orig_xml": o, "later_xml": l, "census_new": cv, "api_prior": a, "api_same": a_s, "flags": fl}
(EVD / "KR0005_s8_compare.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
(EVD / "KR0005_s8_compare.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
