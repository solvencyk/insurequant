# -*- coding: utf-8 -*-
"""룰 커버리지를 **선언하고 기계로 대조한다** (owner 2026-08-21).

## 왜 필요한가

골든 테스트는 `있는 것`을 박제한다. `있어야 하는데 없는 것`은 모른다 — 룰을 아예 안 쓰면
골든은 그 부재까지 같이 고정한다. 실제로 그렇게 됐다: 항목 12·13·24·25·26 은 **어떤 룰도
참조하지 않는데** 게이트는 몇 달간 RED=0 이었고, 2026-08-21 에 손으로 뒤져서야 발견됐다
(흥국생명 2023.3Q item24=8,313 이 원문에 없는 날조값이었다).

owner 지적: "validator가 매번 검증룰 까먹거나 몇개 빼먹는 것도 비슷한 이유 아니냐."
맞다. 그런데 원인은 "룰이 git 에 없어서"가 아니다 — 룰은 이미 코드로 git 에 있다.
없는 것은 **'무엇이 검사돼야 하는가'라는 선언**이고, 선언이 없으면 빠진 것을 셀 수가 없다.

## 어떻게 재나 — 변이(mutation)

각 (항목, 컬럼)의 값을 전부 흔들어 놓고 룰엔진을 다시 돌려, **finding 의 status 가 하나라도
바뀌는지** 본다. 안 바뀌면 그 칸은 어떤 룰도 안 보는 것이다. 정적 분석(어느 룰이 어느 item 을
참조하나)과 달리 이건 속일 수 없다 — 룰이 있어도 실제로 안 걸리면 무방비로 잡힌다.
`run_validation` 1회 0.03초, 전수 46항목 x 2컬럼 ≈ 3초.

## 이 테스트가 실패하면

- **GUARDED 로 선언했는데 무방비로 측정됨** = 룰이 사라졌거나 약해졌다. 심각. 되돌려라.
- **무방비로 선언했는데 GUARDED 로 측정됨** = 누가 커버리지를 늘렸다. 좋은 일이다.
  아래 MANIFEST 에서 그 항목을 지워 반영하라(그래야 다시 없어질 때 이 테스트가 잡는다).

## 이 테스트가 증명하지 **못하는** 것 — 동어반복

변이시험은 "룰이 이 칸을 본다"를 증명한다. **"룰이 실패할 수 있다"는 증명하지 않는다.**
값을 파이프라인이 항등식에 맞게 되맞춰(reconcile) 저장하면, 룰은 실데이터에서 영원히 통과하고
변이시험은 여전히 GUARDED 로 나온다. 실측 반례(2026-08-21): `item4`(Ⅰ 순자산)가
`fill_period_to_disclosure._reconcile_item4_from_components` / `recalc_kics_derived.py` 때문에
공시값이 아니라 자식합으로 덮여 있어, **rule 2 의 잔차가 484건 중 452건에서 정확히 0** 이다
(억원 반올림 표에서 7개 항목 합이 93% 확률로 딱 떨어질 수는 없다). 즉 rule 2 는 GUARDED 로
측정되지만 실데이터에서는 구조적으로 못 터진다.

동어반복 탐지는 **잔차 분포**를 봐야 한다(정확히 0 비율이 비정상적으로 높으면 입력이 공시값이
아니라 파생값이다). 그건 이 테스트가 아니라 게이트 룰의 몫이다 — 티켓 발주됨.

## 두 층을 다 잰다

룰이 두 파일에 흩어져 있다 — 일반 항등식은 `kics_json_rules.run_validation`(적용전 위주),
`적용후` 검사의 상당 부분은 `scripts/validate_kics_disclosure.py` 의 별도 축(mmult15/17/19 ·
R1 · R2 · R5 · R6 · R7 · R8 · 36_irr · 기타요구자본 합)에 나중에 덧댄 것이다. 그래서 **층별로
따로 잰다**:

1. `test_item_coverage_matches_manifest` — 룰엔진만. 빠르다(~10초). 아래 PRE/POST 매니페스트.
2. `test_full_gate_coverage_matches_manifest` — 게이트 전체를 서브프로세스 없이 in-process 로
   돌려(`--master` 로 흔든 사본을 물린다) **엔진이 못 보는 칸을 게이트는 보는지** 확인한다.
   엔진 무방비 48칸만 검사하므로 ~40초.

실측(2026-08-21): 엔진 무방비 48칸 중 **44칸은 게이트 전체가 잡는다.** 진짜 사각은 **4칸**
= `item12`·`item13` 의 적용전·적용후. 즉 "적용후 43칸 무방비"는 엔진만 본 과장이었다.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MASTER = ROOT / "kics_disclosure.json"

# 룰엔진이 내보내야 하는 룰 id 전량. 추가·개명·삭제하면 여기도 고쳐야 테스트가 통과한다.
DECLARED_RULES = {
    "1",          # item1 = item2 + item3
    "2",          # item4 = sum(items 5-11)
    "3",          # 영구 SKIP (item4-item12+item13 다리 — 대상을 item1 로 잡아 2.7% 밖에 안 닫힌다.
                  #            item2 로 잡으면 88.8%. 티켓 inbox/validation/20260821T1100Z)
    "4",          # item15 = sqrt(R4[17-20]) + item21
    "5",          # item14 = item15 - item22 + item23
    "6",          # item16 = sum(17..21) - item15
    "7",          # item27 = item1 / item14 * 100
    "8",          # item28 = item2 / item14 * 100
    "8_life",     # item17 = sqrt(R7[29-35])
    "8_post",     # item28 적용후
    "9",          # 경과조치 방향성 (item2 적용후)
    "10",         # 경과조치 방향성 (item14 적용후)
    "19_market",  # item19 = sqrt(MARKET_M[36-40])
    "36_irr",     # item36 = f(41-46)
    # --- 보완자본 한도 3줄(47/48/49) 축, 2026-08-21 신설 -------------------
    # 적재 직후 게이트가 exit 0 이었던 1,299칸을 덮는다. 네 축의 **증거력이 서로 다르다**:
    "2_tier1_bridge",           # item2 = item4 − (item12 − 한도초과) − item13  [RED, 주 룰]
    "2_tier1_bridge_post",      #   위 적용후 (관계식 미확립 → YELLOW)
    "3_tier2_composition",      # item3 = min(47,48)+49 (CAPPED) | = 47 (UNCAPPED)
                                #   | = item13 (TFI_NA — 표 자체가 미기재) [RED]
    "3_tier2_composition_post", #   위 적용후 (관계식 미확립 → YELLOW)
    "47_tier2_census",          # 47/48/49 완전성·부호·자릿수·중복행·전기한도잔존 [RED]
    "47_tier2_census_post",     #   위 적용후 (스코프 무관 → 적용후도 RED)
    "48_tier2_limit",           # item48 = item14_적용전 × 50%  [YELLOW — 아래 참조]
    "48_tier2_limit_post",      #   위 적용후 (분모는 적용후가 아니라 **적용전** SCR)
    # --- TFI 표 자신의 기본자본/보완자본(50/51) 축, 2026-08-22 신설 -----------
    # parser 가 코리안리 7분기분을 적재했는데 이 두 항목을 보는 룰이 하나도 없었다.
    # **이 테스트가 그걸 즉시 잡았다**(item50[값]·item51[값] 7칸씩 무방비) — 설계대로 동작했다.
    # 47/48/49 때는 1,285칸이 조용히 통과했고 손으로 뒤져서야 발견됐던 것과 대비된다.
    #
    # 2026-08-22 (2차) — parser 가 431버킷을 백필하자 이 두 축이 **127칸 RED** 로 터졌다.
    # 전수 분해 결과 데이터 오염 0건, 전부 룰 커버리지 결손이었다. 선언을 그 수정에 맞춘다.
    "50_tfi_tier_split",           # item50 + item51 = item52 (같은 표 지급여력금액 행) [RED]
    "50_tfi_tier_split_post",      #   위 적용후 — **2026-08-24 등식 승격.** 종전에는 등식의
                                   #   비교 대상(item52)이 마스터에 없어 범위검사였다. parser
                                   #   iter-10 이 428버킷에 실었으므로 적용전·적용후 **둘 다**
                                   #   같은 식이 됐다. item52 결측 버킷에서만 종전 폴백
                                   #   (적용전=item1 대조 / 적용후=범위검사)이 산다.
                                   #   승격 실측: 적용후 YELLOW 70 → 69칸이 등식으로 닫히고,
                                   #   **GREEN 이던 6칸이 RED 로 뒤집혔다**(카카오페이 5버킷
                                   #   item52 100배 + 삼성화재 2025.3Q 적용후 자릿수 전치).
                                   #   그 6칸이 이 승격의 값어치다 — 종전 comparand(item1)로는
                                   #   구조적으로 못 보는 오류였다.
    "51_tfi_tier2_composition",    # item51 = 축 B 와 **같은 `_tier2_branch`** (target=51) [RED]
    "51_tfi_tier2_composition_post",  # 위 적용후 (관계식 미확립 → YELLOW)
    # --- TFI 표 메모행(53/54) 축, 2026-08-24 신설 -----------------------------
    # parser iter-10 이 52/53/54 를 적재하자 이 테스트가 즉시 "무방비" 로 실패했다 —
    # 설계대로다. 52 는 축 E 의 comparand 로 흡수했고, 53/54 는 **항등식의 항이 아니라
    # 메모행**이라 별도 축을 만들었다. 등식으로 승격하지 않은 근거는 룰 docstring 참조
    # (`item51 == min(47,48)+49+item54` 전수 시뮬: 새로 닫힘 1 · 새로 깨짐 218).
    "53_tfi_memo_rows",            # census(적용전) · 부호 · 53+54 ≤ item51           [RED]
    "53_tfi_memo_rows_post",       #   위 적용후 — census 는 안 건다(원문에 적용후 칸이
                                   #   대부분 없다, 관측 12개사). 부호·포함관계는 돈다.
}

# **통과가 증거가 아닌 축** — 로더가 그 관계를 강제하므로 GREEN 이 추출 정확성을 뜻하지 않는다.
# parser 가 100배 사고를 고치면서 스케일 배율(÷1 vs ÷100) 판별 앵커를 `item48 ≈ item14 × 50%`
# 로 바꿨다. 즉 이 식을 가장 잘 만족하는 배율을 골라 저장한다 → 검사하면 당연히 통과한다.
# 그래서 이 축은 blocking(RED)이 아니라 review(YELLOW)로 낸다. 여기 등재된 룰이 RED 를 내기
# 시작하면 그건 '증거력 없는 축이 blocking 으로 승격됐다'는 뜻이라 아래 테스트가 막는다.
LOADER_ENFORCED_RULES = {"48_tier2_limit", "48_tier2_limit_post"}

# 적용후 관계식이 **아직 확립되지 않은** 축. 적용전에서는 닫히는데 적용후에서는 안 닫히고,
# raw 대조 결과 추출은 정확하다(한화손해 2023.2Q: 적용전 정확, 적용후 잔차 5,872.17).
# 확립 못 한 것을 위반이라고 단정하면 220칸이 전부 오탐이 되므로 YELLOW 로 둔다.
# **확립되면 RED 로 승격하고 여기서 지워라.**
#
# 2026-08-22: `51_tfi_tier2_composition_post` 추가. 같은 반증 양식이 코리안리 자체 데이터에도
# 있다 — 2023.2Q 적용전 min(6167.44, 9832.38)+24.99 = 6,192.43 = item51_전 (정확) 인데
# 적용후는 min(581.39, 9832.38)+24.99 = 606.38 ≠ item51_후 5,209.20 (잔차 4,602.82).
# `50_tfi_tier_split_post` 는 **여기 없다** — 합계 항등식이라 스코프에 무관하고 실측 7/7 통과다.
POST_UNESTABLISHED_RULES = {"2_tier1_bridge_post", "3_tier2_composition_post",
                            "51_tfi_tier2_composition_post"}

# `3_tier2_composition` 이 GREEN 을 내는 **모든 갈래**. 갈래를 늘릴 때마다 여기 등재해야 하고,
# 아래 테스트가 갈래마다 "값을 흔들면 GREEN 이 아니게 된다" 를 실데이터로 증명한다.
#
# 왜 필요한가 (2026-08-22): 이 축의 RED 27건을 전수 분류하니 12건이 "발행사가 TFI 표 세 행을
# 전부 0 으로 인쇄한 회사" 였다 — 한도 항등식의 입력이 아예 없다. 갈래를 나누는 것은 옳지만
# **나누기만 하면 검사가 아니라 분류다.** 바로 전날 `48_tier2_limit` 이 로더 강제라 무의미해진
# 전례가 있어(LOADER_ENFORCED) 같은 실수를 기계로 막는다. 갈래를 하나 늘리고 falsifiability
# 를 증명하지 않으면 그 갈래는 면제와 구별되지 않는다.
#
# 2026-08-24: 갈래가 4 → 6 으로 늘었다. `item47`(보완자본 한도 적용 전)의 **스코프가 발행사마다
# 다르다**는 것이 원문 대조로 확정됐기 때문이다(한화생명 2025.2Q p18 = 포함 / IBK연금 2025.3Q
# p16 = 제외). 스코프가 갈리면 한도초과액 계산식이 갈리고, 그 값이 `2_tier1_bridge` 에 그대로
# 들어간다 — 안 갈랐던 동안 한화생명 2025.2Q 다리가 −30,095 로 틀렸고 그것이 "발행사 모순" 으로
# 오진돼 owner 판단 면제까지 갔다.
#
# **새 이름이 기존 이름의 접두사가 아니라는 점이 중요하다.** 게이트·테스트가
# `"branch=CAPPED" in detail` 같은 부분문자열로 갈래를 읽으므로 `CAPPED_INCL` 같은 이름을
# 쓰면 두 갈래가 한 이름으로 뭉개져 조용히 오분류된다.
# `test_branch_names_are_not_prefixes_of_each_other` 가 기계로 막는다.
COMPOSITION_BRANCHES = {
    "CAPPED":    "target == min(47,48) + 49 — 한도가 실제로 자른다 (item47 스코프=EXCL)",
    "UNCAPPED":  "target == item47 — 한도로 안 잘림 (item47 스코프=EXCL)",
    "BOTH":      "위 둘 다 성립(초과액도 item49 도 0) (item47 스코프=EXCL)",
    "I49_IN_I47_CAPPED":
                 "target == min(47−49, 48) + 49 — item47 이 item49 를 포함해 인쇄되는 회사에서 "
                 "한도가 실제로 자른다. 한도초과 = (47−49) − 48.",
    "I49_IN_I47_UNCAPPED":
                 "target == item47 — 같은 회사에서 한도가 구속하지 않는 분기(초과액 0). "
                 "2026-08-24 이전에는 이 칸들이 `UNCAPPED` 로 뭉뚱그려져 있었고, 그래서 "
                 "한도가 구속하는 분기의 오분류가 드러나지 않았다.",
    "TFI_NA_OK": "47=48=49=0 이고 item14>0 → item48 은 한도가 아니다(해당사항 없음). "
                 "대체 항등식 target == item13 으로 검산한다. 실측 24/24 성립.",
}

# 이 갈래를 쓰는 **모든** 축과 각 축의 대상 셀. 2026-08-22 (2차) 에 축 F 가 합류했다.
#
# 왜 표로 두나: 축 F 는 하루 동안 갈래 없이 `min(47,48)+49` 만 검사했고 적용전 67칸이 RED
# 였다. 그중 62칸이 축 B 가 **이미 갖고 있던** 갈래를 안 가져와서 생긴 오탐이다. 갈래를
# 공유한다는 사실을 선언으로 박아 두면, 새 축이 또 자기 갈래를 재구현할 때 아래 시험이 막는다.
COMPOSITION_AXES = {
    "3_tier2_composition": 3,        # 헤드라인 [경과조치 적용 전 지급여력비율 세부] 의 보완자본
    "51_tfi_tier2_composition": 51,  # TFI 표 자신의 보완자본(47/48/49 의 부모행)
}

# 적용전(값)에서 **어떤 룰도 보지 않는** 항목. 빈 dict 가 목표다.
#
# 2026-08-21: item12·13 이 여기서 빠졌다 — `2_tier1_bridge` 가 배선되면서 실제로 검사된다.
# 오래 막혀 있던 이유는 다리에 필요한 '보완자본 한도 초과액' 이 스키마에 없었기 때문인데,
# parser 가 항목 47/48/49 를 적재해 초과액 = max(0, item47 − item48) 로 계산 가능해졌다.
# 실측(2026-08-22 갱신): 검사 477 · 통과 467 · 잔차 10. 후보식 전수 비교 —
#   초과항 없음 425/52 · 무조건 더함 440/37 · CAPPED 조건부 461/16 ·
#   **CAPPED 조건부 + item12 상한 클램프 467/10**(채택). 클램프 근거는 발행사 각주가
#   한도초과액을 불인정항목의 *구성요소*로 정의한다는 것 — 근사치가 상한을 넘으면 그 값은
#   다른 데서 온 것이다. 임계를 키운 게 아니라 불가능한 값을 잘라낸 것이라, 클램프가 발동하는
#   10칸 중 9칸에서 다리가 **정확히** 닫히고 남은 1칸(한화생명 2025.2Q)은 그대로 RED 다.
PRE_UNGUARDED = {
    24: "item23 = item24 + item25 + item26 룰 미배선. 실측 오탐 0(적용전 401검사/400통과). "
        "이 구멍 때문에 흥국생명 2023.3Q item24=8,313(원문은 '-') 날조값이 안 잡혔다.",
    25: "위와 같은 룰.",
    26: "위와 같은 룰.",
}

# 적용후(값_적용후)에서 룰엔진이 보는 항목. 나머지는 전부 엔진 사각(모듈 docstring 참조).
#
# 2026-08-21: {2, 14, 28} → 10개로 늘었다. 보완자본 한도 축을 **적용전만 배선하고 끝내지 않고**
# 적용후 미러를 같이 만든 결과다(3·4·12·13·47·48·49 추가). 적용후 축 중 둘은 관계식이 아직
# 확립되지 않아 YELLOW 지만, **변이시험 기준으로는 검사되는 칸**이다 — 값을 흔들면 상태가 바뀐다.
#
# 2026-08-22: {1, 50, 51} 추가. `50_tfi_tier_split_post`(item50+item51 == item1, 같은 컬럼)를
# 배선한 결과다. **적용전 룰만 만들고 끝내지 않는다** 는 불변식대로 적용후 미러를 같이 만들었고,
# 그 덕에 item1 의 적용후 컬럼도 처음으로 엔진 커버리지에 들어왔다.
#
# ⚠️ 이 플래그는 **이진값이라 '몇 칸이 검사되나'를 담지 못한다.** 2026-08-22 (2차) 에 parser
# 백필로 50/51 이 431버킷/39개사로 늘어 item1_적용후 커버리지가 7 → 431칸이 됐지만, 나머지
# 57버킷은 아직 엔진 사각이다 — 그건 `50_tfi_tier_split` 의 SKIP 사유로 게이트가 매 실행 센다
# (`TFI_TIER_ROWS_ABSENT_NO_TABLE` 48 · `TFI_TIER_ROWS_ABSENT_BACKLOG` 9).
# 뒤의 9칸은 47/48/49 는 있는데 50/51 만 없는 버킷이라 **명확한 추출갭**이다(parser 발주 대상).
#
# 2026-08-24: {52, 53, 54} 추가. parser iter-10 이 실은 1,291셀이 하루도 무방비로 있지 않게
# 같은 라운드에 배선했다. **item52 는 축 E 의 comparand 로 흡수**돼 적용전·적용후 둘 다
# 등식이 됐다(아래 ⚠️⚠️ 경고가 해소됐다). 53/54 는 부호·포함관계로 적용후에서도 검사된다.
#
# ⚠️ 이 플래그는 **이진값이라 '몇 칸이 검사되나'를 담지 못한다.** item53/54 의 적용후 셀은
# 60/59 칸뿐이고(원문이 메모행을 적용전 칸에만 인쇄한다), 나머지 버킷은 검사할 셀 자체가 없다.
# 그건 `53_tfi_memo_rows_post` 의 SKIP 사유 `TFI_MEMO_POST_COLUMN_ABSENT` 로 매 실행 세어진다.
POST_GUARDED = {1, 2, 3, 4, 12, 13, 14, 28, 47, 48, 49, 50, 51, 52, 53, 54}

# **게이트 전체(엔진 + validate_kics_disclosure 축)로도** 못 잡는 항목. 여기가 진짜 사각이다.
# 빈 dict 가 목표. 값을 흔들어도 게이트 출력이 한 글자도 안 바뀌는 칸들이다.
# 2026-08-21: **비었다.** 종전 item12·13 은 `2_tier1_bridge` 배선으로 해소됐다 — 막고 있던
# 원인('보완자본 한도 초과액'이 스키마에 없음)이 항목 47/48/49 적재로 사라졌다.
# 빈 dict 가 목표 상태이고, 지금 그 상태다. 새로 사각이 생기면 아래 테스트가 막는다.
GATE_BLIND: dict[int, str] = {}


def _tfi_map():
    """게이트와 **같은 로더**로 적용여부 사이드카를 읽는다.

    매니페스트가 룰엔진을 게이트와 다른 입력으로 돌리면, 여기서 GUARDED 로 측정된 칸이
    게이트에서는 무방비일 수 있다 — 측정 자체가 거짓이 된다."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_kics_disclosure import _load_tfi_applicability
    return _load_tfi_applicability()


