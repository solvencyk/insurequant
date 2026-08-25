# -*- coding: utf-8 -*-
"""미배선 4파일의 스키마·커버리지 실측 — 어떤 검사를 걸 수 있는지 정하려고 본다.

사용: python scripts/_probes/probe_20260825_unwired_files_shape.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def head(o, n=900):
    return json.dumps(o, ensure_ascii=False)[:n]


def main() -> int:
    print("=" * 90)
    print("1) NB_CSM_multiple.json")
    print("=" * 90)
    nb = j("NB_CSM_multiple.json")
    print(f"  rows={len(nb)}  keys={list(nb[0])}")
    qs = sorted({r["공시분기"] for r in nb})
    cos = sorted({r["원수사명"] for r in nb})
    print(f"  quarters({len(qs)})={qs}")
    print(f"  companies={len(cos)}")
    for k in nb[0]:
        if k in ("원보험사코드", "원수사명", "티커", "생손보여부", "공시분기"):
            continue
        nn = sum(1 for r in nb if r.get(k) is not None)
        print(f"    {k:28s} non-null={nn:4d}/{len(nb)}")
    print("  sample:", head(nb[0], 400))

    print("\n" + "=" * 90)
    print("2) data/dart/viz/csm_amort_schedule.json")
    print("=" * 90)
    a = j("data/dart/viz/csm_amort_schedule.json")
    print(f"  period={a['period']}  companies={len(a['companies'])}")
    c0 = a["companies"][0]
    print(f"  company keys={list(c0)}")
    print("  sample:", head(c0, 700))

    print("\n" + "=" * 90)
    print("3) data/dart/viz/csm_waterfall_history.json")
    print("=" * 90)
    h = j("data/dart/viz/csm_waterfall_history.json")
    print(f"  unit={h['unit']}  source={h['source']}")
    print(f"  periods={h['periods']}")
    print(f"  stage_order={h['stage_order']}")
    print(f"  companies={len(h['companies'])}")
    hc = h["companies"][0]
    print(f"  company keys={list(hc)}")
    print("  sample:", head(hc, 700))

    print("\n" + "=" * 90)
    print("4) data/dart/viz/insurance_pl_breakdown.json")
    print("=" * 90)
    p = j("data/dart/viz/insurance_pl_breakdown.json")
    print(f"  period={p['period']}  companies={len(p['companies'])}")
    pc = p["companies"][0]
    print(f"  company keys={list(pc)}")
    print("  sample:", head(pc, 700))

    print("\n" + "=" * 90)
    print("마스터 쪽 대조 후보")
    print("=" * 90)
    wf = j("CSM_waterfall.json")
    items = defaultdict(int)
    for r in wf:
        items[(r.get("항목번호"), (r.get("항목명") or "").replace(" ", ""))] += 1
    print("  CSM_waterfall 항목:", sorted(items.items())[:30])
    wq = sorted({r["공시분기"] for r in wf})
    print(f"  CSM_waterfall quarters({len(wq)})={wq}")
    pl = j("PL_breakdown.json")
    pitems = defaultdict(int)
    for r in pl:
        pitems[(r.get("항목번호"), (r.get("항목명") or "").replace(" ", ""))] += 1
    print("  PL_breakdown 항목:", sorted(pitems.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
