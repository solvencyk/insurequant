# -*- coding: utf-8 -*-
"""d1: read-only. For every PL master (company, quarter) with a DART FS-API cache pair (original filing / next-year filing),
compare Tier-1 items: original-filing column (thstrm) vs later-filing prior column (frmtrm), and what the master holds.
Writes d1_scan.json.  No repo file is written except this evidence dir."""
import sys, json, os
from pathlib import Path
from collections import defaultdict
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import validate_master_tables as V, fetch_dart_fs as fdf
OUT = ROOT / "data/_derived/remaining_20261022/d_census"
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = defaultdict(dict); NAME = {}
for r in pl:
    M[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = (r.get("값"), r.get("값_당분기")); NAME[r["원보험사코드"]] = r["원수사명"]
kr2cc = dict(V._tax22_corp_codes())
# fallback: meta.json in raw dirs
for mp in sorted((ROOT / "data/dart").glob("FY*_Q*/raw/KR*_*/meta.json")):
    code = mp.parent.name.split("_")[0]
    if code not in kr2cc:
        try:
            cc = json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
            if cc: kr2cc[code] = cc
        except Exception: pass
CACHE = ROOT / "data/dart/_fs_api_cache"

def load(cc, year, reprt, div):
    p = CACHE / f"{cc}_{year}_{reprt}_{div}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def parse_same(cc, q):
    reprt = fdf.REPRT[q[5:]]; annual = q[5:] == "4Q"
    for div in ("OFS", "CFS"):
        d = load(cc, q[:4], reprt, div)
        if d is None: continue
        t = fdf._parse(d, annual)
        if t: return t, div
    return None, None

def parse_prior(cc, q):
    reprt = fdf.REPRT[q[5:]]; annual = q[5:] == "4Q"; nxt = str(int(q[:4]) + 1)
    for div in ("OFS", "CFS"):
        d = load(cc, nxt, reprt, div)
        if d is None: continue
        for a in d.get("list", []) or []:
            if annual:
                a["thstrm_amount"], a["thstrm_add_amount"] = a.get("frmtrm_amount"), ""
            else:
                a["thstrm_amount"] = a.get("frmtrm_q_amount"); a["thstrm_add_amount"] = a.get("frmtrm_add_amount")
        t = fdf._parse(d, annual)
        if t: return t, div
    return None, None

res = []
nocc = set()
for (code, q), m in sorted(M.items()):
    cc = kr2cc.get(code)
    if not cc:
        nocc.add(code); continue
    t1, d1 = parse_same(cc, q); t2, d2 = parse_prior(cc, q)
    if not t2: continue
    items = {}
    for k in sorted(k for k in set(t1 or {}) | set(t2) if isinstance(k, int)):
        a, b = (t1 or {}).get(k), t2.get(k)
        mv = (m.get(k) or (None, None))[0]
        items[k] = {"same": a, "prior": b, "master": mv}
    res.append({"code": code, "name": NAME[code], "q": q, "div_same": d1, "div_prior": d2, "items": items})
(OUT / "d1_scan.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("pairs with both caches:", len(res), "companies without corp_code:", sorted(nocc))
