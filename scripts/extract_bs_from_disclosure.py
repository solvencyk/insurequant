#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""17BS 경영공시 백필 오케스트레이터 (2026-09-11, inbox/parser/20260911T0109Z).

data/disclosure(정기경영공시 raw PDF)에서 IFRS17_BS.json 의 21개 항목을 뽑아
data/_derived/bs_from_disclosure_parts/<KR코드>.json 에 회사별로 적재한다. 마스터/오버라이드
파일은 이 스크립트가 건드리지 않는다 -- 반영은 별도 병합 스크립트가 셀 단위 UPSERT 로 한다
(동시 세션 lost-update 방지, CLAUDE.md 불변식).

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_bs_from_disclosure.py --company KR1010
  ... --company KR1010,KR0051,KR1098          (콤마로 여러 회사)
  ... --company all                            (TIER2 15개사 전부)
  ... --validate                                (비순환 검증: TIER-1 회사 x 중간분기 x 항목1/2/3)

## 방법 요지

1. 표 하나 = 단위 하나. 항목1(안 되면 2, 3)의 raw 값을 그 회사의 가장 가까운 기존
   관측치(마스터 또는 이미 이번 실행에서 채택된 값)와 맞춰 표 전체의 배율을 한 번만 정한다
   (`common.resolve_table_scale`).
2. 코어(1/2/3) 산술검산(1==2+3)이 그 분기·그 표 전체의 품질 게이트다 -- 실패하면 그 표에서는
   아무것도(항목4·세부항목 포함) 신뢰하지 않는다.
3. 세부항목(10~31, 코어 제외)은 라벨이 맞아도 회사가 그 개념을 마스터와 다르게 담을 수 있어
   (항목13 상각후원가측정 부모/자식 혼재, 항목24 기타부채 뭉침배수 변동 등, 조사 20260911),
   그 회사의 실제 Q4(마스터에 이미 DART 원천 값이 있다)에서 같은 방법으로 재현되는지 먼저
   검사한다(`calibrate_detail_items`). 통과한 (회사,항목) 만 나머지 분기에 적용한다.
4. 법정준비금 5~8 은 이미 검증된 reserve.py(=기존 프로브)를 그대로 쓰고, **마스터에 이미 값이
   있는 셀은 건드리지 않는다**(이 백필은 결측 채우기 전용 -- 84th/85th pass 가 이미 다듬은
   값을 재작업하지 않는다).
5. QoQ ±30% 초과는 hold(스킵+사유). 애매하면 전부 skip_reason 을 남기고 빈 칸으로 둔다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.bs_disclosure import common, reserve  # noqa: E402
from scripts.build_equity_composition_tier2 import TIER2  # noqa: E402
from _quarter_horizon import quarter_range, latest_quarter  # noqa: E402

PARTS_DIR = ROOT / "data" / "_derived" / "bs_from_disclosure_parts"
PARTS_DIR.mkdir(parents=True, exist_ok=True)

# 항목1(자산총계)만 무조건 신뢰한다 -- 분류경계 이슈가 없고(반대말이 없다) 축척 기준점이다.
# **항목2/3(부채·자본총계)는 코어인데도 보정게이트를 받는다 -- 2026-09-11 비순환 검증
# 실측으로 이유가 확인됐다**: TIER-1(DART 직접 대조 가능) KR0070/KR0071 두 회사에서 경영공시
# 표의 부채총계/자본총계가 마스터(DART)와 각각 -1~2% / +15~23% 어긋났다(예: KR0070
# 2023.1Q 부채 15,901,502 vs 마스터 16,096,704, 자본 1,045,052 vs 890,288 -- 신종자본증권류
# 하이브리드 자본상품의 부채/자본 분류가 두 원천에서 다른 것으로 보인다). **항등식(1=2+3)은
# 이 오류를 못 잡는다** -- 같은 합계 안에서 2<->3 로 값이 옮겨가므로 자산총계 쪽 identity는
# 그대로 닫힌다. 그래서 항목2/3도 항목10~31과 같은 Q4 재현검사를 거친다.
CORE_ANCHOR_ITEM = 1
CALIBRATED_ITEMS = (2, 3, 4, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31)
# 그 회사의 마스터에 이 항목이 **한 번도 없어서** 애초에 Q4 로 재현검사할 대상이 없는 경우
# (예: KR1010 항목31 -- 마스터에 행 자체가 없다), 통째로 막으면 티켓이 요구하는 "원문에
# 있는 항목은 전부 넣는다"를 못 지킨다(owner 확정 1번). 그래서 **라벨이 단일개념이라 애매할
# 여지가 적은 항목만** 이 경우에 한해 미검증으로 통과시킨다("방법"에 unverified 로 표시해
# 최종 보고에서 구분되게 한다). 항목2/3(위 실측으로 위험 확인)·13(부모/자식 혼재)·
# 20/21(흡수 관계)·24(뭉침배수 변동)·22/23(희귀해 검증사례 없음)은 **여기 없다** -- Q4 앵커가
# 하나도 없으면 그냥 스킵한다.
SAFE_WHEN_UNTESTED_ITEMS = frozenset({4, 10, 11, 12, 14, 15, 30, 31})
# 백필 대상(TIER2 15개사 + 분기공시사 5개사) 중 손해보험사(kics_disclosure.json 생손보여부
# 실측) -- 항목8(보증준비금)은 이 회사들에겐 개념 자체가 없다(R_RSV_8 가드, build_ifrs17_bs.py
# 의 동일 로직). KR0002 한화손해·KR0005 흥국화재는 2026-09-11 범위 확대(분기공시사 5개사
# 포함, owner 정정)로 추가.
NONLIFE_TIER2 = frozenset({"KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR1098",
                           "KR0002", "KR0005"})