def _findings(rows, tfi=None):
    from solvency.validation.kics_json_rules import run_validation
    r = run_validation(rows, tfi_applicability=_tfi_map() if tfi is None else tfi)
    return r["findings"] if isinstance(r, dict) else r


def _sig(findings):
    return {(f["원보험사코드"], f["공시분기"], f["rule"]): f["status"] for f in findings}


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def test_rule_id_set_matches_manifest(rows):
    """엔진이 내보내는 룰 id == 선언된 집합. 양방향."""
    emitted = {f["rule"] for f in _findings(rows)}
    missing = DECLARED_RULES - emitted
    extra = emitted - DECLARED_RULES
    assert not missing, (
        f"선언된 룰이 엔진에서 안 나온다: {sorted(missing)}. "
        "룰이 삭제·개명됐거나 조건이 좁아져 한 번도 발화하지 않는다.")
    assert not extra, (
        f"엔진이 선언되지 않은 룰을 내보낸다: {sorted(extra)}. "
        "DECLARED_RULES 에 목적 한 줄과 함께 추가하라 — 선언 없는 룰은 아무도 그 존재를 모른다.")


def test_loader_enforced_axes_never_become_blocking(rows):
    """**통과가 증거가 아닌 축은 RED 를 내면 안 된다.**

    `48_tier2_limit` 은 parser 가 스케일 배율을 고를 때 쓰는 바로 그 식이다. 로더가 만족시킨
    관계를 blocking 으로 세면 게이트의 RED=0 이 '검사했는데 깨끗하다' 가 아니라 '로더가
    자기 산수를 다시 확인했다' 가 된다 — 이 저장소가 두 달을 날린 false-green 의 정확한 형태다.

    이 축을 지우지 않고 남겨 두는 이유는 회귀 감시다(로더가 앵커를 또 바꾸면 여기가 먼저 움직인다).
    다만 증거력이 없다는 사실을 **기계가 강제**해야 다음 세션이 무심코 승격시키지 못한다."""
    by_rule = {}
    for f in _findings(rows):
        by_rule.setdefault(str(f["rule"]), set()).add(f["status"])
    for rule in sorted(LOADER_ENFORCED_RULES):
        assert rule in by_rule, f"{rule} 이 사라졌다 — 회귀 감시 축이 없어졌다"
        assert "RED" not in by_rule[rule], (
            f"{rule} 이 RED 를 낸다. 이 축은 로더가 강제하므로 통과도 실패도 추출 정확성의 "
            "증거가 아니다 — blocking 으로 올리려면 먼저 로더가 이 식을 앵커로 쓰지 않게 "
            "바꿔야 한다(그때 LOADER_ENFORCED_RULES 에서 지워라).")
    for rule in sorted(POST_UNESTABLISHED_RULES):
        assert rule in by_rule, f"{rule} 이 사라졌다"
        assert "RED" not in by_rule[rule], (
            f"{rule} 의 적용후 관계식은 아직 확립되지 않았다(raw 반증: 한화손해 2023.2Q). "
            "RED 로 올리려면 원문 근거로 관계식을 먼저 확정하고 "
            "POST_UNESTABLISHED_RULES 에서 지워라.")


