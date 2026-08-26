# -*- coding: utf-8 -*-
"""PL↔워터폴 CSM상각 교차대조의 **미순회 사각** 전수 측정 (validation, 2026-08-26).

룰 3z 는 `for (co,q) in env.pl` 로 돈다 → PL 버킷이 통째로 없으면 완전 침묵.
여기서 세 가지를 센다:
  ① 워터폴 상각 >= MIN 인데 PL 버킷 자체가 없는 자리  (완전 침묵 = 사각)
  ② PL 버킷은 있는데 원수CSM상각이 None/0 인 자리      (현재 RED 를 내는 자리)
  ③ 회사별 PL/워터폴 분기 축 (축 결손인지 회사 특성인지 가르기 위해)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_master_tables import CSM_AMORT_MIN_EOK, load_long  # noqa: E402

TIER2 = ["생명장기손익", "생명장기원수손익", "원수CSM상각", "원수위험조정변동", "원수예실차",
         "기타생명장기원수손익", "생명장기재보험손익", "재보험CSM상각", "재보험위험조정변동",
         "재보험예실차", "기타생명장기재보험손익", "자동차손익", "일반손익"]


def main() -> None:
    pl = load_long("PL_breakdown.json")
    wf = load_long("CSM_waterfall.json")

    print(f"PL buckets={len(pl)}  WF buckets={len(wf)}")

    # ① 미순회 사각
    silent = []
    for (co, q), m in sorted(wf.items()):
        amort = m.get("CSM상각")
        if not isinstance(amort, (int, float)) or abs(amort) < CSM_AMORT_MIN_EOK:
            continue
        if (co, q) not in pl:
            silent.append((co, q, abs(amort)))
    print(f"\n[1] WF 상각>={CSM_AMORT_MIN_EOK} 인데 PL 버킷 부재 = {len(silent)}")
    for co, q, a in sorted(silent, key=lambda x: -x[2]):
        print(f"    {co:24s} {q}  WF상각 {a:10,.1f}억")

    # ② PL 버킷은 있는데 원수CSM상각 결측
    half = []
    for (co, q), m in sorted(pl.items()):
        w = wf.get((co, q))
        if not w:
            continue
        amort = w.get("CSM상각")
        if not isinstance(amort, (int, float)) or abs(amort) < CSM_AMORT_MIN_EOK:
            continue
        d = m.get("원수CSM상각")
        if d is None or d == 0:
            filled = [k for k in TIER2 if isinstance(m.get(k), (int, float))]
            half.append((co, q, abs(amort), len(filled), len(m)))
    print(f"\n[2] PL 버킷 존재하나 원수CSM상각 None/0 = {len(half)}")
    for co, q, a, nf, tot in half:
        print(f"    {co:24s} {q}  WF상각 {a:10,.1f}억  tier2채워짐 {nf}/{len(TIER2)}  PL항목 {tot}")

    # ③ 회사별 분기 축
    cos = sorted({co for co, _q, _a in silent})
    print(f"\n[3] 사각 회사 {len(cos)}사의 분기 축")
    plq = defaultdict(set)
    wfq = defaultdict(set)
    for co, q in pl:
        plq[co].add(q)
    for co, q in wf:
        wfq[co].add(q)
    for co in cos:
        print(f"    {co}")
        print(f"        PL: {sorted(plq[co])}")
        print(f"        WF: {sorted(wfq[co])}")

    out = ROOT / "data" / "_derived" / "pl_amort_blindspot_20260826.json"
    out.write_text(json.dumps({
        "silent": [{"company": c, "quarter": q, "wf_amort_eok": round(a, 2)} for c, q, a in silent],
        "half_filled": [{"company": c, "quarter": q, "wf_amort_eok": round(a, 2),
                         "tier2_filled": nf} for c, q, a, nf, _ in half],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