FLOOR = "2023.1Q"
FORBIDDEN_QUARTERS = {"2021.4Q", "2022.4Q"}  # IFRS4<->17 경계, owner 금지(되묻지 않음)


def target_quarters_for(kr: str, known: dict) -> list[str]:
    hi = latest_quarter(floor=FLOOR)
    horizon = [q for q in quarter_range(FLOOR, hi) if q not in FORBIDDEN_QUARTERS]
    # 코어 3항목(1/2/3) 이 **전부** 있어야 "이미 됨" 이다 -- 항목1 만 확인하던 종전 로직은
    # 실측(2026-09-11 round2): KR1010 2023.1Q~2024.2Q 는 항목1·2 는 이미 있고 항목3(자본총계,
    # 유상증자로 QoQ 가드에 걸려 1라운드에서 hold)만 빠져 있었는데, 항목1 만 보고 "이미 채움"
    # 으로 판정해 재처리 대상에서 **조용히 제외**됐다 -- 티켓이 이름을 짚어 요구한 케이스가
    # 바로 이 사각이었다.
    have1 = set((known.get((kr, 1)) or {}).keys())
    have2 = set((known.get((kr, 2)) or {}).keys())
    have3 = set((known.get((kr, 3)) or {}).keys())
    have_core = have1 & have2 & have3
    return [q for q in horizon if q not in have_core]


def calibrate_detail_items(kr: str, known: dict) -> tuple[dict[int, dict[str, str]], set[int], bool]:
    """세부항목(10~31)을 그 회사의 실제 Q4 **전부**에서 재현 검사해, 항목별로
    {q4: convention} 을 돌려준다(회사 전체에 컨벤션 하나를 고정하지 않는다 -- 조사 20260911
    실측: 항목13 은 2025년 계정명 변경으로 같은 회사도 시기에 따라 '자식 개별' vs '자식합'
    이 갈린다. 적용은 caller 가 목표분기에 **가장 가까운** Q4 의 컨벤션을 쓴다).

    두번째 반환값 `tested`: 마스터에 그 항목의 Q4 앵커가 **한 번이라도 있어서** 실제로
    검사가 된 항목 집합 -- 이게 비어 있으면 "검사했는데 실패"가 아니라 "검사할 대상 자체가
    없었다"는 뜻이라 caller 가 다르게 취급한다(SAFE_WHEN_UNTESTED_ITEMS 참조).

    세번째 반환값 `q4_table_found`: 이 회사의 Q4 경영공시 **어느 한 곳에서라도** 별도BS 표를
    찾았는지. False 면 "검사했는데 항목이 안 맞았다"가 아니라 **애초에 대조할 표 자체가
    없었다**는 뜻이다(실측 2026-09-11: KR0051 등 일부 회사는 연차 경영공시 본문이
    "감사보고서·재무상태표·...등은 첨부파일 참조"뿐이라 Q4 에는 표가 없고, 중간분기에만
    본문 표가 실린다 -- Q4 만 보고 "이 회사는 위험"이라 판정하면 안 된다). caller 는 이
    신호로 항목2/3 의 안전-미검증 허용 여부를 그 회사 단위로 넓힌다."""
    result: dict[int, dict[str, str]] = {}
    tested: set[int] = set()
    q4_table_found = False
    q4s = sorted(q for q in (known.get((kr, 1)) or {}) if q.endswith(".4Q"))
    for q4 in q4s:
        pdf = common.pick_pdf(q4, kr)
        if pdf is None:
            continue
        table = common.best_bs_table(pdf)
        if table is None:
            continue
        q4_table_found = True
        rows, groups, page_idx = table
        extracted = common.extract_row_values(rows, groups)
        scale = common.resolve_table_scale(extracted["items"], known, kr, q4)
        if scale is None:
            continue
        factor, _unit, _anchor = scale
        for item in CALIBRATED_ITEMS:
            master_v = (known.get((kr, item)) or {}).get(q4)
            if master_v is None:
                continue
            tested.add(item)
            tol = max(common.IDENTITY_TOL_ABS, common.IDENTITY_TOL_REL * abs(master_v))
            if item == 13:
                for conv, raw in common.amort_candidates(extracted).items():
                    if abs(raw * factor - master_v) <= tol:
                        result.setdefault(item, {})[q4] = conv
                        break
                continue
            raw = extracted["items"].get(item)
            if raw is not None and abs(raw * factor - master_v) <= tol:
                result.setdefault(item, {})[q4] = "direct"
    return result, tested, q4_table_found