@pytest.mark.parametrize("rule", sorted(COMPOSITION_AXES))
def test_composition_branch_set_matches_manifest(rows, rule):
    """엔진이 실데이터에서 쓰는 갈래 == 선언된 갈래. 갈래를 늘리면 여기도 고쳐야 한다.

    갈래 이름이 detail 에 안 박히면 게이트 출력만 보고는 어떤 근거로 통과했는지 알 수 없다.
    **갈래를 공유하는 모든 축**에 같은 잣대를 댄다 — 한 축만 검사하면 다른 축이 조용히
    자기 갈래를 재구현해도 안 걸린다(2026-08-22 축 F 에서 실제로 그랬다)."""
    seen = set()
    for f in _findings(rows):
        if f["rule"] != rule or f["status"] != "GREEN":
            continue
        for name in COMPOSITION_BRANCHES:
            if f"branch={name}" in f.get("detail", ""):
                seen.add(name)
                break
        else:
            raise AssertionError(
                f"{rule} 통과 사유에 갈래 이름이 없다: {f['원보험사코드']} {f['공시분기']} "
                f"detail={f.get('detail')!r}. 갈래 없는 통과는 추적이 불가능하다.")
    extra = seen - set(COMPOSITION_BRANCHES)
    assert not extra, f"{rule}: 선언되지 않은 갈래가 통과를 만들고 있다: {sorted(extra)}"


