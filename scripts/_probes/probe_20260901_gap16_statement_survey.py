"""For each of the 16 b_raw_no_pl cells: does the raw contain a 포괄손익계산서-like table?
Print its header + first rows so we can classify the layout family."""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402

CEN = json.loads((ROOT / "data/_derived/pl_coverage_census_20260901.json").read_text(encoding="utf-8"))
grid, pc = CEN["grid"], CEN["per_company"]

targets = []
for code in sorted(grid):
    for q, cell in grid[code].items():
        if cell["verdict"] == "b_raw_no_pl":
            targets.append((code, q, cell["raw_all"]))
targets.sort(key=lambda t: (t[0], t[1]))

IS_MARKERS = ("보험영업수익", "보험손익", "보험서비스결과", "영업수익", "당기순이익",
              "법인세비용차감전순이익", "보험수익")


def looks_like_is(t):
    flat = " ".join(" ".join("" if c is None else str(c) for c in r) for r in (t.rows or [])[:40])
    cap = (t.caption or "")
    score = sum(1 for m in IS_MARKERS if m in flat or m in cap)
    return score >= 3 and ("당기순이익" in flat or "법인세" in flat)


for code, q, raws in targets:
    print("=" * 110)
    print(f"### {code} {pc[code]['name']}  {q}")
    dirs = [r["dir"] for r in raws if not r["no_filing"] and (r["n_xml"] or r["has_zip"])]
    tables = []
    for d in dirs:
        xs = sorted(glob.glob(d + "/*.xml")) + sorted(glob.glob(d + "/xml/*.xml"))
        print(f"    dir={d}  xml={len(xs)}")
        for x in xs:
            try:
                tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
            except Exception as e:  # noqa: BLE001
                print(f"      parse error {Path(x).name}: {e}")
    print(f"    tables={len(tables)}   extract_tier1 -> "
          f"{'None' if extract_tier1(tables, code=code) is None else 'DICT'}")
    cands = [t for t in tables if looks_like_is(t)]
    print(f"    income-statement-like tables: {len(cands)}")
    for t in cands[:2]:
        print(f"      caption={ (t.caption or '')[:90]!r}")
        print(f"      header={t.header}")
        for r in (t.rows or [])[:16]:
            print("        " + " | ".join("" if c is None else str(c) for c in r)[:150])
        print()
