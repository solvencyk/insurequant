#!/usr/bin/env python3
"""Validate K-ICS 금리민감도 master (kics_rate_sensitivity.json).

Rules (owner spec: docs/agents/kics-rate-sensitivity-spec.md §5):
  RS1_RATIO_IDENTITY (RED) — per (사,분기,경과조치)·each shock column c:
      비율[c] ≈ 지급여력금액[c] / 지급여력기준금액[c] × 100.  tol max(0.5%p, 0.5%·|비율|).
  RS2_BASE_ANCHOR (RED) — base column vs kics_disclosure.json, **both phases** (2026-09-21):
      적용전 base ≈ item1/item14/item27 `값`, 적용후 base ≈ the same items' `값_적용후`.
      tol 금액 2억 / 비율 0.5%p. Until 2026-09-21 only 적용전 was anchored although the spec
      (§5 RS2 "적용후는 값_적용후 있을 때만") always said both — the parser's 2026.2Q fix method
      (적용전→적용후 mirror for non-appliers) had no anchor at all. `값_적용후` missing is counted
      and printed (rs2_na), not silently skipped.
  RS3_DIRECTION_SANITY (YELLOW) — 생보: 금리하락(−100bp) 시 비율 하락이 통상; 역방향 flag.
  RS4_COVERAGE_CENSUS (YELLOW) — 회사가 인접 분기 보유한데 사이 hole. FY2023~2024.Q3 부재는 정상.
  RS5_DISCLOSURE_COVERAGE (RED, 2026-09-01 신설) — kics_disclosure.json을 정본 코호트로 삼는
      census: REGIME_START 이후 짝수분기(2Q/4Q)에서 kics_disclosure에 있는 (회사,분기)가
      kics_rate_sensitivity에 통째로 없으면 RED. 2026.2Q 28개사 결측(RS1-4 어느 룰도 못 잡음 —
      "없는 셀"은 SKIP되지 findings 자체가 안 생김, coverage-census-mandatory 원칙)을 계기로 신설.
      홀수분기(1Q/3Q)는 census에서 제외 — 실측 0/268(2023.1Q~2026.1Q 7개 홀수분기 전체, 전사)로
      간이공시 cadence 확정(36-40/41-46과 동일 계열), 개별 회사 확인 아님. REGIME_START 이전
      짝수분기(~2024.2Q)도 제외 — 표 서식 자체가 그 전엔 없었음(스펙 §4).
  RS6_PHASE_LEVEL_CENSUS (RED, 2026-09-21 신설, inbox/validation/20260921T0100Z) — RS5 sees a
      bucket that is *wholly* absent; RS6 sees the grid *inside* a present bucket. For every
      cohort (회사,분기) present in the master, each phase (적용전/적용후) must have all three
      measures (지급여력비율/지급여력금액/지급여력기준금액) and every present row must have all five
      shock cells. Kinds: ROW_MISSING · NULL_CELLS · UNKNOWN_LABEL (경과조치여부/measure구분 outside
      the vocabulary — such a row would otherwise look like a hole *and* be invisible) · ORPHAN
      ((코드,분기) not in the kics_disclosure cohort — the reverse of RS5).
      Why it exists: 2026.2Q had 3 companies with 적용전 3 rows and 적용후 0 rows and RS1-5 all
      passed (RS4/RS5 are bucket-level; RS1-3 only judge cells that exist). Severity is RED, not
      YELLOW-first, because this is a census of expected cells (결측은 SKIP이 아니라 RED) and the
      2026.2Q case would have reached the live panel again under YELLOW. Pre-existing holes are
      listed in RS6_KNOWN_HOLES as a *routed backfill worklist* (printed every run, inert-checked),
      not as legit absence.

Documented exceptions (RED but not blocking): see RS1_EXCEPTIONS · RS2_EXCEPTIONS · RS5_EXCEPTIONS ·
RS6_KNOWN_HOLES below — each with the raw evidence or the routing ticket.

Output: data/_derived/kics_rate_sensitivity_validation.json. exit 0 if RED=0 (exception 제외) else 2.
`run(rs_rows, kd_rows)` is pure (no I/O) so tests/test_rule_coverage_manifest.py can mutate a copy.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover — non-console stdout
    pass

from _quarter_horizon import quarter_horizon  # noqa: E402

SHOCK_COLS = ["-100bp", "-50bp", "base", "+50bp", "+100bp"]
MEASURES = ("지급여력비율", "지급여력금액", "지급여력기준금액")
PHASES = ("적용전", "적용후")
# RS2 documented exceptions: (회사, 분기) basis 차이 (별도 vs 연결) — RED여도 게이트 블록 안 함.
# 현대해상 2026.2Q: 원문 자체가 같은 필링 안 두 표에서 지급여력기준금액 base를 다르게 인쇄
# (md_inbox/FY2026_Q2/KR0009_현대해상.md L1245 "6-8-2) 금리 민감도 분석" 표=73,338 vs L1268
# "6-8-3) 환율 민감도 분석" 표=73,335, kics_disclosure item14=73335는 후자와 일치) — Δ3(0.004%),
# RS1은 두 표 각자 내부적으로 자기정합(153284/73338*100=209.00=인쇄값과 정확히 일치이므로
# 파싱오류 아님, 발행사 표간 반올림 불일치. "issuer-inconsistent keep as disclosed" 원칙에
# 따라 금리민감도표에 실제 인쇄된 값(73,338)을 그대로 보존 (2026-09-01).
# 키는 (회사, 분기) 로 **두 phase 에 같이** 걸린다 — 사유(basis·표간 불일치)가 필링 단위이고, 두 회사
# 모두 적용후 행이 적용전의 미러라 같은 잔차가 적용후에도 그대로 나온다(2026-09-21 실측 DB 3·현대 1).
RS2_EXCEPTIONS = {("DB손해보험", "2025.2Q"), ("현대해상", "2026.2Q")}
# RS1 documented exceptions: (회사, 분기, 경과조치, 컬럼) — 원문 PDF 자체의 오류(파싱 결함 아님).
# 예별손해보험 2024.4Q: raw p.75 "6-8-2) 금리 민감도 분석" 표에서 경과조치 후 지급여력기준금액
# 행의 △100bp/△50bp 두 칸이 모두 "9,170"으로 인쇄돼 있다(fitz word-bbox로 좌표까지 대조 —
# 두 값이 각자의 열 헤더 위치에 정확히 위치, docling 오독이 아니라 원문 자체 중복/오타).
# 역산한 참값(비율 -30.98, 금액 -3,022 기준)은 약 9,754.7이지만 원문에 그 숫자가 없어 추측
# 주입 대신 원문 그대로 두고 예외 처리 (2026-08-31, scripts/_probes/probe_20260831_yebyeol_pdf_page.py).
RS1_EXCEPTIONS = {("예별손해보험", "2024.4Q", "적용후", "-100bp")}

# 비율행 정렬을 위한 회복 regime 시작 (이전 분기는 서식 도입 전이라 hole 정상)
REGIME_START = "2024.4Q"
# 지평은 마스터에서 파생한다(`scripts/_quarter_horizon.py`). 2026-08-29 까지 여기도
# `2026.1Q` 로 끝나는 리터럴이었다 — K-ICS 2026.2Q 공시가 들어오는 순간 RS4 커버리지
# census 가 그 분기를 **조용히 건너뛸** 자리였다(현재 kics 마스터 최신은 2026.1Q 라 아직
# 발현 전. 발현하고 나서 고치면 늦다).
ALL_Q = quarter_horizon()

# RS5 documented exceptions: (원보험사코드, 공시분기) — kics_disclosure엔 있는데 kics_rate_
# sensitivity에 통째로 없는 REGIME 내 짝수분기 결손. 전부 2026-09-01 세션 **이전부터** 있던
# 결손이고, 이번 세션 범위는 2026.2Q뿐이라 원인 미규명 상태로 문서화만 한다(추측 주입 금지 —
# "빈 칸이 낫다"). 2024.4Q 13사 + 2025.2Q 4사, 전수측정
# scripts/_probes/probe_20260901_ratesens_census_survey.py 재현. 향후 백필 세션 후보.
RS5_EXCEPTIONS = {
    ("KR0005", "2024.4Q"), ("KR0029", "2024.4Q"), ("KR0070", "2024.4Q"), ("KR0071", "2024.4Q"),
    ("KR0072", "2024.4Q"), ("KR0076", "2024.4Q"), ("KR0079", "2024.4Q"), ("KR0080", "2024.4Q"),
    ("KR0094", "2024.4Q"), ("KR0097", "2024.4Q"), ("KR0099", "2024.4Q"), ("KR1010", "2024.4Q"),
    ("KR1098", "2024.4Q"),
    ("KR0029", "2025.2Q"), ("KR0079", "2025.2Q"), ("KR0080", "2025.2Q"), ("KR1098", "2025.2Q"),
}

# RS6 routed backfill worklist: (원보험사코드, 공시분기, 경과조치여부) whose phase-level holes
# pre-date the rule (2026-09-21 census of ALL regime quarters:
# scripts/_probes/_probe_20260921_ratesens_phase_census.py → 10 buckets · 30 missing rows · 1
# all-null row). **Not legit absence** — the same three companies' 2026.2Q analogues were extraction
# gaps (raw footnote "선택경과조치 미적용 → 전·후 동일", parser mirrored them on 2026-09-21). Each key
# is routed cell-by-cell to parser-kics:
#   inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md
# A key that no longer fires is reported as RS6 inert (YELLOW) so the list cannot outlive the hole.
# KR0150 서울보증 2024.4Q is the reverse shape: 적용전 3 rows missing, and the 적용후 지급여력기준금액
# row present with all 5 shock cells null (RS1 skipped it: `bv in (None, 0)`).
RS6_KNOWN_HOLES = {
    ("KR0050", "2024.4Q", "적용후"), ("KR0050", "2025.2Q", "적용후"), ("KR0050", "2025.4Q", "적용후"),
    ("KR0051", "2025.4Q", "적용후"),
    ("KR0069", "2024.4Q", "적용후"), ("KR0069", "2025.2Q", "적용후"), ("KR0069", "2025.4Q", "적용후"),
    ("KR0087", "2024.4Q", "적용후"),
    ("KR0150", "2024.4Q", "적용전"), ("KR0150", "2024.4Q", "적용후"),
    ("KR1098", "2025.4Q", "적용후"),
}


def load_rs():
    return json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))


def load_kd():
    return json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))


def _group_rs(rows):
    g = defaultdict(dict)  # (회사, 분기, 경과조치) -> {measure구분: row}
    for r in rows:
        g[(r["원수사명"], r["공시분기"], r["경과조치여부"])][r["measure구분"]] = r
    return g


def _disclosure_cohort(kd_rows):
    """(원보험사코드, 공시분기) -> 원수사명, for every row in kics_disclosure.json — the
    RS5/RS6 census's expected population (that master's coverage census already guarantees
    this is complete per quarter, so it's the right cohort to anchor against)."""
    cohort = {}
    for r in kd_rows:
        cohort[(r["원보험사코드"], r["공시분기"])] = r["원수사명"]
    return cohort


