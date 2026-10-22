# -*- coding: utf-8 -*-
"""d12: how many master (company, quarter) cells have item 19 (and derived 18) computed with a printed-negative expense sign?  Read-only.
Rule: fetch_dart_fs._parse computes 19 = fi - fe + ri - re assuming fe/re are printed POSITIVE.  If the filing prints them negative, 19 is wrong."""
import json, sys, os
from pathlib import Path
from collections import defaultdict
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import fetch_dart_fs as F
OUT = ROOT / "data/_derived/remaining_20261022/d_census"
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = defaultdict(dict); NAME = {}
for r in pl:
    if str(r["항목번호"]) in ("19", "17", "18"): M[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = r["값"]
    NAME[r["원보험사코드"]] = r["원수사명"]
cc_of = {}
for mp in (ROOT / "data/dart").glob("FY*_Q*/raw/KR*_*/meta.json"):
    try: cc_of.setdefault(mp.parent.name.split("_")[0], json.loads(mp.read_text(encoding="utf-8")).get("corp_code"))
    except Exception: pass
REPRT = F.REPRT
bad = []; n = 0
for (code, q), m in sorted(M.items()):
    cc = cc_of.get(code)
    if not cc or "19" not in m or m["19"] is None: continue
    for div in ("OFS", "CFS"):
        p = ROOT / "data/dart/_fs_api_cache" / f"{cc}_{q[:4]}_{REPRT[q[5:]]}_{div}.json"
        if p.exists(): break
    else: continue
    d = json.loads(p.read_text(encoding="utf-8")); annual = q[5:] == "4Q"
    vals = {}
    for a in d.get("list", []):
        if a.get("sj_div") not in ("IS", "CIS"): continue
        aid = a.get("account_id") or ""
        raw = a.get("thstrm_amount") if annual else (a.get("thstrm_add_amount") or a.get("thstrm_amount"))
        v = F._to_num(raw)
        if v is not None and aid in F.FIN.values() and aid not in vals: vals[aid] = v / 1e6
    fe, re_ = vals.get(F.FIN["ins_exp"]), vals.get(F.FIN["re_exp"])
    fi, ri = vals.get(F.FIN["ins_inc"]), vals.get(F.FIN["re_inc"])
    if fe is None and re_ is None: continue
    n += 1
    neg = (fe is not None and fe < 0) or (re_ is not None and re_ < 0)
    # master value as the parser computes it vs the sign-normalised value
    calc = (fi or 0) - (fe or 0) + (ri or 0) - (re_ or 0)
    norm = (fi or 0) - abs(fe or 0) + (ri or 0) - abs(re_ or 0)
    if neg and abs(m["19"] - calc) < 1.0 and abs(calc - norm) > 1.0:
        bad.append((NAME[code], q, round(m["19"] / 100, 1), round(norm / 100, 1)))
print("cells with an expense line:", n, " master item 19 computed on a printed-negative expense line:", len(bad))
for b in bad: print("  ", b)
(OUT / "d12_sign19_scan.txt").write_text("cells with an expense line: %d  master item 19 computed from a printed-negative expense line: %d\n" % (n, len(bad)) + "\n".join(f"{a} {b} master={c} sign-normalised={d} (eok)" for a, b, c, d in bad) + "\n", encoding="utf-8")
