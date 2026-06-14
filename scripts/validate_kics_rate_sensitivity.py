#!/usr/bin/env python3
"""Validate K-ICS 금리민감도 master (kics_rate_sensitivity.json).

Rules (owner spec: docs/agents/kics-rate-sensitivity-spec.md §5):
  RS1_RATIO_IDENTITY (RED) — per (사,분기,경과조치)·each shock column c:
      비율[c] ≈ 지급여력금액[c] / 지급여력기준금액[c] × 100.  tol max(0.5%p, 0.5%·|비율|).
  RS2_BASE_ANCHOR (RED) — 적용전 base column vs kics_disclosure.json:
      base 금액≈item1, base 기준금액≈item14, base 비율≈item27.  tol 금액 2억 / 비율 0.5%p.
  RS3_DIRECTION_SANITY (YELLOW) — 생보: 금리하락(−100bp) 시 비율 하락이 통상; 역방향 flag.
  RS4_COVERAGE_CENSUS (YELLOW) — 회사가 인접 분기 보유한데 사이 hole. FY2023~2024.Q3 부재는 정상.

Documented exception: KR0011 DB손해 2025.2Q RS2 — 금리민감도표가 별도재무제표 기준,
  헤드라인 item1/14/27은 연결 기준 → basis 차이(파싱오류 아님), 게이트 블록 안 함.

Output: data/_derived/kics_rate_sensitivity_validation.json. exit 0 if RED=0 (exception 제외) else 2.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

SHOCK_COLS = ["-100bp", "-50bp", "base", "+50bp", "+100bp"]
# RS2 documented exceptions: (회사, 분기) basis 차이 (별도 vs 연결) — RED여도 게이트 블록 안 함.
RS2_EXCEPTIONS = {("DB손해보험", "2025.2Q")}

# 비율행 정렬을 위한 회복 regime 시작 (이전 분기는 서식 도입 전이라 hole 정상)
REGIME_START = "2024.4Q"
ALL_Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
         "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]


def load_rs():
    d = json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))
    g = defaultdict(dict)  # (회사, 분기, 경과조치) -> {measure구분: row}
    for r in d:
        g[(r["원수사명"], r["공시분기"], r["경과조치여부"])][r["measure구분"]] = r
    return g, d


def load_kics():
    d = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    idx = defaultdict(dict)
    for r in d:
        n = r.get("항목번호")
        if n is not None:
            idx[(r["원수사명"], r["공시분기"])][n] = r.get("값")
    return idx


def main() -> int:
    g, rows = load_rs()
    kics = load_kics()

    rs1, rs2, rs2_exc, rs3, rs4 = [], [], [], [], []

    # ---- RS1: 비율 ≈ 금액/기준금액 ×100 ----
    for (co, q, gj), m in g.items():
        rat, amt, bas = m.get("지급여력비율"), m.get("지급여력금액"), m.get("지급여력기준금액")
        if not (rat and amt and bas):
            continue
        for c in SHOCK_COLS:
            rv, av, bv = rat.get(c), amt.get(c), bas.get(c)
            if rv is None or av is None or bv in (None, 0):
                continue
            expected = av / bv * 100.0
            tol = max(0.5, 0.005 * abs(rv))
            if abs(expected - rv) > tol:
                rs1.append((co, q, gj, c, round(rv, 2), round(expected, 2)))

    # ---- RS2: 적용전 base vs kics_disclosure item1/14/27 ----
    CHK = [("지급여력금액", 1, 2.0), ("지급여력기준금액", 14, 2.0), ("지급여력비율", 27, 0.5)]
    for (co, q, gj), m in g.items():
        if gj != "적용전":
            continue
        kd = kics.get((co, q), {})
        for meas, item_no, tol in CHK:
            mr = m.get(meas)
            if not mr:
                continue
            try:
                bv, kv = float(mr.get("base")), float(kd.get(item_no))
            except (TypeError, ValueError):
                continue
            if abs(bv - kv) > tol:
                rec = (co, q, meas, round(bv, 2), round(kv, 2), round(bv - kv, 2))
                (rs2_exc if (co, q) in RS2_EXCEPTIONS else rs2).append(rec)

    # ---- RS3: 생보 금리하락→비율하락 (역방향 YELLOW) ----
    for (co, q, gj), m in g.items():
        row = m.get("지급여력비율")
        if not row:
            continue
        is_life = row.get("생손보여부") == "생명보험"
        b, d100 = row.get("base"), row.get("-100bp")
        if is_life and b is not None and d100 is not None and d100 > b + 0.5:
            rs3.append((co, q, gj, round(d100, 2), round(b, 2)))

    # ---- RS4: 커버리지 census (regime 내 인접 hole) ----
    # 회사별 cadence 인식: 1Q/3Q 보유 이력 있으면 분기공시, 없으면 반기(2Q/4Q)공시.
    # 반기 회사의 1Q/3Q 부재는 정상(hole 아님) — parser 메시지(Q2/Q4 반기 regime) 반영.
    have = defaultdict(set)
    for (co, q, gj) in g:
        have[co].add(q)
    regime_q = [q for q in ALL_Q if q >= REGIME_START]
    for co, qs in have.items():
        held = [q for q in regime_q if q in qs]
        if len(held) < 2:
            continue
        has_odd = any(q.endswith(("1Q", "3Q")) for q in held)
        expected_q = regime_q if has_odd else [q for q in regime_q if q.endswith(("2Q", "4Q"))]
        lo, hi = expected_q.index(held[0]), expected_q.index(held[-1])
        for i in range(lo, hi + 1):
            if expected_q[i] not in qs:
                rs4.append((co, expected_q[i]))

    # ---- report ----
    print("=" * 74)
    print(f"K-ICS 금리민감도 검증  (cohort {len(have)}사, {len(g)} 사·분기·경과조치 그룹)")
    print("=" * 74)
    print(f"RS1_RATIO_IDENTITY (RED):  fail={len(rs1)}")
    for co, q, gj, c, rv, ev in rs1[:20]:
        print(f"   RED {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev}")
    print(f"RS2_BASE_ANCHOR (RED):  fail={len(rs2)}  (+exception {len(rs2_exc)})")
    for co, q, meas, bv, kv, df in rs2:
        print(f"   RED {co:14s} {q} {meas}: base={bv} vs disclosure={kv} (Δ{df:+})")
    for co, q, meas, bv, kv, df in rs2_exc:
        print(f"   EXC {co:14s} {q} {meas}: base={bv} vs disclosure={kv} (Δ{df:+}) — basis 차이(별도/연결), documented")
    print(f"RS3_DIRECTION_SANITY (YELLOW):  flag={len(rs3)}")
    for co, q, gj, d100, b in rs3[:15]:
        print(f"   YEL {co:14s} {q} {gj}: 금리−100bp 비율 {d100} > base {b} (역방향)")
    print(f"RS4_COVERAGE_CENSUS (YELLOW):  hole={len(rs4)}")
    for co, q in rs4[:20]:
        print(f"   YEL {co:14s} {q} (regime 내 hole)")

    red_total = len(rs1) + len(rs2)  # exception 제외
    print()
    print("#" * 74)
    print(f"SUMMARY  RS1:{len(rs1)}RED | RS2:{len(rs2)}RED(+{len(rs2_exc)}exc) | "
          f"RS3:{len(rs3)}Y | RS4:{len(rs4)}Y | gate RED={red_total}")
    print("#" * 74)

    out = ROOT / "data" / "_derived" / "kics_rate_sensitivity_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "_meta": {"groups": len(g), "companies": len(have), "gate_red": red_total},
        "RS1_ratio_identity": [dict(zip(["회사", "분기", "경과조치", "컬럼", "비율", "expected"], r)) for r in rs1],
        "RS2_base_anchor": [dict(zip(["회사", "분기", "measure", "base", "disclosure", "diff"], r)) for r in rs2],
        "RS2_exceptions": [dict(zip(["회사", "분기", "measure", "base", "disclosure", "diff"], r)) for r in rs2_exc],
        "RS3_direction": [dict(zip(["회사", "분기", "경과조치", "m100bp", "base"], r)) for r in rs3],
        "RS4_coverage_hole": [dict(zip(["회사", "분기"], r)) for r in rs4],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if red_total == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