@pytest.mark.parametrize("rule", sorted(COMPOSITION_AXES))
def test_every_composition_branch_is_falsifiable(rows, rule):
    """**갈래를 나눈 것이 면제가 아님을 실데이터로 증명한다.**

    갈래마다 대표 (회사,분기) 를 하나 뽑아 대상 셀(공시 보완자본)을 크게 흔들고, 그 갈래에서도
    통과가 깨지는지 본다. 흔들어도 GREEN 이면 그 갈래는 검사가 아니라 자동통과다 — 이 저장소가
    두 달을 날린 false-green 의 정확한 형태이고, `48_tier2_limit` 에서 한 번 더 봤다."""
    item = COMPOSITION_AXES[rule]
    rep: dict[str, tuple[str, str]] = {}
    for f in _findings(rows):
        if f["rule"] != rule or f["status"] != "GREEN":
            continue
        for name in COMPOSITION_BRANCHES:
            if f"branch={name}" in f.get("detail", "") and name not in rep:
                rep[name] = (f["원보험사코드"], f["공시분기"])
    assert rep, f"{rule} 이 실데이터에서 한 번도 통과하지 않는다 — 배선 확인"

    survived = []
    for name, (code, quarter) in sorted(rep.items()):
        mutated = copy.deepcopy(rows)
        hit = 0
        for r in mutated:
            if (r.get("원보험사코드") == code and r.get("공시분기") == quarter
                    and str(r.get("항목번호")) == str(item) and r.get("값") not in (None, "")):
                r["값"] = str(float(str(r["값"]).replace(",", "")) + 9_999.0)
                hit += 1
        assert hit, f"{name} 대표 {code} {quarter} 의 item{item} 셀을 못 찾았다"
        after = {(f["원보험사코드"], f["공시분기"], f["rule"]): f["status"]
                 for f in _findings(mutated)}
        if after.get((code, quarter, rule)) == "GREEN":
            survived.append(f"{name} ({code} {quarter}) — item{item} 을 9,999 흔들어도 통과")
    assert not survived, (
        f"{rule}: 갈래가 검사가 아니라 면제가 됐다:\n  " + "\n  ".join(survived)
        + "\n갈래를 늘릴 때는 그 갈래 안에서 RED 가 나는 것을 같이 증명해야 한다.")