def _kics_index(kd_rows):
    """(원수사명, 공시분기) -> {항목번호: (값, 값_적용후)}."""
    idx = defaultdict(dict)
    for r in kd_rows:
        n = r.get("항목번호")
        if n is not None:
            idx[(r["원수사명"], r["공시분기"])][n] = (r.get("값"), r.get("값_적용후"))
    return idx


def _in_regime(q: str) -> bool:
    return q >= REGIME_START and q.endswith(("2Q", "4Q"))


def run(rs_rows, kd_rows) -> dict:
    """Pure evaluation — returns every finding list plus `gate_red`. No I/O, no printing."""
    g = _group_rs(rs_rows)
    kics = _kics_index(kd_rows)
    cohort = _disclosure_cohort(kd_rows)

    rs1, rs1_exc, rs2, rs2_exc, rs3, rs4, rs5, rs5_exc = [], [], [], [], [], [], [], []
    rs2_na = Counter()

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
                rec = (co, q, gj, c, round(rv, 2), round(expected, 2))
                (rs1_exc if (co, q, gj, c) in RS1_EXCEPTIONS else rs1).append(rec)

    # ---- RS2: base vs kics_disclosure item1/14/27 — 적용전 ↔ 값, 적용후 ↔ 값_적용후 ----
    CHK = [("지급여력금액", 1, 2.0), ("지급여력기준금액", 14, 2.0), ("지급여력비율", 27, 0.5)]
    for (co, q, gj), m in g.items():
        col = 0 if gj == "적용전" else 1
        kd = kics.get((co, q), {})
        for meas, item_no, tol in CHK:
            mr = m.get(meas)
            if not mr:
                continue
            try:
                bv = float(mr.get("base"))
            except (TypeError, ValueError):
                rs2_na[f"{gj}:base_null"] += 1
                continue
            try:
                kv = float((kd.get(item_no) or (None, None))[col])
            except (TypeError, ValueError):
                rs2_na[f"{gj}:headline_missing"] += 1
                continue
            if abs(bv - kv) > tol:
                rec = (co, q, gj, meas, round(bv, 2), round(kv, 2), round(bv - kv, 2))
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

    # ---- RS5: kics_disclosure를 정본 코호트로 삼는 census (2026-09-01) ----
    # SKIP-on-missing은 검증 무력화다 — RS1-4는 "있는 값이 맞는가"만 보고 "있어야 할 값이
    # 있는가"는 안 본다. kics_disclosure는 자체 coverage census 게이트가 있어(같은 분기
    # 회사수 완전성 보장) 정본 코호트로 쓰기 안전하다. 홀수분기 제외 근거는 모듈 docstring.
    rs_codes_by_q = defaultdict(set)
    for r in rs_rows:
        rs_codes_by_q[r["공시분기"]].add(r["원보험사코드"])
    for (code, q), name in sorted(cohort.items()):
        if not _in_regime(q):
            continue
        if code in rs_codes_by_q.get(q, set()):
            continue
        rec = (code, name, q)
        (rs5_exc if (code, q) in RS5_EXCEPTIONS else rs5).append(rec)

    # ---- RS6: phase-level census inside present buckets (2026-09-21) ----
    # RS5 stops at "the bucket exists". This walks the expected grid inside it: 2 phases x
    # 3 measures x 5 shock cells. A row whose label is outside the vocabulary is flagged rather
    # than ignored (it would look like a hole under the right label and be invisible under its
    # own), and a row whose (코드,분기) is not in the cohort is flagged as an orphan (RS5's reverse).
    g_code = defaultdict(dict)  # (코드, 분기, 경과조치) -> {measure: row}
    rs6, rs6_exc, fired_keys = [], [], set()
    for r in rs_rows:
        code, q, ph, meas = r["원보험사코드"], r["공시분기"], r["경과조치여부"], r["measure구분"]
        g_code[(code, q, ph)][meas] = r
        if ph not in PHASES or meas not in MEASURES:
            rs6.append((code, r["원수사명"], q, ph, meas, "UNKNOWN_LABEL",
                        f"경과조치여부/measure구분 not in {PHASES}/{MEASURES}"))
        elif (code, q) not in cohort:
            rs6.append((code, r["원수사명"], q, ph, meas, "ORPHAN",
                        "(코드,분기) not in kics_disclosure cohort"))
    for (code, q), name in sorted(cohort.items()):
        if not _in_regime(q) or code not in rs_codes_by_q.get(q, set()):
            continue  # RS5 territory (whole bucket absent) or outside the regime
        for ph in PHASES:
            m = g_code.get((code, q, ph), {})
            for meas in MEASURES:
                row = m.get(meas)
                if row is None:
                    rec = (code, name, q, ph, meas, "ROW_MISSING", "")
                else:
                    nulls = [c for c in SHOCK_COLS if row.get(c) is None]
                    if not nulls:
                        continue
                    rec = (code, name, q, ph, meas, "NULL_CELLS", ",".join(nulls))
                key = (code, q, ph)
                if key in RS6_KNOWN_HOLES:
                    fired_keys.add(key)
                    rs6_exc.append(rec)
                else:
                    rs6.append(rec)
    rs6_inert = sorted(RS6_KNOWN_HOLES - fired_keys)

    red_total = len(rs1) + len(rs2) + len(rs5) + len(rs6)  # exception 제외
    return {
        "groups": len(g), "companies": len(have), "gate_red": red_total,
        "rs1": rs1, "rs1_exc": rs1_exc, "rs2": rs2, "rs2_exc": rs2_exc, "rs2_na": dict(rs2_na),
        "rs3": rs3, "rs4": rs4, "rs5": rs5, "rs5_exc": rs5_exc,
        "rs6": rs6, "rs6_exc": rs6_exc, "rs6_inert": rs6_inert,
    }


