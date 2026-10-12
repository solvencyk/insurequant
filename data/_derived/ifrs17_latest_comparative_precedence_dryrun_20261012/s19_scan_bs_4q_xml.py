"""Read-only census (offline) - IFRS17_BS year-end 자산총계(1)/부채총계(2)/자본총계(3) from the DART audit-report XML (_00760.xml / main body):
master vs the original annual report's 당기 column vs the NEXT annual report's 전기 (comparative) column.

Covers every company with two consecutive annual reports on disk - in particular the unlisted insurers that have no FS-API cache (the FS-API census s18 cannot see them).
Table pick: first table whose first-column labels (whitespace removed) contain 자산총계, 부채총계, 자본총계 and whose header carries a (당) and a (전) period cell.
Unit: the printed amounts are 원 / 천원 / 백만원; the factor to 백만원 is the candidate (1e-6, 1e-3, 1, 1e-9) that puts 자산총계 closest to the master.
Output bs_4q_scan_xml.csv, bs_4q_scan_xml_summary.json
"""
from __future__ import annotations

import csv
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _norm  # noqa: E402
from scripts.build_net_income_breakdown import to_num  # noqa: E402

bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
M, NAMES = {}, {}
for r in bs:
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]
LAB = {"자산총계": 1, "부채총계": 2, "자본총계": 3}


def annual_dirs(kr, y):
    return sorted((ROOT / "data/dart" / f"FY{y}_Q4" / "raw").glob(f"{kr}_*"))


def read_bs(rd):
    """-> (cur{item:val}, prior{item:val}) in the printed unit, or None"""
    xs = sorted(set(list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml"))), key=lambda p: (not p.name.endswith("_00760.xml"), -p.stat().st_size))
    for x in xs:
        if x.name.endswith("_00761.xml"):
            continue
        try:
            for t in _iter_tables_with_context(x):
                labs = {_norm(r[0]).replace(" ", ""): r for r in t.rows if r}
                if not all(k in labs for k in LAB):
                    continue
                hdr = " ".join(c for r in t.header for c in r)
                if "(당)" not in hdr.replace(" ", "") and "당기" not in hdr:
                    continue
                cur, pri = {}, {}
                for k, it in LAB.items():
                    nums = [to_num(c) for c in labs[k][1:] if to_num(c) is not None]
                    if len(nums) >= 2:
                        cur[it], pri[it] = nums[0], nums[1]
                if len(cur) == 3:
                    return cur, pri, x.name
        except Exception:
            continue
    return None


def factor(val, master):
    if master in (None, 0) or val in (None, 0):
        return None
    best = min((1e-9, 1e-6, 1e-3, 1.0), key=lambda f: abs(abs(val * f) / abs(master) - 1))
    return best if abs(abs(val * best) / abs(master) - 1) < 0.25 else None


rows, cnt = [], Counter()
# companies covered by the FS-API census (s18) are skipped: their cache is the structured source and this XML pick can hit a mislabeled attachment
fsapi_krs = set()
for m in glob.glob(str(ROOT / "data/dart/FY*_Q*/raw/KR*/meta.json")):
    try:
        cc = json.loads(Path(m).read_text(encoding="utf-8")).get("corp_code")
    except Exception:
        continue
    if cc and glob.glob(str(ROOT / "data/dart/_fs_api_cache" / f"{cc}_*_11011_*.json")):
        fsapi_krs.add(Path(m).parent.name.split("_")[0])
krs = sorted({Path(p).name.split("_")[0] for p in glob.glob(str(ROOT / "data/dart/FY*_Q4/raw/KR*"))} - fsapi_krs)
print("companies without FS-API annual cache (XML census scope):", len(krs), krs)
for kr in krs:
    for y in (2022, 2023, 2024, 2025):
        d0, d1 = annual_dirs(kr, y), annual_dirs(kr, y + 1)
        if not d0 or not d1:
            continue
        a0, a1 = None, None
        for rd in d0:
            a0 = read_bs(rd)
            if a0:
                break
        for rd in d1:
            a1 = read_bs(rd)
            if a1:
                break
        if not a0 or not a1:
            cnt["UNREADABLE"] += 1
            rows.append({"kr": kr, "name": NAMES.get(kr, ""), "quarter": f"{y}.4Q", "item": "", "cls": "UNREADABLE", "note": f"orig={bool(a0)} later={bool(a1)}"})
            continue
        q = f"{y}.4Q"
        # period guard: the later report's CURRENT column must reproduce the master's year-end of the later year (else the attachment is not that year's statement)
        m_next = M.get((kr, f"{y+1}.4Q", 1))
        f_chk = factor(a1[0].get(1), m_next)
        if m_next is not None and (f_chk is None or abs(a1[0][1] * f_chk - m_next) > max(1.0, 1e-4 * abs(m_next))):
            cnt["PERIOD_MISMATCH"] += 1
            rows.append({"kr": kr, "name": NAMES.get(kr, ""), "quarter": q, "item": "", "cls": "PERIOD_MISMATCH", "note": "later report current column != master of the later year"})
            continue
        for it in (1, 2, 3):
            mv = M.get((kr, q, it))
            ov_raw, lv_raw = a0[0].get(it), a1[1].get(it)
            f0 = factor(ov_raw, mv)
            f1 = f_chk if f_chk is not None else factor(lv_raw, mv)       # the later report's own unit (current column vs master of the later year): big restatements (>25%) must not break the unit fit
            if mv is None:
                cnt["NO_MASTER"] += 1
                continue
            if f0 is None or f1 is None:
                cnt["UNIT_UNRESOLVED"] += 1
                continue
            ov, lv = ov_raw * f0, lv_raw * f1
            tol = max(1.0, 1e-5 * abs(mv))
            s_mo, s_ol, s_ml = abs(mv - ov) <= tol, abs(ov - lv) <= tol, abs(mv - lv) <= tol
            if s_mo and s_ol:
                cls = "SAME_ALL"
            elif s_mo and not s_ol:
                cls = "RESTATED_STALE"
            elif (not s_mo) and s_ml:
                cls = "RESTATED_ADOPTED"
            elif s_ol and not s_mo:
                cls = "MASTER_NEQ_BOTH_FILINGS"          # both filings agree with each other, only the master differs
            else:
                cls = "MASTER_NEQ_ORIG"
            cnt[cls] += 1
            if cls != "SAME_ALL":
                rows.append({"kr": kr, "name": NAMES.get(kr, ""), "quarter": q, "item": it, "master": mv, "orig": round(ov, 6), "later": round(lv, 6), "cls": cls,
                             "later_file": a1[2], "note": f"{rd.name}"})
cols = ["kr", "name", "quarter", "item", "master", "orig", "later", "cls", "later_file", "note"]
with open(HERE / "bs_4q_scan_xml.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
json.dump(dict(cnt), open(HERE / "bs_4q_scan_xml_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(dict(cnt))
for r in rows:
    if r["cls"] in ("RESTATED_STALE", "MASTER_NEQ_BOTH_FILINGS", "MASTER_NEQ_ORIG", "RESTATED_ADOPTED"):
        print(r["cls"], r["kr"], r["name"][:8], r["quarter"], "item", r["item"], "master", r.get("master"), "orig", r.get("orig"), "later", r.get("later"))
