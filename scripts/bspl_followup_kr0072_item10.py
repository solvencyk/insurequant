#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3 finding F-1: KR0072 (케이디비생명) PL item 10 (재보험 위험조정 변동), 3개월 vs 누적.

For every DART filing 2023.1Q..2026.2Q it prints the two '(2) 위험해제로 인한 비금융위험에 대한 위험조정' rows of the 보험손익 note
(first = 원수, second = 재보험) with their column layout, the production handler's output for item 5/10, and the master YTD.
Read-only.  Output: data/_derived/bspl_followup_20261011/finding_kr0072_item10_3month_vs_cumulative.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402

CODE = sys.argv[1] if len(sys.argv) > 1 else "KR0072"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / (f"finding_{CODE.lower()}_item10_3month_vs_cumulative.json")


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    mv = {(r["공시분기"], str(r["항목번호"])): (r.get("값"), r.get("값_당분기")) for r in pl if r["원보험사코드"] == CODE}
    res = []
    for q in QS:
        fy = f"FY{q[:4]}_Q{q[5]}"
        dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{CODE}_*"))
        if not dirs:
            res.append({"quarter": q, "note": "no raw"})
            continue
        xml = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]
        tables = list(_iter_tables_with_context(xml))
        try:
            out = C.LIFE_HANDLERS[CODE](tables)
        except Exception as e:  # noqa: BLE001
            out = {"error": repr(e)}
        rows = []
        for i, t in enumerate(tables):
            for r in t.rows:
                if r and "".join(str(c) for c in r[:2]).startswith("(2)위험해제로인한비금융위험") or (r and str(r[0]).replace(" ", "").startswith("(2)위험해제로인한비금융위험")):
                    hdr = " ".join(str(c) for rr in (t.header or []) for c in rr)[:120]
                    rows.append({"table": i, "line": t.line_no, "header": hdr, "row": [str(c) for c in r[:7]]})
        res.append({"quarter": q, "xml": xml.name, "handler_item5": out.get(5), "handler_item10": out.get(10),
                    "master_item10_ytd_qtr": mv.get((q, "10")), "master_item5_ytd_qtr": mv.get((q, "5")), "ra_release_rows": rows[:4]})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for r in res:
        print(r["quarter"], "handler5/10:", r.get("handler_item5"), r.get("handler_item10"), "master10:", r.get("master_item10_ytd_qtr"))
        for x in r.get("ra_release_rows", []):
            print("    line", x["line"], "|", x["header"][:60], "|", x["row"][1:])


if __name__ == "__main__":
    main()