def main() -> int:
    res = run(load_rs(), load_kd())
    rs1, rs1_exc, rs2, rs2_exc = res["rs1"], res["rs1_exc"], res["rs2"], res["rs2_exc"]
    rs3, rs4, rs5, rs5_exc = res["rs3"], res["rs4"], res["rs5"], res["rs5_exc"]
    rs6, rs6_exc, rs6_inert = res["rs6"], res["rs6_exc"], res["rs6_inert"]

    # ---- report ----
    print("=" * 74)
    print(f"K-ICS 금리민감도 검증  (cohort {res['companies']}사, {res['groups']} 사·분기·경과조치 그룹)")
    print("=" * 74)
    print(f"RS1_RATIO_IDENTITY (RED):  fail={len(rs1)}  (+exception {len(rs1_exc)})")
    for co, q, gj, c, rv, ev in rs1[:20]:
        print(f"   RED {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev}")
    for co, q, gj, c, rv, ev in rs1_exc:
        print(f"   EXC {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev} — 원문 자체 오류(중복인쇄), documented")
    print(f"RS2_BASE_ANCHOR (RED):  fail={len(rs2)}  (+exception {len(rs2_exc)})  "
          f"[적용전↔값 · 적용후↔값_적용후 · 대조불가 {res['rs2_na'] or 0}]")
    for co, q, gj, meas, bv, kv, df in rs2:
        print(f"   RED {co:14s} {q} {gj} {meas}: base={bv} vs disclosure={kv} (Δ{df:+})")
    for co, q, gj, meas, bv, kv, df in rs2_exc:
        print(f"   EXC {co:14s} {q} {gj} {meas}: base={bv} vs disclosure={kv} (Δ{df:+}) — basis 차이(별도/연결)·표간 불일치, documented")
    print(f"RS3_DIRECTION_SANITY (YELLOW):  flag={len(rs3)}")
    for co, q, gj, d100, b in rs3[:15]:
        print(f"   YEL {co:14s} {q} {gj}: 금리−100bp 비율 {d100} > base {b} (역방향)")
    print(f"RS4_COVERAGE_CENSUS (YELLOW):  hole={len(rs4)}")
    for co, q in rs4[:20]:
        print(f"   YEL {co:14s} {q} (regime 내 hole)")
    print(f"RS5_DISCLOSURE_COVERAGE (RED):  missing={len(rs5)}  (+exception {len(rs5_exc)})")
    for code, name, q in rs5:
        print(f"   RED {code:8s} {name:16s} {q}  in kics_disclosure but absent from rate_sensitivity")
    for code, name, q in rs5_exc:
        print(f"   EXC {code:8s} {name:16s} {q}  pre-existing gap, not this session's scope, documented")
    print(f"RS6_PHASE_LEVEL_CENSUS (RED):  hole={len(rs6)}  (+known/routed {len(rs6_exc)} rows in "
          f"{len({(r[0], r[2], r[3]) for r in rs6_exc})} (코드,분기,phase) keys)  inert={len(rs6_inert)}")
    for code, name, q, ph, meas, kind, det in rs6:
        print(f"   RED {code:8s} {name:16s} {q} {ph} {meas}: {kind} {det}")
    for code, name, q, ph, meas, kind, det in rs6_exc:
        print(f"   EXC {code:8s} {name:16s} {q} {ph} {meas}: {kind} {det} — pre-existing, routed to parser-kics (RS6_KNOWN_HOLES)")
    for code, q, ph in rs6_inert:
        print(f"   YEL {code:8s} {q} {ph}: RS6_KNOWN_HOLES entry no longer fires — remove it (inert exception)")

    red_total = res["gate_red"]
    print()
    print("#" * 74)
    print(f"SUMMARY  RS1:{len(rs1)}RED(+{len(rs1_exc)}exc) | RS2:{len(rs2)}RED(+{len(rs2_exc)}exc) | "
          f"RS3:{len(rs3)}Y | RS4:{len(rs4)}Y | RS5:{len(rs5)}RED(+{len(rs5_exc)}exc) | "
          f"RS6:{len(rs6)}RED(+{len(rs6_exc)}known,{len(rs6_inert)}inert) | gate RED={red_total}")
    print("#" * 74)

    out = ROOT / "data" / "_derived" / "kics_rate_sensitivity_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    RS2_KEYS = ["회사", "분기", "경과조치", "measure", "base", "disclosure", "diff"]
    RS6_KEYS = ["코드", "회사", "분기", "경과조치", "measure", "kind", "detail"]
    out.write_text(json.dumps({
        "_meta": {"groups": res["groups"], "companies": res["companies"], "gate_red": red_total,
                  "rs2_not_comparable": res["rs2_na"]},
        "RS1_ratio_identity": [dict(zip(["회사", "분기", "경과조치", "컬럼", "비율", "expected"], r)) for r in rs1],
        "RS1_exceptions": [dict(zip(["회사", "분기", "경과조치", "컬럼", "비율", "expected"], r)) for r in rs1_exc],
        "RS2_base_anchor": [dict(zip(RS2_KEYS, r)) for r in rs2],
        "RS2_exceptions": [dict(zip(RS2_KEYS, r)) for r in rs2_exc],
        "RS3_direction": [dict(zip(["회사", "분기", "경과조치", "m100bp", "base"], r)) for r in rs3],
        "RS4_coverage_hole": [dict(zip(["회사", "분기"], r)) for r in rs4],
        "RS5_disclosure_coverage_missing": [dict(zip(["코드", "회사", "분기"], r)) for r in rs5],
        "RS5_exceptions": [dict(zip(["코드", "회사", "분기"], r)) for r in rs5_exc],
        "RS6_phase_level_holes": [dict(zip(RS6_KEYS, r)) for r in rs6],
        "RS6_known_holes_routed": [dict(zip(RS6_KEYS, r)) for r in rs6_exc],
        "RS6_known_holes_inert": [dict(zip(["코드", "분기", "경과조치"], r)) for r in rs6_inert],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if red_total == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