def test_composition_axes_share_one_branch_definition():
    """**갈래 정의가 하나뿐임을 소스 수준에서 못 박는다.**

    각 축이 자기 갈래를 재구현하면 같은 이름이 다른 뜻을 갖는다 — 축 F 가 하루 동안 갈래를
    아예 안 갖고 있어서 67칸을 오탐한 것이 그 실패의 첫 단계였다. 여기서는 두 축이 정말로
    같은 함수를 부르는지, 그리고 갈래→status 매핑이 복제되지 않았는지 확인한다."""
    from solvency.validation import kics_json_rules as K
    for rule, item in COMPOSITION_AXES.items():
        assert item in (3, 51), f"{rule} 의 대상 셀 선언이 이상하다"
    # 갈래 판정 함수는 하나이고 대상 셀만 인자로 받는다
    import inspect
    sig = inspect.signature(K._tier2_branch)
    assert "target_item" in sig.parameters, (
        "_tier2_branch 가 대상 셀을 인자로 안 받는다 — 축마다 갈래를 복제하게 된다")
    # status 매핑도 공유 상수 하나에서 온다
    assert K._COMPOSITION_RED_BRANCHES == frozenset({"NEITHER", "TFI_NA_RED"})
    assert K._COMPOSITION_SKIP_BRANCHES == frozenset({"INPUT_MISSING", "TFI_NA_NO_INPUT"})
    # 갈래는 스코프를 인자로 받는다 — 회사별 item47 스코프가 안 들어오면 룰이 한 관행만 안다
    assert "scope" in sig.parameters, (
        "_tier2_branch 가 item47 스코프를 인자로 안 받는다 — 스코프가 갈리는 회사에서 "
        "한도초과액이 item49 만큼 과대·과소 계산된다(2026-08-24 한화생명 2025.2Q 사고)")


