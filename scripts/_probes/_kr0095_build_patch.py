# -*- coding: utf-8 -*-
"""Builds data/_derived/_patch_2026q2_KR0095.json for the KR0095 (메트라이프생명보험)
2026.2Q RED-fix task. See report to owner for full narrative; this script only
assembles the already-verified numbers (see scripts/_probes/_kr0095_verify.py
output for the identity/cross-quarter checks) into the patch schema.

Does NOT touch kics_disclosure.json.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = REPO / "data" / "_derived" / "_patch_2026q2_KR0095.json"

MD = "md_inbox/FY2026_Q2/KR0095_메트라이프생명보험.md"
PDF = "data/disclosure/FY2026_Q2/pdf/KR0095_메트라이프생명보험.pdf"

# ---------------------------------------------------------------------------
# Evidence strings (reused across several cells)
# ---------------------------------------------------------------------------
EV_NONAPPLIER = (
    f"{MD} L372 '당사는 공통 및 선택적용 경과조치를 모두 적용하지 않고 있습니다.' + "
    f"L374-382 (경과조치 종류표: TFI/RPT/TAC/TIR/TER/TIRR/PCA_DEFER 전부 X) + "
    f"data/_derived/kics_transition_applicability.json: KR0095 전 13개 분기(2023.3Q-2026.1Q) "
    f"전부 TFI=RPT=TAC=TIR=TER=TIRR=PCA_DEFER=X."
)
EV_HEADLINE = (
    f"{MD} L52-53 '지급여력비율 (경과조치 전) 232.4' / '지급여력비율 (경과조치 후) 232.4' "
    f"(동일값, 1-1.주요경영지표 표)."
)
EV_TFI_1 = (
    f"{MD} L428-439 '[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 관련' "
    f"표(단위 백만원) — 경과조치 적용전/적용후 두 컬럼이 모든 행에서 동일: "
    f"지급여력비율 232.4/232.4, 지급여력금액 4,856,281/4,856,281, 기본자본 2,670,904/2,670,904, "
    f"보완자본 2,185,377/2,185,377, 지급여력기준금액 2,089,392/2,089,392."
)
EV_TFI_2 = (
    f"{MD} L459-482 '2) 선택적용 경과조치 관련 ② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치' "
    f"표(단위 백만원) — 적용전/적용후 전 행 동일: 기본요구자본 2,751,917/2,751,917, "
    f"생명·장기손해보험위험액 2,136,851/2,136,851(하위: 사망 198,843/198,843·장수 40,187/40,187·"
    f"장해질병 488,610/488,610·장기재물기타 0/0·해지 1,751,572/1,751,572·사업비 373,364/373,364·"
    f"대재해 79,447/79,447), 일반손해보험위험액 0/0, 시장위험액 925,253/925,253, "
    f"신용위험액 154,754/154,754, 운영위험액 168,959/168,959, 법인세조정액 662,525/662,525, "
    f"기타요구자본 0/0."
)
EV_TFI_3 = (
    f"{MD} L494-513 '③ 주식위험 경과조치 또는 금리위험 경과조치' 표(단위 백만원) — "
    f"적용전/적용후 전 행 동일: 시장위험액 하위 금리위험 374,468/374,468, 주식위험 453,338/453,338, "
    f"부동산위험 36,161/36,161, 외환위험 650,450/650,450, 자산집중위험 0/0."
)
EV_IRR = (
    f"{PDF} p.27(1-indexed) '6-4.시장위험 관리 ② 금리위험액 현황' 표(단위 백만원), "
    f"'당기(2026.2Q)' 컬럼 'Ⅲ.순자산가치' 행: 충격전 4,856,281 / 충격후[평균회귀 4,849,046 · "
    f"금리상승 4,622,611 · 금리하락 4,961,985 · 금리평탄 4,573,675 · 금리경사 5,068,922], "
    f"'Ⅳ.금리위험액' 374,468(=item36 기존값 3744.68억과 일치). "
    f"이 페이지는 docling MD의 keyword_window 파싱범위(source_page_ranges 27-29 제외)에서 "
    f"빠져 있어 MD grep로는 안 잡힘 — fitz로 원본 PDF p27 직접 확인. "
    f"동일 표의 '직전반기(2025.4Q)' 컬럼(p.28) 수치를 100으로 나누면 kics_disclosure.json의 "
    f"기존 2025.4Q item41-46(49279.78/49379.89/47485.94/49404.48/46449.23/51552.56)과 "
    f"소수점 둘째자리까지 완전히 일치 — 표 해석·매핑이 정확함을 교차검증함. "
    f"항등식 검산: item36=sqrt(max(R상승,R하락)^2+max(R평탄,R경사)^2)+R평균회귀, R=item41-시나리오 "
    f"-> 기대값 3739.34, 실측(기존 item36) 3744.68, 차 5.34 (tol=max(eff_tol,5%)=187.2 이내 정합)."
)
EV_48_FIX = (
    f"{MD} L435 '보완자본 한도 | 1,044,696 | 1,044,696' (백만원) = 10446.96억. "
    f"기존 마스터 item48 값 '21854'는 L433 '보완자본 | 2,185,377 | 2,185,377'(=item3, 21853.77≈21854)과 "
    f"동일값 — 라벨매칭이 '보완자본 한도'를 '보완자본'과 혼동한 오맵(2026-08-29 KR0050 온보딩에서 "
    f"발견된 것과 동일 실패모드, scripts/fix_20260829_kr0050_2026q2_onboarding.py 참고). "
    f"교차검증: 보완자본한도 = SCR(item14=20894) x 50% = 10447.0 ≈ 10446.96 (자본 tiering 공식과 일치, "
    f"21854는 이 공식과 무관). 자체검산(KR0050 precedent와 동일 항등식): "
    f"item51(21853.77) == min(item47=0,item48=10446.96)+item49(21853.77)+item54(0) = 21853.77 정확 일치."
)
EV_TFI_MISSING = (
    f"{MD} L428-439 표에서 item47/49/50/51/53/54 에 해당하는 행이 종전 파싱에서 누락(item48/52만 "
    f"부분적재됐고 48은 위처럼 오염). 원문 그대로 신규 UPSERT."
)
EV_5354_BLANK = (
    f"{MD} L437-438 '(기발행 신종자본증권) | 0 | ' / '(기발행 후순위채무) | 0 | ' — "
    f"적용후 컬럼이 원문에 문자 그대로 공란(0도 아니고 빈칸). KR0095 자신의 2025.4Q/2026.1Q 마스터도 "
    f"동일 패턴(값=0, 값_적용후=None)이라 이 회사의 기존 관례와 일치 — 결측이 아니라 원천이 공란."
)

# ---------------------------------------------------------------------------
# item -> (name copied verbatim from KR0095's own kics_disclosure.json rows, value)
# ---------------------------------------------------------------------------
NAMES = {
    1: "가. 지급여력금액", 2: "기본자본", 3: "보완자본",
    4: "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", 5: "1. 보통주",
    6: "2. 자본항목 중 보통주 이외의 자본증권", 7: "3. 이익잉여금", 8: "4. 자본조정",
    9: "5. 기타포괄손익누계액", 10: "6. 비지배지분", 11: "7. 조정준비금",
    12: "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)",
    13: "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)",
    14: "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)", 15: "Ⅰ. 기본요구자본",
    16: "- 분산효과 : (1+2+3+4+5) - Ⅰ", 17: "1. 생명장기손해보험위험액",
    18: "2. 일반손해보험위험액", 19: "3. 시장위험액", 20: "4. 신용위험액", 21: "5. 운영위험액",
    22: "Ⅱ. 법인세조정액", 23: "Ⅲ. 기타 요구자본(1+2+3)",
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
    27: "다. 지급여력비율 : 가 ÷ 나 × 100",
    29: "1-1. 사망위험액", 30: "1-2. 장수위험액", 31: "1-3. 장해·질병위험액",
    32: "1-4. 장기재물·기타위험액", 33: "1-5. 해지위험액", 34: "1-6. 사업비위험액",
    35: "1-7. 대재해위험액",
    36: "3-1. 금리위험액", 37: "3-2. 주식위험액", 38: "3-3. 부동산위험액",
    39: "3-4. 외환위험액", 40: "3-5. 자산집중위험액",
    41: "3-1-0. 금리위험 순자산가치(충격전)", 42: "3-1-1. 금리위험 순자산가치(평균회귀)",
    43: "3-1-2. 금리위험 순자산가치(금리상승)", 44: "3-1-3. 금리위험 순자산가치(금리하락)",
    45: "3-1-4. 금리위험 순자산가치(금리평탄)", 46: "3-1-5. 금리위험 순자산가치(금리경사)",
    47: "보완자본 한도 적용 전", 48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)", 51: "보완자본(TFI표, 공통적용경과조치)",
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

# RED #1 core+adjust chain (existing 값, unchanged) -- mirror only
RED1_CORE = {1: 48563, 2: 26709, 3: 21854, 14: 20894, 15: 27519, 16: 6339, 17: 21367,
             18: 0, 19: 9253, 20: 1548, 21: 1690, 22: 6625, 23: 0, 27: 232.42557672}
# extra items mirrored for full-row consistency (already 값-present, not part of the
# blocking census set but same non-applier fact governs them; zero new risk -- pure
# copy of already-validated 값)
EXTRA_MIRROR = {4: 48563, 5: 2097, 6: 0, 7: 34028, 8: 0, 9: -4109, 10: 0, 11: 16547,
                12: 0, 13: 21854, 24: 0, 25: 0, 26: 0,
                29: 1988.43, 30: 401.87, 31: 4886.1, 32: 0, 33: 17515.72, 34: 3733.64,
                35: 794.47, 36: 3744.68, 37: 4533.38, 38: 361.61, 39: 6504.5, 40: 0}

# RED #2: fresh from raw PDF p27 (both 값/값_적용후 identical, non-applier)
IRR_NEW = {41: 48562.81, 42: 48490.46, 43: 46226.11, 44: 49619.85, 45: 45736.75, 46: 50689.22}

# bonus: TFI memo table 47-54 (new + item48 correction)
TFI_NEW = {47: 0, 49: 21853.77, 50: 26709.04, 51: 21853.77, 53: 0, 54: 0}
TFI_FIX = {48: 10446.96}   # was wrong (21854, = item3 mismap)
TFI_MIRROR_ONLY = {52: 48563}  # already present & correct-enough, just add 값_적용후

cells = []


def add(item, val, val_post, evidence):
    cells.append({
        "항목번호": item,
        "항목명": NAMES[item],
        "값": val,
        "값_적용후": val_post,
        "근거": evidence,
    })


# --- RED #1: core capital/requirement chain, mirror 값_적용후 = 값 ---
core_evidence = " | ".join([EV_NONAPPLIER, EV_HEADLINE, EV_TFI_1, EV_TFI_2, EV_TFI_3])
for item, val in RED1_CORE.items():
    add(item, val, val, f"[RED#1 TRAILING] {core_evidence}")

# --- extra same-quarter mirror (4-13,24-26,29-40) for full-row consistency ---
extra_evidence = " | ".join([EV_NONAPPLIER, EV_TFI_2, EV_TFI_3])
for item, val in EXTRA_MIRROR.items():
    add(item, val, val, f"[비RED, 동일 미러 원칙 확장] {extra_evidence}")

# --- RED #2: 36_irr items 41-46, fresh source, both 전/후 identical ---
for item, val in IRR_NEW.items():
    add(item, val, val, f"[RED#2 36_irr] {EV_IRR}")

# --- bonus: TFI memo table 47-54 ---
for item, val in TFI_NEW.items():
    ev = EV_TFI_MISSING if item not in (53, 54) else (EV_TFI_MISSING + " " + EV_5354_BLANK)
    val_post = None if item in (53, 54) else val
    add(item, val, val_post, f"[비RED, TFI표 보완] {ev}")
for item, val in TFI_FIX.items():
    add(item, val, val, f"[비RED, 데이터 오류 정정] {EV_48_FIX}")
for item, val in TFI_MIRROR_ONLY.items():
    add(item, val, val, f"[비RED, TFI표 미러] {EV_TFI_1}")

cells.sort(key=lambda c: c["항목번호"])

patch = {
    "company_code": "KR0095",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "메트라이프생명보험은 2023.3Q부터 2026.1Q까지 13개 분기 연속 경과조치(TFI/RPT/TAC/TIR/TER/"
        "TIRR/PCA_DEFER) 전부 미적용(X) — data/_derived/kics_transition_applicability.json 확인. "
        "2026.2Q 원문도 '당사는 공통 및 선택적용 경과조치를 모두 적용하지 않고 있습니다'(L372) + "
        "종류표 전부 X(L374-382)로 동일 확인. RED#1(TRAILING, item1/2/3/14-23/27후 결측)은 KR0050 "
        "2026.2Q 온보딩(scripts/fix_20260829_kr0050_2026q2_onboarding.py 섹션 C)과 동일한 "
        "'값_적용후=값' 미러로 닫힘 — 이번엔 추가로 원문 [지급여력비율의 경과조치 적용에 관한 사항] "
        "①②③ 세 표가 전부 적용전=적용후를 셀 단위로 직접 인쇄하고 있어(추정이 아니라 원문 대조 "
        "확인), item1/2/3/14/15/17/18/19/20/21/22/23/27은 간접추정이 아닌 직접 증거로 미러링함. "
        "이 김에 이미 값이 있던 item4-13/24-26/29-40(총괄표+생명장기+시장위험 세부)도 동일 원칙으로 "
        "값_적용후를 채웠음(RED 목록엔 없지만 동일 사실관계이고 원문이 셀 단위로 직접 확인해줌 -- "
        "item29-40은 raw TFI 표 백만원 값을 100으로 나눈 결과가 기존 마스터 값과 소수점 둘째자리까지 "
        "완전 일치해 재검증도 겸함). "
        "RED#2(36_irr, item41-46 결측)는 docling MD가 keyword_window 파싱이라 해당 페이지(원본 PDF "
        "p27, '금리위험액 현황' 표)를 통째로 건너뛴 것이 원인 -- fitz로 원본 PDF 직접 확인해 6개 값 "
        "전부 채움. 2025.4Q 직전분기 비교컬럼(p28)으로 표 해석을 교차검증(소수점 둘째자리까지 완전 "
        "일치) + item36 역산 항등식으로 정합성 확인(오차 5.34, tol 187.2 이내). "
        "부가 발견: item48(보완자본 한도)의 기존 저장값 '21854'는 실제로 item3(보완자본)과 동일한 "
        "값이 잘못 들어간 라벨 혼동(2026-08-29 KR0050 온보딩에서 확인된 것과 동일 실패모드) -- "
        "원문 및 '보완자본한도=SCR*50%' 공식(20894*0.5=10447≈10446.96) 둘 다로 교차검증해 10446.96으로 "
        "정정. item47/49/50/51/53/54는 같은 표에서 신규 UPSERT(53/54는 원문 자체가 적용후 공란이라 "
        "값_적용후=null 유지, KR0095 2025.4Q/2026.1Q 마스터의 기존 관례와 동일)."
    ),
    "unfixable": [],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(cells)} cells to {OUT}")
for c in cells:
    print(f"  item{c['항목번호']:>2} {c['항목명']!r:60} 값={c['값']!r} 값_적용후={c['값_적용후']!r}")