def _qoq_gate(known: dict, kr: str, item: int, q: str, v: float) -> tuple[bool, str | None]:
    """(ok, hold_reason). 직전 하나만 앵커로 쓰던 것을 **직전·직후 양방향**으로 바꾼다(2026-09-11
    round2, inbox 20260911T0920Z 요구 (B)) -- 유상증자·자본확충처럼 계단식으로 뛴 값은 "가까운"
    쪽이 아니라 "같은 단(레벨)" 인 쪽 앵커로만 검증된다(예: KR1010 은 2023 년 증자로 레벨이
    바뀌어 직전(2022.4Q, 실제로는 ANCHOR_FORBIDDEN_QUARTERS 라 더 이전) 쪽은 항상 이탈하지만
    직후(2023.4Q, 이미 마스터에 있는 증자후 값)와는 맞는다). 둘 중 하나라도 ±30% 안이면 통과.
    둘 다 있는데 둘 다 밖이면 hold(사유는 DART 공시이력 확인 대상 -- 이 함수는 기계 게이트만
    담당, 사유 확인은 호출부/사람이 한다). 앵커가 아예 없으면(방향 무관) 과거와 동일하게 통과."""
    before = common.nearest_before(known, kr, item, q)
    after = common.nearest_after(known, kr, item, q)
    if before is None and after is None:
        return True, None
    if before is not None and common.qoq_ok(v, before[0]):
        return True, None
    if after is not None and common.qoq_ok(v, after[0]):
        return True, None
    parts = []
    if before is not None:
        parts.append(f"이전 {before[0]}({before[1]})")
    if after is not None:
        parts.append(f"이후 {after[0]}({after[1]})")
    return False, f"QoQ ±30% 초과(hold, 양방향 다 이탈): {v} vs " + " / ".join(parts)


def _nearest_convention(calib_item: dict[str, str] | None, q: str) -> str | None:
    if not calib_item:
        return None
    best_q4 = min(calib_item, key=lambda q4: common.qdist(q4, q))
    return calib_item[best_q4]


def _cell(value, pdf, page_idx, sha, quarter, unit_name, anchor_item, method):
    return {
        "값": value,
        "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        "page": (page_idx + 1) if isinstance(page_idx, int) else None,  # 1-based(사람이 읽기)
        "sha256": sha,
        "축척": unit_name,
        "앵커항목": anchor_item,
        "방법": method,
        "근거": f"정기경영공시 {quarter} raw PDF 별도재무상태표, {method} 추출"
                f"(inbox/parser/20260911T0109Z 백필)",
    }


