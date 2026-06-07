#!/usr/bin/env python3
"""Validate master tables: data/dart/viz/pl_breakdown_master.json + CSM_waterfall.json.

Implements V8 consumer code:
  - CSM_WATERFALL_CLOSING_IDENTITY : 기초+신계약+이자+가정+상각 = 기말  (CSM_waterfall, 억원)
  - PL_BRIDGE_DART_INTERNAL        : 8-eq P&L bridge                  (pl_breakdown_master, 백만원)
  - CSM_CROSSCHECK_WATERFALL_VS_PL : pl.원수CSM상각(+) + wf.CSM상각(-)*100 ≈ 0

Both masters long-format. PL master is **백만원**, CSM waterfall is **억원**:
cross-check aligns by ×100 (억→백만). Item names space-normalized.
Tolerance per equation: max(0.1%·|expected|, floor). floor = 2억 (waterfall) / 200백만 (PL).
An equation is SKIPPED if its LHS or any RHS term is missing (None) — 0.0 is a valid value.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

PL_PATH = "data/dart/viz/pl_breakdown_master.json"
WF_PATH = "CSM_waterfall.json"


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def load_long(path: str) -> dict:
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    idx: dict = defaultdict(dict)
    for r in d:
        idx[(r["원수사명"], r["공시분기"])][norm(r["항목명"])] = r["값"]
    return idx


# ---- PL bridge equations: (label, LHS_key, [(RHS_key, sign), ...]) ----
# 보험손익은 dual-form(별도 처리): 회사마다 보험손익 = ΣLOB(bare) 또는 ΣLOB+기타영업수익-기타사업비용(adj).
# 손보(DB/현대/흥국/메리츠 등)는 기타영업수익·기타사업비용이 보험손익 라인 밖(별도 영업비용)이라 bare.
# 삼성화재 등은 adj. 둘 중 하나 닫히면 PASS.
PL_EQS = [
    ("생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
     "생명장기원수손익",
     [("원수CSM상각", 1), ("원수위험조정변동", 1), ("원수예실차", 1), ("기타생명장기원수손익", 1)]),
    ("생명장기재보험손익 = 재보험CSM상각+재보험RA+재보험예실차+기타재보험",
     "생명장기재보험손익",
     [("재보험CSM상각", 1), ("재보험위험조정변동", 1), ("재보험예실차", 1), ("기타생명장기재보험손익", 1)]),
    ("생명장기손익 = 원수손익+재보험손익",
     "생명장기손익",
     [("생명장기원수손익", 1), ("생명장기재보험손익", 1)]),
    ("투자손익 = 투자이익+보험금융손익",
     "투자손익",
     [("투자이익", 1), ("보험금융손익", 1)]),
    ("영업이익 = 보험손익+투자손익",
     "영업이익",
     [("보험손익", 1), ("투자손익", 1)]),
    ("세전이익 = 영업이익+영업외손익",
     "세전이익",
     [("영업이익", 1), ("영업외손익", 1)]),
    ("당기순이익 = 세전-법인세",
     "당기순이익",
     [("세전이익", 1), ("법인세", -1)]),
]

# 등식별 abs floor (백만원). 영업이익은 0근처 회사(KDB 등) 과민 방지로 완화.
EQ_FLOOR = {"영업이익 = 보험손익+투자손익": 600.0}
DEFAULT_FLOOR = 200.0


def main() -> int:
    pl = load_long(PL_PATH)
    wf = load_long(WF_PATH)

    # ===== 1. CLOSING_IDENTITY (CSM_waterfall, 억원) =====
    need = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
    ci_pass = ci_skip = 0
    ci_fail = []
    for (co, q), m in sorted(wf.items()):
        if any(m.get(k) is None for k in need):
            ci_skip += 1
            continue
        lhs = sum(m[k] for k in need[:-1])
        rhs = m["기말CSM"]
        diff = lhs - rhs
        if abs(diff) > max(0.001 * abs(rhs), 2.0):
            ci_fail.append((co, q, round(rhs, 1), round(diff, 1)))
        else:
            ci_pass += 1

    print("=" * 78)
    print(f"1. CLOSING_IDENTITY (CSM_waterfall, 억원)  pass={ci_pass} fail={len(ci_fail)} skip={ci_skip}")
    print("=" * 78)
    for co, q, rhs, diff in ci_fail:
        print(f"  FAIL {co:14s} {q}  기말={rhs:>11.1f}  diff={diff:>+10.1f}  ({diff/rhs*100:+.1f}%)")

    # ===== 1b. CSM_PLAUSIBILITY (절댓값 sanity — closing identity가 못 잡는 것) =====
    # closing identity는 내부 산술 합산만 봐서 (a)분기 복붙 (b)기말 QoQ 폭락 같은
    # 절댓값 이상을 통과시킴. 별도 plausibility 체크로 보강.
    QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
          "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]
    wf_co: dict = defaultdict(dict)
    for (co, q), m in wf.items():
        wf_co[co][q] = m
    dup_rows = []     # (co, [분기...]) — 같은 회사 내 기말 CSM 동일 (복붙 의심)
    spike_rows = []   # (co, q_prev, q, prev, cur, dq) — 기말 QoQ |Δ|>50%
    for co, qmap in sorted(wf_co.items()):
        # 복붙: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일.
        # CSM 잔액은 매분기 변하므로 동일 = 분기 데이터 복붙(2025를 2024로 채움 등) 강력 의심.
        end_sigs: dict = defaultdict(list)
        for q, m in qmap.items():
            e = m.get("기말CSM")
            if e is not None:
                end_sigs[round(e, 1)].append(q)
        for v, qq in end_sigs.items():
            if len(qq) > 1:
                dup_rows.append((co, sorted(qq)))
        for i in range(1, len(QS)):
            p = qmap.get(QS[i - 1], {}).get("기말CSM")
            c = qmap.get(QS[i], {}).get("기말CSM")
            if p is not None and c is not None and abs(p) > 1e-6 and abs((c - p) / p) > 0.50:
                spike_rows.append((co, QS[i - 1], QS[i], p, c, (c - p) / p))

    # 연속성: FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말 (YTD 연초값 고정 방식).
    # 작년 기말 = 올해 기시. 2023은 2022 데이터 없어 SKIP.
    FY_Q = {
        "2024": ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
        "2025": ["2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q"],
        "2026": ["2026.1Q"],
    }
    PREV_CLOSE = {"2024": "2023.4Q", "2025": "2024.4Q", "2026": "2025.4Q"}
    cont_rows = []   # (co, q, 기초, 전년말기말, 전년말분기)
    for co, qmap in sorted(wf_co.items()):
        for fy, qq in FY_Q.items():
            pc = qmap.get(PREV_CLOSE[fy], {}).get("기말CSM")
            if pc is None:
                continue
            for q in qq:
                o = qmap.get(q, {}).get("기초CSM")
                if o is None:
                    continue
                if abs(o - pc) > max(0.005 * abs(pc), 2.0):
                    cont_rows.append((co, q, o, pc, PREV_CLOSE[fy]))

    print()
    print("=" * 78)
    print(f"1b. CSM_PLAUSIBILITY  복붙(dup)={len(dup_rows)} 기말QoQ폭변(spike)={len(spike_rows)} 연속성위반(cont)={len(cont_rows)}")
    print("=" * 78)
    for co, qq in dup_rows:
        print(f"  DUP   {co:14s} 기말 CSM 동일(복붙 의심): {qq}")
    for co, qp, q, p, c, dq in spike_rows:
        print(f"  SPIKE {co:14s} {qp}->{q}: 기말 {p:.0f} -> {c:.0f} ({dq*100:+.0f}%)")
    for co, q, o, pc, pcq in cont_rows:
        print(f"  CONT  {co:14s} {q} 기초={o:.0f} ≠ {pcq} 기말={pc:.0f}  (Δ{o-pc:+.0f})")

    # ===== 2. PL_BRIDGE (pl_breakdown_master, 백만원) =====
    pb_pass = pb_skip = 0
    pb_fail = []
    eq_fail_count = defaultdict(int)
    for (co, q), m in sorted(pl.items()):
        # --- 보험손익 dual-form (bare ΣLOB / adj +기타영업수익-기타사업비용) ---
        bo = m.get("보험손익")
        lob = [m.get("생명장기손익"), m.get("자동차손익"), m.get("일반손익")]
        if bo is None or any(x is None for x in lob):
            pb_skip += 1
        else:
            bare = sum(lob)
            cands = [bare]
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            if oi is not None and oe is not None:
                cands.append(bare + oi - oe)
            diff = min((c - bo for c in cands), key=abs)
            if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
                pb_fail.append((co, q, "보험손익(dual)", round(bo, 1), round(diff, 1)))
                eq_fail_count["보험손익(dual)"] += 1
            else:
                pb_pass += 1
        # --- 나머지 등식 ---
        for label, lhs_key, terms in PL_EQS:
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                pb_skip += 1
                continue
            rhs = sum(sign * m[k] for k, sign in terms)
            diff = rhs - lhs
            if abs(diff) > max(0.001 * abs(lhs), EQ_FLOOR.get(label, DEFAULT_FLOOR)):
                pb_fail.append((co, q, label, round(lhs, 1), round(diff, 1)))
                eq_fail_count[label] += 1
            else:
                pb_pass += 1

    print()
    print("=" * 78)
    print(f"2. PL_BRIDGE (pl_breakdown_master, 백만원)  pass={pb_pass} fail={len(pb_fail)} skip={pb_skip}")
    print("=" * 78)
    print("  -- fail count by equation --")
    for label, n in sorted(eq_fail_count.items(), key=lambda x: -x[1]):
        print(f"    {n:>3d}  {label}")
    print("  -- fail detail (first 35) --")
    for co, q, label, lhs, diff in pb_fail[:35]:
        print(f"  FAIL {co:14s} {q}  [{label.split('=')[0].strip()}]  lhs={lhs:.1f} diff={diff:+.1f}")

    # ===== 3. CSM_CROSSCHECK (pl.원수CSM상각 + wf.CSM상각*100 ≈ 0, 백만원) =====
    # 4Q-only: pl 원수CSM상각/wf CSM상각 모두 YTD 누적이라 1~3Q는 분기배분 차이로 틀어짐.
    # 연말(4Q=연간 누계)에서만 동일 기준 → 4Q만 비교, 1~3Q SKIP.
    # cross-table(서로 다른 DART 표: PL 보험수익 구성 vs CSM 변동표)이라 표간 반올림/집계 차이로
    # 수% 편차는 구조적 → 3단계 tol: OK ≤ max(5%,300mn) / MINOR ≤ 10%(경고,pass) / FAIL > 10%.
    cc_pass = cc_minor = cc_skip = 0
    cc_fail = []
    cc_minor_rows = []
    common = sorted(set(pl) & set(wf))
    for (co, q) in common:
        if not q.endswith(".4Q"):
            cc_skip += 1
            continue
        # wf '발행한 보험계약' CSM상각 = 원수(direct) + 수재(assumed reinsurance). For a
        # reinsurer (코리안리) the PL splits these into 원수CSM상각(4) + 수재CSM상각(4-1):
        # both are issued contracts, so the PL side must add 수재 to match the rollforward.
        # (출재/retro = 9-1 출재CSM상각, a HELD reinsurance asset — excluded, not added.)
        p_dir = pl[(co, q)].get("원수CSM상각")       # 백만원, 보험수익 기여 → 양수
        p_assumed = pl[(co, q)].get("수재CSM상각")   # 재보험사만 존재 (수재 발행계약)
        p = None if p_dir is None else p_dir + (p_assumed or 0.0)
        w = wf[(co, q)].get("CSM상각")               # 억원, CSM 감소 → 음수
        if p is None or w is None:
            cc_skip += 1
            continue
        w_mn = w * 100.0                              # 억 → 백만
        s = p + w_mn
        abs_s = abs(s)
        rel = abs_s / abs(p) if p else 0.0
        if abs_s <= max(0.05 * abs(p), 300.0):
            cc_pass += 1
        elif rel <= 0.10:
            cc_minor += 1
            cc_minor_rows.append((co, q, round(p, 1), round(w_mn, 1), round(s, 1), rel))
        else:
            cc_fail.append((co, q, round(p, 1), round(w_mn, 1), round(s, 1), rel))

    print()
    print("=" * 78)
    print(f"3. CSM_CROSSCHECK (pl.원수CSM상각 + wf.CSM상각 ≈ 0, 4Q-only 백만원)  "
          f"common={len(common)} pass={cc_pass} minor={cc_minor} fail={len(cc_fail)} skip={cc_skip}")
    print("   tol: OK≤max(5%,300mn) / MINOR≤10%(경고) / FAIL>10%")
    print("=" * 78)
    for co, q, p, w, s, rel in cc_fail[:35]:
        print(f"  FAIL  {co:14s} {q}  pl={p:>+12.1f}  wf={w:>+12.1f}  sum={s:>+10.1f}  ({rel*100:+.1f}%)")
    for co, q, p, w, s, rel in cc_minor_rows[:35]:
        print(f"  MINOR {co:14s} {q}  pl={p:>+12.1f}  wf={w:>+12.1f}  sum={s:>+10.1f}  ({rel*100:+.1f}%)")

    print()
    print("#" * 78)
    print(f"SUMMARY  closing:{ci_pass}P/{len(ci_fail)}F/{ci_skip}S | "
          f"plausibility:{len(dup_rows)}dup/{len(spike_rows)}spike/{len(cont_rows)}cont | "
          f"pl_bridge:{pb_pass}P/{len(pb_fail)}F/{pb_skip}S | "
          f"crosscheck:{cc_pass}P/{cc_minor}M/{len(cc_fail)}F/{cc_skip}S")
    print("#" * 78)
    return 0 if not (ci_fail or pb_fail or cc_fail or dup_rows or spike_rows or cont_rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
