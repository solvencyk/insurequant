# -*- coding: utf-8 -*-
"""PL_EQS 9식 동어반복 census (조사 전용, 읽기만 한다).

각 등식에 대해:
  - evaluated / skip (게이트와 동일한 결측 규칙)
  - 잔차가 **정확히 float 0.0** 인 비율  (구성상 0 의 지문)
  - |잔차| < 1e-9 / < 1e-6 / floor 이내
  - 잔차 분위수
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import validate_master_tables as V  # noqa: E402


def main():
    pl = V.load_long(V.PL_PATH)
    print(f"buckets = {len(pl)}   master = {V.PL_PATH}")
    print()
    hdr = (f"{'eq':<52} {'eval':>5} {'skip':>5} {'==0.0':>7} {'%':>6} "
           f"{'<1e-9':>6} {'<1e-6':>6} {'p50':>10} {'p90':>12} {'max':>14}")
    print(hdr)
    print("-" * len(hdr))
    detail = {}
    for label, lhs_key, terms in V.PL_EQS:
        resids = []
        n_eval = n_skip = 0
        exact = lt9 = lt6 = 0
        for (co, q), m in sorted(pl.items()):
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                n_skip += 1
                continue
            rhs = sum(sign * m[k] for k, sign in terms)
            adj = V.PL_EQ_ADJ.get(label)
            if adj and all(m.get(k) is not None for k, _ in adj):
                rhs = min((rhs, rhs + sum(s * m[k] for k, s in adj)),
                          key=lambda c: abs(c - lhs))
            d = rhs - lhs
            n_eval += 1
            if d == 0.0:
                exact += 1
            if abs(d) < 1e-9:
                lt9 += 1
            if abs(d) < 1e-6:
                lt6 += 1
            resids.append((abs(d), co, q))
        resids.sort()
        a = [r[0] for r in resids]

        def q_(p):
            if not a:
                return float("nan")
            return a[min(len(a) - 1, int(p * len(a)))]

        pct = 100.0 * exact / n_eval if n_eval else float("nan")
        print(f"{label[:52]:<52} {n_eval:>5} {n_skip:>5} {exact:>7} {pct:>5.1f}% "
              f"{lt9:>6} {lt6:>6} {q_(0.50):>10.4g} {q_(0.90):>12.4g} "
              f"{(a[-1] if a else float('nan')):>14.4g}")
        detail[label] = resids[-6:]

    print()
    print("== 각 등식 최대잔차 상위 6 (|잔차|, 회사, 분기) ==")
    for label, rs in detail.items():
        print(f"\n{label}")
        for d, co, q in reversed(rs):
            print(f"   {d:>16.4f}  {co}  {q}")


if __name__ == "__main__":
    main()