def test_branch_names_are_not_prefixes_of_each_other():
    """**갈래 이름이 서로의 접두사이면 안 된다.**

    게이트 출력·테스트·면제 원장이 전부 `"branch=<이름>" in detail` 이라는 **부분문자열**로
    갈래를 읽는다. `CAPPED` 와 `CAPPED_INCL` 처럼 지으면 뒤엣것이 앞엣것으로 읽혀 두 갈래가
    한 이름으로 뭉개지고, 그 오분류는 어떤 출력에도 안 나타난다. 2026-08-24 에 스코프 갈래를
    추가하면서 실제로 밟을 뻔한 함정이라 기계로 못 박는다."""
    from solvency.validation import kics_json_rules as K
    names = sorted(set(COMPOSITION_BRANCHES) | K._TIER2_UNCAPPED_BRANCHES
                   | K._TIER2_EXCESS_BEARING_BRANCHES
                   | K._COMPOSITION_RED_BRANCHES | K._COMPOSITION_SKIP_BRANCHES)
    bad = [(a, b) for a in names for b in names if a != b and b.startswith(a)]
    assert not bad, (
        f"갈래 이름이 서로의 접두사다: {bad} — 부분문자열 판독이 두 갈래를 한 이름으로 뭉갠다")


def test_every_excess_bearing_branch_is_declared():
    """**한도초과액을 다리에 더하는 갈래 집합이 갈래 정의와 어긋나지 않게 한다.**

    `2_tier1_bridge` 는 `_TIER2_EXCESS_BEARING_BRANCHES` 에 든 갈래에서만 한도초과액을 더한다.
    갈래를 새로 만들면서 이 집합을 안 고치면 **새 갈래는 조용히 초과액 0 으로 취급**돼 다리가
    틀린 채 통과한다 — 이 저장소가 반복해서 당한 '룰이 그 대상을 순회조차 안 한다' 형태다.
    (2026-08-24 시뮬레이션에서 실제로 이 누락 때문에 수정이 아무 효과도 못 냈다.)"""
    from solvency.validation import kics_json_rules as K
    undeclared = K._TIER2_EXCESS_BEARING_BRANCHES - set(COMPOSITION_BRANCHES)
    assert not undeclared, (
        f"초과액을 더하는 갈래인데 매니페스트에 선언이 없다: {sorted(undeclared)}")
    # 초과액을 더하는 갈래와 '한도 미구속' 갈래는 겹칠 수 없다
    assert not (K._TIER2_EXCESS_BEARING_BRANCHES & K._TIER2_UNCAPPED_BRANCHES), (
        "같은 갈래가 '한도 미구속' 이면서 '초과액을 더한다' 로 동시에 분류돼 있다")


