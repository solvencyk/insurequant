# -*- coding: utf-8 -*-
"""`_identity_tautology_census` 의 통계를 **PL_EQS 에 그대로 적용**해 본다.

이 탐지기를 PL 축에 배선하면 잡히는지 확인하는 것이 목적이다. 결론을 미리 쓰면:
잡히지 않는다. 그리고 **틀린 방향으로** 잡는다 — 진짜 검산 축(EQ8)이 동어반복 축(EQ2)보다
더 '동어반복스럽게' 나온다. 귀무모형이 이 마스터에서 성립하지 않기 때문이다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as K  # noqa: E402
import validate_master_tables as V  # noqa: E402

VERDICT = {0: "TAUTOLOGY", 1: "TAUTOLOGY", 2: "PARTIAL", 3: "TAUTOLOGY",
           4: "REAL", 5: "TAUTOLOGY", 6: "TAUTOLOGY", 7: "REAL", 8: "REAL"}


def main():
    axes, drift = K._taut_axes()
    print(f"_taut_axes() 가 도는 축 = {len(axes)} 개 — 전부 K-ICS item 번호 축:")
    print("   " + ", ".join(a for a, *_r in axes))
    print(f"PL_breakdown / validate_master_tables 축 = 0 개\n")

    pl = V.load_long(V.PL_PATH)
    print(f"{'eq':<46} {'n':>4} {'zeros':>6} {'rate':>7} {'null':>7} {'excess':>7} "
          f"{'z':>8}  {'RED?':>5}  판정")
    print("-" * 122)
    for i, (label, lhs_key, terms) in enumerate(V.PL_EQS):
        n = zeros = 0
        exp = var = 0.0
        for (co, q), m in pl.items():
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                continue
            vals = [m[k] for k, _ in terms]
            k_eff = sum(1 for v in vals if v != 0)
            if k_eff < 2:
                continue
            p = K._taut_null_p0(k_eff)
            n += 1
            exp += p
            var += p * (1 - p)
            if abs(sum(sg * m[k] for k, sg in terms) - lhs) < K._TAUT_ZERO_EPS:
                zeros += 1
        rate = zeros / n if n else 0.0
        null = exp / n if n else 0.0
        excess = rate / null if null else 0.0
        z = (zeros - exp) / var ** 0.5 if var > 0 else 0.0
        red = (excess >= K._TAUT_EXCESS_FLOOR and z >= K._TAUT_Z_FLOOR
               and n >= K._TAUT_MIN_CELLS)
        print(f"{label[:46]:<46} {n:>4} {zeros:>6} {rate:>7.3f} {null:>7.3f} "
              f"{excess:>7.2f} {z:>8.1f}  {'RED' if red else '-':>5}  {VERDICT[i]}")
    print(f"\n임계: excess >= {K._TAUT_EXCESS_FLOOR} AND z >= {K._TAUT_Z_FLOOR} "
          f"AND n >= {K._TAUT_MIN_CELLS}")


if __name__ == "__main__":
    main()
