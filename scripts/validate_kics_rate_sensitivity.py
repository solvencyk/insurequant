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
RS6_KNOWN_HOLES below — each with the raw evidence or the routing ticket. Since 2026-10-10 new RS1·RS5
registrations go to the **pinned** device (`_RS1_ISSUER_INCONSISTENT` · `_RS5_SOURCE_ABSENT`,
`rs_pinned_exemptions`) that re-checks cells·residual·raw sha·manifest·evidence ledger every run and turns
a broken or no-longer-needed registration back into RED (`RS_EXEMPTION_*`, counted in gate RED).

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

# ---------------------------------------------------------------------------
# 근거 박제형 면제 장치 — 룰 RS1(발행사 자기모순) · RS5(원천 부재)  (owner 승인 2026-10-10, 재보사 단계 10)
# ---------------------------------------------------------------------------
# 위 세 등재부(RS1/RS2/RS5_EXCEPTIONS)는 **키 집합**이다 — 등재된 키는 근거 재확인 없이 영원히 빠진다.
# 재보사 단계 11 뒤 남은 RED 5건(제네럴 2026.2Q +100bp 비율 인쇄 자기모순 2 · 마이브라운 「해당사항
# 없음」 3)은 값을 만들 수 없는 칸이지만, 같은 방식으로 넣으면 셀이 바뀌거나 새 문서가 들어와도 아무도
# 모른다. 그래서 K-ICS 게이트의 `_IDENT_ISSUER_INCONSISTENT`(잔차·입력 셀 박제)·`_CENSUS_SOURCE_ABSENT`
# (raw sha·매니페스트·근거 원장 재확인)와 같은 사상으로 **매 실행 재검산**한다. 통째 skip 이 아니다.
#   등재 키 = (원보험사코드, 공시분기). 등재부 이름 = 근거 원장(`data/_gold/kics_exemption_provenance.json`)
#   의 `registry`. K-ICS 게이트 `_exemption_registries()`·`_code_pin_map()` 에도 등록돼 있어 원장 기록이
#   없거나 원장 박제가 코드와 다르면 K-ICS 게이트·데이터계약 게이트가 **한 겹 더** 막는다.
# 매 실행 확인(하나라도 깨지면 그 버킷은 면제되지 않고 원래 RED 그대로 + 장치 RED `RS_EXEMPTION_*`):
#   ① 형식 — 사유 종류·승인일·raw 박제·(RS1) 박제 셀이 잔차의 입력 3칸을 다 덮는가        → MALFORMED
#   ② 아직 필요한가 — 박제한 RED 가 지금도 발화하는가. 안 하면 「등재를 풀어라」 RED          → INERT
#      (review 가 아닌 이유: 남겨 두면 그 칸이 나중에 다시 깨질 때 이 등재가 조용히 덮는다)
#   ③ (RS1) 입력 셀(비율·금액·기준금액)이 박제값 그대로인가 · 잔차(비율 − 금액/기준금액×100)가 박제값
#      ±0.01 인가                                                  → CELL_MISSING / CELL_DRIFT / RESIDUAL_DRIFT
#   ④ raw 폴더 `data/disclosure/FY{Y}_Q{n}/raw/{code}[._]*` 파일 집합·sha256 == 박제(새 판이 들어오면 다시
#      판정할 차례)와 다운로더 매니페스트 그 분기 항목(status ok · sha 일치 · 새 판 없음)   → RAW_CHANGED / MANIFEST_DRIFT
#   ⑤ 근거 원장 — VERIFIED · claim_kind == 사유 종류 · (RS1) expected_residual == 코드 박제 · 인용 원천을
#      **게이트가 다시 열어** present/absent 마커 재확인                                   → LEDGER_DISAGREE
# raw·매니페스트·마커 재확인은 K-ICS 게이트의 같은 함수(`_census_raw_state`·`_census_manifest_entry`·
# `_verify_absent_markers`)를 부른다 — 판정 기준이 두 게이트에서 갈리지 않게.
# 면제된 칸은 조용해지지 않는다: 매 실행 「박제 면제」 줄로 인쇄하고 산출 JSON 에도 남긴다.
_RS_PIN_TOL = 0.01
_RS_EXEMPT_KINDS = {
    "_RS1_ISSUER_INCONSISTENT": {"ISSUER_INCONSISTENT"},
    # SECTION_ABSENT: 위험관리 절이 「해당사항 없음」으로 끝나고 민감도 절(6-8) 자체가 없다.
    # STATED_NOT_APPLICABLE: 민감도 절에 「금리 민감도 분석 : 해당사항 없음」이 인쇄돼 있다.
    "_RS5_SOURCE_ABSENT": {"SECTION_ABSENT", "STATED_NOT_APPLICABLE"},
}