def test_item_coverage_matches_manifest(rows):
    """각 (항목, 컬럼)을 오염시켜 룰이 알아채는지 전수 확인하고 MANIFEST 와 대조한다."""
    base = _sig(_findings(rows))
    items = sorted({int(r["항목번호"]) for r in rows if str(r.get("항목번호", "")).isdigit()})

    wrong_guarded, wrong_unguarded = [], []
    for item in items:
        for col in ("값", "값_적용후"):
            perturbed = copy.deepcopy(rows)
            n = 0
            for r in perturbed:
                if str(r.get("항목번호")) == str(item) and r.get(col) not in (None, ""):
                    try:
                        r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
                        n += 1
                    except ValueError:
                        pass
            if n == 0:
                continue                      # 그 컬럼에 셀이 없으면 검사할 것도 없다
            after = _sig(_findings(perturbed))
            guarded = any(base[k] != after.get(k) for k in base)

            if col == "값":
                expected = item not in PRE_UNGUARDED
            else:
                expected = item in POST_GUARDED

            if expected and not guarded:
                wrong_guarded.append(f"item{item}[{col}] {n}칸 오염 → 아무 룰도 반응 없음")
            elif not expected and guarded:
                wrong_unguarded.append(f"item{item}[{col}] 이제 검사된다")

    assert not wrong_guarded, (
        "검사되고 있어야 할 칸이 무방비다 — 룰이 사라졌거나 약해졌다:\n  "
        + "\n  ".join(wrong_guarded))
    assert not wrong_unguarded, (
        "커버리지가 늘었다. MANIFEST 를 갱신하라(안 그러면 다시 없어질 때 못 잡는다):\n  "
        + "\n  ".join(wrong_unguarded))


