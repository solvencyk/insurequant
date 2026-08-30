#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IFRS17 BS master (17BS 시트 스키마) -- Simplified high-level BS: assets / liabilities /
equity / AOCI / 법정준비금(해약환급금·비상위험·대손) only. Sole 17BS master since
2026-08-14 (owner archived the earlier equity_composition.json, items 1-49 -- "항목 ㅈㄴ
많은 것들"; see archive/2026-08_equity_composition/README.md).

Source = data/dart/_fs_api_cache/*.json (fetch_dart_fs.py's cache -- standard account_id
match, no new fetching logic) + data/dart/FY*/raw/*.xml (body-XML note fallback for items
5-7, and Tier-2's full BS for 15 non-listed insurers -- both via
build_equity_composition_tier2.py's parse_filing(), reused unchanged, name notwithstanding).
Units 백만원 (API is 원 -> /1e6). Basis: OFS(별도) by default -- owner 2026-08-14 P-1:
BASIS_CFS (삼성생명/메리츠) is a PL-only rule (그 gold 답지가 연결이라 만든 것); applying it
to BS made 삼성생명's 2025.2Q/3Q assets read as a stale-frozen CFS duplicate of 2025.1Q.
Narrow conditional CFS fallback added 2026-08-15 (owner+validation, Q-2): only when OFS's
items 1/2/3 are entirely absent (e.g. 한화손보 2026.2Q's OFS BS is a 4-row blank shell) --
see `extract_quarter()`. corp_code resolved by name at runtime.

Schema (10 columns, no 값_당분기 -- everything here is a stock/point-in-time item):
  원보험사코드 / 원수사명 / 티커 / 생손보여부 / 항목번호 / 항목명 / 섹션 / 레벨 / 공시분기 / 값
섹션 = 자산|부채|자본|준비금 (T자 레이아웃 그룹핑). 레벨 = 1(총계 타일: 1/2/3) | 2(그 외 전부,
드릴다운 세부-- AOCI·준비금 포함). Items 8/10+ (owner 2026-08-15, capped at ~15 lines total
across all three sections -- a curated highlight set, not an exhaustive account census; no
closure/residual accounting against 1/2/3 is attempted or expected). Item8(보증준비금)
added same-day as a 4th 법정준비금 type alongside 5/6/7.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_ifrs17_bs.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, REPRT  # reuse, not copy
from scripts.build_equity_composition_tier2 import (  # reuse, not copy
    TIER2, parse_filing, parse_financial_soundness_periods,
)
from scripts import reserve_extract  # 회사별 준비금 핸들러 (FS API에 준비금 없는 27개사)

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
DART = ROOT / "data" / "dart"
OUT = ROOT / "IFRS17_BS.json"
# owner가 원문을 직접 보고 확정했는데 추출기가 아직 못 잡는 셀. 마지막 단계에서 덮어쓴다
# (마스터 JSON을 손으로 고치면 다음 빌드에 사라지므로 반드시 이 파일을 거친다).
CARRY_OUT = ROOT / "data" / "_derived" / "bs_carry_forward_cells.json"
OVERRIDES = ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json"
INV_REPRT = {v: k for k, v in REPRT.items()}  # "11013" -> "1Q"
# parse_filing()'s item numbers (its own BS+reserve-note schema) -> this master's 1-8
TIER2_ITEM_MAP = {40: 1, 41: 2, 1: 3, 6: 4, 10: 5, 12: 6, 14: 7, 17: 8}
# Same map, reused for the Tier-1 body-XML note fallback below (item 4/AOCI excluded --
# Tier-1's own FS-API face-of-BS is higher confidence and always tried first for that item).
NOTE_ITEM_MAP = {10: 5, 12: 6, 14: 7, 17: 8}
# 본문 XML BS의 T자 드릴다운 세부(자산/부채/자본 하이라이트) -> 이 마스터 항목번호.
# parse_filing이 200번대로 돌려준다(준비금 노트 키 10~18과 충돌 방지, 2026-08-20).
BS_DETAIL_ITEM_MAP = {200 + i: i for i in (10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31)}
# 본문 XML BS에서 온 소스 키 전부 -- 아래 표-단위 개연성 게이트가 걸리는 범위.
BS_SOURCE_KEYS = {40, 41, 1, 6} | set(BS_DETAIL_ITEM_MAP)
# 개연성 게이트 (2026-08-20): 본문 XML은 한 필링에 BS 후보 표가 4~6개라 표 선택이 틀리면
# 연결/전기/전환일 값이 조용히 들어온다. `_pick_bs_table`이 순위로 걸러내지만 2023.1Q처럼
# 절 제목이 비표준인 필링은 여전히 샌다 -- 그래서 **그 회사의 FS-API 실적(±4분기 이내)과
# 자산총계가 15% 넘게 어긋나면 그 표에서 나온 값을 통째로 버린다.** 부분 채택이 아니라
# 표 단위로 버리는 이유: 틀린 건 개별 행이 아니라 "어느 표를 골랐나"라서다.
# owner 원칙대로 틀린 값보다 빈 칸이 낫다(RESERVE_MAX_MN 주석과 같은 판단).
BS_PLAUSIBILITY_TOL = 0.15
BS_PLAUSIBILITY_MAX_DIST = 4


def _qnum(quarter: str) -> int:
    y, q = quarter.split(".")
    return int(y) * 4 + int(q[0])


def _bs_table_plausible(anchors, kr, quarter, assets_mn):
    """자산총계(항목1) 기준 표-단위 개연성. 앵커(FS-API 실적)가 없으면 통과."""
    ser = anchors.get(kr)
    if not ser or assets_mn is None:
        return True
    n = _qnum(quarter)
    best = min(ser, key=lambda k: (abs(k - n), k))
    if abs(best - n) > BS_PLAUSIBILITY_MAX_DIST or not ser[best]:
        return True
    return abs(assets_mn - ser[best]) <= abs(ser[best]) * BS_PLAUSIBILITY_TOL

META = {}
for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    c = r.get("원보험사코드")
    if c and c not in META:
        META[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))

LABELS = {
    1: "자산총계", 2: "부채총계", 3: "자본총계",
    # 법정준비금 4종: 이름을 `~준비금 적립액`으로 통일한다 (2026-08-19, validation
    # 20260819T0754Z G절 + owner 승인). 2026-08-19부터 네 항목 모두 owner 확정 공식
    # `적립액 = 기적립액 + 적립(환입)예정액`의 **합산액**을 싣는데(PENDING_ACCOUNT_IDS),
    # 이름만 옛 정의로 남아 있어 값과 어긋났다 -- 항목8 `보증준비금 기적립액`은 실제론
    # 합산액이었고, 항목6 `비상위험준비금 기말`만 혼자 '기말' 계열이었다. 항목명은 화면
    # 라벨로도 나가므로 바꾸면 publishing 경유로 designer에 통지할 것.
    4: "기타포괄손익 누계액", 5: "해약환급금준비금 적립액",
    6: "비상위험준비금 적립액", 7: "대손준비금 적립액", 8: "보증준비금 적립액",
    # BS 세부 하이라이트 (owner 2026-08-15: T자 레이아웃 드릴다운용, 전 계정 총망라 아니고
    # 최대 15줄 예산 -- 95개 distinct account_id census 후 재무상태표에서 가장 중요한 지표만
    # 선별, 자산/부채/자본 합쳐 13개). 항목번호는 섹션별 10/20/30대로만 구분, 빈 자리는 향후
    # 여유 -- 폐쇄검산 대상 아님(owner: 전수 분해가 아니라 하이라이트).
    10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
    12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산",
    14: "재보험계약자산", 15: "유형자산",
    20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 23: "차입부채",
    24: "기타부채",
    30: "자본금", 31: "이익잉여금",
}
# T자 레이아웃 그룹핑 (owner 2026-08-15 계약: designer는 항목번호를 하드코딩하지 않고 섹션·
# 레벨로만 그룹핑). 레벨: 1=총계 타일(1/2/3), 그 외 전부 2(드릴다운 세부, AOCI·준비금 포함).
# item8(보증준비금)도 준비금 -- 이익잉여금(31) 내부 적립이라 자본 L2 합에서 제외 그대로.
SECTION = {1: "자산", 2: "부채", 3: "자본", 4: "자본", 5: "준비금", 6: "준비금", 7: "준비금",
           8: "준비금",
           10: "자산", 11: "자산", 12: "자산", 13: "자산", 14: "자산", 15: "자산",
           20: "부채", 21: "부채", 22: "부채", 23: "부채", 24: "부채",
           30: "자본", 31: "자본"}


def _section_level(item: int) -> tuple[str, int]:
    return SECTION.get(item, "?"), (1 if item in (1, 2, 3) else 2)


# item4 (AOCI)'s dart_ 확장태그 fallback is handled separately in extract_quarter() --
# NOT listed here, since it must apply only when the standard tag is absent (see below).
ACCOUNT_IDS = {
    1: ("ifrs-full_Assets",),
    2: ("ifrs-full_Liabilities",),
    3: ("ifrs-full_Equity",),
    4: ("ifrs-full_AccumulatedOtherComprehensiveIncome",),
    5: ("dart_SurrenderValueReserve",),
    # 비상위험준비금, "가능하면" (owner P-5). 2026-08-15: dart_CatastropheReserve는 표준태그
    # 없는 회사 9곳이 대신 쓰는 배타적 대안 라벨(census 확인, ifrs-full_ 표준태그와 동시출현
    # 0건) -- item10 현금 대안 체인과 같은 안전한 패턴, 튜플에 같이 둔다.
    6: ("ifrs-full_ReserveForCatastrophe", "dart_CatastropheReserve"),
    7: ("dart_RegulatoryReserveForCreditLoss",),       # 대손준비금, "가능하면" (owner P-5)
    # 보증준비금, "가능하면" -- 2026-08-15 owner 추가 지시. 처음엔 "2사만 보유(교보생명·
    # 미래에셋생명)"로 알았으나 2026-08-19 raw census(21개 생보사 최신 필링 전수)에서 최소
    # 11개사가 실제 공시함이 드러남 -- 이 태그(FS-API 표준 XBRL)를 쓰는 회사가 2사뿐인 것이지
    # 개념 자체가 희귀한 게 아니었다. 나머지는 body-XML 노트(NOTE_ITEM_MAP 경유, item17)로 보강.
    8: ("dart_GuranteeReserve",),
    # BS 세부 하이라이트 -- 대안 태그는 회사마다 배타적으로 쓰여(census 확인, 동시출현 無)
    # 튜플에 같이 둬도 안전. item13(상각후원가측정금융자산)은 부모/자식 co-occurrence가
    # 회사마다 다른 유일한 케이스라 별도 처리(AMORTISED_COST_* 아래).
    10: ("ifrs-full_CashAndCashEquivalents", "dart_CashAndDuefromBanks",
         "dart_DueFromBanksAtAmortisedCost"),
    11: ("ifrs-full_FinancialAssetsAtFairValueThroughProfitOrLoss",),
    12: ("ifrs-full_FinancialAssetsAtFairValueThroughOtherComprehensiveIncome",),
    14: ("ifrs-full_ReinsuranceContractsHeldThatAreAssets",),
    15: ("ifrs-full_PropertyPlantAndEquipment",),
    20: ("ifrs-full_InsuranceContractsIssuedThatAreLiabilities",),
    21: ("ifrs-full_ReinsuranceContractsHeldThatAreLiabilities",),
    22: ("ifrs-full_InvestmentContractsLiabilities",),
    23: ("ifrs-full_Borrowings",),
    24: ("ifrs-full_OtherNonfinancialLiabilities",),
    30: ("ifrs-full_IssuedCapital",),
    31: ("ifrs-full_RetainedEarnings",),
}
# 적립(환입)예정액 짝태그 (owner 2026-08-19, inbox/parser/20260819T0500Z): FS-API가 법정준비금
# 4종을 기적립액/적립(환입)예정액 두 개의 별도 XBRL 태그로 나눠 낸다. 공시상 진짜 "적립액"
# 합계 = 기적립액(위 ACCOUNT_IDS) + 적립(환입)예정액(아래) -- owner 실측: 메리츠 비상위험
# 2023.4Q 321,055+31,556=352,611이 그 회사 재무건전성표(P1) 값과 정확히 일치. 이 태그를
# 안 읽는 게 지금까지 item5/6/7/8이 기적립액만 실은 근본 원인이었다(item5/8의 body-XML Part A
# 롤포워드는 이 간극을 필링별로 메워온 것 -- FS-API가 직접 주면 그게 우선하되 서로 배타적이지
# 않음, 아래서 두 소스 다 반영).
PENDING_ACCOUNT_IDS = {
    5: ("dart_SurrenderValueReserveToBeAdded",),
    6: ("dart_CatastropheReserveToBeAdded",),
    7: ("dart_RegulatoryReserveForCreditLossToBeAdded",),
    8: ("dart_GuranteeReserveToBeAdded",),
}
RESERVE_ITEMS = (5, 6, 7, 8)
# 계정명 기반 폴백 (owner 2026-08-19 답지 대조에서 발견). FS-API에서 준비금 **기적립액 행은
# `account_id`가 `-표준계정코드 미사용-`**으로 오는 회사가 많다 -- 표준 XBRL 코드가 붙는 건
# `...ToBeAdded`(적립예정액) 쪽뿐이라, 태그로만 찾으면 **증분만 잡히고 잔액이 통째로 빠진다.**
# 실측(2026.2Q OFS): 삼성화재 비상위험 기적립액 2,662,011이 `-표준계정코드 미사용-`이라 안
# 잡혀 예정액 △14,488만 남았고(owner 답지의 0.5%), KB손보·DB손보·코리안리·서울보증·롯데손보도
# 전부 같은 형태였다. 그래서 태그로 못 찾은 항목은 **계정명**으로 한 번 더 찾는다.
RESERVE_NAMES = {5: "해약환급금준비금", 6: "비상위험준비금", 7: "대손준비금", 8: "보증준비금"}
# 기적립액 계열 접미사. "적립액"(기 없음)도 같은 뜻이다 -- owner 명시: "계정명이 `적립액`(기
# 없음)이어도 합산한다". DB손해보험처럼 이름 전체가 괄호로 묶인(차감표시) 경우도 있어 괄호는
# 매칭 전에 벗긴다.
ACCRUED_SUFFIXES = ("기적립액", "적립액", "잔액")
PENDING_SUFFIX = "예정액"
# 법정준비금 상한 sanity (백만원). 국내 최대 보험사의 해약환급금준비금이 2026년 기준 7조원대
# (한화생명 7조1,097억, 2026-08-09 보도)이고 업권 전체가 58조원대이므로, 한 회사 한 개념이
# 2000만백만원(=20조원)을 넘으면 태그 오분류/단위오류다. 실측 적발: 한화손해보험 2025.4Q
# 대손준비금이 △65,432,530백만원(=65조원)으로 나왔는데 이 회사 총자산(약 20조원)의 3배라
# 성립 불가 -- FS-API가 그 분기에 다른 개념을 이 태그로 실은 것으로 보인다. 값을 추측해
# 고치지 않고 **버린다**(미공시로 남김) -- 틀린 값을 싣는 것보다 빈 칸이 낫다.
RESERVE_MAX_MN = 2e7
# (회사, 항목) 쌍 중 이 준비금이 **매 분기 재산정**(비누적)이라 일반 forward-fill(직전 분기
# 값 복제)을 적용하면 안 되는 곳. 케이디비생명보험 item5(해약환급금준비금)은 미처리결손금
# 상태라 기적립액이 항상 '-'로 남고 그 분기의 적립예정액만 잔액이 된다 -- 회사가 매 분기
# 새로 계산해 공시하지, 이전 분기 잔액을 이어받지 않는다. 실측(parser 2026-08-21,
# inbox/parser/20260820T2340Z): 2025.1Q 원문 1,338(잔액) / 2025.2Q 원문 "당반기말 및
# 전기말 현재 해약환급금준비금으로 적립한 내역은 없습니다"(0) / 2025.3Q 원문도 동일 문구(0)
# / 2025.4Q(연차) 원문 "당기말 및 전기말 현재 ... 적립한 내역은 없습니다"(0, 2024.4Q도
# 소급 확인) / 2026.1Q 23,550 / 2026.2Q 4,323 -- 인접 분기가 몇 배씩 다르다. 일반
# forward-fill을 걸면 2025.2Q~4Q가 1,338로 잘못 복제돼(회사 자신의 명시적 부인과 직접
# 모순) R-RSV-1 BASELINE으로 계속 걸렸다. 이 쌍은 forward-fill 루프에서 제외한다 --
# 채울 근거가 없으면 빈 칸(disclosed_none 등재는 validation 확인 후).
NO_FORWARD_FILL_CELLS: frozenset[tuple[str, int]] = frozenset({("KR0072", 5)})
ALL_ITEMS = tuple(sorted(LABELS))
# item13: 회사마다 부모(총계 태그)만 쓰거나, 자식 3종만 쓰거나, 둘 다 쓰되 일치하거나(진짜
# 부모-자식), 둘 다 쓰는데 액수가 안 맞는(census 2026-08-15: 24사 중 4사 -- KR0001/69/70/83)
# 경우까지 있어 "부모 있으면 무조건 부모 채택, 없을 때만 자식 합산" 규칙으로 통일 -- 이중계상
# 위험이 있는 방향(자식 우선)이 아니라 안전한 방향(부모 우선)으로 고정.
AMORTISED_COST_PARENT = "ifrs-full_FinancialAssetsAtAmortisedCost"
AMORTISED_COST_CHILDREN = ("dart_LoansAtAmortisedCost", "dart_SecuritiesAtAmortisedCost",
                           "dart_OtherFinancialAssetsAtAmortisedCost")
# item4 conditional fallback (owner 2026-08-14 P-2): 한화생명/흥국생명 등 일부 분기는 AOCI를
# 표준태그 대신 이 확장태그로 공시한다(태그만 갈아탄 것 -- 값이 0인 게 아니다, 라벨도 그대로
# "기타자본구성요소"). 채택 조건 = 같은 (회사,분기) BS에 표준태그가 아예 없을 때만(검증:
# 캐시 254건 전수 스캔 결과 표준+확장 동시존재 0건, 확장태그단독 13건 = 한화생명7+흥국생명6,
# 정확히 owner 목록과 일치). 무조건 매핑하면 다른 회사의 진짜 자본조정 계정을 AOCI로 오분류한다.
AOCI_FALLBACK_ID = "dart_ElementsOfOtherStockholdersEquity"


def _num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", "")) / 1e6
    except ValueError:
        return None


def _basis_data(cc: str, year: str, reprt: str, basis: str) -> list[dict]:
    p = CACHE / f"{cc}_{year}_{reprt}_{basis}.json"
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    if d.get("status") != "000":
        return []
    return d.get("list") or []


def _extract_from_list(lst: list[dict]) -> tuple[dict[int, float], set[int]]:
    out = {}
    pending_seen: set[int] = set()  # items whose FS-API 적립예정액 tag was found -- caller
    # uses this to skip the body-XML Part A fold-in for these (avoid double-counting the
    # same addition once from FS-API here and again from the note-table harvest).
    for item, ids in ACCOUNT_IDS.items():
        for a in lst:
            if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
                continue
            if a.get("account_id") in ids:
                v = _num(a.get("thstrm_amount"))
                if v is not None:
                    # ⚠ 여기서 절댓값을 취하면 안 된다. 준비금 stock이 음수일 수 없는 건
                    # 맞지만, 절댓값은 **마지막 합계에서** 취해야 한다
                    # (`_rollforward_reserve_series` 배출 지점). 기적립액만 abs 하고 예정액은
                    # 부호를 살리면 두 관례가 섞여 깨진다 -- 실측(2026-08-19): DB손해보험은
                    # 기적립·예정 **둘 다 음수**로 찍는 차감표시(contra) 필러라
                    # abs(-1,378,571) + (-136,483) = 1,242,088이 나왔지만
                    # 정답은 |(-1,378,571) + (-136,483)| = 1,515,054다. 부호를 살려 더한 뒤
                    # 마지막에 한 번만 절댓값을 취하면 두 관례(양수표시 삼성화재·코리안리,
                    # 음수표시 DB손보) 모두 옳게 나온다.
                    if item in RESERVE_ITEMS and abs(v) > RESERVE_MAX_MN:
                        break   # 성립 불가 규모 -> 이 항목은 미공시로 남긴다
                    out[item] = v
                break
    # 준비금 기적립액 계정명 폴백 -- 태그가 `-표준계정코드 미사용-`이라 위 루프가 못 찾은 것을
    # 계정명으로 건진다(RESERVE_NAMES 주석의 실측 참조). 이미 태그로 찾았으면 건드리지 않는다.
    def _clean_nm(a):
        return (a.get("account_nm") or "").replace(" ", "").strip("()（）")

    for item, concept in RESERVE_NAMES.items():
        if item in out:
            continue
        for a in lst:
            if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
                continue
            nm = _clean_nm(a)
            if not nm.startswith(concept):
                continue
            rest = nm[len(concept):]
            if rest not in ACCRUED_SUFFIXES:
                continue
            v = _num(a.get("thstrm_amount"))
            if v is not None and abs(v) <= RESERVE_MAX_MN:
                out[item] = v   # 부호 유지 (절댓값은 최종 합계에서 -- 위 주석 참조)
            break

    # 법정준비금 적립(환입)예정액 합산 (owner 2026-08-19, inbox/parser/20260819T0500Z) --
    # 기적립액이 없어도(0/미확보) 예정액만 있는 회사가 있을 수 있어 0.0 기본값으로 더한다
    # (item5/8의 body-XML Part A 롤포워드와 동일한 관례). 표준태그가 없으면 계정명으로 폴백.
    for item, ids in PENDING_ACCOUNT_IDS.items():
        concept = RESERVE_NAMES[item]
        for a in lst:
            if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
                continue
            nm = _clean_nm(a)
            by_tag = a.get("account_id") in ids
            by_name = nm.startswith(concept) and nm[len(concept):].endswith(PENDING_SUFFIX)
            if not (by_tag or by_name):
                continue
            v = _num(a.get("thstrm_amount"))
            if v is not None:
                # ⚠ 예정액은 **부호를 살려서** 더한다. 계정명이 "적립(환입)예정액"인 그대로,
                # 음수는 환입(reserve 감소)이라 빼는 게 맞다 -- 한때 기적립액과 똑같이
                # 절댓값을 취했다가 환입을 적립으로 뒤집었다. owner 답지 2건이 이를 확정한다
                # (2026.2Q OFS 실측): 코리안리 대손 1,028 + (△230) = **798**,
                # 롯데손보 해약환급금 344,461 + (△18,711) = **325,750** -- 둘 다 owner
                # 수기값과 원 단위까지 일치한다(절댓값을 쓰면 1,258 / 363,172로 어긋난다).
                # 최종 음수 방지는 배출 지점(`_rollforward_reserve_series`)이 따로 맡는다.
                combined = out.get(item, 0.0) + v
                if abs(combined) <= RESERVE_MAX_MN:
                    out[item] = combined
                    pending_seen.add(item)
            break
    if 4 not in out:
        for a in lst:
            if a.get("sj_div") == "BS" and a.get("account_detail") == "-" \
                    and a.get("account_id") == AOCI_FALLBACK_ID:
                v = _num(a.get("thstrm_amount"))
                if v is not None:
                    out[4] = v
                break
    # item13: parent tag wins whenever present (never double-count against children);
    # only sum the 3 children when the parent tag is absent entirely for this filer.
    by_id = {}
    for a in lst:
        if a.get("sj_div") == "BS" and a.get("account_detail") == "-":
            by_id.setdefault(a.get("account_id"), a)
    if AMORTISED_COST_PARENT in by_id:
        v = _num(by_id[AMORTISED_COST_PARENT].get("thstrm_amount"))
        if v is not None:
            out[13] = v
    else:
        vs = [_num(by_id[c].get("thstrm_amount")) for c in AMORTISED_COST_CHILDREN if c in by_id]
        vs = [v for v in vs if v is not None]
        if vs:
            out[13] = sum(vs)
    return out, pending_seen


def _rollforward_reserve_series(item_num, rows, quarters_by_co, additions,
                                 retro=None, negative_guard=False, p1_overrides=None,
                                 fs_api_pending_companies=frozenset(),
                                 handler_cells=frozenset()):
    """Shared Part A(fold-in)/P1(override)/C(2022 retro)/forward/backward rollforward
    machinery for one legal-reserve item (5/6/7/8) -- item5와 item8에서 거의 동일한 코드가
    두 번 반복돼 있던 것을 2026-08-19에 일반화(owner: 항목6/7도 같은 공식 필요 지시가 계기).

    - additions: {(kr,fy): that FY's own pending(적립예정액) total}, harvested by the caller
      via parse_filing() (item5=item11, item6=item13, item7=item15, item8=item18).
    - retro: item5 전용 Part C(2022년말 소급) -- 다른 3개 항목은 None.
    - negative_guard: 준비금 stock은 구조적으로 음수일 수 없다(모든 4개 개념 공통 원칙) --
      fold-in 결과가 음수면 스킵(이 회사/분기는 부호관례가 안 풀린 것으로 보고 값을 안 쏜다),
      guessed 음수를 내보내지 않는다.
    - p1_overrides: {(kr,y,qn): value}, "재무건전성 등 기타 참고사항" 절 3기간 표(owner
      2026-08-19)처럼 회사가 직접 공시한 잔액 -- fold-in보다 우선해 series를 덮어쓴다.
    - fs_api_pending_companies: 이 회사들은 FS-API 자체가 기적립액+적립예정액을 이미 합산해
      series에 실었다(PENDING_ACCOUNT_IDS, owner 2026-08-19 inbox 20260819T0500Z) -- 그
      위에 body-XML의 additions를 또 더하면 이중계상이라 이 회사들은 fold-in을 건너뛴다.
    - handler_cells: {(kr, item, quarter)} -- `reserve_extract` 전용 핸들러가 채운 셀.
      핸들러는 이미 총액을 주므로 그 셀의 fold-in은 건너뛴다(셀 단위, 회사 단위 아님).

    Returns (rows_with_item_replaced, stats: dict)."""
    series: dict[str, dict[tuple[int, int], float]] = {}
    for r in rows:
        if r["항목번호"] == item_num:
            y, qn = r["공시분기"].split(".")
            series.setdefault(r["원보험사코드"], {})[(int(y), int(qn[0]))] = r["값"]

    q4_fixed = q4_guarded = fs_api_skipped = 0
    for (kr, fy), add in additions.items():
        if kr in TIER2 or kr not in META:
            continue
        # 이 (회사, 그 FY의 Q4) 값이 이미 `기적립액+적립(환입)예정액` 총액이면 여기서 또
        # 더하면 안 된다 -- 예정액이 두 번 들어간다. 두 경로가 총액을 준다:
        #   (a) FS-API 예정액 짝태그(PENDING_ACCOUNT_IDS)를 실어준 회사 -> 회사 단위
        #   (b) `reserve_extract` 전용 핸들러 -> owner 공식대로 합산해 반환하는 게 계약
        #       (common.py `combine()`), 단 **셀 단위**로 판정해야 한다. 회사 단위로 막으면
        #       핸들러가 커버하지 못한 분기까지 fold-in이 사라져 반대로 과소계상된다
        #       (실측: 회사 단위로 막았더니 2023말 업권합계가 +14.7% -> -12.8%로 뒤집힘).
        if kr in fs_api_pending_companies or (kr, item_num, f"{fy}.4Q") in handler_cells:
            fs_api_skipped += 1
            continue
        s = series.setdefault(kr, {})
        folded = s.get((fy, 4), 0.0) + add
        if negative_guard and folded < 0:
            q4_guarded += 1
            continue
        s[(fy, 4)] = folded
        q4_fixed += 1

    # P1(재무건전성 3기간 표)은 **빈칸 채우기 전용**이다 -- FS-API가 준 값을 덮지 않는다.
    # 처음엔 "회사가 직접 공시한 잔액"이라 더 권위 있다고 보고 무조건 override 했는데,
    # 2023.4Q·2024.4Q를 FS-API 원문(기적립 + 부호있는 예정)과 전수 대조하니 P1이 더 나은 값을
    # 더 나쁜 값으로 덮고 있었다(2026-08-19 실측): KB손해보험 2023.4Q 비상위험이 원문
    # 1,058,272+77,045=1,135,317인데 마스터엔 11,319, 코리안리 비상위험은 1,378,548인데
    # 337,861. P1 표의 행 선택이 회사에 따라 어긋나는 것으로, 그 진단 전까지는 FS-API를
    # 신뢰하고 P1은 FS-API가 침묵한 칸에만 쓴다(그 용도로는 2022.4Q·2023.1~2Q처럼 API가
    # status 013만 주는 구간에서 여전히 유일한 소스다).
    p1_applied = 0
    if p1_overrides:
        for (kr, y, qn), v in p1_overrides.items():
            s = series.setdefault(kr, {})
            if (y, qn) in s:
                continue
            s[(y, qn)] = v
            p1_applied += 1

    c_filled = 0
    if retro:
        for (kr, fy), val in retro.items():
            if kr not in META:
                continue
            s = series.setdefault(kr, {})
            if (fy - 1, 4) not in s:
                s[(fy - 1, 4)] = val
                c_filled += 1

    # 롤포워드/백필로 **빌더가 복제해 만든** 칸. 원천 공시가 아니라 직전 관측치의 사본이므로
    # "연속 동일값"의 근거가 될 수 없다 -- 그걸 결함으로 세면 우리가 만든 사본을 우리가 결함으로
    # 다시 세는 순환이 된다(검증 R-RSV-1, inbox/parser/20260820T0430Z). 사이드카로 내보내
    # 검증이 연속성 판정에서 빼도록 한다. **각 구간의 첫 칸(진짜 공시분기)은 여기 안 들어간다.**
    filled_cells: set[tuple[str, str]] = set()
    forward_added = 0
    for kr, qlist in sorted(quarters_by_co.items()):
        # TIER2(연1회 공시사)도 여기 포함된다 -- owner 2026-08-20 이월 결정. 아래 backward
        # 루프는 계속 제외한다(그쪽은 look-ahead 가 되므로).
        if kr not in META:
            continue
        if (kr, item_num) in NO_FORWARD_FILL_CELLS:
            continue
        s = series.setdefault(kr, {})
        for (y, qn) in sorted(qlist):
            if (y, qn) in s:
                continue
            if qn > 1 and (y, qn - 1) in s:
                val = s[(y, qn - 1)]
            elif qn == 1 and (y - 1, 4) in s:
                val = s[(y - 1, 4)]
            else:
                continue
            s[(y, qn)] = val
            filled_cells.add((kr, f"{y}.{qn}Q"))
            forward_added += 1

    # 뒤채움(backward fill)은 **없다** -- 2026-08-20에 제거했다(검증 발주
    # inbox/parser/20260820T1900Z). 나중 분기 값을 그 FY의 앞 분기로 복사하는 것은
    # ① 그 시점에 아직 공시되지 않은 값을 과거에 소급하는 look-ahead 이고,
    # ② 폴드인이 그 FY의 적립예정액을 Q4에 얹으므로 **그 FY 적립분만큼 계통적으로 과대계상**
    #    된다(앞 분기의 진짜 잔액은 직전 FY 처분 후 잔액이다),
    # ③ 실측으로 확인됐다: 삼성화재 2023.2Q 해약환급금준비금이 마스터 916,764 인데 그 필링이
    #    직접 공시한 값은 556,503(1.65배 과대), 현대해상 2023.1Q 도 원문 4,391,552 인데
    #    2023.3Q 값 3,603,897 이 들어와 있었다(이쪽은 반대로 과소).
    # TIER2 는 원래부터 이 루프에서 제외돼 있었고("backward 로 채우면 look-ahead"), 그 판단이
    # Tier-1 에도 똑같이 적용된다는 것이 이번 결론이다. 채울 근거가 있으면 P1 표·회사별
    # 핸들러로 **실관측을 채우고**, 근거가 없으면 빈 칸으로 둔다(틀린 값보다 빈 칸).
    backward_added = 0

    # 최종 배출 지점의 공통 안전장치 -- 이 항목의 모든 소스(FS-API 태그 / 회사별 핸들러 /
    # 범용 노트추출 / P1 표 / 롤포워드)가 여기 한 곳으로 모이므로, 소스마다 따로 막는 대신
    # 여기서 한 번에 건다 (owner 2026-08-19, inbox/parser/20260819T0500Z):
    #   (1) 준비금 stock은 음수 불가 -> 절댓값. 원표가 음수인 건 경제적 잔액이 아니라 자사
    #       이익잉여금 내역의 차감표시(contra) 관례다. 진짜 환입은 전분기 대비 '감소'로 나온다.
    #   (2) 성립 불가 규모는 버린다(추측해 고치지 않는다). 실측: 한화손해보험 2025.4Q
    #       대손준비금이 65조원으로 나왔는데 이 회사 총자산의 3배다 -- 원표에서 다른 개념을
    #       집은 것이므로 틀린 값을 싣느니 빈 칸으로 둔다.
    rows = [r for r in rows if r["항목번호"] != item_num]
    section, level = _section_level(item_num)
    written = dropped = 0
    for kr, s in series.items():
        if kr not in META:
            continue
        name, ticker, sb = META[kr]
        for (y, qn), val in s.items():
            val = abs(val)
            if val > RESERVE_MAX_MN:
                dropped += 1
                continue
            rows.append({
                "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "항목번호": item_num, "항목명": LABELS[item_num], "섹션": section, "레벨": level,
                "공시분기": f"{y}.{qn}Q", "값": round(val, 6),
            })
            written += 1
    stats = {"written": written, "q4_fixed": q4_fixed, "q4_guarded": q4_guarded,
              "fs_api_skipped": fs_api_skipped, "p1": p1_applied, "c_filled": c_filled,
              "forward": forward_added, "backward": backward_added, "dropped": dropped,
              "filled_cells": sorted(filled_cells)}
    return rows, stats


def extract_quarter(cc: str, year: str, reprt: str) -> tuple[dict[int, float], str, set[int]]:
    """BS series is OFS(별도) by default (owner 2026-08-14 P-1: BASIS_CFS is a PL-only
    rule). Conditional CFS fallback (owner 2026-08-15, validation Q-2,
    inbox/parser/20260815T0018Z): ONLY when OFS's core totals (items 1/2/3) are entirely
    absent -- not merely different, structurally missing, e.g. 한화손보 2026.2Q: OFS's BS
    section is a 4-row blank shell (무형자산/투자부동산/유형자산/사용권자산, all amounts
    blank), while CFS has the real 45-row filing. Narrowly scoped on purpose so this can't
    reopen the bug P-1 fixed (삼성생명's CFS returning a stale same-value duplicate across
    quarters while OFS was fine -- OFS has 1/2/3 there, so this fallback never triggers for
    that case). Returns (values, basis_used, pending_seen) -- caller logs which cells fell
    back, since this master has no provenance sidecar to persist it in."""
    out, pending_seen = _extract_from_list(_basis_data(cc, year, reprt, "OFS"))
    if not all(i in out for i in (1, 2, 3)):
        cfs_out, cfs_pending = _extract_from_list(_basis_data(cc, year, reprt, "CFS"))
        if all(i in cfs_out for i in (1, 2, 3)):
            return cfs_out, "CFS", cfs_pending
    return out, "OFS", pending_seen


def main():
    rows = []
    n_companies = 0
    census: dict[str, list[str]] = {}
    # (kr, fy) -> parse_filing()'s item16: that FY's filing's OWN "전기" column for the
    # item5 addition. Only ever non-redundant for fy=2023 (owner Part C, 2026-08-19,
    # inbox/parser/20260819T0116Z) -- see its application near the item5 rollforward below.
    retro_2022: dict[tuple[str, int], float] = {}
    # item -> {kr}: FS-API가 그 항목의 적립예정액 태그를 실제로 실어준 회사들(위
    # PENDING_ACCOUNT_IDS). 이 회사는 series 값에 이미 예정액이 포함돼 있으므로 아래
    # 롤포워드에서 body-XML additions를 또 더하면 안 된다(이중계상 방지).
    fs_pending_by_item: dict[int, set[str]] = {5: set(), 6: set(), 7: set(), 8: set()}
    NAME_OVERRIDE = {"KR0029": "AIG"}  # "AIG손해보험" doesn't resolve; DART lists it as "AIG"
    for kr, (name, ticker, sb) in sorted(META.items()):
        cc = resolve_corp(NAME_OVERRIDE.get(kr, name))
        if not cc:
            census[kr] = ["resolve_corp failed"]
            continue
        files = sorted(CACHE.glob(f"{cc}_*_*_*.json"))
        if not files:
            census[kr] = ["no cache files at all"]
            continue
        periods = sorted({(f.stem.split("_")[1], f.stem.split("_")[2]) for f in files})
        got_any = False
        for year, reprt in periods:
            qlabel = INV_REPRT.get(reprt)
            if not qlabel:
                continue
            vals, basis, pending_seen = extract_quarter(cc, year, reprt)
            if not vals:
                continue
            for it in pending_seen:
                fs_pending_by_item[it].add(kr)
            if basis == "CFS":
                print(f"  CFS fallback: {kr} {year}.{qlabel} (OFS had no 자산/부채/자본)")
            got_any = True
            quarter = f"{year}.{qlabel}"
            for item in ALL_ITEMS:
                if item not in vals:
                    continue
                section, level = _section_level(item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": item, "항목명": LABELS[item], "섹션": section, "레벨": level,
                    "공시분기": quarter, "값": round(vals[item], 6),
                })
        if got_any:
            n_companies += 1
        else:
            census[kr] = [f"{len(periods)} periods in cache, none had usable BS rows"]

    # Tier-2 (15 non-listed, no XBRL FS): same body-XML note extractor, item-renumbered
    # onto this master's 1-7 schema via TIER2_ITEM_MAP.
    tier2_added = 0
    for kr, name in sorted(TIER2.items()):
        if kr not in META:
            continue
        _, ticker, sb = META[kr]
        for fy_dir in sorted(DART.glob("FY*_Q*")):
            m = fy_dir.name.replace("FY", "").split("_Q")
            quarter = f"{m[0]}.{m[1]}Q"
            dirs = sorted((fy_dir / "raw").glob(f"{kr}_*"))
            if not dirs:
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                continue
            try:
                vals, _diag = parse_filing(xmls[0])
            except Exception:
                continue
            fy = int(m[0])
            if m[1] == "4" and 16 in vals:
                retro_2022[(kr, fy)] = vals[16]
            # 전용 핸들러가 있으면 준비금 4종은 그쪽이 우선한다 -- Tier-2도 예외가 아니다.
            # (이 루프가 핸들러를 안 타서 메트라이프 FY2023 2,091,379백만원이 통째로 빠져
            # 2023말 업권합계가 2조원 가까이 모자랐다. 2026-08-19 실측.) 나머지 항목
            # (자산/부채/자본/AOCI)은 아래 TIER2_ITEM_MAP 경로 그대로.
            try:
                _handled2 = reserve_extract.extract(kr, xmls[0])
            except Exception:
                _handled2 = {}
            for _ni, _v in _handled2.items():
                if _v is None:
                    continue
                _sec, _lv = _section_level(_ni)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": _ni, "항목명": LABELS[_ni], "섹션": _sec,
                    "레벨": _lv, "공시분기": quarter, "값": round(_v, 6),
                })
                tier2_added += 1
            _detail_ok = 40 in vals  # 총계 없는 드릴다운은 싣지 않는다 (위 Tier-1 주석 참조)
            for src_item, new_item in (tuple(TIER2_ITEM_MAP.items())
                                       + tuple(BS_DETAIL_ITEM_MAP.items())):
                if new_item in _handled2:
                    continue  # 핸들러가 이미 채운 준비금 항목은 건너뛴다(중복행 방지)
                if src_item in BS_DETAIL_ITEM_MAP and not _detail_ok:
                    continue
                if src_item not in vals:
                    continue
                v = vals[src_item]
                if new_item == 5:
                    # Part A (owner 2026-08-19): item5 = 기적립액(item10) + that FY's
                    # own 적립(환입)예정액(item11) -- every Tier-2 row IS a FY-end
                    # filing (quarter is always "<fy>.4Q"), so this applies unconditionally
                    # here, unlike the Tier-1 path below which only adds it at Q4.
                    v = v + vals.get(11, 0.0)
                elif new_item == 8:
                    # item8 (보증준비금), same combination as item5 above -- raw census
                    # (2026-08-19) confirmed the same 기적립액+적립(환입)예정액=잔액ID for
                    # this concept (KB라이프생명·신한라이프생명, exact match to the last
                    # 백만원). None of the current TIER2 (annual-only) companies have shown
                    # a nonzero 보증준비금 in this session's raw scan, but wired for when
                    # one does rather than left as a silent gap.
                    v = v + vals.get(18, 0.0)
                section, level = _section_level(new_item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                    "레벨": level, "공시분기": quarter, "값": round(v, 6),
                })
                tier2_added += 1
        census.pop(kr, None)

    # Tier-1 reserve-notes fallback (owner P-5: 해약환급금준비금=정규, 비상위험·대손=
    # "가능하면"/pass). Same parse_filing() call Tier-2 already makes -- items 12/14 come
    # back in the same dict at zero extra cost when the table has them ("같은 표에서
    # 딸려 나오면 줍는 정도", not a reason to go fetch anything new). Only fills gaps in
    # what the FS-API cache already produced above; never overwrites a Tier-1 FS-API value.
    by_key: dict[tuple[str, str], set[int]] = {}
    for r in rows:
        by_key.setdefault((r["원보험사코드"], r["공시분기"]), set()).add(r["항목번호"])
    # ⚠ 여기서 by_key만 순회하면 **FS-API가 그 분기에 아무 행도 안 준 회사는 통째로 건너뛴다**
    # -- 폴백이 가장 필요한 케이스에서 폴백이 안 도는 구조적 버그였다(2026-08-19 발견).
    # 실측: 흥국화재 2026.2Q는 DART FS API 응답이 BS 1행짜리 빈 껍데기(사용권자산만)라
    # `by_key`에 (KR0005,'2026.2Q') 키 자체가 안 생겼고, 본문 XML은 디스크에 멀쩡히 있는데도
    # 준비금이 0사로 남았다(같은 회사 2026.1Q는 18항목 정상). 한화손보 2026.2Q도 같은 부류
    # (OFS 4행 blank shell). owner 발주(inbox/parser/20260819T0500Z)의 B그룹 13사는 아예
    # XBRL 자체를 안 내므로 전 분기가 이 상태다. -> 디스크에 raw가 있는 (회사,분기)를 전부
    # 후보로 넣는다. 이미 값이 있으면 아래 `wanted` 계산에서 자연히 건너뛰므로 덮어쓰기 위험 없음.
    for fy_dir in sorted(DART.glob("FY*_Q*")):
        m = fy_dir.name.replace("FY", "").split("_Q")
        quarter = f"{m[0]}.{m[1]}Q"
        for d in sorted((fy_dir / "raw").glob("KR*")):
            kr = d.name.split("_")[0]
            if kr in META and kr not in TIER2:
                by_key.setdefault((kr, quarter), set())
    # FS-API가 실제로 준 자산총계 = 본문 XML 표 선택을 검산할 앵커 (위 게이트 참조).
    bs_anchors: dict[str, dict[int, float]] = {}
    for r in rows:
        if r["항목번호"] == 1 and r["원보험사코드"] not in TIER2:
            bs_anchors.setdefault(r["원보험사코드"], {})[_qnum(r["공시분기"])] = r["값"]
    notes_added = 0
    handler_added = 0
    bs_rejected: list[tuple[str, str]] = []
    handler_cells: set[tuple[str, int, str]] = set()
    for (kr, quarter), present in sorted(by_key.items()):
        if kr in TIER2 or kr not in META:
            continue
        wanted = {new for old, new in NOTE_ITEM_MAP.items() if new not in present}
        if not wanted:
            continue
        fy, qn = quarter.split(".")
        dirs = sorted((DART / f"FY{fy}_Q{qn[0]}" / "raw").glob(f"{kr}_*"))
        if not dirs:
            continue
        xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
        if not xmls:
            continue
        name, ticker, sb = META[kr]
        # 1순위: 회사별 전용 핸들러(scripts/reserve_extract/) -- FS API에 준비금이 없는 27개사용
        # (owner 발주 inbox/parser/20260819T0500Z). 이미 항목번호 5/6/7/8로 돌려주므로 매핑 불요.
        try:
            handled = reserve_extract.extract(kr, xmls[0])
        except Exception:
            handled = {}
        for new_item, v in handled.items():
            if new_item not in wanted or v is None:
                continue
            section, level = _section_level(new_item)
            rows.append({
                "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                "레벨": level, "공시분기": quarter, "값": round(v, 6),
            })
            wanted.discard(new_item)
            handler_cells.add((kr, new_item, quarter))
            handler_added += 1
        # 2순위: 범용 노트 추출(parse_filing) -- 전용 핸들러가 없거나 일부 항목만 채운 경우.
        # BS 총계 폴백도 여기서 같이 태운다(아래).
        try:
            vals, _diag = parse_filing(xmls[0])
        except Exception:
            vals = None
        # BS 총계(항목1/2/3/4) 폴백 -- Tier-1은 총계를 FS-API에서만 가져오는데, 그 분기 응답이
        # 없거나 빈 껍데기면 준비금만 있고 총계가 빈 행이 남는다(census RED). 실측 2026-08-19:
        # 서울보증보험 2024.4Q는 downloader가 사업보고서를 새로 수집해줘 준비금은 잡혔는데
        # 코어 1/2/3/4가 통째로 비어 게이트가 RED 4건을 냈다. 흥국화재 2026.2Q(FS-API가 BS
        # 1행짜리 빈 껍데기)도 같은 부류다 -- validation 20260819T0754Z A-3이 지적한 형태.
        # parse_filing은 이미 Tier-2용으로 BS를 읽으므로(40=자산·41=부채·1=자본·6=AOCI)
        # 그 결과를 TIER2_ITEM_MAP 그대로 재사용한다. **이미 있는 값은 덮지 않는다.**
        if vals and not _bs_table_plausible(bs_anchors, kr, quarter, vals.get(40)):
            bs_rejected.append((kr, quarter))
            vals = {k: v for k, v in vals.items() if k not in BS_SOURCE_KEYS}
        if vals:
            # 드릴다운 세부는 **총계가 있을 때만** 싣는다. 카카오페이손보처럼 부모/자식 2단
            # 들여쓰기 BS(5열, 부모 합계가 다른 열에 있음)는 자식 한 줄만 우연히 잡혀서
            # "헤드라인 없는 세부 한 칸"짜리 (회사,분기)를 만들어냈고, census가 그 키를
            # 인식하는 순간 코어 1/2/3/4 결측으로 RED 4건이 떴다(2026-08-20 실측,
            # KR1098 2024.4Q·2025.4Q). 화면상으로도 총계 없는 드릴다운은 쓸모가 없다.
            detail_ok = (40 in vals) or (1 in present)
            for src_item, new_item in (((40, 1), (41, 2), (1, 3), (6, 4))
                                       + tuple(BS_DETAIL_ITEM_MAP.items())):
                if new_item in present or src_item not in vals:
                    continue
                if src_item in BS_DETAIL_ITEM_MAP and not detail_ok:
                    continue
                section, level = _section_level(new_item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                    "레벨": level, "공시분기": quarter, "값": round(vals[src_item], 6),
                })
                notes_added += 1
        if not wanted or not vals:
            continue
        for old_item, new_item in NOTE_ITEM_MAP.items():
            if new_item not in wanted or old_item not in vals:
                continue
            # item8(보증준비금)은 실측상 생명보험 전용 개념이다 (2026-08-28, validate_
            # statutory_reserves.py R-RSV-8 파생 룰 + census: 이 마스터의 nonzero item8
            # 보유사 16/16이 전부 생명보험, 손해보험은 0사 -- 서울보증보험조차 item8 행이
            # 아예 없다). 손보사 필링에도 "보증준비금" 이름의 표 행이 boilerplate 로 찍혀
            # 있고 값이 0인 경우가 있는데(KB손해보험 FY2024 사업보고서 실측), 이건 그
            # 회사가 이 준비금을 '보유하되 0'이 아니라 개념 자체가 해당 없음(N/A)이다.
            # 미공시를 0으로 채우면 업권 합계·census 가 오염된다(R-RSV-8 메시지 그대로) --
            # 틀린 값(가짜 0)을 싣느니 빈 칸으로 둔다.
            if new_item == 8 and sb != "생명보험":
                continue
            section, level = _section_level(new_item)
            rows.append({
                "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                "레벨": level, "공시분기": quarter, "값": round(vals[old_item], 6),
            })
            notes_added += 1

    # Item 5 (해약환급금준비금 기적립액) roll-forward gap-fill (owner 2026-08-14, hand-verified
    # in insurequant_master_tables.xlsx before this landed): the reserve balance only moves
    # at the FY-end appropriation, so an interim quarter with no independent disclosure
    # carries the same balance as the FY's own most recent known figure.
    #
    # Part A (owner re-authorization, 2026-08-19, inbox/parser/20260819T0116Z -- a prior
    # session had stopped this change; owner explicitly re-instructed it this time, so it is
    # NOT being reverted on the strength of that history): item5 previously = 기적립액
    # (item10) ALONE at every quarter, including FY-end (Q4) -- which is always the
    # PRE-appropriation balance as filed, since that FY's own addition (item11, disclosed in
    # the SAME Q4 filing) only formally posts to 기적립액 once the FOLLOWING year's AGM
    # approves it (verified across 메리츠화재/현대해상/한화손보/롯데손보/삼성화재: FS-API's
    # own dart_SurrenderValueReserve tag reports 0 at that FY's own Q4, then jumps to the
    # full appropriated total starting the NEXT year's Q1 onward, flat until the following
    # Q4). So every company's own FY-end snapshot was the one stale quarter in an otherwise-
    # correct series, and the whole series read a year late. Fix: fold that FY's item11 onto
    # item5's OWN Q4 value below (whatever it already is -- FS-API tag, notes-fallback, or
    # nothing at all, e.g. 삼성화재's 2023.4Q was missing outright) -- then STOP re-adding it
    # at the following Q1 (single point of truth, no double-count).
    additions: dict[tuple[str, int], float] = {}   # (kr, fy) -> that FY's item-11 total
    additions6: dict[tuple[str, int], float] = {}  # same, item-13 (비상위험 적립예정액)
    additions7: dict[tuple[str, int], float] = {}  # same, item-15 (대손 적립예정액)
    additions8: dict[tuple[str, int], float] = {}  # same, item-18 (보증준비금 적립예정액)
    for kr in sorted(META):
        if kr in TIER2:
            continue
        for fy_dir in sorted(DART.glob("FY*_Q4")):
            fy = int(fy_dir.name.replace("FY", "").split("_Q")[0])
            dirs = sorted((fy_dir / "raw").glob(f"{kr}_*"))
            if not dirs:
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                continue
            try:
                vals, _diag = parse_filing(xmls[0])
            except Exception:
                continue
            if 11 in vals:
                additions[(kr, fy)] = vals[11]
            if 13 in vals:
                additions6[(kr, fy)] = vals[13]
            if 15 in vals:
                additions7[(kr, fy)] = vals[15]
            if 16 in vals:
                retro_2022[(kr, fy)] = vals[16]
            if 18 in vals:
                additions8[(kr, fy)] = vals[18]

    quarters_by_co: dict[str, list[tuple[int, int]]] = {}
    for kr, quarter in by_key:
        y, qn = quarter.split(".")
        quarters_by_co.setdefault(kr, []).append((int(y), int(qn[0])))
    # 회사가 관측된 첫 분기와 마지막 분기 **사이의 빈 분기**를 그리드에 넣는다 -- 그래야 아래
    # forward gap-fill이 그 칸까지 닿는다. 준비금 잔액은 결산 처분 시점에만 움직이므로 중간
    # 분기는 직전 분기 잔액을 그대로 들고 가는 게 경제적 실질이고, 이 마스터의 롤포워드가 이미
    # 그 규약이다. 그런데 그리드가 "FS-API가 행을 줬거나 raw가 디스크에 있는 분기"로만 만들어져
    # 있어서, 소스가 통째로 없는 분기는 채워지지도 않았다 -- 실측(2026-08-19): 2023.1Q·2023.2Q는
    # **전 회사 FS-API status 013**(무응답)이고 FY2023_Q2 raw는 6개사분만 디스크에 있어,
    # 한화손해보험·미래에셋생명·동양생명 등이 2023.2Q에 행 자체가 없었다(0이 아니라 결측).
    # 범위 **바깥**으로는 절대 늘리지 않는다(없는 과거/미래를 지어내지 않는다).
    interior_added = 0
    tier2_carry_added = 0
    tier2_carry_cells: list[tuple[str, str]] = []
    max_quarter = max(quarters_by_co[k][0] for k in quarters_by_co) if quarters_by_co else (0, 0)
    for qlist in quarters_by_co.values():
        for cell in qlist:
            if cell > max_quarter:
                max_quarter = cell
    for kr, qlist in quarters_by_co.items():
        if kr not in META:
            continue
        have = set(qlist)
        lo, hi = min(have), max(have)
        if kr in TIER2:
            # owner 결정 2026-08-20: **연1회 공시사도 기말 준비금을 중간분기로 이월한다.**
            # 이 회사들은 감사보고서만 연 1회 내므로 관측 분기가 `<FY>.4Q` 뿐이고, 그래서
            # 중간분기 업권 합계에서 통째로 빠져 있었다 -- 2024.6말 앵커 괴리 -19.3% 의
            # 실제 원인이 이 8개사(2023.4Q 기준 합 5.8조)였다(inbox/parser/20260819T0500Z).
            # 준비금 잔액은 결산 처분 시점에만 움직이므로 "마지막으로 공시된 잔액을 그대로
            # 들고 간다"가 경제적 실질이고, Tier-1 에 이미 적용 중인 규약과 같다.
            # 방향은 **forward(hold-forward) 전용**이다 -- backward 로 채우면 그 시점에
            # 아직 공시되지 않은 값을 과거에 소급하는 look-ahead 가 된다(아래 backward
            # 루프는 TIER2 를 계속 제외한다).
            # 뒤로는 **최대 3분기**만 늘린다: 연간 공시 주기 한 바퀴 분량이고, 공시가 끊긴
            # 회사의 잔액을 무한정 끌고 가지 않게 하는 상한이다.
            y, qn = hi
            extended = (y + (qn + 3 - 1) // 4, (qn + 3 - 1) % 4 + 1)
            hi = min(extended, max_quarter)
            if hi <= (y, qn):
                continue
        for y in range(lo[0], hi[0] + 1):
            for qn in (1, 2, 3, 4):
                cell = (y, qn)
                if lo <= cell <= hi and cell not in have:
                    qlist.append(cell)
                    if kr in TIER2:
                        tier2_carry_added += 1
                        tier2_carry_cells.append((kr, f"{y}.{qn}Q"))
                    else:
                        interior_added += 1
    # P1 (owner 2026-08-19, top of inbox/parser/20260819T0116Z -- posted AFTER, and
    # explicitly superseding, the A/B/C instructions below: "A(기적립액+전입액 산술) →
    # 불필요. 표 값을 그대로 쓴다"): DART 반기/사업보고서 "II. 사업의 내용 -> 5. 재무건전성
    # 등 기타 참고사항" 절의 3기간(당기/전기/전전기) 표 -- the filer's own disclosed ENDING
    # BALANCE, no arithmetic. Found by table ROW CONTENT (parse_financial_soundness_periods,
    # exact concept-name label match), not section markup -- two mutually exclusive DART XML
    # dialects exist (confirmed 2026-08-19: SECTION-2/TITLE/ENG vs HTML-comment "===== N: "),
    # and neither dialect's own subtitle text is consistent across filers, so content-based
    # matching is the only approach that generalizes (verified: reproduces owner's exact
    # hand-checked figures for both 메리츠화재[dialect A]/현대해상[dialect B] byte-for-byte).
    # Tier-1 only (Tier-2 files 감사보고서, no "사업의 내용" chapter to have this in).
    #
    # More authoritative than Part A's fold-in above (a company's own explicit balance, not a
    # derived sum), so it OVERWRITES series[kr][(y,qn)] wherever found. Each filing gives 3
    # periods that overlap adjacent filings (a FY2024_Q4 filing's own 당기 = a FY2025_Q4
    # filing's 전기, both nominally "2024년말") -- resolved by preferring the filing where
    # that quarter WAS 당기 (its own audited figure) over a later filing's comparative column
    # (could be a restatement), via two dicts merged with 당기 taking priority on conflict.
    # 항목6/7(비상위험·대손)도 같은 표에서 공짜로 나오므로 같이 잡되(owner F절: "항목5 56셀,
    # 항목6 19셀, 항목7 19셀"), 이 둘은 series/rollforward 인프라가 없어 rows에 직접 씀 --
    # 겹치는 기존 값은 제거 후 재삽입(교체), 새 분기는 그냥 추가.
    p1_own: dict[tuple[str, int, int], float] = {}
    p1_other: dict[tuple[str, int, int], float] = {}
    p1_67_own: dict[tuple[str, int, int, int], float] = {}
    p1_67_other: dict[tuple[str, int, int, int], float] = {}
    P1_ITEM_MAP = {10: 5, 12: 6, 14: 7}
    p1_diag = 0
    # 분기 스코프: **전 분기(Q1~Q4)**를 스캔한다. 예전엔 Q4+Q2만 봤는데, 이 표는 1·3분기
    # 보고서에도 똑같이 실리고 당기 열이 그 분기의 실제 잔액이다 -- 안 보면 그 칸은 '원천
    # 없음'으로 분류돼 롤포워드 복제 대상이 된다. 실측(inbox/parser/20260820T1900Z):
    # 메리츠화재 2023.1Q 비상위험 328,904 / 대손 63,276 이 원문 표에 그대로 있는데
    # 마스터엔 2022년말 값 321,055 / 42,012 이 복사돼 있었다. 헤더 실측으로 비교 열 매핑도
    # 확인함 -- 1·2·3분기 필링 전부 [당기, 제(n-1)기 연간, 제(n-2)기 연간] 로 같다.
    for kr in sorted(META):
        if kr in TIER2:
            continue
        for fy_dir in sorted(DART.glob("FY*_Q*")):
            m = fy_dir.name.replace("FY", "").split("_Q")
            fy, qn = int(m[0]), int(m[1])
            dirs = sorted((fy_dir / "raw").glob(f"{kr}_*"))
            if not dirs:
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                continue
            try:
                p1_vals, p1d = parse_financial_soundness_periods(xmls[0])
            except Exception:
                continue
            p1_diag += len(p1d)
            for old_item, (v_own, v1, v2) in p1_vals.items():
                new_item = P1_ITEM_MAP[old_item]
                if new_item == 5:
                    p1_own[(kr, fy, qn)] = v_own
                    if v1 is not None:
                        p1_other.setdefault((kr, fy - 1, 4), v1)
                    if v2 is not None:
                        p1_other.setdefault((kr, fy - 2, 4), v2)
                else:
                    p1_67_own[(kr, new_item, fy, qn)] = v_own
                    if v1 is not None:
                        p1_67_other.setdefault((kr, new_item, fy - 1, 4), v1)
                    if v2 is not None:
                        p1_67_other.setdefault((kr, new_item, fy - 2, 4), v2)

    # P1 단위 안전장치 -- 이 표는 "(단위 : 백만원)"이 공시 관행이라 파서가 백만원을 고정값으로
    # 쓰는데, **억원으로 찍는 회사가 있다**(KB손해보험 실측: P1 비상위험 2023.1Q 10,815 인데
    # 같은 회사 FS-API 실적은 1,058,272 = 정확히 ~100배). 그 표의 비교 열이 이미 마스터에
    # 들어가 2021~2022년 KB 비상위험이 9,778/10,583(억원)으로 8칸 박혀 있었다. 회사 자신의
    # 관측치(FS-API/노트/핸들러가 준 값, 롤포워드 이전)와 배수가 10배 밖이면 그 (회사,항목)의
    # P1을 통째로 버린다 -- 준비금 잔액이 분기 사이에 10배 움직이는 일은 없으므로 100배 단위
    # 오판만 걸리고 정상 표는 안 건드린다. 틀린 값보다 빈 칸이 낫다(RESERVE_MAX_MN과 같은 판단).
    observed: dict[tuple[str, int], list[tuple[int, float]]] = {}
    for r in rows:
        if r["항목번호"] in (5, 6, 7, 8):
            observed.setdefault((r["원보험사코드"], r["항목번호"]), []).append(
                (_qnum(r["공시분기"]), r["값"]))
    p1_unit_rejected: list[str] = []

    def _p1_unit_ok(kr: str, item: int, y: int, qn: int, v: float) -> bool:
        obs = observed.get((kr, item))
        if not obs or not v:
            return True                      # 대조할 관측치가 없으면 기각할 근거도 없다
        target = y * 4 + qn
        _, ref = min(obs, key=lambda t: abs(t[0] - target))
        if not ref:
            return True
        ratio = v / ref
        if 0.1 <= ratio <= 10:
            return True
        p1_unit_rejected.append(f"{kr} item{item} {y}.{qn}Q ({v:,.0f} vs 관측 {ref:,.0f})")
        return False

    p1_own = {k: v for k, v in p1_own.items() if _p1_unit_ok(k[0], 5, k[1], k[2], v)}
    p1_other = {k: v for k, v in p1_other.items() if _p1_unit_ok(k[0], 5, k[1], k[2], v)}
    p1_67_own = {k: v for k, v in p1_67_own.items() if _p1_unit_ok(k[0], k[1], k[2], k[3], v)}
    p1_67_other = {k: v for k, v in p1_67_other.items() if _p1_unit_ok(k[0], k[1], k[2], k[3], v)}

    p1_item5 = {**p1_other, **p1_own}
    # 항목6/7의 P1 override도 같은 형태로 정리 -- 아래 공용 롤포워드에 넘긴다.
    p1_item67: dict[int, dict[tuple[str, int, int], float]] = {6: {}, 7: {}}
    for (kr, item, y, qn), v in {**p1_67_other, **p1_67_own}.items():
        p1_item67[item][(kr, y, qn)] = v

    # 항목 5/6/7/8 전부 같은 롤포워드를 탄다 (owner 2026-08-19: "적립액 = 기적립액 +
    # 적립(환입)예정액"이 4개 준비금 공통 공식). 예전엔 item5와 item8에 거의 같은 코드가 두
    # 벌 있었는데 항목6/7까지 세 벌째를 복사하는 대신 `_rollforward_reserve_series`로 합쳤다.
    #
    # Part C(2022년말 소급)는 item5 전용이다 -- 해약환급금준비금은 2023년 신설 제도라 2022년말이
    # 구조적 공백이고, 그 공백을 메울 수 있는 유일한 근거가 일부 필러의 소급가정 전기컬럼
    # (item16, 한화생명 FY2023 각주 "제도의 시행시기는 당기(2023년)부터이나, 전기초부터 적용을
    # 가정하여...전입액을 산출", 전기 값 1,269,282백만)이다. 나머지 3개 준비금은 그 이전부터
    # 존재했으므로 소급 채움 대상이 아니다.
    #
    # negative_guard는 item8만 켠다 -- 한화생명은 확정 양수 신규적립을 평범한 양수로, 흥국생명은
    # 같은 종류의 사건(자사 서술문 "당기 보증준비금 적립 예정액은 149,151백만원입니다"로 양수
    # 확인)을 괄호(음수)로 찍는데 라벨이 양쪽 다 "적립(환입)"/"환입(적립)" 겸용이라 행 단위로는
    # 방향을 가릴 수 없다. 두 개의 상충 사례로 회사별 부호 규칙을 추측하는 대신 집계 단계에서
    # 막는다(음수가 되는 fold-in은 스킵). item5/6/7은 그런 상충 사례가 아직 없어 안 켠다.
    reserve_stats = {}
    rows, reserve_stats[5] = _rollforward_reserve_series(
        5, rows, quarters_by_co, additions, retro=retro_2022,
        p1_overrides=p1_item5, fs_api_pending_companies=fs_pending_by_item[5],
        handler_cells=handler_cells)
    rows, reserve_stats[6] = _rollforward_reserve_series(
        6, rows, quarters_by_co, additions6,
        p1_overrides=p1_item67[6], fs_api_pending_companies=fs_pending_by_item[6],
        handler_cells=handler_cells)
    rows, reserve_stats[7] = _rollforward_reserve_series(
        7, rows, quarters_by_co, additions7,
        p1_overrides=p1_item67[7], fs_api_pending_companies=fs_pending_by_item[7],
        handler_cells=handler_cells)
    rows, reserve_stats[8] = _rollforward_reserve_series(
        8, rows, quarters_by_co, additions8, negative_guard=True,
        fs_api_pending_companies=fs_pending_by_item[8], handler_cells=handler_cells)

    # owner-확정 오버라이드 (마지막 단계) -- 기존 셀이면 값만 교체, 없는 셀이면 새로 추가.
    ov_replaced = ov_added = 0
    if OVERRIDES.exists():
        cells = json.loads(OVERRIDES.read_text(encoding="utf-8")).get("cells", {})
        idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
        for k, spec in cells.items():
            kr, item_s, quarter = k.split("|")
            item = int(item_s)
            v = float(spec["값"])
            hit = idx.get((kr, item, quarter))
            if hit is not None:
                hit["값"] = round(v, 6)
                ov_replaced += 1
            elif kr in META:
                name, ticker, sb = META[kr]
                section, level = _section_level(item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": item, "항목명": LABELS[item], "섹션": section, "레벨": level,
                    "공시분기": quarter, "값": round(v, 6),
                })
                ov_added += 1

    # 오버라이드가 **새로 만든** 기준값을 그 뒤 분기로 이월한다 (2026-08-30).
    #
    # 계측으로 확인한 순서 버그: 오버라이드는 롤포워드가 끝난 뒤에 적용되므로, 오버라이드가
    # 없던 칸을 새로 만들면(`ov_added`) 그 값은 **이월될 기회가 없다.** 실측 —
    # 에이아이에이생명(KR0080, 연1회 공시사)의 item5 는 롤포워드 시점에 2024.4Q·2025.4Q 뿐이라
    # 2025·2026 중간분기만 채워졌고, 오버라이드가 그 뒤에 넣은 2023.4Q(761,784)는 2024.1Q~3Q 로
    # 넘어가지 못했다. 같은 회사 item7 은 원래 2023.4Q 가 있어서 정상 이월됐다 — 항목마다
    # 결과가 갈린 이유가 이것이다.
    #
    # 오버라이드를 롤포워드 앞으로 옮기는 방식은 쓰지 않는다: Q4 fold-in(그 FY 적립예정액을
    # Q4 값에 얹는 단계)이 오버라이드 값 위에 또 더해 **이중계상**이 된다. 그래서 뒤에서
    # 같은 규칙으로 한 번 더 돌리되 **빈 칸만** 채운다(기존 값은 건드리지 않는다).
    ov_carried: list[tuple[str, int, str]] = []
    if ov_added:
        have = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows}
        by_ci: dict[tuple[str, int], dict[tuple[int, int], float]] = {}
        for r in rows:
            if r["항목번호"] in (5, 6, 7, 8) and r["값"] is not None:
                y, qn = r["공시분기"].split(".")
                by_ci.setdefault((r["원보험사코드"], r["항목번호"]), {})[(int(y), int(qn[0]))] = r["값"]
        for (kr, item), s in sorted(by_ci.items()):
            if (kr, item) in NO_FORWARD_FILL_CELLS or kr not in META:
                continue
            for (y, qn) in sorted(quarters_by_co.get(kr, [])):
                if (y, qn) in s:
                    continue
                prev = (y, qn - 1) if qn > 1 else (y - 1, 4)
                if prev not in s:
                    continue
                val = s[prev]
                s[(y, qn)] = val
                quarter = f"{y}.{qn}Q"
                if (kr, item, quarter) in have:
                    continue
                name, ticker, sb = META[kr]
                section, level = _section_level(item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": item, "항목명": LABELS[item], "섹션": section, "레벨": level,
                    "공시분기": quarter, "값": round(val, 6),
                })
                ov_carried.append((kr, item, quarter))
        if ov_carried:
            print(f"  오버라이드 후속 이월: {len(ov_carried)}칸 "
                  f"({', '.join(f'{k} item{i} {q}' for k, i, q in ov_carried[:6])}"
                  f"{' ...' if len(ov_carried) > 6 else ''})")

    rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    # 이월로 생긴 (회사,분기)를 기계가 읽을 수 있게 남긴다. 이 칸들은 **준비금만 있고 코어
    # 총계(1/2/3/4)가 원천적으로 없다** -- 연1회 공시사는 그 분기에 재무제표를 내지 않는다.
    # 검증의 BS 코어 census 가 이 목록을 면제 근거로 쓸 수 있게 하려는 것이다
    # (inbox/validation/20260820T1130Z). 마스터 자체엔 provenance 필드가 없어 사이드카로 뺀다.
    carried = {}
    for kr, q in sorted(set(tier2_carry_cells)):
        carried.setdefault(kr, []).append(q)
    rollfilled: dict[str, dict[str, list[str]]] = {}
    for _it in (5, 6, 7, 8):
        for kr, q in reserve_stats[_it].get("filled_cells", []):
            rollfilled.setdefault(kr, {}).setdefault(str(_it), []).append(q)
    # 오버라이드 후속 이월분도 같은 성격(빌더가 복제한 칸)이라 같이 남긴다 — 검증이
    # "연속 동일값" 을 결함으로 세지 않도록 하는 것이 이 사이드카의 목적이다.
    for kr, _it, q in ov_carried:
        lst = rollfilled.setdefault(kr, {}).setdefault(str(_it), [])
        if q not in lst:
            lst.append(q)
    CARRY_OUT.write_text(json.dumps({
        "_readme": [
            "IFRS17_BS.json 에서 '연1회 공시사 기말 준비금 이월'로 생긴 (회사, 분기) 목록.",
            "owner 결정 2026-08-20 (inbox/parser/20260819T0500Z 확인요청 1번).",
            "이 칸들은 준비금(항목 5/6/7/8)만 있고 코어 총계(1/2/3/4)는 **원천적으로 없다** --",
            "해당 회사는 그 분기에 재무제표를 아예 제출하지 않는다(감사보고서 연 1회만).",
            "값은 직전 연간필링의 기말 잔액을 그대로 들고 온 것(hold-forward, 최대 3분기).",
            "build_ifrs17_bs.py 가 매 빌드에서 다시 쓴다 -- 손으로 고치지 말 것.",
        ],
        "rule": "hold_forward_annual_only_filer",
        "companies": carried,
        "cell_count": len(set(tier2_carry_cells)),
        "_rollforward_readme": [
            "아래 rollforward_filled 는 위 이월과 **다른 축**이다. Tier-1 포함 전 회사에서,",
            "그 (회사,항목,분기)의 원천이 없어 빌더가 직전 관측치를 복제해 채운 칸이다",
            "(forward/backward gap-fill). 2021~2023.1Q 구간이 특히 많다 -- 그 분기는 FS-API 가",
            "전사 013(무응답)이라 원천이 통째로 없다.",
            "복제 칸은 '연속 동일값'의 근거가 될 수 없다(사본을 결함으로 다시 세는 순환).",
            "각 구간의 첫 칸(진짜 공시분기)은 여기 포함되지 않으므로 검증 강도는 유지된다.",
        ],
        "rollforward_filled": rollfilled,
        "rollforward_cell_count": sum(len(v) for d in rollfilled.values() for v in d.values()),
    }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print(f"  owner 오버라이드: {ov_replaced} 교체 + {ov_added} 신규 ({OVERRIDES.name})")
    for it in (5, 6, 7, 8):
        st = reserve_stats[it]
        print(f"  item{it} ({LABELS[it]}): {st['written']} rows = {st['q4_fixed']} Q4-fold-in"
              f" + {st['p1']} P1(표 직접공시) + {st['c_filled']} 2022소급"
              f" + {st['forward']} forward + {st['backward']} backward"
              f" [{st['fs_api_skipped']} skipped: FS-API가 예정액 이미 합산"
              f"{', ' + str(st['q4_guarded']) + ' skipped: 음수방어' if st['q4_guarded'] else ''}"
              f"{', ' + str(st['dropped']) + ' dropped: 성립불가 규모' if st['dropped'] else ''}]")
    print(f"  P1 원천: {len(p1_own)} own-period + {len(p1_other)} comparative-column cells, "
          f"{p1_diag} tables skipped (implausible magnitude)")
    if p1_unit_rejected:
        print(f"  P1 단위 게이트 기각: {len(p1_unit_rejected)}칸 (회사 관측치 대비 10배 밖) "
              + ", ".join(p1_unit_rejected[:10])
              + (f" …외 {len(p1_unit_rejected)-10}" if len(p1_unit_rejected) > 10 else ""))
    if bs_rejected:
        print(f"  본문XML BS 개연성 게이트 기각: {len(bs_rejected)}건 "
              f"(자산총계가 FS-API 실적 대비 ±{BS_PLAUSIBILITY_TOL:.0%} 밖) "
              + ", ".join(f"{k} {q}" for k, q in bs_rejected[:12]))
    print(f"  내부 공백 분기 그리드 보강: {interior_added}칸 (소스가 통째로 없는 중간분기)")
    print(f"  연1회 공시사 기말잔액 이월(owner 2026-08-20): {tier2_carry_added}칸 "
          f"(hold-forward, 마지막 연간필링 뒤 최대 3분기)")
    print(f"wrote {OUT}: {len(rows)} rows ({tier2_added} Tier-2, {notes_added} Tier-1 notes, "
          f"{handler_added} 회사별 핸들러, "
          f"{n_companies}/{len(META)} Tier-1 companies + {len(TIER2)} Tier-2 companies)")
    if census:
        print(f"  {len(census)} companies with NO usable data:")
        for kr, why in sorted(census.items()):
            print(f"    {kr} ({META[kr][0]}): {why[0]}")


if __name__ == "__main__":
    main()