# RS1 — 발행사 표 안 자기모순. 공시 그대로 두고 잔차를 박제한다(owner 결정 2026-10-10 10-① 과 같은 원칙).
# `cells` 키 "경과조치|measure|컬럼", `findings` 키 "RS1|경과조치|컬럼" → 잔차(비율 − 금액/기준금액×100).
_RS1_ISSUER_INCONSISTENT: dict[tuple[str, str], dict] = {
    # 제네럴재보험 KR1103 2026.2Q +100bp — raw FY2026_Q2 p16 「2) 금리민감도 분석」 두 블록(경과조치 전·후,
    # 비적용사라 같은 숫자)이 지급여력금액 856 · 지급여력기준금액 270 · 지급여력비율 319.78 을 인쇄한다.
    # 856/270×100 = 317.04 (Δ2.74, 허용 1.60). 서술문 「100bp상승시 25%p 상승」은 비율 행(319.78 − 294.19)과
    # 맞고, 금액·기준금액 행은 정수 억원이라 어긋난다. 나머지 4개 컬럼은 허용 안(최대 Δ0.44).
    ("KR1103", "2026.2Q"): {
        "kind": "ISSUER_INCONSISTENT", "approved": "owner 2026-10-10",
        "raw": {"data/disclosure/FY2026_Q2/raw/KR1103_제네럴재보험.pdf":
                "df75fb630ac5e7b22728779e4cdf07689d9465cf22ba6b52655a9d112c63f6e9"},
        "cells": {"적용전|지급여력비율|+100bp": 319.78, "적용전|지급여력금액|+100bp": 856.0,
                  "적용전|지급여력기준금액|+100bp": 270.0,
                  "적용후|지급여력비율|+100bp": 319.78, "적용후|지급여력금액|+100bp": 856.0,
                  "적용후|지급여력기준금액|+100bp": 270.0},
        "findings": {"RS1|적용전|+100bp": 2.743, "RS1|적용후|+100bp": 2.743},
    },
}

# RS5 — 그 분기 문서는 있는데 금리민감도 표가 원천에 없다(마이브라운 KR1108, 2025년 6월 본인가 신설사).
# 근거: parser 단계 11 런로그 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_11.md` §1.4, validation
# 단계 10 fitz 재확인(문서 전체 「100bp」 0회).
_RS5_SOURCE_ABSENT: dict[tuple[str, str], dict] = {
    # p17 「Ⅵ. 위험관리 6-1~6-4 : 해당사항 없음」으로 절이 끝나고 6-8 절이 없다. 문서 전체 「민감도」 0회.
    ("KR1108", "2025.2Q"): {
        "kind": "SECTION_ABSENT", "approved": "owner 2026-10-10",
        "raw": {"data/disclosure/FY2025_Q2/raw/KR1108_마이브라운반려동물전문보험.pdf":
                "b76a53d5a06c980324eb7c1518a7195bc7d1cd6558f4463dd9d387e1367eeed7"}},
    # p50 「6-8. 위험 민감도 … 2) 금리 민감도 분석 : 해당사항 없음」.
    ("KR1108", "2025.4Q"): {
        "kind": "STATED_NOT_APPLICABLE", "approved": "owner 2026-10-10",
        "raw": {"data/disclosure/FY2025_Q4/raw/KR1108_마이브라운반려동물전문보험.pdf":
                "d15809306d91bf32ae3c82db44e05a83f320cbefb7b4efcef815bca2b3f0ee7a"}},
    # p34 같은 문구.
    ("KR1108", "2026.2Q"): {
        "kind": "STATED_NOT_APPLICABLE", "approved": "owner 2026-10-10",
        "raw": {"data/disclosure/FY2026_Q2/raw/KR1108_마이브라운반려동물전문보험.pdf":
                "b6fd31d4c395f0abe65ce3c74bf49ce394083cdc25d87bb1545f570b0a8127a4"}},
}