def _mutate(rows, item, col):
    """(항목, 컬럼) 을 통째로 흔든 사본과 흔든 셀 수."""
    out, n = copy.deepcopy(rows), 0
    for r in out:
        if str(r.get("항목번호")) == str(item) and r.get(col) not in (None, ""):
            try:
                r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
                n += 1
            except ValueError:
                pass
    return out, n


def test_full_gate_coverage_matches_manifest(rows, tmp_path):
    """엔진이 못 보는 칸을 **게이트 전체**는 보는지. 진짜 사각은 GATE_BLIND 뿐이어야 한다."""
    import contextlib
    import io
    import re

    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_kics_disclosure as gate

    # main() 은 실행마다 artifacts/kics_validation/ 에 report_<ts>.json 을 쓰고
    # **report_latest.json 을 덮어쓴다**. 변이 데이터의 결과가 그 stable-name 포인터에 남으면
    # 다음에 그 파일을 읽는 사람·스크립트가 쓰레기를 보게 된다 — 원본을 떠 놨다가 되돌린다.
    artifacts = ROOT / "artifacts" / "kics_validation"
    artifacts.mkdir(parents=True, exist_ok=True)
    before = set(artifacts.glob("*"))
    latest = artifacts / "report_latest.json"
    latest_backup = latest.read_bytes() if latest.exists() else None
    master = tmp_path / "master.json"

    def gate_output(rs):
        master.write_text(json.dumps(rs, ensure_ascii=False), encoding="utf-8")
        buf, argv = io.StringIO(), sys.argv[:]
        sys.argv = ["gate", "--master", str(master)]
        try:
            with contextlib.redirect_stdout(buf):
                gate.main()
        finally:
            sys.argv = argv
        # 매 실행 달라지는 타임스탬프·리포트 파일명은 지운다
        return re.sub(r"\d{8}T\d{6}Z", "T", buf.getvalue())

    # 게이트 1회가 세션 초 0.79초에서 룰이 늘며 ~4초가 됐다. 48칸 전수는 그만큼 선형으로 늘어
    # 훅을 84초 -> 267초로 밀어올렸다. 그래서 두 속도로 나눈다:
    #   기본(로컬 pytest)  = GATE_BLIND 선언분만 셀 단위 + 나머지는 한 번에 묶어 확인. 게이트 6회.
    #   FULL_COVERAGE_SWEEP=1 = 48칸 전수. **훅이 이 모드로 돌린다** — push 는 드물고,
    #                           "한 칸이 조용히 사각이 되는 것"을 놓치면 이 테스트의 존재 이유가 없다.
    full = os.environ.get("FULL_COVERAGE_SWEEP") == "1"
    # range 상한은 **마스터에 실재하는 최대 항목번호 + 1** 이어야 한다. 하드코딩된 47 이
    # 신규 항목 47/48/49 를 통째로 스윕 밖으로 밀어냈던 전례가 있어(2026-08-21) 데이터에서 뽑는다.
    max_item = max((int(r["항목번호"]) for r in rows
                    if str(r.get("항목번호", "")).isdigit()), default=46)
    targets = ([(i, "값") for i in sorted(PRE_UNGUARDED)]
               + [(i, "값_적용후") for i in range(1, max_item + 1) if i not in POST_GUARDED])
    try:
        base = gate_output(rows)
        blind, caught = [], []
        declared = [(i, c) for i, c in targets if i in GATE_BLIND]
        others = [(i, c) for i, c in targets if i not in GATE_BLIND]

        for item, col in (targets if full else declared):
            mutated, n = _mutate(rows, item, col)
            if n == 0:
                continue
            (caught if gate_output(mutated) != base else blind).append((item, col, n))

        if not full:
            # 나머지는 한꺼번에 흔든다. 게이트가 **아무 반응도 안 하면** 그 축들이 통째로
            # 죽은 것이므로 잡힌다. 한 칸만 조용히 사각이 되는 경우는 이 묶음으로 못 잡는다 —
            # 그래서 훅은 FULL_COVERAGE_SWEEP=1 로 돈다.
            batch, total = rows, 0
            for item, col in others:
                batch, n = _mutate(batch, item, col)
                total += n
            if total and gate_output(batch) == base:
                blind.extend((i, c, 0) for i, c in others)
    finally:
        for f in set(artifacts.glob("*")) - before:
            with contextlib.suppress(OSError):
                f.unlink()
        if latest_backup is not None:
            latest.write_bytes(latest_backup)
        elif latest.exists():
            with contextlib.suppress(OSError):
                latest.unlink()

    unexpected_blind = [f"item{i}[{c}] {n}칸" for i, c, n in blind if i not in GATE_BLIND]
    now_covered = sorted({i for i, _c, _n in caught} & set(GATE_BLIND))

    assert not unexpected_blind, (
        "게이트 전체로도 못 잡는 칸이 새로 생겼다 — 축이 사라졌거나 좁아졌다:\n  "
        + "\n  ".join(unexpected_blind))
    assert not now_covered, (
        f"item{now_covered} 가 이제 검사된다. GATE_BLIND 에서 지워라 — "
        "안 지우면 다시 사각이 될 때 이 테스트가 못 잡는다.")
