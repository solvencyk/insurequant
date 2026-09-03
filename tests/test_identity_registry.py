# -*- coding: utf-8 -*-
"""**산술 항등식 레지스트리** — 등식이어야 할 것이 밴드로 구현되는 것을 기계로 막는다.

## 왜 있나 (owner 2026-08-25)

owner 원문: *"별도 축이 아니라 기존 rule 이 의무적으로 돌게 하면 된다고. 내가 정해준 rule 을
성실하게 다 돌리기만 했어도 진작에 잡혔잖아."* / *"0.7~1.4 band 가 아니라 당연히 1 이어야돼."*

owner 가 지정한 등식 "워터폴 CSM상각 = PL CSM상각(부호 반대)" 은 코드에 **등식이 아니라
배수 범위검사**로 들어가 있었다:

    scripts/validate_data_contract.py   _XCHK_LO, _XCHK_HI = 0.4, 2.5

실측: 대조 가능한 346버킷 중 **그 밴드가 잡은 것 0건.** 에이비엘생명 2025.1~3Q 의 복사 결함
(비율 1.09~1.12)이 그냥 통과했고, 데이터를 정정한 뒤 그 6분기 비율은 0.9999~1.0001 이다 —
등식은 원래 성립한다. 게다가 **대조식 자체가 틀려 있었다**(PL 원수 + 재보험을 더했는데
재보험=출재는 별도의 보유 재보험계약자산 워터폴이다). 틀린 식으로 재니 잔차가 커 보였고,
잔차가 커 보이니 밴드를 넓혔고, 밴드가 넓으니 진짜 결함이 지나갔다.

**즉 룰이 없어서가 아니라, 등식이어야 할 것을 2.5배까지 봐주는 밴드로 구현해 둔 것이 원인이다.**

## 이 파일이 강제하는 것

`REGISTRY` 는 이 저장소에서 "A = B" 로 성립해야 하는 관계를 **전수 열거**하고, 각각을 셋 중
하나로 못박는다:

  · `IDENTITY`  — 등식. **반올림 오차만** 허용한다(상대 ≤ `IDENTITY_MAX_REL`).
  · `RANGE`     — 범위검사가 정당한 축(단위오류·off-by-year 같은 총량 오류 그물). **사유 필수.**
  · `HEURISTIC` — 통계적 의심 신호. 등식이 아니다. **사유 필수.**

그리고 다음을 기계로 검사한다:

  1. 선언한 허용오차가 **코드의 실제 상수와 같은가** (몰래 넓히면 여기서 막힌다)
  2. `IDENTITY` 인데 밴드면 FAIL — 넓히려면 `RANGE` 로 재분류하고 사유를 쓰거나,
     `documented_widening`(사유 + 티켓 + 실측비용)을 등재해야 통과한다
  3. 각 등식이 **변이시험에서 실제로 발화**하는가 (값을 흔들었는데 아무 룰도 안 울면 무검사)
  4. K-ICS 룰엔진이 내보내는 룰 id 가 **전부 여기 등재돼 있는가** (새 룰이 성격 분류 없이
     들어오는 것을 막는다)
  5. 검증기 소스에 **등재되지 않은 새 임계 상수**가 생기면 잡는다

## 선례

`tests/test_push_gate_wiring.py`(게이트가 훅에 걸려 있는가) ·
`tests/test_rule_coverage_manifest.py`(어떤 칸이 어떤 룰에 실제로 검사받는가) 와 같은 계열이다.
저 둘은 "룰이 도는가" 를 강제한다. 이 파일은 **"도는 룰이 등식인가"** 를 강제한다.
"""
from __future__ import annotations

import ast
import copy
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

# ---------------------------------------------------------------------------
# IDENTITY 의 허용오차 상한 — "반올림 수준" 의 기준
# ---------------------------------------------------------------------------
# owner 는 "당연히 1" 이라고 말한다. 그 말을 기계가 읽을 수 있는 형태로 옮기면:
# **등식의 상대 허용오차는 이 저장소 데이터의 반올림 단위를 넘을 수 없다.**
#
# 실측한 반올림 단위(저장 granularity):
#   · kics_disclosure       억원 정수  → 항당 ±0.5억. 합 항등식은 최대 7항 → ±3.5억이 상한이고
#                                        룰엔진은 그보다 좁은 flat 2.0억을 쓴다.
#   · CSM_waterfall(루트)   억원 1자리 → ±0.05억
#   · PL_breakdown          백만원      → ±0.005억
#   · csm_waterfall(viz)    백만원      → ±0.5백만
# 상대폭으로 환산하면 실측 잔차 분포는 전부 p90 ≤ 0.1% 안에 들어온다(아래 각 항목의
# `measured` 참조). 그래서 상한을 **1%** 로 잡는다 — 관측 반올림폭의 10배 이상 여유이며,
# owner 가 문제 삼은 "2.5배 밴드" 와는 두 자릿수 차이다. 1% 를 넘겨야 하면 그건 반올림이
# 아니라 **설명이 필요한 계통 차이**이므로 RANGE 로 재분류하거나 documented_widening 을 쓴다.
IDENTITY_MAX_REL = 0.01

# 사유는 "느슨하게 했음" 같은 한 줄로 때울 수 없게 최소 길이를 건다(면제를 값싸게 만들지 않는다).
MIN_REASON_CHARS = 60


_FN_CACHE: dict[Path, set[str]] = {}