# 근거 원장 registry 이름 → 등재부. K-ICS 게이트 `_exemption_registries()` 가 이 dict 를 읽는다.
RS_EXEMPTION_REGISTRIES = {"_RS1_ISSUER_INCONSISTENT": _RS1_ISSUER_INCONSISTENT,
                           "_RS5_SOURCE_ABSENT": _RS5_SOURCE_ABSENT}


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


def _kd_gate():
    """K-ICS 게이트 모듈(같은 raw·매니페스트·마커 함수를 쓰려고). 지연 import — 그쪽도 이 모듈을
    지연 import 하므로 순환이 생기지 않는다."""
    import validate_kics_disclosure as kd_gate  # noqa: PLC0415
    return kd_gate


def _rs_ledger_problems(entry: dict | None, registry: str, kind: str,
                        pins: dict | None = None) -> list[str]:
    """근거 원장 한 건 → 문제 목록(빈 목록이면 통과). ⑤ 의 본체."""
    if entry is None:
        return [f"근거 원장에 registry {registry} 기록이 없다"]
    g = _kd_gate()
    probs = []
    if entry.get("status") != "VERIFIED":
        probs.append(f"status={entry.get('status')!r}")
    if entry.get("claim_kind") != kind:
        probs.append(f"claim_kind {entry.get('claim_kind')!r} ≠ 코드 {kind!r}")
    if pins is not None:
        have = entry.get("expected_residual") or {}
        if set(have) != set(pins):
            probs.append(f"expected_residual 축 목록 {sorted(have)} ≠ 코드 {sorted(pins)}")
        for k in sorted(set(have) & set(pins)):
            try:
                if abs(float(have[k]) - float(pins[k])) > _RS_PIN_TOL:
                    probs.append(f"expected_residual {k}: 원장 {have[k]} ≠ 코드 {pins[k]}")
            except (TypeError, ValueError):
                probs.append(f"expected_residual {k}: 원장 {have[k]!r} 숫자 아님")
    v = entry.get("verify") or {}
    if not g._verify_markers_ran(v):
        probs.append("verify 마커가 대조되지 않았다(파일 부재 또는 마커 없음)")
    else:
        contradicted, why = g._verify_absent_markers(v)
        if contradicted:
            probs.append(f"인용 원천 재확인 실패 — {why}")
    return probs


def _rs_raw_manifest_problems(code: str, q: str, raw_pin: dict, root=None) -> list[tuple[str, str]]:
    """④ raw 폴더·다운로더 매니페스트 → [(rule, detail)]. K-ICS census 장치와 같은 함수를 쓴다."""
    g = _kd_gate()
    out = []
    have = g._census_raw_state(code, q, root)
    if have is None:
        return [("RS_EXEMPTION_MALFORMED", f"분기 문자열 {q!r} 해석 불가")]
    if have != raw_pin:
        new = sorted(set(have) - set(raw_pin))
        gone = sorted(set(raw_pin) - set(have))
        moved = sorted(p for p in set(have) & set(raw_pin) if have[p] != raw_pin[p])
        out.append(("RS_EXEMPTION_RAW_CHANGED",
                    f"raw 폴더가 박제와 다르다 — 새 파일 {new} · 사라진 파일 {gone} · sha 바뀜 {moved}. "
                    "새 판이 들어왔거나 바뀌었다 — 다시 판정하고 등재를 고쳐라"))
    entry, why = g._census_manifest_entry(code, q, root)
    if entry is None:
        out.append(("RS_EXEMPTION_MANIFEST_DRIFT", why))
    else:
        probs = []
        if entry.get("status") != "ok":
            probs.append(f"status {entry.get('status')!r} ≠ 'ok'")
        f = str(entry.get("file") or "")
        if f not in raw_pin:
            probs.append(f"매니페스트 file {f!r} 가 raw 박제에 없다")
        elif entry.get("sha256") != raw_pin[f]:
            probs.append(f"매니페스트 sha256 {str(entry.get('sha256'))[:12]}… ≠ 박제")
        if entry.get("versions"):
            probs.append(f"새 판 {len(entry['versions'])}건이 매니페스트에 기록됐다")
        if probs:
            out.append(("RS_EXEMPTION_MANIFEST_DRIFT", " · ".join(probs)))
    return out


