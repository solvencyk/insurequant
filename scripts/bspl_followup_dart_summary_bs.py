#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c extra: can the DART body XML of the 2023.1Q / 2023.2Q listed-company reports fill the BS holes? (read-only)

The production body-XML fallback (`build_equity_composition_tier2.parse_filing`) returns a consolidated / wrong table for these two quarters (FS-API status 013).
The XML does contain the SEPARATE statement (a 「요약재무상태표」 table, basis marker OFS).  For every listed company and quarter this probe
  1. finds the OFS tables with 자산총계/부채총계/자본총계 whose totals tie to the master's items 1/2/3 of that quarter (the tie proves basis AND scale),
  2. reads the lines 현금및현금성자산(10) 유형자산(15) 보험계약부채(20) 재보험계약부채(21) 기타부채(24) 기타포괄손익누계액(4) 자본금(30) 이익잉여금(31),
  3. compares every line with the master: EQUAL (method validated) / DIFF (method or master wrong) / BLANK (fillable).
Output: data/_derived/bspl_followup_20261011/dart_summary_bs_probe.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from scripts import build_equity_composition_tier2 as T  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073",
          "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104", "KR1000"]
LINES = {10: "현금및현금성자산", 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채", 24: "기타부채", 4: "기타포괄손익누계액", 30: "자본금", 31: "이익잉여금"}
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "dart_summary_bs_probe.json"


def num(s):
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("△") or s.startswith("-") and len(s) > 1
    s = s.strip("()").lstrip("△-")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def norm(lab):
    return re.sub(r"[\s]+", "", T._bs_label(lab))


def main():
    only = set(sys.argv[1:])
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {}
    for r in bs:
        if r["값"] is not None:
            mv[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r["값"]
    res = []
    for code in LISTED:
        if only and code not in only:
            continue
        for fy, q in (("FY2023_Q1", "2023.1Q"), ("FY2023_Q2", "2023.2Q")):
            dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))
            if not dirs:
                res.append({"code": code, "quarter": q, "status": "NO_RAW"})
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                res.append({"code": code, "quarter": q, "status": "NO_XML"})
                continue
            xml = xmls[0]
            raw_lines = xml.read_text(encoding="utf-8", errors="replace").split("\n")
            markers = T._unit_markers_by_line(raw_lines)
            bmarks = T._bs_basis_markers(raw_lines)
            tot = {i: mv.get((code, i, q)) for i in (1, 2, 3)}
            found = []
            for t in _iter_tables_with_context(xml):
                rows = {}
                for r in t.rows:
                    if not r or not r[0]:
                        continue
                    lab = norm(r[0])
                    nums = [num(c) for c in r[1:4]]
                    if lab not in rows:
                        rows[lab] = nums
                if not all(k in rows for k in ("자산총계", "부채총계", "자본총계")):
                    continue
                scale = T._find_unit(markers, t.line_no)
                basis = T._find_basis(bmarks, t.line_no)
                if rows["자산총계"][0] is None:
                    continue
                # scale: the table is in 백만원 when 자산총계 ties to the master within rounding (x1 or x1e-6 for won tables)
                cur = {k: rows[k][0] for k in ("자산총계", "부채총계", "자본총계")}
                tie = None
                for f in (1.0, 1e-6, 1e-3, 100.0):
                    ok = True
                    for k, i in (("자산총계", 1), ("부채총계", 2), ("자본총계", 3)):
                        m = tot.get(i)
                        if m is None or cur[k] is None or abs(cur[k] * f - m) > max(1.5, 0.0002 * abs(m)):
                            ok = False
                    if ok:
                        tie = f
                        break
                found.append({"line": t.line_no, "basis_marker": basis, "scale": scale, "caption": (t.caption or "")[:60], "tie_factor": tie,
                              "values": {k: rows.get(v, [None])[0] for k, v in LINES.items() if v in rows}, "n_rows": len(t.rows)})
            tied = [f for f in found if f["tie_factor"] is not None]
            rec = {"code": code, "quarter": q, "xml": xml.name, "tables_with_totals": len(found), "tied": []}
            for f in tied:
                comp = {}
                for it, v in f["values"].items():
                    if v is None:
                        continue
                    val = v * f["tie_factor"]
                    m = mv.get((code, it, q))
                    if m is None:
                        comp[it] = {"state": "BLANK", "dart": round(val, 3)}
                    else:
                        comp[it] = {"state": "EQUAL" if abs(val - m) <= max(1.5, 0.0002 * abs(m)) else "DIFF", "dart": round(val, 3), "master": m}
                rec["tied"].append({"line": f["line"], "basis_marker": f["basis_marker"], "caption": f["caption"], "items": comp})
            res.append(rec)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    from collections import Counter
    c = Counter()
    for r in res:
        if "tied" not in r:
            c[r["status"]] += 1
            continue
        if not r["tied"]:
            c["NO_TIED_TABLE"] += 1
        for t in r["tied"][:1]:
            for it, d in t["items"].items():
                c[d["state"]] += 1
    print(dict(c))
    for r in res:
        if "tied" not in r:
            print(r["code"], r["quarter"], r["status"])
            continue
        if not r["tied"]:
            print(r["code"], r["quarter"], "no table ties to master totals; tables with totals:", r["tables_with_totals"])
            continue
        t = r["tied"][0]
        print(r["code"], r["quarter"], f"line {t['line']} {t['basis_marker']} {t['caption']!r}:",
              " ".join(f"{it}:{d['state']}" + (f"({d['dart']:,.0f})" if d["state"] != "EQUAL" else "") for it, d in sorted(t["items"].items())))


if __name__ == "__main__":
    main()