def _functions_in(path: Path) -> set[str]:
    """파일이 정의하는 함수 이름 전부(중첩 포함). impl 선언이 썩는 것을 막는다."""
    if path not in _FN_CACHE:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        _FN_CACHE[path] = {n.name for n in ast.walk(tree)
                           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return _FN_CACHE[path]


def _c(module: str, name: str):
    """검증기 모듈의 살아 있는 상수를 읽는다 — 선언과 코드가 갈라지면 테스트가 막는다."""
    mod = __import__(module, fromlist=["*"])
    return getattr(mod, name)


# ===========================================================================
# REGISTRY
# ===========================================================================
# 필드
#   statement : 등식의 진술. **부호 규약 포함.**
#   impl      : [(파일, 함수)] — 구현 위치. 같은 등식이 여러 곳이면 전부 적는다.
#   kind      : IDENTITY | RANGE | HEURISTIC
#   tol       : 현재 구현된 허용오차 {"abs":.., "rel":.., "unit":".."}
#   tol_from  : [(모듈, 상수명, 선언값)] — 코드에서 읽어 대조한다(선언 ↔ 코드 동기화 강제)
#   measured  : 실측 잔차 분포 요약(이 tol 이 왜 이 값인지의 증거)
#   reason    : RANGE/HEURISTIC 필수 — 왜 등식이 아닌가
#   documented_widening : IDENTITY 인데 상한을 넘길 때 필수 {"why","ticket","measured_cost"}
#   mutation  : "inline"(아래 변이시험이 직접 흔든다) | "tests/<file>"(그 테스트에 위임)
REGISTRY: dict[str, dict] = {
    # -------------------------------------------------------------------
    # IFRS17 — CSM_waterfall / PL_breakdown
    # -------------------------------------------------------------------
    "csm_amort_identity": {
        "statement": "PL(원수CSM상각 + 수재CSM상각) == |CSM_waterfall.CSM상각|. "
                     "PL 은 보험수익 기여라 양수, 워터폴은 CSM 감소라 음수 — 절댓값으로 맞춘다. "
                     "출재(재보험/9-1)는 **보유** 재보험계약자산이라 더하지 않는다.",
        "impl": [("scripts/validate_master_tables.py", "_check_csm_crosscheck"),
                 ("scripts/validate_data_contract.py", "check_cross_source")],
        "kind": "IDENTITY",
        "tol": {"abs": 0.1, "rel": 0.0005, "unit": "억원"},
        "tol_from": [("validate_master_tables", "CSM_AMORT_TOL_ABS_EOK", 0.1),
                     ("validate_master_tables", "CSM_AMORT_TOL_REL", 0.0005),
                     ("validate_data_contract", "CSM_AMORT_TOL_REL", 0.0005)],
        "measured": "346버킷: 잔차 p50 0.029억 · p75 0.040억 · p90 0.21억, 318건이 tol 안. "
                    "밖 28건은 data/_gold/csm_amort_identity_ledger.json 에 건별 박제. "
                    "종전 밴드(배수 0.4~2.5, 대조식 원수+재보험)가 잡은 것은 0건이었다.",
        "mutation": "inline",
    },
    "GOLD_OVERLAY_DRIFT": {
        "statement": "빌더 fresh 소스의 값 == gold 오버레이의 값. 같으면 gold 는 화면을 안 바꾸는 "
                     "**마스크**이고(그래서 밑에서 빌더가 회귀해도 아무도 못 본다), 그 상태를 "
                     "셀 단위로 박제해 두었다가 등식이 깨지면 RED. 단위·부호는 두 파일이 같은 "
                     "표기를 쓴다(CSM 억원 · PL 백만원, 변환 없음).",
        "impl": [("scripts/validate_data_contract.py", "gold_overlay_verdict"),
                 ("scripts/validate_data_contract.py", "check_gold_overlay")],
        "kind": "IDENTITY",
        "tol": {"abs": 0.05, "rel": 0.0, "unit": "각 마스터 표기단위(CSM 억원 · PL 백만원)"},
        "tol_from": [("validate_data_contract", "GOLD_OVERLAY_TOL_EXACT", 0.005),
                     ("validate_data_contract", "GOLD_OVERLAY_TOL_ROUND", 0.05)],
        "measured": "2026-08-30 전수(CSM 270칸 · PL 198칸). |소스−gold| 가 두 덩어리로 갈린다: "
                    "CSM 은 소스(csm_waterfall_master_diag)가 소수 1자리, gold 가 2자리라 재현의 "
                    "상한이 정확히 0.05 이고(28건 0.00 · 58건 0<d≤0.05), 그 위 첫 값은 0.30 이다. "
                    "PL(백만원)은 26건 0.00 · 3건 ≤0.0317 이고 그 위 첫 값이 18.0 — 0.05 는 두 "
                    "경우 모두 빈 구간 안이다. 넓히면 마스크 집합이 부풀어 그만큼 DRIFT 가 안 "
                    "터지므로, tests/test_rule_coverage_manifest.GOLD_OVERLAY_CENSUS 가 마스크 "
                    "칸 수(86/29)를 박제해 그 경로를 막는다. 마스크 115칸은 "
                    "data/_gold/gold_overlay_ledger.json 에 셀 단위 박제.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "csm_closing_identity_root": {
        "statement": "기초CSM + 신계약CSM + 이자부리 + 가정및경험조정 + CSM상각 == 기말CSM "
                     "(루트 CSM_waterfall.json, 억원. 상각은 음수로 저장돼 있어 그대로 더한다)",
        "impl": [("scripts/validate_master_tables.py", "_check_closing_identity")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.001, "unit": "억원"},
        "tol_from": [],   # 함수 내부 리터럴 max(0.001*|기말|, 2.0)
        "measured": "358버킷 전건 통과(fail=0). 억원 1자리 6항 합의 반올림 상한 ±0.3억보다 넉넉.",
        "mutation": "inline",
    },
    "csm_closing_identity_viz": {
        "statement": "위와 같은 rollforward 항등식을 연간 viz 산출물(백만원)에서 재검산",
        "impl": [("scripts/validate_csm_waterfall.py", "check_balance")],
        "kind": "IDENTITY",
        "tol": {"abs": 200.0, "rel": 0.001, "unit": "백만원"},
        "tol_from": [("validate_csm_waterfall", "REL_TOL", 0.001),
                     ("validate_csm_waterfall", "ABS_TOL_MN", 200.0)],
        "measured": "41사: 0.5%/500mn·0.1%/200mn·0.05%/100mn 어디서도 위반 0 — "
                    "2026-08-25 에 루트 구현과 폭을 맞췄다(조이는 비용 0).",
        "mutation": "inline",
    },
    "csm_within_fy_opening": {
        "statement": "YTD 컨벤션상 같은 FY 의 모든 분기 기초CSM 은 동일하다(= 전년말 기말)",
        "impl": [("scripts/validate_master_tables.py", "_check_plausibility"),
                 ("scripts/validate_csm_continuity.py", "check_company")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.01, "unit": "억원"},
        "tol_from": [("validate_csm_continuity", "WITHIN_FY_TOL", 0.01)],
        "measured": "92 FY-그룹. master_tables 는 max(2억,0.5%)+문서화 면제셋으로 이미 엄격. "
                    "csm_continuity 는 2026-08-25 에 5% → 1% (새 blocking RED 0 — 유일하게 "
                    "새로 걸린 메리츠화재 FY2023 은 WFY_EXCEPTIONS 등재분이라 YELLOW).",
        "mutation": "inline",
    },
    "csm_fy_boundary_continuity": {
        "statement": "기초CSM[FY.1Q] == 기말CSM[prevFY.4Q] (FY 경계 연속성)",
        "impl": [("scripts/validate_data_contract.py", "check_csm_continuity"),
                 ("scripts/validate_master_tables.py", "_check_plausibility")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.005, "unit": "억원"},
        "tol_from": [("validate_data_contract", "CSM_CONT_TOL_REL", 0.005),
                     ("validate_data_contract", "CSM_CONT_TOL_ABS", 2.0)],
        "measured": "면제는 건별 등재(하나생명 2024.4Q Δ+73억, raw 확정 소급재작성)이며 "
                    "박제 잔차를 매 실행 재검산한다. owner 2026-06-16: break 는 무조건 RED.",
        "mutation": "inline",
    },
    "csm_boundary_magnitude_net": {
        "statement": "위 경계 항등식의 **총량 그물** — off-by-year / 별도↔연결 / ×N basis swap "
                     "처럼 자릿수급으로 틀어진 것만 잡는다",
        "impl": [("scripts/validate_csm_continuity.py", "check_company")],
        "kind": "RANGE",
        "tol": {"abs": 0.0, "rel": 0.10, "unit": "비율"},
        "tol_from": [("validate_csm_continuity", "BOUNDARY_TOL", 0.10)],
        "measured": "69 경계. 미세 항등식은 위 `csm_fy_boundary_continuity` 가 max(2억,0.5%) + "
                    "건별 면제 등재부로 이미 검사한다 — 여기서 같은 폭으로 다시 걸면 같은 "
                    "면제를 두 곳에 복사해야 한다(면제 중복이 이 저장소의 사고 유형).",
        "reason": "이 축의 목적은 등식의 미세 잔차가 아니라 **연도 뒤바뀜·기준 뒤바뀜** 같은 "
                  "총량 오류다(파일 docstring: closing-identity 가 구조적으로 못 보는 것). "
                  "그 오류는 항상 10% 를 크게 넘으므로 넓은 폭이 목적에 맞고, 좁히면 이미 "
                  "판별이 끝난 건을 면제 없이 다시 RED 로 올린다. 미세 등식의 집행자는 "
                  "validate_data_contract 의 CSM_CONT 다.",
        "mutation": "inline",
    },
    "pl_bridge": {
        "statement": "PL 손익 다리 9식(2026-08-28: 총포괄손익 == 당기순이익 + 기타포괄손익 신설,"
                     " ticket inbox/parser/20260828T0113Z; 2026-08-28 기타포괄손익 == "
                     "26+27+28+29+30+32(item32=기타 포괄손익(미분류) catch-all) 추가, ticket "
                     "inbox/parser/20260828T1600Z) + 보험손익 dual-form"
                     "(보험손익 == 생명장기 + 자동차 + 일반, 또는 그 합 + 기타영업수익 − "
                     "기타사업비용; 2026-08-29 leg-coverage 확장 — 결측 LOB 다리를 0 으로 채워 "
                     "판정하므로 다리가 빠진 버킷도 SKIP 이 아니라 PASS/FAIL 로 착지한다, "
                     "ticket inbox/validation/20260829T1500Z; 2026-08-29 b — ΣLOB 에 **추가 LOB "
                     "다리**(항목번호 `2-N`, load_pl_extra_lob) 가산. 표준 3슬롯이 LOB 의 전부라는 "
                     "가정이 재보험사에서 오탐을 냈다, ticket inbox/parser/20260829T1700Z §2). 예: 영업이익 == "
                     "보험손익 + 투자손익, 당기순이익 == 세전이익 − 법인세 (백만원, 부호는 "
                     "마스터 저장 부호 그대로)",
        "impl": [("scripts/validate_master_tables.py", "_check_pl_bridge")],
        "kind": "IDENTITY",
        "tol": {"abs": 200.0, "rel": 0.001, "unit": "백만원"},
        "tol_from": [("validate_master_tables", "DEFAULT_FLOOR", 200.0)],
        "measured": "3,057 통과 / 35 실패(전건 data/_gold/pl_bridge_baseline.json 등재) / 468 "
                    "skip (2026-08-29 leg-coverage 신설 전: 3,025P/13F/522S; 추가 LOB 가산 전: "
                    "3,045P/47F/468S). 보험손익 축만 떼어 보면 356 버킷 중 306 통과 · 32 실패 · "
                    "18 skip 이고, 그 18 은 전부 item1 자체가 결측이라 좌변이 없는 2023 분기다"
                    "(NOLHS 로 건별 인쇄, coverage census 소관). 신설 전에는 결측 다리 때문에 "
                    "71 버킷(19.9%)이 통째 SKIP 이었고 coverage census 의 key_items 에도 "
                    "13(자동차)·14(일반)이 없어 두 검사가 같은 구멍을 공유했다. "
                    "**leg-coverage 신설판은 코리안리재보험 12분기를 오탐했다**(2026-08-29 b 정정): "
                    "item13(자동차) 결측이 1,456~53,464백만원을 싣고 있다고 찍었지만 원문에 자동차 "
                    "LOB 자체가 없고(parser 전 분기 raw grep, commit 15a61d1), 잔차는 통째로 "
                    "등식이 빠뜨린 네 번째 LOB 다리 item`2-1`(장기재보험 손익)이었다 — 빌더의 "
                    "Tier-2 RC 게이트는 같은 항을 `_extra_lob` 으로 이미 더하고 있었으므로 "
                    "**빌더와 검증기가 서로 다른 등식을 쓰고 있었다.** 가산 후 12분기 전부 "
                    "|잔차| ≤ 2.8백만원, 새로 깨지는 버킷 0건(scripts/_probes/"
                    "probe_20260829_extra_lob_simulation.py, 356 버킷 전수). 하이픈 항목 census: "
                    "마스터의 하이픈 항목번호는 154셀(코리안리 `2-1`~`12-1` 11종 × 14분기)이 "
                    "전부이고, 그중 어떤 룰이라도 읽는 것은 `4-1`(수재 CSM상각, CSM_AMORT_PL_LEGS)"
                    "과 이번에 배선한 `2-1` 둘뿐 — 나머지 9종 126셀은 여전히 무검사다. 그 9종의 "
                    "부모-자식 항등식(2-1=3-1+8-1 등 3식)은 **배선하지 않았다**: 핸들러가 "
                    "item7/12 를 plug 로, item2 를 합으로 만들어(pl_breakdown/companies.py::leg) "
                    "잔차가 14/14 전건 정확히 0.000000000 인 동어반복이라 배선하면 커버리지를 "
                    "만들어낼 뿐 검증이 안 된다(실측 scripts/_probes/"
                    "probe_20260829_hyphen_tautology.py). "
                    "0.1% 는 백만원 정수 저장의 반올림 폭. 8번째 식(총포괄손익=24+25)만 "
                    "따로 보면 282개 CIS-보유 셀 전건 잔차 0.000(scripts/_probes/"
                    "census_oci_labels_pass2.py) — 반올림조차 없이 정확히 닫힌다. 9번째 식"
                    "(기타포괄손익=26+27+28+29+30+32)은 221개 항 전부 존재 셀 중 220 통과·1 실패"
                    "(교보생명보험 2025.4Q, DART 이중 CF헤지 태그 — item28이 dominant 태그만 "
                    "취해 나머지 태그값이 어느 항등식에도 안 잡히는 기존 설계, baseline 등재), "
                    "132건은 잔차 정확히 0.000(scripts/_probes/residual_distribution_item32.py).",
        "mutation": "inline",
    },
    "tax22_source_crosscheck": {
        "statement": "|PL 항목22(세전이익) − 항목24(당기순이익)| == |DART FS-API 원천 법인세 "
                     "계정(ifrs-full_IncomeTaxExpenseContinuingOperations)| (백만원). "
                     "부호는 대조하지 않는다 — 발행사마다 법인세비용의 부호 관행이 다르고"
                     "(양수 금액 vs 괄호 차감) 그것이 애초에 빌더가 item23 을 잔차로 덮은 "
                     "이유다(build_pl_breakdown.assemble L226-228 주석). "
                     "2026-08-29 신설, ticket inbox/validation/20260829T2130Z.",
        "impl": [("scripts/validate_master_tables.py", "_check_tax22_crosscheck")],
        "kind": "IDENTITY",
        "tol": {"abs": 200.0, "rel": 0.001, "unit": "백만원"},
        "tol_from": [("validate_master_tables", "TAX22_FLOOR", 200.0),
                     ("validate_master_tables", "TAX22_REL", 0.001)],
        "measured": "**item22 를 보는 유일한 룰이다.** `당기순이익 = 세전 − 법인세` 는 빌더가 "
                    "item23 을 22−24 로 418/418 무조건 덮어써서 구성상 참이고, 그래서 item22 를 "
                    "max(10,000백만, |v|×30%) 흔들어도 게이트 전체(validate_master_tables + "
                    "validate_data_contract)에서 신규 RED 이 **0 건**이었다"
                    "(scripts/_probes/probe_20260829_pl_eqs_mutation.py · "
                    "probe_20260829_pl_eqs_datacontract_mutation.py). 원천 법인세 계정은 그 "
                    "418/418 에 실재하는데 assemble() 이 곧바로 버린다. "
                    "전 버킷 시뮬레이션(scripts/_probes/probe_20260829_item22_tax_crosscheck_sim.py, "
                    "356 버킷): 대조가능 **282 · PASS 282 · FAIL 0**, 잔차 |원천세|−|22−24| 는 "
                    "median=p90=max=**0.000백만원**(127건은 정확히 0, 282건 전부 ≤1). "
                    "SKIP 74 = FS-API 캐시 없음 56(핸들러/HTML 경로 회사) + 마스터 22/24 결측 18. "
                    "**그 74 버킷의 item22 는 여전히 무검사다** — 게이트가 사유별로 세어 인쇄한다. "
                    "변이시험(scripts/_probes/probe_20260829_tax22_rule_mutation.py): 같은 주입에 "
                    "NAIVE·CONSTRUCTIVE 둘 다 **탐지율 100.0%**(282/282 신규 FAIL) — 배선 전 "
                    "0.0% 에서 바뀐 지점이다. "
                    "**증명하지 못하는 것**: _parse 가 22·24·23 을 일관되게 잘못된 기준(연결 vs "
                    "별도)에서 골랐다면 셋 다 같이 틀려 이 등식은 닫힌다. 기준 오선택은 다른 축 소관.",
        "mutation": "inline",
    },
    "pl_oci_vs_bs_aoci": {
        "statement": "PL 항목25(기타포괄손익) 값_당분기 ≈ IFRS17_BS 항목4(기타포괄손익 누계액) "
                     "의 QoQ 증감(백만원). owner 티켓 inbox/parser/20260828T0113Z §작업3 룰2.",
        "impl": [("scripts/validate_master_tables.py", "_check_pl_oci_vs_bs_aoci")],
        "kind": "HEURISTIC",
        "tol": {"abs": 2000.0, "rel": 0.20, "unit": "백만원 / 비율(|ΔBS| 기준)"},
        "tol_from": [("validate_master_tables", "OCI_AOCI_TOL_ABS_MN", 2000.0),
                     ("validate_master_tables", "OCI_AOCI_TOL_REL", 0.20)],
        "measured": "scripts/_probes/simulate_pl_oci_vs_bs_aoci.py, 259개 비교가능 셀(양쪽 "
                    "다 있는 (회사,분기)): 잔차 중앙값·p25 = 정확히 0.000(다수가 완전히 닫힘 — "
                    "개념 자체는 맞다는 근거) 이지만 p90=13,770백만·p95=59,067백만·"
                    "max=5,391,139백만(삼성생명 2025.4Q, 상대 22.8%). rel100%+abs10,000백만 "
                    "관대한 문턱에서도 259건 중 2건은 못 닫힌다. 최악 30건 중 17건(56.7%, "
                    "기저율 25% 대비 과다)이 4Q(연차) 분기에 몰려 있다 — 실제 배선(20%/2,000백만) "
                    "기준 259건 중 13건 flag(94.6% 통과). 결과: artifacts/parser/"
                    "pl_oci_vs_bs_aoci_simulation.json.",
        "reason": "등식이 아니다 — 재분류조정(FVOCI 매도 시 누계 OCI가 P&L로 이동)·자본거래·"
                  "법인세 조정이 그 분기 CIS 순유량과 BS 잔액 QoQ 증감을 회계상 구조적으로 "
                  "갈라놓을 수 있다. 4Q 쏠림은 이 저장소에 이미 문서화된 별개 패턴(build_root_"
                  "masters.py: '신계약CSM 당분기가 음수(4Q 연차 재서술 artifact)')과 같은 계열 "
                  "— 4Q 연차보고서가 계리적 가정 개정 등을 자본에 직접 반영하는 사례. owner "
                  "지시대로 RED 아닌 YELLOW(다운스트림/exit code 미차단)로 배선했다.",
        "mutation": "tests/test_master_tables_golden.py",
    },
    "dividend_payout": {
        "statement": "배당성향 == 배당총액 / 당기순이익 × 100 (DART 공시 배당성향 대조)",
        "impl": [("scripts/validate_data_contract.py", "check_dividend")],
        "kind": "IDENTITY",
        "tol": {"abs": 0.5, "rel": 0.0, "unit": "%p"},
        "tol_from": [("validate_data_contract", "DIV_PAYOUT_TOL_PP", 0.5)],
        "measured": "DART 공시 배당성향이 소수 1자리 반올림이라 ±0.05%p 가 이론 상한이고 "
                    "0.5%p 는 그 10배 여유. 분자·분모 각각의 억원 반올림까지 흡수한다.",
        "mutation": "tests/test_master_tables_golden.py",
    },
    "capsec_master_vs_source": {
        "statement": "자본증권 마스터의 발행잔액 == per-bond 원천(DART/FSC)의 해당 슬라이스 합",
        "impl": [("scripts/validate_data_contract.py", "check_census")],
        "kind": "IDENTITY",
        "tol": {"abs": 1.0, "rel": 0.01, "unit": "억원"},
        "tol_from": [("validate_data_contract", "_CAPSEC_AMOUNT_TOL_EOK", 1.0),
                     ("validate_data_contract", "_CAPSEC_AMOUNT_TOL_REL", 0.01)],
        "measured": "per-bond 원천은 원 단위, 마스터는 억원 — 종목 수만큼 반올림이 누적된다. "
                    "1% 는 IDENTITY 상한 그 자체이며 더 넓히면 RANGE 로 재분류해야 한다.",
        "mutation": "tests/test_deploy_assets.py",
    },
    "capsec_prior_drop": {
        "statement": "직전 배포본 대비 전체 발행잔액 급감 감시(보조 그물)",
        "impl": [("scripts/validate_data_contract.py", "check_census")],
        "kind": "HEURISTIC",
        "tol": {"abs": 0.0, "rel": 0.20, "unit": "비율"},
        "tol_from": [("validate_data_contract", "_CAPSEC_PRIOR_DROP_REL", 0.20)],
        "measured": "YELLOW 전용. 1차 판정은 원천 레코드 존재 여부(위 항목)가 한다.",
        "reason": "등식이 아니다 — 발행·상환으로 잔액은 정당하게 움직인다. 20% 는 '이 정도 "
                  "급감이면 사람이 봐야 한다'는 임계일 뿐 어떤 값이 옳다는 주장이 아니다.",
        "mutation": "tests/test_deploy_assets.py",
    },
    "ifrs17_bs_balance": {
        "statement": "자산총계(item1) == 부채총계(item2) + 자본총계(item3)  (IFRS17_BS, 백만원)",
        "impl": [("scripts/validate_data_contract.py", "check_ifrs17_bs")],
        "kind": "IDENTITY",
        "tol": {"abs": 1.0, "rel": 0.001, "unit": "백만원"},
        "tol_from": [("validate_data_contract", "IFRS17_BS_TOL_ABS", 1.0),
                     ("validate_data_contract", "IFRS17_BS_TOL_REL", 0.001)],
        "measured": "회계 항등식이라 원문에서 반드시 닫힌다 — 안 닫히면 연결/별도 오선택 · "
                    "단위 오적용 · 행 오인식 중 하나다. 0.1% 는 백만원 정수 저장의 반올림 폭.",
        "mutation": "tests/test_ifrs17_bs_golden.py",
    },
    "csm_steps_dart_vs_ir": {
        "statement": "DART CSM 워터폴 단계 ↔ IR 팩트시트 같은 단계",
        "impl": [("scripts/validate_data_contract.py", "check_cross_source")],
        "kind": "RANGE",
        "tol": {"abs": 1.0, "rel": 0.005, "unit": "억원"},
        "tol_from": [("validate_data_contract", "IR_STEP_TOL_ABS_EOK", 1.0),
                     ("validate_data_contract", "IR_STEP_TOL_REL", 0.005)],
        "measured": "2026-08-26 실측: 파싱본 6개(KR0008/KR0011/KR0068/KR0069×2/KR0087) "
                    "36 step-pair 전건 |Δ| ≤ 0.055억, worst Δ/tol 0.0188. 그 전 밴드 "
                    "max(5%,100억) 은 커밋 8a3b930 의 연결 누출(Δ 69.6~1,043.9억)을 "
                    "**0/6 놓쳤다** — 조인 뒤 6/6 검출, live RED 는 0.",
        "reason": "등식이 아니다 — IR 원천마다 **인쇄 정밀도**가 다르다(조원 차트는 ±50억 "
                  "그리드). 스코프는 이제 확정됐다: IR = 별도(삼성생명 시트 라벨 "
                  "`CSM 상세 (별도)` · 한화생명 각주 `※ SAP 기준(별도)`)이고 마스터도 별도라 "
                  "**두 원천은 같은 숫자여야 한다**. 그래서 종전의 '작성시점·범위가 달라 "
                  "같을 이유가 없다' 는 사유는 폐기하고, 남은 폭은 원천 정밀도 몫만이다.",
        "mutation": "tests/test_deploy_assets.py",
    },
    "nb_csm_multiple": {
        "statement": "산출 신계약 CSM 배수 ≈ IR 공시 배수",
        "impl": [("scripts/validate_nb_csm_multiple.py", "main")],
        "kind": "HEURISTIC",
        "tol": {"abs": 3.0, "rel": 0.25, "unit": "배"},
        "tol_from": [("validate_nb_csm_multiple", "REL_TOL", 0.25),
                     ("validate_nb_csm_multiple", "ABS_TOL", 3.0)],
        "measured": "분모(월납환산 초회보험료)의 스코프가 회사·IR 마다 다르다(보장성만/전체/"
                    "개인만). 같은 숫자가 나올 수 없다.",
        "reason": "분자는 DART 신계약 CSM, 분모는 KIDI·IR 의 월납환산 보험료인데 **분모의 "
                  "정의가 회사마다 다르다**(PREFERRED_SCOPE 가 회사별로 다른 것이 그 증거). "
                  "'얼추 비슷한가' 를 보는 축이지 등식이 아니다.",
        "mutation": "tests/test_deploy_assets.py",
    },
    "sensitivity_unit_sanity": {
        "statement": "회사별 max|csm_delta| 가 또래 median 대비 자릿수급으로 튀는가(단위 미정규화)",
        "impl": [("scripts/validate_master_tables.py", "sensitivity_unit_sanity")],
        "kind": "RANGE",
        "tol": {"abs": 0.0, "rel": 1000.0, "unit": "배(또래 median 대비)"},
        "tol_from": [],
        "measured": "현대해상이 원 단위라 삼성화재의 640배였던 사고의 회귀가드.",
        "reason": "회사마다 CSM 규모가 실제로 100배 다르다 — 같아야 할 값이 아니다. 이 축은 "
                  "**단위(원/만원/억원) 미정규화**라는 자릿수 오류만 잡도록 설계된 범위검사다.",
        "mutation": "tests/test_master_tables_golden.py",
    },
    "kics_rate_sensitivity_ratio": {
        "statement": "금리민감도 표: 비율[c] == 지급여력금액[c] / 지급여력기준금액[c] × 100 "
                     "(충격 컬럼 c 각각)",
        "impl": [("scripts/validate_kics_rate_sensitivity.py", "main")],
        "kind": "IDENTITY",
        "tol": {"abs": 0.5, "rel": 0.005, "unit": "%p"},
        "tol_from": [],
        "measured": "억원 정수 분자·분모의 반올림이 비율에 옮겨붙는 폭. RS1 실측 위반 0.",
        "mutation": "tests/test_deploy_assets.py",
    },
    "kics_rate_sensitivity_anchor": {
        "statement": "금리민감도 base 컬럼(적용전) == kics_disclosure item1 / item14 / item27",
        "impl": [("scripts/validate_kics_rate_sensitivity.py", "main")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원(비율은 0.5%p)"},
        "tol_from": [],
        "measured": "문서화된 예외 1건(DB손해 2025.2Q — 민감도표는 별도, 헤드라인은 연결).",
        "mutation": "tests/test_deploy_assets.py",
    },
    # -------------------------------------------------------------------
    # K-ICS 룰엔진 — 변이시험은 tests/test_rule_coverage_manifest.py 가 전수로 돌린다
    # (항목 × 컬럼을 흔들어 finding status 가 바뀌는지 본다. 여기서 재구현하지 않는다.)
    # -------------------------------------------------------------------
    **{
        rid: {
            "statement": stmt,
            "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
            "kind": "IDENTITY",
            "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
            "tol_from": [],
            "measured": "flat eff_tol 2.0억 = 억원 정수 저장 항의 반올림(±0.5) 누적 상한. "
                        "이미지/OCR 회사만 10.0.",
            "mutation": "tests/test_rule_coverage_manifest.py",
        }
        for rid, stmt in {
            "1": "item1(지급여력금액) == item2(기본자본) + item3(보완자본)",
            "2": "item4(Ⅰ 순자산) == sum(item5..item11)",
            "4": "item15(기본요구자본) == sqrt([17,18,19,20]·R4) + item21",
            "5": "item14(지급여력기준금액) == item15 − item22 + item23",
            "6": "item16(분산효과) == sum(item17..item21) − item15",
            "2_tier1_bridge": "item2 == item4 − (item12 − 한도초과) − item13",
            "2_tier1_bridge_post": "위 다리 등식을 [값_적용후] 컬럼에서 재검산 — 적용전만 배선하고 적용후를 안 걸면 그 컬럼이 통째로 무방비가 된다(2026-08-21 실측)",
            "3_tier2_composition": "item3 == min(47,48)+49 (CAPPED) | == 47 (UNCAPPED) | == item13 (TFI_NA)",
            "3_tier2_composition_post": "위 보완자본 구성 등식을 [값_적용후] 컬럼에서 재검산 (적용후 관계식 미확립 구간은 YELLOW 로 낸다)",
            "50_tfi_tier_split": "item50 + item51 == item52 (TFI 표 자신의 지급여력금액 행)",
            "50_tfi_tier_split_post": "TFI 표 자신의 적용후 컬럼에서 item50후 + item51후 == item52후. 2026-08-24 에 범위검사에서 등식으로 승격했고 GREEN 이던 6칸이 RED 로 뒤집혔다",
            "51_tfi_tier2_composition": "item51 == 축 B 와 같은 _tier2_branch (target=51)",
            "51_tfi_tier2_composition_post": "TFI 표 보완자본(item51)의 적용후 컬럼을 같은 _tier2_branch 로 재검산 (적용후 관계식 미확립 구간은 YELLOW)",
        }.items()
    },
    "7": {
        "statement": "item27(지급여력비율) == item1 / item14 × 100",
        "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "%p (초소형 분모는 동적 확대)"},
        "tol_from": [],
        "measured": "동적식 max(eff_tol, |expected|·0.5/|item14| + 50/|item14|) — 카카오페이처럼 "
                    "item14 가 20억이면 억원 반올림이 비율을 ±120%p 흔든다. 정상 분모에선 "
                    "사실상 2.0. 실측 n=488 잔차 rel p90 0.0003%.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "8": {
        "statement": "item28(기본자본비율) == item2 / item14 × 100",
        "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "%p (초소형 분모는 동적 확대)"},
        "tol_from": [],
        "measured": "rule 7 과 같은 동적식. 실측 n=488 잔차 rel p90 0.0000%.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "7_post": {
        "statement": "item27 적용후 == item1_적용후 / item14_적용후 × 100",
        "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "%p (초소형 분모는 동적 확대)"},
        "tol_from": [],
        "measured": "2026-08-25 신설. 없는 동안 item1_적용후가 완전 무방비였다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "8_post": {
        "statement": "item28 적용후 == item2_적용후 / item14_적용후 × 100",
        "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "%p (초소형 분모는 동적 확대)"},
        "tol_from": [],
        "measured": "적용전 rule 8 과 동일한 동적 tol (2026-07-12 에 불일치 교정).",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "8_life": {
        "statement": "item17(생명장기손해보험위험액) == sqrt(S'·R7·S), S = item29..item35",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_transition_basic"),
                 ("scripts/validate_kics_disclosure.py", "_transition_mmult_after")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.01, "unit": "억원"},
        "tol_from": [("solvency.validation.kics_json_rules", "DIVERSIFIED_SQRT_TOL_REL", 0.01)],
        "measured": "n=364 잔차 rel p50 0.0023% · p90 0.049%. **2026-08-25 에 5% → 1% 로 조였고 "
                    "새로 걸린 것 0건** — 5% 는 '7개 하위항목 반올림 누적' 을 이유로 붙어 "
                    "있었지만 실측 누적폭이 그 1/50 이었다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "8_life_census": {
        "statement": "item17(생명장기손해보험위험액) > 0 이면 item29~35 가 전부 존재해야 한다 "
                     "— 값의 일치가 아니라 **존재**를 보는 census 룰",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_life_subrisk_census")],
        "kind": "HEURISTIC",
        "reason": "등식이 아니다 — 값끼리의 관계가 아니라 **셀의 존재 여부**를 본다. "
                  "값의 정합은 `8_life`(item17 == sqrt(S'·R7·S))가 이미 IDENTITY 로 검사하며, "
                  "그 룰은 29~35 가 전부 있어야만 성립하므로 하나라도 없으면 SKIP 한다. "
                  "이 룰은 바로 그 SKIP 구간을 덮는다. 게다가 '있어야 하는가' 자체가 수식이 "
                  "아니라 제도(짝수분기 전체공시 / 홀수분기는 경과조치 적용사만)와 원문 표 "
                  "게재 여부로 정해지므로, 등식으로 환원할 수 없고 등재부 lookup 이 필요하다.",
        "tol": {"abs": None, "rel": None, "unit": "존재 여부(수치 비교 없음)"},
        "tol_from": [],
        "measured": "2026-09-03 신설. 기존 `8_life` 는 항등식이라 29~35 가 **하나라도 없으면 "
                    "SKIP** 했고, 그래서 '부모는 있는데 자식이 통째로 없다' 가 RED=0 으로 "
                    "통과했다 — 실측 131칸. owner 제보(현대해상·KB손해 2026.2Q, 하나손해 "
                    "2026.1Q)로 드러나 이 룰로 사각을 메웠다. 판정은 짝수분기=전사 필수, "
                    "홀수분기 2024년~=경과조치 적용사만 필수, 원문에 4-2-2 ②표가 없는 칸은 "
                    "등재부(data/_gold/kics_subrisk_source_absent.json) lookup 으로 SKIP. "
                    "등재부를 비우면 RED 24건이 뜨는 것을 반증으로 확인했다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "19_market": {
        "statement": "item19(시장위험액) == sqrt(V'·MARKET_M·V), V = item36..item40",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_market_irr"),
                 ("scripts/validate_kics_disclosure.py", "_transition_mmult_after")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.01, "unit": "억원"},
        "tol_from": [("solvency.validation.kics_json_rules", "DIVERSIFIED_SQRT_TOL_REL", 0.01)],
        "measured": "n=356 잔차 rel p50 0.0037% · p90 0.083%. 5% → 1% 로 조여도 위반 0건.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "36_irr": {
        "statement": "item36(금리위험액) == f(item41..item46 충격시나리오 순자산가치)",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_market_irr")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.05, "unit": "억원"},
        "tol_from": [("solvency.validation.kics_json_rules", "IRR_DERIVED_TOL_REL", 0.05)],
        "measured": "n=226 잔차 rel p50 0.0005% · p90 0.898% · p99 4.69%.",
        "documented_widening": {
            "why": "1% 로 조이면 12건이 새로 걸리는데 **12/12 전부 actual > expected 인 양(+)의 "
                   "계통편차**(+1.08%~+4.69%; 교보·미래에셋·코리안리·롯데·NH농협·메트라이프·BNP, "
                   "전부 짝수분기)다. 부호가 한쪽으로만 몰리는 것은 데이터 12건이 동시에 틀린 "
                   "것이 아니라 **파생식이 원문 산출식의 하한**이라는 지문이다. 원문 산출식을 "
                   "확정하기 전에 조이면 오탐 12건을 만든다. 조이지 않는 것이 정당하다는 뜻이 "
                   "아니라 **원인 미규명이라는 뜻**이다.",
            "ticket": "inbox/_resolved/20260825T1520Z__validation__MULTI__csm_amort_identity_28_ledgered_buckets.md",
            "measured_cost": "tol 1% → 위반 17건(현행 5% 는 5건). 순증 12건.",
        },
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "9": {
        "statement": "경과조치 방향성: item2_적용후 >= item2_적용전 (준비금 경과조치는 "
                     "가용자본을 올리지 내리지 않는다)",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_transition_capital")],
        "kind": "RANGE",
        "tol": {"abs": 2.0, "rel": 0.0005, "unit": "억원"},
        "tol_from": [],
        "measured": "n=229. 잔차 rel p50 9.6% — 애초에 '같아야 하는' 값이 아니다.",
        "reason": "**부등식이지 등식이 아니다.** 경과조치가 자본을 얼마나 올리는지는 회사·분기마다 "
                  "다르고 정답이 없다. 이 룰이 검사하는 것은 크기가 아니라 **방향**(내려가면 "
                  "추출오류)이다. tol 은 부등호 경계의 반올림 여유일 뿐 밴드가 아니다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "10": {
        "statement": "경과조치 방향성: item14_적용전 >= item14_적용후 (요구자본 경과조치는 "
                     "기준금액을 내리지 올리지 않는다)",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_transition_capital")],
        "kind": "RANGE",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
        "tol_from": [],
        "measured": "n=238. 잔차 rel p50 34% — 같아야 하는 값이 아니다.",
        "reason": "rule 9 와 같은 **부등식** 축이다. 요구자본 경과조치가 기준금액을 얼마나 내리는지는 회사·분기마다 다르고 정답이 없다 — 이 룰이 보는 것은 크기가 아니라 방향이며, 올라가면 추출오류다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "48_tier2_limit": {
        "statement": "item48(보완자본 인정한도) == item14_적용전 × 50%",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_tier2_limit")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
        "tol_from": [],
        "measured": "n=460. **통과가 증거가 아니다** — parser 의 배율(÷1 vs ÷100) 판별 앵커가 "
                    "바로 이 식이라 로더가 이 식을 가장 잘 만족하는 값을 골라 저장한다. "
                    "그래서 blocking(RED)이 아니라 YELLOW 로 낸다(회귀 감시용).",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    "48_tier2_limit_post": {
        "statement": "item48_적용후 == item14_**적용전** × 50% (분모는 적용후가 아니다 — "
                     "TFI 는 가용자본만 움직이고 요구자본은 안 건드린다)",
        "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_tier2_limit")],
        "kind": "IDENTITY",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
        "tol_from": [],
        "measured": "item14 가 전≠후인 216칸에서 `item14_전×50%` 와 맞는 것 215칸, "
                    "`item14_후×50%` 와 맞는 것 0칸. 로더 강제 축이라 YELLOW.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
    **{
        rid: {
            "statement": stmt,
            "impl": [("src/solvency/validation/kics_json_rules.py", "_validate_tier2_limit")],
            "kind": "RANGE",
            "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
            "tol_from": [],
            "measured": "등식 축(3_tier2_composition · 50_tfi_tier_split)이 따로 있다.",
            "reason": reason,
            "mutation": "tests/test_rule_coverage_manifest.py",
        }
        for rid, stmt, reason in [
            ("47_tier2_census",
             "item47/48/49 의 완전성 · 부호(금액이라 음수 불가) · 자릿수(|값| ≤ item14 × ceiling) "
             "· 중복행 · 전기한도 잔존",
             "**census·부호·자릿수 검사이지 등식이 아니다.** '세 행이 다 있는가', '음수가 아닌가', "
             "'단위 스케일이 맞는가' 는 어떤 값과 같아야 한다는 주장이 아니다. 이 축의 값 단위 "
             "등식은 3_tier2_composition 이 담당한다."),
            ("47_tier2_census_post", "item47/48/49 의 완전성·부호·자릿수·중복행 census 를 [값_적용후] 컬럼에서 그대로 재검산한다",
             "적용전과 같은 census·부호·자릿수 축이다. 어떤 값과 같아야 한다는 주장이 아니라 '행이 다 있는가·음수가 아닌가·단위가 맞는가' 를 본다. 스코프와 무관해 적용후도 RED 로 건다."),
            ("53_tfi_memo_rows",
             "기발행 신종자본증권(53) · 후순위채무(54): census · 부호 · 53+54 <= item51",
             "**포함관계 부등식이다.** 등식 승격을 실제로 시뮬레이션했고 기각됐다 — "
             "`item51 == min(47,48)+49+item54` 전수 시뮬 결과 새로 닫힘 1 · 새로 깨짐 218. "
             "메모행이지 항등식의 항이 아니다."),
            ("53_tfi_memo_rows_post", "기발행 신종자본증권(53)·후순위채무(54)의 부호와 53+54 <= item51 포함관계를 적용후 컬럼에서 재검산 (census 는 안 건다 — 원문에 적용후 칸이 대부분 없다)",
             "적용전과 같은 포함관계 부등식 축이다(53+54 <= item51). 등식이 아니며 승격 시뮬도 기각됐다(새로 닫힘 1 · 새로 깨짐 218). census 만 빼고 부호·포함관계는 적용후에서도 돈다."),
        ]
    },
    "3": {
        "statement": "item4 − item12 + item13 다리 (item1 대상)",
        "impl": [("src/solvency/validation/kics_json_rules.py", "run_validation")],
        "kind": "HEURISTIC",
        "tol": {"abs": 2.0, "rel": 0.0, "unit": "억원"},
        "tol_from": [],
        "measured": "대상을 item1 로 잡으면 2.7% 만 닫히고 item2 로 잡으면 88.8% 가 닫힌다.",
        "reason": "**영구 SKIP.** 다리의 대상 항목이 잘못 잡혀 있어 성립하지 않는다 — 등식으로 "
                  "고치는 작업은 `2_tier1_bridge` 가 대신하고 있고, 이 룰 자체는 티켓 "
                  "inbox/validation/20260821T1100Z 에서 폐기·교체를 다룬다. 여기 남겨 두는 "
                  "이유는 지워 버리면 '그런 축이 있었다' 는 사실까지 사라지기 때문이다.",
        "mutation": "tests/test_rule_coverage_manifest.py",
    },
}


# ===========================================================================
# 1) 선언 ↔ 코드 동기화
# ===========================================================================
def test_declared_tolerances_match_code():
    """선언한 허용오차가 코드의 실제 상수와 같은가. 몰래 넓히면 여기서 막힌다."""
    bad = []
    for rid, e in REGISTRY.items():
        for module, const, declared in e.get("tol_from", []):
            try:
                live = _c(module, const)
            except (ImportError, AttributeError) as exc:
                bad.append(f"{rid}: {module}.{const} 를 읽을 수 없다 ({exc})")
                continue
            if live != declared:
                bad.append(f"{rid}: {module}.{const} 선언 {declared} != 코드 {live} — "
                           f"허용오차를 바꿨으면 REGISTRY 도 같이 고쳐라")
    assert not bad, "선언과 코드가 갈라졌다:\n  " + "\n  ".join(bad)


# ===========================================================================
# 2) IDENTITY 는 밴드일 수 없다
# ===========================================================================
def test_identity_tolerances_are_rounding_level():
    """IDENTITY 로 선언한 축은 상대 허용오차가 반올림 수준이어야 한다.

    넓혀야 하면 두 길뿐이다:
      · `RANGE`/`HEURISTIC` 로 재분류하고 **왜 등식이 아닌지** 쓴다
      · `documented_widening` 에 사유 + 티켓 + 실측비용을 등재한다
    둘 다 안 하면 FAIL. 이것이 `_XCHK_LO/_HI = 0.4, 2.5` 가 몇 달을 살아남은 경로를 막는다.
    """
    bad = []
    for rid, e in REGISTRY.items():
        if e["kind"] != "IDENTITY":
            continue
        rel = e["tol"].get("rel", 0.0)
        if rel <= IDENTITY_MAX_REL:
            continue
        dw = e.get("documented_widening")
        if not dw:
            bad.append(f"{rid}: IDENTITY 인데 상대 허용오차 {rel:.1%} > 상한 "
                       f"{IDENTITY_MAX_REL:.0%} 이고 documented_widening 이 없다 — "
                       f"조이거나, RANGE 로 재분류하고 사유를 쓰거나, 등재하라")
            continue
        for field in ("why", "ticket", "measured_cost"):
            if len(str(dw.get(field, "")).strip()) < (MIN_REASON_CHARS if field == "why" else 8):
                bad.append(f"{rid}: documented_widening.{field} 가 비었거나 너무 짧다")
        # 티켓은 **실재해야 한다** — 없는 파일을 가리키는 면제는 면제가 아니라 방치다.
        # 단 티켓은 종결되면 `inbox/<stage>/` → `inbox/_resolved/` 로 옮겨진다(정상 수명주기).
        # 그때마다 이 테스트가 깨지면 "티켓을 닫으면 게이트가 막힌다"가 되어 닫기를 미루게
        # 된다 — 실제로 2026-08-26 에 그렇게 한 번 막혔다. 그래서 **두 자리 다** 본다.
        # 어느 쪽에도 없으면 여전히 FAIL(그게 이 검사의 본론이다).
        tk = str(dw.get("ticket", "")).strip()
        if tk:
            here = ROOT / tk
            sibling = (ROOT / "inbox" / "_resolved" / here.name if "_resolved" not in here.parts
                       else ROOT / "inbox" / "parser" / here.name)
            if not here.exists() and not sibling.exists():
                bad.append(f"{rid}: documented_widening.ticket 이 가리키는 파일이 없다 "
                           f"(활성·_resolved 양쪽 확인) — {tk}")
    assert not bad, "등식이 밴드로 구현돼 있다:\n  " + "\n  ".join(bad)


def test_non_identity_entries_carry_a_reason():
    """RANGE/HEURISTIC 은 **왜 등식이 아닌지** 를 반드시 적어야 한다.

    사유 없이 RANGE 로 옮기는 것이 이 테스트를 무력화하는 유일한 방법이므로 여기서 막는다.
    """
    bad = []
    for rid, e in REGISTRY.items():
        if e["kind"] == "IDENTITY":
            continue
        r = str(e.get("reason", "")).strip()
        if len(r) < MIN_REASON_CHARS:
            bad.append(f"{rid}: kind={e['kind']} 인데 사유가 {len(r)}자 "
                       f"(최소 {MIN_REASON_CHARS}자) — 왜 등식이 아닌지 써라")
    assert not bad, "성격 분류에 사유가 없다:\n  " + "\n  ".join(bad)


def test_every_entry_is_well_formed():
    """등재 항목이 최소 필드를 갖췄는가 (진술·구현위치·성격·허용오차·실측)."""
    bad = []
    for rid, e in REGISTRY.items():
        if e.get("kind") not in ("IDENTITY", "RANGE", "HEURISTIC"):
            bad.append(f"{rid}: kind 가 IDENTITY/RANGE/HEURISTIC 중 하나가 아니다")
        if len(str(e.get("statement", "")).strip()) < 20:
            bad.append(f"{rid}: statement 가 없거나 너무 짧다 (부호 규약 포함해 진술하라)")
        if not e.get("impl"):
            bad.append(f"{rid}: impl(구현 위치)이 비었다")
        for path, fn in e.get("impl", []):
            if not (ROOT / path).exists():
                bad.append(f"{rid}: impl 파일이 없다 — {path}")
                continue
            if fn not in _functions_in(ROOT / path):
                bad.append(f"{rid}: {path} 에 {fn}() 가 없다 — 함수가 개명·삭제됐다면 "
                           f"REGISTRY 의 impl 도 같이 고쳐라")
        if not str(e.get("measured", "")).strip():
            bad.append(f"{rid}: measured(실측 근거)가 비었다")
        if not e.get("mutation"):
            bad.append(f"{rid}: mutation 선언이 없다")
        m = e.get("mutation")
        if m != "inline" and not (ROOT / str(m)).exists():
            bad.append(f"{rid}: mutation 위임 대상 {m} 이 없다")
    assert not bad, "등재 형식 위반:\n  " + "\n  ".join(bad)


# ===========================================================================
# 3) 룰엔진이 내보내는 룰이 전부 등재돼 있는가 (선언 누락 차단)
# ===========================================================================
def test_every_declared_kics_rule_is_classified():
    """`test_rule_coverage_manifest.DECLARED_RULES` 의 모든 룰이 여기 성격 분류를 갖는가.

    새 K-ICS 룰을 배선하면 저기서 한 번, 여기서 또 한 번 막힌다 — 저쪽은 '무엇을 검사하나',
    이쪽은 '그게 등식인가'. 룰을 넣으면서 성격을 안 정하는 길이 없어진다.
    """
    sys.path.insert(0, str(ROOT / "tests"))
    from test_rule_coverage_manifest import DECLARED_RULES  # noqa: E402
    missing = sorted(DECLARED_RULES - set(REGISTRY))
    assert not missing, (
        "K-ICS 룰이 항등식 레지스트리에 없다 — IDENTITY/RANGE/HEURISTIC 중 하나로 분류하라:\n  "
        + "\n  ".join(missing))


def test_mutation_delegation_is_real():
    """변이시험을 다른 테스트에 위임했다면 그 테스트가 실제로 그 축을 다루는가.

    `mutation: "tests/x.py"` 라고 적어 놓고 그 파일이 이 룰을 모르면 위임이 아니라 회피다.
    """
    sys.path.insert(0, str(ROOT / "tests"))
    # 그 파일은 **두 룰 계열**을 선언한다 — K-ICS 룰엔진 id(`DECLARED_RULES`)와 2026-08-30
    # 신설 gold 오버레이 축(`GOLD_OVERLAY_RULES`). 한쪽만 보면 gold 축의 정당한 위임이
    # "회피"로 오판된다. 위임이 진짜인지 = 그 파일이 이 축을 실제로 다루는지가 요점이므로
    # 그 파일이 선언한 이름 전부를 본다.
    from test_rule_coverage_manifest import (  # noqa: E402
        DECLARED_RULES, GOLD_OVERLAY_RULES)
    covered = set(DECLARED_RULES) | set(GOLD_OVERLAY_RULES)
    bad = []
    for rid, e in REGISTRY.items():
        if e.get("mutation") != "tests/test_rule_coverage_manifest.py":
            continue
        if rid not in covered:
            bad.append(f"{rid}: 변이시험을 rule_coverage_manifest 에 위임했는데 "
                       f"그쪽 DECLARED_RULES 에 없다")
    assert not bad, "위임이 비어 있다:\n  " + "\n  ".join(bad)


# ===========================================================================
# 4) 등재되지 않은 새 임계 상수 탐지
# ===========================================================================
# 검증기 소스의 모듈 레벨 상수 중 **비교 임계로 보이는 이름**을 전수로 긁어, 레지스트리가
# 참조하지 않는 것을 잡는다. 이것이 `_XCHK_LO/_HI` 같은 상수가 아무 선언 없이 태어나는 것을
# 막는 그물이다. 임계가 아닌 것(경로·라벨·구조)은 아래 allowlist 에 **사유와 함께** 넣는다.
# 이름이 임계처럼 생겼는가. 두 갈래로 본다 —
#   · **포함**: TOL / BAND / THRESH / EPS / FLOOR / CEILING / MARGIN / TOLERANCE
#     (`CSM_AMORT_TOL_ABS_EOK` · `DIV_PAYOUT_TOL_PP` 처럼 접미사가 더 붙는 형태를 놓치지 않는다.
#      좁게 '끝나는가' 로만 보면 그 둘이 새어 나갔다 — 실측으로 확인하고 넓혔다.)
#   · **끝남**: _LO / _HI / _REL / _ABS / _RATIO / _PP  (`_XCHK_LO`, `_XCHK_HI` 가 이 갈래다)
_THRESHOLD_NAME = re.compile(
    r"^_?[A-Z][A-Z0-9_]*?"
    r"(?:(?:TOL|TOLERANCE|BAND|THRESH|EPS|FLOOR|CEILING|MARGIN)[A-Z0-9_]*"
    r"|_(?:LO|HI|REL|ABS|RATIO|PP))$")

_SCANNED = [
    "scripts/validate_data_contract.py",
    "scripts/validate_master_tables.py",
    "scripts/validate_csm_waterfall.py",
    "scripts/validate_csm_continuity.py",
    "scripts/validate_nb_csm_multiple.py",
    "src/solvency/validation/kics_json_rules.py",
    "scripts/validate_kics_disclosure.py",
    "scripts/validate_kics_rate_sensitivity.py",
    "scripts/validate_statutory_reserves.py",
    "scripts/validate_live_artifacts.py",
    "scripts/validate_nb_csm_multiple.py",
]

# 레지스트리 항목의 임계가 아닌 상수 — **전부 사유가 붙어 있어야 한다.**
_NOT_A_COMPARISON_THRESHOLD = {
    "IMAGE_OCR_TOLERANCE": "임계가 아니라 회사군별 기본 허용오차 자체(이미지/OCR 공시사 10.0억). "
                           "이 값을 쓰는 룰은 각자 레지스트리에 등재돼 있다.",
    "IRR_PIN_TOL": "IRR 면제의 박제 잔차 재검산 폭 0.01억 — 등식 허용오차가 아니라 박제한 값이 그대로인지 보는 폭이다.",
    "RESTATEMENT_TOL": "소급재작성 등재부의 셀 대조 폭 0.5억 — 두 값이 같아야 한다는 등식이 아니라 "
                       "마스터가 as_filed/as_restated **어느 쪽 값인지 가르는** 판정 폭이다. "
                       "공시본이 억원 정수 그리드로 인쇄되므로 반올림 0.5 를 넘으면 어느 쪽도 "
                       "아닌 제3의 값(PIN_DRIFT)으로 본다.",
    "RESTATEMENT_CASCADE_TOL_DEFAULT": "재작성 채택 연쇄(_adoption_cascades)의 박제 잔차 재검산 "
                       "기본 폭 0.5억 — 등식 허용오차가 아니라 박제해 둔 잔차가 그대로인지 보는 "
                       "폭이다. 엔트리별 `tol` 로 덮어쓸 수 있다(IRR_PIN_TOL 과 같은 성격).",
    "TIER2_ZERO_EPS": "47/48/49 가 사실상 0(인쇄값 0 또는 대시)인지 가르는 판정 임계 0.5억 — 두 값이 같아야 한다는 주장이 아니라 갈래(TFI_NA)를 정하는 분류 상수다.",
    "TIER2_LIMIT_RATIO": "보완자본 인정한도 비율 0.5 그 자체 — 허용오차가 아니라 48_tier2_limit 등식의 계수다(item48 == item14 × 50%).",
    "TIER2_SCALE_CEILING": "|값| > item14 × 이 배수면 단위스케일 오류로 보는 자릿수 sanity 상한. 등식 허용오차가 아니며 47_tier2_census 축이 소비한다.",
    "CSM_AMORT_TOL_ABS_EOK": "csm_amort_identity 항목이 tol_from 으로 참조한다(abs 항 0.1억).",
    "CSM_AMORT_PIN_TOL_ABS_EOK": "등재부 박제 재검산 폭 — 등식 허용오차가 아니다.",
    "CSM_AMORT_PIN_TOL_REL": "등재부 박제 재검산 폭의 상대 항 — 등식 자체의 허용오차가 아니라 박제해 둔 잔차가 그대로인지 보는 폭이다.",
    "CSM_AMORT_MIN_EOK": "대조 스코프 하한 10억 — 상각이 그보다 작으면 반올림이 지배해 대조가 의미 없다. 허용오차가 아니다.",
    "DEFAULT_FLOOR": "pl_bridge 항목이 tol_from 으로 참조한다(백만원 abs floor 200).",
    "EQ_FLOOR": "pl_bridge 의 등식별 abs floor 예외(영업이익 600백만) — pl_bridge 항목과 같은 축이며 0 근처 회사의 과민반응만 완화한다.",
    "_XCHK_MIN_AMORT_EOK": "CSM_AMORT_MIN_EOK 의 별칭 — 대조 스코프 하한이며 허용오차가 아니다. 옛 _XCHK_LO/_HI 밴드가 지워진 자리에 남은 이름이다.",
    "_CSM_PLAUS_MIN_SAMPLE": "코호트 통계를 낼 최소 표본수 — 값 비교 임계가 아니라 표본이 너무 적어 판단할 수 없는 경우를 가르는 가드다.",
    "_CHILD_MATERIAL_FLOOR": "부모-자식 완전성 census 에서 유의미한 자식으로 볼 하한(5억). 두 값을 비교하는 허용오차가 아니라 스코프 상수다.",
    "_TRANS_EFFECT_MARGIN": "경과조치가 실제로 효과를 냈는지(적용후 유실·복사 위장인지) 가르는 마진 1.0%p — 두 값이 같아야 한다는 주장이 아니라 '움직였는가' 를 가르는 판정 상수다. 정상 셀은 수십~백%p 차이고 복사 위장은 |diff|<0.1 이라 사이가 비어 있다.",
    "_TRANS_EFFECT_MARGIN_PCT": "위 마진의 상대 항 0.15 — 소액·자본잠식 회사(|적용전|이 작음)에서 절대 1.0%p 가 과해 진짜 개선폭까지 COPY 로 오탐하던 것을 비례로 줄인다.",
    "_TRANS_EFFECT_MARGIN_FLOOR": "위 마진의 하한 0.1%p — 값이 같아야 한다는 주장이 아니라 움직임이 관측 가능한가를 가르는 스코프 상수다.",
    "_RATIO_SPIKE_FLOOR": "지급여력비율 시계열 급변을 볼 최소 폭 30%p — 등식이 아니라 이상치 탐지 하한이며 YELLOW 전용이다.",
    "_AXIS_EVAL_RATE_FLOOR": "축이 실제로 평가된 비율의 하한 — 커버리지 감시용이며 두 값을 비교하는 허용오차가 아니다.",
    "_TAUT_EXCESS_FLOOR": "동어반복 탐지기의 자체 임계 — tests/test_identity_tautology.py 가 "
                          "변이시험으로 강제한다.",
    "_TAUT_Z_FLOOR": "동어반복 탐지기의 z-score 하한 — 잔차 분포의 이상 여부를 재는 통계 임계이지 등식 허용오차가 아니다. test_identity_tautology.py 가 변이시험으로 강제한다.",
    "_TAUT_ZERO_EPS": "동어반복 탐지기가 잔차가 정확히 0 인 칸을 셀 때 float 잡음을 흡수하는 폭(1e-6). 실제 granularity 0.01 보다 훨씬 작다.",
    "_TAUT_PIN_EXCESS_TOL": "동어반복 박제값 재검산 폭 — 박제가 그대로인지 보는 것이지 등식의 허용오차가 아니다.",
    "_LIFE8_PIN_TOL": "8_life 면제(미래에셋 2023.2Q)의 박제 잔차 재검산 폭 0.01억 — 면제가 박제한 값에서 벗어났는지 보는 것이지 등식 허용오차가 아니다.",
    "_TIER2_PIN_TOL": "tier2/다리 발행사 자기모순 면제의 박제 잔차 재검산 폭 0.01억 — 위와 같은 성격이며 등식 허용오차가 아니다.",
    "_ROW_ANCHOR_BAND": "원문에서 행 앵커를 찾을 때의 탐색 폭(파싱 보조) — 두 값을 비교하는 임계가 아니다.",
    "ANCHOR_TOL": "법정준비금 앵커 대조 폭 — validate_statutory_reserves 소관이며 그 게이트를 data-contract 가 import 해 돌린다. 별도 축이라 여기서 재등재하지 않는다.",
    "EQ_TAUTOLOGY": "임계가 아니라 **문자열 라벨**이다(값 \"TAUTOLOGY\"). "
                    "PL_EQ_EVIDENCE 가 등식별로 REAL/TAUTOLOGY/PARTIAL 중 하나를 선언하고 "
                    "SUMMARY 가 pass 를 그 셋으로 갈라 인쇄한다 — 구성상 참인 등식의 pass 를 "
                    "'검사했더니 깨끗' 으로 오독하지 않게 하는 장치이지 두 값을 비교하는 폭이 아니다.",
    "DIVERSIFIED_SQRT_TOL_REL": "8_life / 19_market 두 항목이 tol_from 으로 참조한다.",
    "IRR_DERIVED_TOL_REL": "36_irr 항목이 tol_from 으로 참조한다(documented_widening 포함).",
}


def _module_level_constants(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and _THRESHOLD_NAME.match(t.id):
                    out.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _THRESHOLD_NAME.match(node.target.id):
                out.add(node.target.id)
    return out


def test_no_undeclared_threshold_constants():
    """검증기에 새 임계 상수가 생기면 레지스트리 등재를 강제한다.

    `_XCHK_LO, _XCHK_HI = 0.4, 2.5` 는 아무 선언 없이 태어나 몇 달을 살았다. 상수 하나가
    등식을 밴드로 바꿔 놓을 수 있으므로, 이름이 임계처럼 생긴 모듈 레벨 상수는 **레지스트리가
    참조하거나(tol_from) allowlist 에 사유와 함께** 있어야 한다.
    """
    referenced = {const for e in REGISTRY.values() for _m, const, _v in e.get("tol_from", [])}
    bad = []
    for rel_path in _SCANNED:
        p = ROOT / rel_path
        if not p.exists():
            continue
        for name in sorted(_module_level_constants(p)):
            if name in referenced or name in _NOT_A_COMPARISON_THRESHOLD:
                continue
            bad.append(f"{rel_path}: {name} — 이 상수가 어떤 등식의 허용오차인지 REGISTRY 에 "
                       f"등재하거나, 임계가 아니면 _NOT_A_COMPARISON_THRESHOLD 에 사유와 함께 넣어라")
    assert not bad, "등재되지 않은 임계 상수:\n  " + "\n  ".join(bad)


def test_allowlisted_constants_carry_a_reason():
    """allowlist 가 사유 없는 통로가 되지 않게."""
    bad = [k for k, v in _NOT_A_COMPARISON_THRESHOLD.items() if len(str(v).strip()) < 20]
    assert not bad, f"사유 없는 allowlist 항목: {bad}"


# ===========================================================================
# 5) 변이시험 — 값을 흔들면 룰이 실제로 발화하는가
# ===========================================================================
# 변이시험이 없으면 "룰이 있다" 와 "룰이 잡는다" 를 구별할 수 없다. K-ICS 축은
# tests/test_rule_coverage_manifest.py 가 전수로 돌리므로 여기서는 **IFRS17 마스터 축**만
# 직접 흔든다(그쪽 매니페스트가 안 보는 영역이고, 이번 사고가 난 자리다).

@pytest.fixture(scope="module")
def _masters():
    import validate_master_tables as V
    return V, V.load_long(V.PL_PATH), V.load_long(V.WF_PATH)


def _pick(idx, need):
    for k, m in sorted(idx.items()):
        if all(isinstance(m.get(n), (int, float)) and m.get(n) for n in need):
            return k
    return None


def test_mutation_csm_amort_identity_fires(_masters):
    """PL 상각을 흔들면 CSM 상각 항등식이 RED 를 낸다 (무검사 탐지)."""
    V, pl, wf = _masters
    key = None
    for k in sorted(set(pl) & set(wf)):
        if V.csm_amort_residual(pl[k], wf[k]) is not None:
            resid, _p, _w = V.csm_amort_residual(pl[k], wf[k])
            if abs(resid) <= V.csm_amort_tol(_w):
                key = k
                break
    assert key, "대조 가능하고 현재 닫혀 있는 버킷이 없다 — 축 자체가 죽었다"

    clean = V.csm_amort_residual(pl[key], wf[key])
    assert abs(clean[0]) <= V.csm_amort_tol(clean[2]), "출발 상태가 이미 깨져 있다"

    mutated = dict(pl[key])
    mutated["원수CSM상각"] = mutated["원수CSM상각"] * 1.02      # 2% — tol(0.05%)의 40배
    dirty = V.csm_amort_residual(mutated, wf[key])
    assert abs(dirty[0]) > V.csm_amort_tol(dirty[2]), (
        f"{key} 의 PL 상각을 2% 흔들었는데 항등식이 여전히 닫힌다 — 허용오차가 밴드다")


def test_mutation_csm_amort_ledger_removal_fires(_masters):
    """등재부에서 줄을 지우면(=선언 삭제) 그 버킷이 RED 로 돌아온다."""
    V, pl, wf = _masters
    ledger = V.csm_amort_ledger().get("entries", {})
    assert ledger, "등재부가 비었다 — 박제가 사라졌는지 확인하라"
    key = sorted(ledger)[0]
    co, _, q = key.partition("|")
    resid = V.csm_amort_residual(pl[(co, q)], wf[(co, q)])
    assert resid is not None, f"{key} 가 더는 대조 대상이 아니다 — 등재부에서 지워라"
    assert abs(resid[0]) > V.csm_amort_tol(resid[2]), (
        f"{key} 가 이제 항등식 안에 들어온다 — 등재부에서 줄을 지워라")
    # 등재를 지운 상태 = verdict NEW = RED 경로
    assert V.csm_amort_ledger_verdict(None, resid[0]) == "NEW"
    # 박제를 흔들면 PIN_DRIFT
    drifted = dict(ledger[key])
    drifted["residual_eok"] = resid[0] * 3 + 100.0
    assert V.csm_amort_ledger_verdict(drifted, resid[0]) == "PIN_DRIFT"


def test_mutation_widening_the_band_is_detected(_masters):
    """허용오차를 넓히면 이 파일의 상한 검사가 잡는다 (밴드 재도입 차단)."""
    e = dict(REGISTRY["csm_amort_identity"])
    e["tol"] = {"abs": 0.1, "rel": 0.60, "unit": "억원"}   # = 옛 0.4~2.5 배수 밴드 수준
    widened = {**REGISTRY, "csm_amort_identity": e}
    offenders = [rid for rid, x in widened.items()
                 if x["kind"] == "IDENTITY" and x["tol"].get("rel", 0.0) > IDENTITY_MAX_REL
                 and not x.get("documented_widening")]
    assert "csm_amort_identity" in offenders, (
        "밴드로 넓혔는데 상한 검사가 못 잡는다 — test_identity_tolerances_are_rounding_level 이 "
        "동어반복이 됐다")


def test_mutation_closing_identity_fires(_masters):
    """워터폴 한 단계를 흔들면 rollforward 항등식이 깨진다."""
    _V, _pl, wf = _masters
    need = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
    key = _pick(wf, need)
    assert key, "6단계가 다 있는 버킷이 없다"
    m = wf[key]
    base = abs(sum(m[k] for k in need[:-1]) - m["기말CSM"])
    assert base <= max(0.001 * abs(m["기말CSM"]), 2.0), "출발 상태가 이미 깨져 있다"
    mm = dict(m)
    mm["신계약CSM"] = mm["신계약CSM"] + max(10.0, abs(m["기말CSM"]) * 0.01)
    dirty = abs(sum(mm[k] for k in need[:-1]) - mm["기말CSM"])
    assert dirty > max(0.001 * abs(m["기말CSM"]), 2.0), (
        f"{key} 의 신계약CSM 을 1% 흔들었는데 closing identity 가 닫힌다")


def test_mutation_pl_bridge_fires(_masters):
    """PL 다리의 한 항을 흔들면 등식이 깨진다."""
    V, pl, _wf = _masters
    label, lhs_key, terms = V.PL_EQS[4]          # 영업이익 = 보험손익 + 투자손익
    key = _pick(pl, [lhs_key] + [k for k, _ in terms])
    assert key, f"{label} 를 검사할 수 있는 버킷이 없다"
    m = pl[key]
    floor = V.EQ_FLOOR.get(label, V.DEFAULT_FLOOR)
    base = abs(sum(s * m[k] for k, s in terms) - m[lhs_key])
    assert base <= max(0.001 * abs(m[lhs_key]), floor), "출발 상태가 이미 깨져 있다"
    mm = dict(m)
    mm["보험손익"] = mm["보험손익"] + max(floor * 10, abs(m[lhs_key]) * 0.05)
    dirty = abs(sum(s * mm[k] for k, s in terms) - mm[lhs_key])
    assert dirty > max(0.001 * abs(m[lhs_key]), floor), (
        f"{key} 의 보험손익을 5% 흔들었는데 {label} 가 닫힌다")


def test_mutation_gate_emits_red_for_broken_identity():
    """게이트 전체(in-process)를 돌려 **실제 finding 이 나오는지** 확인한다.

    위 시험들은 항등식 헬퍼가 잡는다는 것을 보인다. 이 시험은 그 헬퍼가 **게이트 배선에
    실제로 연결돼 있는지** 를 본다 — 이 저장소에서 룰이 죽는 흔한 방식이 '헬퍼는 맞는데
    아무도 안 부른다' 이기 때문이다(2026-08-21 에 호출처 0 인 게이트가 5개였다).
    """
    import validate_data_contract as gate
    env = gate.Env()
    key = next((k for k in sorted(set(env.pl) & set(env.wf))
                if (r := gate.csm_amort_residual(env.pl[k], env.wf[k])) is not None
                and abs(r[0]) <= gate.csm_amort_tol(r[2])), None)
    assert key, "닫혀 있는 대조 버킷이 없다"

    clean = gate.GateResult()
    gate.check_cross_source(clean, env)
    hits = [f for f in clean.findings
            if f.company == key[0] and f.quarter == key[1]
            and str(f.rule).startswith("CSM_AMORT_IDENTITY")]
    assert not hits, f"흔들기 전인데 {key} 에 이미 finding 이 있다: {hits}"

    env2 = copy.copy(env)
    env2.pl = dict(env.pl)
    env2.pl[key] = dict(env.pl[key])
    env2.pl[key]["원수CSM상각"] = env2.pl[key]["원수CSM상각"] * 1.05
    dirty = gate.GateResult()
    gate.check_cross_source(dirty, env2)
    reds = [f for f in dirty.red
            if f.company == key[0] and f.quarter == key[1]
            and str(f.rule).startswith("CSM_AMORT_IDENTITY")]
    assert reds, (
        f"{key} 의 PL 상각을 5% 흔들었는데 게이트가 RED 를 안 낸다 — 룰이 배선돼 있지 않거나 "
        f"허용오차가 밴드다")
