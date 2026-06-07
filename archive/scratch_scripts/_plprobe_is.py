# -*- coding: utf-8 -*-
"""Probe income-statement candidates for one (code, FYdir). Dumps each matched
포괄손익계산서 table with its key lines, so we can see why Tier-1 mis-picks."""
import sys
import glob
import os
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
import scripts.build_pl_breakdown as P  # noqa: E402

CODE = sys.argv[1]
FYDIR = sys.argv[2]  # e.g. FY2024_Q4


def xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


tables = []
for d in glob.glob(f"data/dart/{FYDIR}/raw/{CODE}_*"):
    for x in xmls_in(d):
        try:
            tables.extend(_iter_tables_with_context(Path(x)))
        except Exception:
            pass

cands = [t for t in tables if P._is_income_statement(t)]
print(f"{CODE} {FYDIR}: {len(tables)} tables, {len(cands)} income-statement candidates\n")
for i, t in enumerate(cands):
    conn = "연결" if P._is_consolidated(t) else "별도"
    cap = (t.caption or "")[:70]
    print(f"--- cand[{i}] {conn}  cap={cap!r}")
    for r in t.rows:
        lab = P._label(r).strip("[]")
        if any(k in lab for k in ("보험손익", "보험서비스결과", "투자손익", "영업이익",
                                  "영업외", "법인세", "당기순이익", "세전", "차감전",
                                  "기타영업수익", "기타사업비용", "보험금융")):
            nums = P._row_nums(r)
            print(f"      {lab[:34]:36} {nums[:4]}")