def process_company(kr: str, known: dict) -> dict:
    targets = target_quarters_for(kr, known)
    cells: dict[str, dict] = {}
    skips: dict[str, dict] = {}

    # 2026-09-11 round2: target_quarters_for 가 코어 3항목(1/2/3) 기준으로 넓어지면서, "항목1은
    # 이미 있는데 항목3만 빠진" 분기(KR1010 등)도 재처리 대상에 들어온다. 그런 분기에서 항목1을
    # **다시 계산은 하되(항등식 검산에 필요) 절대 다시 쓰지 않는다** -- 1라운드(그리고 그 전부터)
    # 들어간 셀은 값이 바뀌면 안 된다는 게이트 불변식을 이 함수 레벨에서 강제한다(마스터
    # read-modify-write 금지 원칙의 연장 -- 이 스냅샷은 이번 호출 시작 시점의 `known` 이다).
    protected_items = {1} | set(CALIBRATED_ITEMS)
    already_present: dict[int, set] = {i: set((known.get((kr, i)) or {}).keys())
                                        for i in protected_items}

    calib, tested, q4_table_found = calibrate_detail_items(kr, known)
    # Q4 경영공시 본문에 표가 아예 없는 회사(실측: KR0051 등 -- "...등은 첨부파일 참조")는
    # 항목2/3 도 구조적으로 대조 불가다. 이건 "대조했는데 안 맞음"(진짜 위험, KR0070/71
    # 하이브리드자본 사례)과 다르므로 항목2/3 까지 안전-미검증 허용을 넓힌다. 13/20/21/24 는
    # 라벨 자체가 개념적으로 애매한 항목이라(부모/자식 혼재·흡수관계·뭉침배수) Q4 대조 가능
    # 여부와 무관하게 계속 막는다.
    #
    # 2026-09-11 round2(inbox 20260911T0920Z 요구 (C)): "그 항목 자체가 Q4 앵커가 없어
    # 애초에 검사할 대상이 없는" 경우도 -- q4_table_found=True(표는 찾았는데 마스터에 그
    # 항목의 Q4 값이 한 번도 없었던 경우 포함 -- 넓힌다. 안전장치는 계속 산다: 항목2/3 은
    # 아래 항등식(1==2+3) 게이트를 반드시 통과해야 pending 에 남는다(실패하면 이 표의 항목1
    # 외 전부 버림, 기존 로직 그대로) -- KR0070/71 하이브리드자본처럼 부채<->자본이 맞바뀌는
    # 위험은 항등식을 못 잡지만(둘 다 같은 합계 안에서 이동), 그 실측 위험사례는 TIER-1
    # 회사(비순환 검증 대상)였지 이번 대상(TIER2+분기공시 5개사)이 아니다. 미검증 통과는
    # method_tag 에 "unverified" 로 남아 owner 리뷰에서 구분 가능하다.
    safe_set = SAFE_WHEN_UNTESTED_ITEMS | {2, 3}
    untested_but_safe = [i for i in CALIBRATED_ITEMS
                         if i not in calib and i not in tested and i in safe_set]
    blocked = [i for i in CALIBRATED_ITEMS
               if i not in calib and i not in untested_but_safe]
    if blocked:
        skips[f"{kr}|_calibration|*"] = {
            "skip_reason": f"Q4 보정 실패(마스터 앵커는 있었는데 후보가 안 맞음) 또는 "
                           f"위험항목이라 미검증 통과 불가 -- 항목 {blocked} 는 전 분기 스킵"}
    if untested_but_safe:
        skips[f"{kr}|_calibration_untested|*"] = {
            "skip_reason": f"항목 {untested_but_safe} 는 마스터에 Q4 앵커가 없거나"
                           f"(q4_table_found={q4_table_found}) 재현검사를 못 했다 -- "
                           f"단일개념 라벨이라(또는 이 회사는 Q4 경영공시 자체에 BS 가 없어)"
                           f" 미검증으로 통과시키되 '방법'에 unverified 로 표시함"
                           f"(owner 리뷰 권장)"}

    for q in sorted(targets, key=common.qkey):
        pdf = common.pick_pdf(q, kr)
        if pdf is None:
            skips[f"{kr}|*|{q}"] = {"skip_reason": "경영공시 PDF 없음"}
            continue

        table = common.best_bs_table(pdf)
        if table is None:
            skips[f"{kr}|*|{q}"] = {"skip_reason": "적격 별도재무상태표 표를 찾지 못함"
                                     " (별도표제/비지배지분부재/운용자산부재 3조건 불충족)"}
        else:
            rows, groups, page_idx = table
            extracted = common.extract_row_values(rows, groups)
            scale = common.resolve_table_scale(extracted["items"], known, kr, q)
            if scale is None:
                skips[f"{kr}|*|{q}"] = {
                    "skip_reason": "축척 후보 0개 또는 2개 이상(앵커 불충분/모호)",
                    "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                    "page": page_idx + 1}
            else:
                factor, unit_name, anchor_item = scale
                sha = common.sha256_file(pdf)

                # 항목1(자산총계) -- 항상 신뢰(축척 기준점, 분류경계 이슈 없음).
                raw1 = extracted["items"].get(1)
                v1 = round(raw1 * factor, 6) if raw1 is not None else None
                if v1 is not None and q not in already_present[1]:
                    ok1, hold_reason1 = _qoq_gate(known, kr, 1, q, v1)
                    if not ok1:
                        skips[f"{kr}|1|{q}"] = {"skip_reason": hold_reason1}
                    else:
                        cells[f"{kr}|1|{q}"] = _cell(v1, pdf, page_idx, sha, q, unit_name,
                                                      anchor_item, "core")
                        known.setdefault((kr, 1), {})[q] = v1
                # else: 이미 마스터에 있음(예: 항목3만 빠진 분기) -- v1 은 항등식 검산용으로만
                # 쓰고 재기록하지 않는다. known 도 기존값을 유지한다(덮어쓰지 않음).

                # 항목2/3/4/10~31 -- 보정게이트 통과분만 후보로 모은다(아직 안 씀).
                pending: dict[int, tuple[float, str]] = {}
                for item in CALIBRATED_ITEMS:
                    conv = _nearest_convention(calib.get(item), q)
                    method_tag = f"detail({conv})" if conv else None
                    if conv is None:
                        if item not in untested_but_safe:
                            continue
                        conv = "direct"    # 미검증-안전항목은 부모/자식 특례가 없다(item13 제외)
                        method_tag = "detail(unverified:no-master-anchor)"
                    raw = (common.amort_candidates(extracted).get(conv) if item == 13
                           else extracted["items"].get(item))
                    if raw is None:
                        continue
                    pending[item] = (round(raw * factor, 6), method_tag)

                # 항등식(1==2+3) -- 항목2·3 둘 다 후보에 있을 때만 검사한다. 실패하면 이
                # 표에서 항목1 을 뺀 **전부**를 버린다 -- 개별 항목이 각자 Q4 보정을 통과했어도
                # "이번 분기에 엉뚱한 표를 골랐을" 위험은 항등식으로만 걸린다.
                lv = pending.get(2, (None, None))[0]
                ev = pending.get(3, (None, None))[0]
                if lv is not None and ev is not None and not common.identity_ok(v1, lv, ev):
                    skips[f"{kr}|1-2-3-detail|{q}"] = {
                        "skip_reason": f"산술검산 실패(항목1 만 유지, 나머지 전부 스킵): "
                                       f"자산={v1} 부채+자본={lv + ev}",
                        "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": page_idx + 1}
                    pending = {}

                for item, (v, method_tag) in pending.items():
                    if q in already_present.get(item, set()):
                        continue  # 이미 마스터에 있음 -- 재기록하지 않는다(기존값 보호)
                    ok_item, hold_reason = _qoq_gate(known, kr, item, q, v)
                    if not ok_item:
                        skips[f"{kr}|{item}|{q}"] = {"skip_reason": hold_reason}
                        continue
                    cells[f"{kr}|{item}|{q}"] = _cell(v, pdf, page_idx, sha, q, unit_name,
                                                       anchor_item, method_tag)
                    known.setdefault((kr, item), {})[q] = v

        # 준비금 5-8: 마스터에 이미 값이 있는 셀은 건드리지 않는다(결측 채우기 전용).
        rvals, rskips = reserve.extract_reserves(pdf)
        sha = common.sha256_file(pdf)
        for item, v in rvals.items():
            # 항목8(보증준비금)은 실측상 생명보험 전용 개념이다(build_ifrs17_bs.py 의 동일
            # 가드 + 검증룰 R_RSV_8). 손보사 필링에도 라벨은 boilerplate 로 찍히지만 개념
            # 자체가 해당없음(N/A)이라 0/값을 넣으면 업권 census 가 오염된다 -- 실측 2026-09-11:
            # 이 가드 없이 첫 백필했다가 5개 손보 TIER2 사(예별·AIG·악사·하나·신한이지)+
            # 카카오페이손해에서 R_RSV_8 RED 가 무더기로 났다.
            if item == 8 and kr in NONLIFE_TIER2:
                continue
            if (known.get((kr, item)) or {}).get(q) is not None:
                continue
            vv = round(v, 6)
            cells[f"{kr}|{item}|{q}"] = {
                "값": vv, "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": None,
                "sha256": sha, "축척": "reserve.py 기내장 환산(억/천/백만/원 자동판정)",
                "앵커항목": None, "방법": "reserve",
                "근거": f"정기경영공시 {q} 준비금 표(기적립액+적립예정액=잔액), "
                        f"scripts/_probes/probe_20260902_surrender_reserve_vs_disclosure.py 재사용"
                        f"(inbox/parser/20260911T0109Z 백필)"}
            known.setdefault((kr, item), {})[q] = vv
        for item, reason in rskips.items():
            if (known.get((kr, item)) or {}).get(q) is None:
                skips[f"{kr}|{item}|{q}"] = {"skip_reason": f"준비금: {reason}"}

    return {"cells": cells, "skips": skips,
            "stats": {"targets": len(targets), "cells": len(cells), "skips": len(skips),
                      "calibrated_items": sorted(calib.keys()),
                      "untested_but_safe_items": sorted(untested_but_safe),
                      "blocked_items": sorted(blocked)}}


def run_validation(known: dict) -> None:
    """비순환 확대 재현: DART 분기 필링 보유 회사(TIER-1, TIER2 아닌 전부) x 중간분기 x
    항목1/2/3. 축척 앵커로 쓴 항목은 순환이라 정확도 집계에서 뺀다."""
    all_companies = sorted({kr for (kr, item) in known if item == 1})
    tier1 = [kr for kr in all_companies if kr not in TIER2]
    n_match = n_mismatch = n_skip = 0
    details = []
    for kr in tier1:
        quarters = sorted((known.get((kr, 1)) or {}).keys(), key=common.qkey)
        interior = [q for q in quarters if not q.endswith(".4Q")]
        for q in interior:
            pdf = common.pick_pdf(q, kr)
            if pdf is None:
                n_skip += 1
                continue
            table = common.best_bs_table(pdf)
            if table is None:
                n_skip += 1
                continue
            rows, groups, page_idx = table
            extracted = common.extract_row_values(rows, groups)
            scale = common.resolve_table_scale(extracted["items"], known, kr, q)
            if scale is None:
                n_skip += 1
                continue
            factor, unit_name, anchor_item = scale
            for item in (1, 2, 3):
                if item == anchor_item:
                    continue  # 축척을 정하는 데 쓰인 항목 -- 순환이라 카운트 제외
                raw = extracted["items"].get(item)
                actual = (known.get((kr, item)) or {}).get(q)
                if raw is None or actual is None:
                    continue
                predicted = raw * factor
                tol = max(1.0, abs(actual) * 0.001)
                if abs(predicted - actual) <= tol:
                    n_match += 1
                else:
                    n_mismatch += 1
                    details.append({"kr": kr, "item": item, "q": q, "predicted": predicted,
                                     "actual": actual,
                                     "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                                     "page": page_idx + 1})
    print(f"비순환 검증(TIER-1 {len(tier1)}사, 항목1/2/3, 앵커항목 제외): "
          f"match={n_match} mismatch={n_mismatch} skip={n_skip}")
    out = ROOT / "data" / "_derived" / "bs_backfill_validation.json"
    out.write_text(json.dumps({"companies": len(tier1), "match": n_match,
                                "mismatch": n_mismatch, "skip": n_skip, "mismatches": details},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", help="콤마로 구분된 KR코드, 또는 'all'(TIER2 15개사 전부)")
    ap.add_argument("--validate", action="store_true",
                     help="비순환 검증만 실행(TIER-1 회사 x 중간분기 x 항목1/2/3)")
    args = ap.parse_args()

    known = common.load_master_index()

    if args.validate:
        run_validation(known)
        return

    if not args.company:
        print("--company KR.... 또는 --validate 가 필요합니다", file=sys.stderr)
        sys.exit(1)
    codes = sorted(TIER2) if args.company == "all" else [c.strip() for c in args.company.split(",")]
    for kr in codes:
        result = process_company(kr, known)
        out_path = PARTS_DIR / f"{kr}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        st = result["stats"]
        print(f"{kr}: targets={st['targets']} cells={st['cells']} skips={st['skips']} "
              f"calibrated={st['calibrated_items']} untested_safe={st['untested_but_safe_items']} "
              f"blocked={st['blocked_items']} -> {out_path}")


if __name__ == "__main__":
    main()