def rs_pinned_exemptions(rs_rows, rs1, rs5, *, ledger=None, root=None,
                         rs1_registry=None, rs5_registry=None) -> dict:
    """RS1·RS5 박제 면제 장치(위 블록 주석 ①~⑤). 매 실행 재검산.

    입력 rs1/rs5 = 기존 등재부를 거친 뒤의 RED 목록(run() 내부 형식). 반환 dict:
      rs1_kept / rs5_kept   — 여전히 RED 인 것(등재 안 됐거나 재검산 실패)
      rs1_pinned / rs5_pinned — 면제된 RED(+ 박제·실측) — 매 실행 인쇄용
      red    — 장치 RED [{rule, code, quarter, registry, detail}] (gate RED 에 더한다)
      detail — RS1 박제 대조 (code, name, quarter, key, pinned, actual, delta)
    `ledger=None` 이면 근거 원장 파일을 읽는다. 등재부 인자는 변이시험용."""
    reg1 = _RS1_ISSUER_INCONSISTENT if rs1_registry is None else rs1_registry
    reg5 = _RS5_SOURCE_ABSENT if rs5_registry is None else rs5_registry
    out = {"rs1_kept": list(rs1), "rs5_kept": list(rs5), "rs1_pinned": [], "rs5_pinned": [],
           "red": [], "detail": []}
    if not reg1 and not reg5:
        return out
    g = _kd_gate()
    if ledger is None:
        ledger = g._load_exemption_ledger()
    led = {}
    if isinstance(ledger, dict) and not ledger.get("_unreadable"):
        for e in ledger.get("entries") or []:
            if isinstance(e, dict) and e.get("registry") in RS_EXEMPTION_REGISTRIES:
                led[(e.get("registry"), e.get("company"), e.get("quarter"))] = e
    rows_by = {}
    name_of = {}
    for r in rs_rows:
        name_of[r.get("원보험사코드")] = r.get("원수사명")
        rows_by[(r.get("원보험사코드"), r.get("공시분기"), r.get("경과조치여부"), r.get("measure구분"))] = r

    def _red(rule, reg, c, q, detail):
        out["red"].append({"rule": rule, "registry": reg, "code": c, "quarter": q, "detail": detail})

    def _shape_ok(reg, c, q, spec, kinds):
        kind, raw_pin = (spec or {}).get("kind"), (spec or {}).get("raw")
        if kind not in kinds or not (spec or {}).get("approved") or not isinstance(raw_pin, dict) \
                or not raw_pin:
            _red("RS_EXEMPTION_MALFORMED", reg, c, q,
                 f"사유 종류 {kind!r}(허용 {sorted(kinds)}) · 승인 {(spec or {}).get('approved')!r} · "
                 f"raw 박제 {'있음' if raw_pin else '없음'} — 원천 문서 sha 를 박제해야 한다")
            return False
        return True

    # ---- RS1 ----
    reg_name = "_RS1_ISSUER_INCONSISTENT"
    exempt_keys = set()
    for (c, q), spec in sorted(reg1.items()):
        if not _shape_ok(reg_name, c, q, spec, _RS_EXEMPT_KINDS[reg_name]):
            continue
        cells, pins = spec.get("cells") or {}, spec.get("findings") or {}
        nm = name_of.get(c, c)
        broken = False
        keys = []
        for key in sorted(pins):
            rid, ph, col = (key.split("|") + ["", "", ""])[:3]
            need = [f"{ph}|{m}|{col}" for m in MEASURES]
            if rid != "RS1" or ph not in PHASES or col not in SHOCK_COLS or any(n not in cells for n in need):
                _red("RS_EXEMPTION_MALFORMED", reg_name, c, q,
                     f"'{key}' — 'RS1|경과조치|컬럼' 이어야 하고 cells 가 그 칸의 비율·금액·기준금액을 다 덮어야 한다")
                broken = True
                continue
            keys.append((key, ph, col))
        if not pins:
            _red("RS_EXEMPTION_MALFORMED", reg_name, c, q, "findings 가 비었다")
            broken = True
        for ck, pinned in sorted(cells.items()):
            ph, meas, col = (ck.split("|") + ["", "", ""])[:3]
            row = rows_by.get((c, q, ph, meas))
            actual = None if row is None else row.get(col)
            if actual is None:
                _red("RS_EXEMPTION_CELL_MISSING", reg_name, c, q,
                     f"{ck} 결측 — 박제값 {pinned} 확인 불가. 결측은 SKIP 이 아니라 RED 다")
                broken = True
            elif abs(float(actual) - float(pinned)) > _RS_PIN_TOL:
                _red("RS_EXEMPTION_CELL_DRIFT", reg_name, c, q,
                     f"{ck} 박제 {pinned} -> 실측 {actual} — owner 판단의 전제(공시 그대로)가 바뀌었다")
                broken = True
        for key, ph, col in keys:
            fired = any(r[0] == nm and r[1] == q and r[2] == ph and r[3] == col for r in rs1)
            if not fired:
                _red("RS_EXEMPTION_INERT", reg_name, c, q,
                     f"{key} 에 RS1 RED 가 없다 — 데이터가 닫혔거나 허용오차가 바뀌었다. 등재를 풀어라 "
                     "(남겨 두면 그 칸이 다시 깨질 때 조용히 덮는다)")
                broken = True
                continue
            try:
                rv = float(rows_by[(c, q, ph, "지급여력비율")][col])
                av = float(rows_by[(c, q, ph, "지급여력금액")][col])
                bv = float(rows_by[(c, q, ph, "지급여력기준금액")][col])
                actual = rv - av / bv * 100.0
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                actual = None
            out["detail"].append((c, nm, q, key, pins[key], None if actual is None else round(actual, 4),
                                  None if actual is None else round(actual - pins[key], 4)))
            if actual is None or abs(actual - float(pins[key])) > _RS_PIN_TOL:
                _red("RS_EXEMPTION_RESIDUAL_DRIFT", reg_name, c, q,
                     f"{key} 박제 {pins[key]} -> 실측 {actual if actual is None else round(actual, 4)} "
                     f"(tol {_RS_PIN_TOL}) — 면제 무효")
                broken = True
        for rule, det in _rs_raw_manifest_problems(c, q, spec["raw"], root):
            _red(rule, reg_name, c, q, det)
            broken = True
        probs = _rs_ledger_problems(led.get((reg_name, c, q)), reg_name, spec["kind"], pins=pins)
        if probs:
            _red("RS_EXEMPTION_LEDGER_DISAGREE", reg_name, c, q, " · ".join(probs))
            broken = True
        if not broken:
            exempt_keys |= {(nm, q, ph, col) for _k, ph, col in keys}
    out["rs1_kept"] = [r for r in rs1 if (r[0], r[1], r[2], r[3]) not in exempt_keys]
    out["rs1_pinned"] = [r for r in rs1 if (r[0], r[1], r[2], r[3]) in exempt_keys]

    # ---- RS5 ----
    reg_name = "_RS5_SOURCE_ABSENT"
    fired5 = {(r[0], r[2]) for r in rs5}
    ok5 = {}
    for (c, q), spec in sorted(reg5.items()):
        if not _shape_ok(reg_name, c, q, spec, _RS_EXEMPT_KINDS[reg_name]):
            continue
        if (c, q) not in fired5:
            _red("RS_EXEMPTION_INERT", reg_name, c, q,
                 "RS5 가 이 (회사,분기)를 결측으로 세지 않는다(금리민감도 행이 생겼거나 코호트가 바뀌었다) — "
                 "등재를 풀어라(남겨 두면 그 버킷이 다시 사라질 때 조용히 덮는다)")
            continue
        broken = False
        for rule, det in _rs_raw_manifest_problems(c, q, spec["raw"], root):
            _red(rule, reg_name, c, q, det)
            broken = True
        probs = _rs_ledger_problems(led.get((reg_name, c, q)), reg_name, spec["kind"])
        if probs:
            _red("RS_EXEMPTION_LEDGER_DISAGREE", reg_name, c, q, " · ".join(probs))
            broken = True
        if not broken:
            ok5[(c, q)] = (spec["kind"], spec["approved"])
    out["rs5_kept"] = [r for r in rs5 if (r[0], r[2]) not in ok5]
    out["rs5_pinned"] = [r + ok5[(r[0], r[2])] for r in rs5 if (r[0], r[2]) in ok5]
    return out


