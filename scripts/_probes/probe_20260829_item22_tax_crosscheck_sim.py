# -*- coding: utf-8 -*-
"""item22(세전이익) 을 `24 + 원천 법인세 계정` 과 대조하는 **전 버킷 시뮬레이션** (읽기 전용).

왜: `PL_EQS` 의 `당기순이익 = 세전 - 법인세` 는 빌더가 `item23 = 22 - 24` 로 무조건 덮기
때문에 구성상 참이다(418/418). 그래서 item22 를 흔들어도 어떤 룰도 안 걸린다(변이시험 0.0%).
원천 법인세 계정(`ifrs-full_IncomeTaxExpenseContinuingOperations`)은 **버려지기 전에**
FS-API 캐시에 그대로 있으므로, 그 값과 마스터의 `|22 - 24|` 를 대조하면 진짜 검산이 된다.

부호는 대조하지 않는다 — 빌더 주석이 명시하듯 발행사마다 법인세비용의 부호 관행이 다르다
(양수 금액 vs 괄호 차감). 그래서 **크기(abs)** 로만 본다.

출력: 대조가능 버킷 수 · 잔차 분포 · 게이트 허용오차에서의 PASS/FAIL · FAIL 건별.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import fetch_dart_fs as F          # noqa: E402
import validate_master_tables as V  # noqa: E402

FLOOR = 200.0
REL = 0.001


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    # (원수사명, 공시분기) -> {항목명: 값}, plus 원보험사코드
    master, code_of = {}, {}
    for r in rows:
        k = (r["원수사명"], r["공시분기"])
        master.setdefault(k, {})[V.norm(r["항목명"])] = r["값"]
        code_of[r["원수사명"]] = r["원보험사코드"]

    n_bucket = len(master)
    stats = {"no_tier1": 0, "no_raw_tax": 0, "no_master_2224": 0, "compared": 0}
    resid, fails, zero_tax = [], [], 0

    for (co, q) in sorted(master):
        m = master[(co, q)]
        m22, m24 = m.get("세전이익"), m.get("당기순이익")
        if m22 is None or m24 is None:
            stats["no_master_2224"] += 1
            continue
        try:
            t1 = F.tier1_for(co, q, code_of.get(co))
        except Exception:
            t1 = None
        if not t1:
            stats["no_tier1"] += 1
            continue
        raw_tax = t1.get(23)
        if raw_tax is None:
            stats["no_raw_tax"] += 1
            continue
        stats["compared"] += 1
        if raw_tax == 0:
            zero_tax += 1
        lhs = abs(m22 - m24)          # 마스터가 법인세로 쓰는 잔차의 크기
        rhs = abs(raw_tax)            # 원천 법인세 계정의 크기
        d = rhs - lhs
        resid.append((abs(d), co, q, lhs, rhs, d))
        tol = max(REL * max(abs(m22), lhs), FLOOR)
        if abs(d) > tol:
            fails.append((co, q, round(m22, 1), round(lhs, 1), round(rhs, 1),
                          round(d, 1), round(tol, 1)))

    print(f"PL 마스터 버킷 = {n_bucket}")
    for k, v in stats.items():
        print(f"  {v:>5}  {k}")
    print(f"  {zero_tax:>5}  ...그 중 원천 법인세 == 0 인 버킷")
    resid.sort()
    if resid:
        import statistics
        vals = [r[0] for r in resid]
        n = len(vals)
        print()
        print(f"잔차 |원천법인세| - |22-24| (백만원)  n={n}")
        print(f"  정확히 0      : {sum(1 for v in vals if v == 0)}")
        print(f"  <= 1          : {sum(1 for v in vals if v <= 1)}")
        print(f"  <= 200(floor) : {sum(1 for v in vals if v <= FLOOR)}")
        print(f"  median        : {statistics.median(vals):,.3f}")
        print(f"  p90           : {vals[int(0.9 * (n - 1))]:,.3f}")
        print(f"  max           : {vals[-1]:,.3f}")
    print()
    print(f"게이트 허용오차 max(0.1%, 200백만) 기준  PASS={stats['compared'] - len(fails)} "
          f"FAIL={len(fails)}")
    for co, q, m22, lhs, rhs, d, tol in fails[:60]:
        print(f"  FAIL {co:16s} {q}  22={m22:>14,.1f}  |22-24|={lhs:>13,.1f}  "
              f"|원천세|={rhs:>13,.1f}  diff={d:>+12,.1f}  tol={tol:,.1f}")
    if len(fails) > 60:
        print(f"  ... 외 {len(fails) - 60} 건")


if __name__ == "__main__":
    main()