def run(rs_rows, kd_rows, *, ledger=None, root=None, rs1_registry=None, rs5_registry=None) -> dict:
    """Evaluation — returns every finding list plus `gate_red`. No printing. Pure over the two
    master row lists except the RS1·RS5 pinned-exemption device, which re-reads the evidence
    ledger, raw sha and downloader manifest every run (pass `ledger=`/registries to override)."""
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

    # ---- RS1·RS5 근거 박제 면제 장치 (2026-10-10) — 재검산 통과분만 RED 목록에서 뺀다 ----
    pin = rs_pinned_exemptions(rs_rows, rs1, rs5, ledger=ledger, root=root,
                               rs1_registry=rs1_registry, rs5_registry=rs5_registry)
    rs1, rs5, pin_red = pin["rs1_kept"], pin["rs5_kept"], pin["red"]

    red_total = len(rs1) + len(rs2) + len(rs5) + len(rs6) + len(pin_red)  # exception 제외, 깨진 등재 포함
    return {
        "groups": len(g), "companies": len(have), "gate_red": red_total,
        "rs1": rs1, "rs1_exc": rs1_exc, "rs2": rs2, "rs2_exc": rs2_exc, "rs2_na": dict(rs2_na),
        "rs3": rs3, "rs4": rs4, "rs5": rs5, "rs5_exc": rs5_exc,
        "rs6": rs6, "rs6_exc": rs6_exc, "rs6_inert": rs6_inert,
        "rs1_pinned": pin["rs1_pinned"], "rs5_pinned": pin["rs5_pinned"],
        "pin_red": pin_red, "pin_detail": pin["detail"],
    }


def main() -> int:
    res = run(load_rs(), load_kd())
    rs1, rs1_exc, rs2, rs2_exc = res["rs1"], res["rs1_exc"], res["rs2"], res["rs2_exc"]
    rs3, rs4, rs5, rs5_exc = res["rs3"], res["rs4"], res["rs5"], res["rs5_exc"]
    rs6, rs6_exc, rs6_inert = res["rs6"], res["rs6_exc"], res["rs6_inert"]
    rs1_pin, rs5_pin, pin_red = res["rs1_pinned"], res["rs5_pinned"], res["pin_red"]

    # ---- report ----
    print("=" * 74)
    print(f"K-ICS 금리민감도 검증  (cohort {res['companies']}사, {res['groups']} 사·분기·경과조치 그룹)")
    print("=" * 74)
    print(f"RS1_RATIO_IDENTITY (RED):  fail={len(rs1)}  (+exception {len(rs1_exc)})")
    for co, q, gj, c, rv, ev in rs1[:20]:
        print(f"   RED {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev}")
    for co, q, gj, c, rv, ev in rs1_exc:
        print(f"   EXC {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev} — 원문 자체 오류(중복인쇄), documented")
    pin_by = {(nm, q, key): (pinned, act, d) for _c, nm, q, key, pinned, act, d in res["pin_detail"]}
    for co, q, gj, c, rv, ev in rs1_pin:
        pinned, act, d = pin_by.get((co, q, f"RS1|{gj}|{c}"), (None, None, None))
        print(f"   PIN {co:14s} {q} {gj} [{c}] 비율={rv} ≠ 금액/기준={ev} — 발행사 자기모순 박제 잔차 "
              f"{pinned} · 실측 {act} (Δ{d}) · 근거 재확인 통과 (_RS1_ISSUER_INCONSISTENT, owner 2026-10-10)")
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
    for code, name, q, kind, appr in rs5_pin:
        print(f"   PIN {code:8s} {name:16s} {q}  원천 부재({kind}) — raw sha·매니페스트·근거 원장 재확인 통과 "
              f"(_RS5_SOURCE_ABSENT, {appr})")
    print(f"RS1·RS5 박제 면제 장치 (RED):  깨진 등재={len(pin_red)}  · 박제 면제 RS1 {len(rs1_pin)}칸 · "
          f"RS5 {len(rs5_pin)}버킷")
    for f in pin_red:
        print(f"   RED {f['rule']} [{f['registry']}] {f['code']} {f['quarter']}: {f['detail']}")
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
          f"RS6:{len(rs6)}RED(+{len(rs6_exc)}known,{len(rs6_inert)}inert) | "
          f"PIN:{len(pin_red)}RED(+{len(rs1_pin)}rs1,{len(rs5_pin)}rs5) | gate RED={red_total}")
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
        "RS1_pinned_exemptions": [dict(zip(["회사", "분기", "경과조치", "컬럼", "비율", "expected"], r))
                                  for r in rs1_pin],
        "RS5_pinned_exemptions": [dict(zip(["코드", "회사", "분기", "kind", "approved"], r)) for r in rs5_pin],
        "RS_pin_device_red": pin_red,
        "RS_pin_detail": [dict(zip(["코드", "회사", "분기", "key", "pinned", "actual", "delta"], r))
                          for r in res["pin_detail"]],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if red_total == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
