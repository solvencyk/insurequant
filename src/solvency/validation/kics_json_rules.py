"""K-ICS disclosure JSON cross-check rules (item-number keyed rows).

R4 (4x4, life-nl=0 others 0.25, item21 excluded from V):
  V = (item17, item18, item19, item20). item15 = sqrt(V' R4 V) + item21.

R7 (7x7 sub-risk matrix from K-ICS standard, items 29-35):
  item17 = sqrt(S' R7 S) when all sub-items present.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

import numpy as np

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_QUARTER = "공시분기"
KEY_ITEM = "항목번호"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"

R4: np.ndarray = np.array(
    [
        [1.0, 0.0, 0.25, 0.25],
        [0.0, 1.0, 0.25, 0.25],
        [0.25, 0.25, 1.0, 0.25],
        [0.25, 0.25, 0.25, 1.0],
    ],
    dtype=float,
)

R7: np.ndarray = np.array(
    [
        [1.0, -0.25, 0.25, 0.0, 0.0, 0.25, 0.25],
        [-0.25, 1.0, 0.0, 0.0, 0.25, 0.25, 0.0],
        [0.25, 0.0, 1.0, 0.0, 0.0, 0.5, 0.25],
        [0.0, 0.0, 0.0, 1.0, 0.0, 0.5, 0.25],
        [0.0, 0.25, 0.0, 0.0, 1.0, 0.5, 0.25],
        [0.25, 0.25, 0.5, 0.5, 0.5, 1.0, 0.25],
        [0.25, 0.0, 0.25, 0.25, 0.25, 0.25, 1.0],
    ],
    dtype=float,
)
R7 = np.maximum(R7, R7.T)
np.fill_diagonal(R7, 1.0)

# Market sub-risk matrix M (item19 = sqrt(V'·M·V), V=[36,37,38,39,40] = 금리·주식·부동산·외환·자산집중).
# Source: kics-market-risk-decomposition.md §2 (<표19>). 대각 1.0, 외환-주식 −0.25,
# 자산집중 행/열 0(대각 제외), 그 외 비대각 0.25.
MARKET_M: np.ndarray = np.array(
    [
        [1.00, 0.25, 0.25, 0.25, 0.00],
        [0.25, 1.00, 0.25, -0.25, 0.00],
        [0.25, 0.25, 1.00, 0.25, 0.00],
        [0.25, -0.25, 0.25, 1.00, 0.00],
        [0.00, 0.00, 0.00, 0.00, 1.00],
    ],
    dtype=float,
)

STATUS_RED = "RED"
STATUS_YELLOW = "YELLOW"
STATUS_GREEN = "GREEN"
STATUS_ERROR = "ERROR"
STATUS_SKIP = "SKIP"

# Image-only PDF insurers: OCR rounding may exceed default tolerance (see KICS-IMG).
IMAGE_OCR_TOLERANCE = 10.0
IMAGE_OCR_COMPANIES = frozenset({"KR0010", "KR0079"})

# ---------------------------------------------------------------------------
# 보완자본 한도 3줄 (항목 47·48·49) — 2026-08-21 신설
# ---------------------------------------------------------------------------
# parser 가 [지급여력비율의 경과조치 적용에 관한 사항] "1) 공통적용 경과조치" 표에서 세 줄을
# 신규 항목으로 적재했다(inbox/parser/20260821T1425Z). **적재 직후 게이트는 exit 0 이었다** —
# 이 세 항목을 보는 룰이 하나도 없어서 1,285 칸이 통째로 무검사로 통과했다. 이 절이 그 구멍이다.
#
#   47 = 보완자본 한도 적용 전
#   48 = 보완자본 한도                    ← item14(지급여력기준금액) × 50%
#   49 = 해약환급금 부족분 상당액 중 해약환급금 상당액 초과분
TIER2_ITEMS: tuple[int, ...] = (47, 48, 49)

# ---------------------------------------------------------------------------
# TFI 표 자신의 기본자본 / 보완자본 (항목 50·51) — 2026-08-22 신설
# ---------------------------------------------------------------------------
# parser 가 코리안리(KR1000) 7분기분을 적재했다(inbox/parser/20260821T1425Z §4). **적재 직후
# 게이트는 exit 2 였지만 이 두 항목을 보는 룰은 하나도 없었다** — 어제 47/48/49 가 1,285칸을
# 무검사로 통과시킨 그 사고와 같은 형태다. 이번엔 `tests/test_rule_coverage_manifest.py` 가
# 즉시 잡았다(item50[값]·item51[값] 7칸씩 무방비). 이 절이 그 구멍을 메운다.
#
#   50 = 기본자본 (TFI표, 공통적용 경과조치)   ← 헤드라인 item2 와 **다른 값일 수 있다**
#   51 = 보완자본 (TFI표, 공통적용 경과조치)   ← 47/48/49 의 부모행. 헤드라인 item3 과 다를 수 있다
#
# ## 어느 표를 어느 룰에 물리나 (orchestrator 2026-08-22 지시)
#
# **47/48/49 의 부모는 item3(헤드라인)이 아니라 item51(같은 표)이다.** 두 표를 섞으면 안 되는
# 이유가 코리안리 원문에 그대로 있다 — FY2023_Q2 raw 한 필링 안에서 같은 개념이 두 값이다:
#
#   p8 `[경과조치 적용 전 지급여력비율 세부]` (억원)  : 기본자본 32,204 · 보완자본 5,209
#   p9 `(1) 공통적용 경과조치 관련` (백만원)          : 경과조치 적용 전 3,122,114 / 619,243
#                                                      경과조치 적용 후 3,220,438 /  520,920
#
# 즉 헤드라인이 "적용 전" 이라 써 놓고 인쇄한 32,204 는 TFI 표의 **적용 후** 값이다(32,204.38).
# 우리 추출 오류가 아니라 발행사가 두 표에서 스코프를 다르게 쓴 것이고, 마스터는 양쪽 다
# 원문대로 담고 있다. 그래서:
#
#   · `51_tfi_tier2_composition` (신설) — **표 안에서만** 닫는다: item51 == min(47,48) + 49.
#     같은 표 · 같은 컬럼이라 스코프 차이가 개입할 여지가 없다. 실측 7/7 적용전 정확
#     (최대 |잔차| 0.01). 47/48/49 가 값 단위로 검사되는 **비순환 축**이 하나 더 생긴다.
#   · `3_tier2_composition` (기존) — 손대지 않는다. item3(헤드라인) 대 47/48/49 비교는
#     **스코프 대조**이고, 그게 깨지는 코리안리 6분기는 위 원문대조로 발행사 자기모순임이
#     확정됐다(면제 초안 대상). 여기서 item51 로 갈아끼우면 그 6칸의 item3 이 이 축에서
#     통째로 빠지고, 진짜 발견이 조용히 사라진다 — 갈래가 아니라 면제가 된다.
TFI_TIER_ITEMS: tuple[int, ...] = (50, 51)

# ---------------------------------------------------------------------------
# TFI 표 자신의 지급여력금액 / 기발행 자본증권 메모행 (항목 52·53·54) — 2026-08-24 신설
# ---------------------------------------------------------------------------
# parser 가 iter-10 에서 1,291셀을 적재했다(inbox/parser/20260821T1425Z). 적재 직후
# `tests/test_rule_coverage_manifest.py` 가 즉시 "52/53/54 무방비"로 실패했다 — 설계대로다.
#
#   52 = 지급여력금액 (TFI표 맨 윗줄)   ← 축 E 적용후를 **범위검사에서 등식으로 승격**시키는 값
#   53 = (기발행 신종자본증권)          ← 메모행. 대다수 필링이 적용전 컬럼에만 인쇄한다
#   54 = (기발행 후순위채무)            ← 메모행. NH농협 2025.4Q 를 닫는 항(단, 전사 공식 아님)
#
# ## item52 는 축 E 의 comparand 다 (범위검사 → 등식 승격)
#
# 2026-08-22 에 축 E 적용후를 범위검사로 둔 이유가 "TFI 표 자신의 지급여력금액 행이 마스터에
# 없다" 였다. 이제 있으므로 **비교 대상을 item52 로 바꾼다.** 적용전도 같이 바꾼다 —
# 종전 comparand 였던 item1(헤드라인)은 **다른 표**라 스코프 차이가 개입할 수 있는데
# item52 는 같은 표·같은 컬럼이다. 실측(2026-08-24, 428버킷):
#   · 적용전 item52 == item1 이 422/428. 어긋나는 6 = 카카오페이 5(아래) + 롯데 2023.1Q
#     (이미 등재된 발행사 자기모순 — comparand 를 바꿔도 잔차 +18 그대로).
#   · 적용후 YELLOW(범위만 통과) 70칸 중 **69칸이 등식으로 닫힌다.** 나머지 1칸은 item52 결측.
#   · **GREEN 이던 6칸이 RED 로 뒤집힌다** — 그게 이 승격의 값어치다(아래).
#
# ⚠️ 이 승격이 잡아낸 false-green (raw 대조 확정, 2026-08-24):
#   · 카카오페이(KR1098) 2023.1Q~2024.1Q **5버킷 item52 가 100배**다. raw FY2023_Q3 p10
#     `지급여력금액 119,870`(백만원)인데 마스터 item52=119870 — 같은 표의 item50 은
#     1,198.70 으로 정확히 ÷100 됐다. 로더가 47/48/49/51 이 전부 "-" 라 "스케일 무관"
#     (ALL_ZERO_TRIVIAL)으로 판정했는데, **같은 표의 item52 는 0 이 아니었다.**
#     기존 축들은 전부 통과했다(축 E 는 item1 과 비교했으므로).
#   · 삼성화재(KR0008) 2025.3Q item52_적용후 = 286,051.95 인데 50+51 = 286,501.96.
#     raw FY2025_Q3 p16 이 `지급여력금액 28,650,195 / 28,605,195` 로 **그렇게 인쇄한다**
#     (자릿수 전치). 같은 표의 지급여력비율은 275.92/275.92 로 불변이고 각주가
#     "당사는 기발행 신종자본증권 및 후순위채무가 없어 … 전·후 지급여력비율이 동일함" 이라
#     발행사 자기모순이다. 28,605,195/10,383,339 = 275.49% ≠ 인쇄된 275.92%.
TFI_TOTAL_ITEM = 52

# 메모행 두 개. **같은 표 연속 2행**이지만 발행사마다 (값 / "-" / 아예 공란) 셋 다 실재한다 —
# raw 대조로 확인했으므로 "부분 결측 = 무조건 행 유실" 로 단정하지 않는다(아래 레지스트리).
TFI_MEMO_ITEMS: tuple[int, ...] = (53, 54)
_TFI_MEMO_ITEM_LABEL = {53: "(기발행 신종자본증권)", 54: "(기발행 후순위채무)"}

# **발행사가 라벨만 찍고 값을 아예 안 넣은 칸** (raw fitz 직접 판독으로 확인). 대시("-")와
# 다르다 — 대시는 0 으로 적재되고, 이쪽은 인쇄 자체가 없어 결측이 정답이다. "틀린 값을
# 싣느니 빈 칸" 이므로 0 으로 메우지 않고, 대신 여기 등재해 census 가 재플래그하지 않게 한다.
# 등재 = "확인했다" 이고, 미등재 결측은 RED 다.
_TFI_MEMO_ISSUER_BLANK: frozenset[tuple[str, str, int]] = frozenset({
    # 현대해상 2026.1Q raw p19: `(기발행 신종자본증권)` 라벨 뒤에 숫자 없이 바로
    # `(기발행 후순위채무) 376,561` 이 온다.
    ("KR0009", "2026.1Q", 53),
    # 동양생명 2024.4Q raw p73: `기발행신종자본증권 344,567` / `기발행 후순위채무`(값 없음).
    # 이 회사는 2024.1Q 에 후순위채 2,000억을 상환했다(같은 필링 주요변동요인).
    ("KR0087", "2024.4Q", 54),
    # 라이나생명 2024.4Q raw p42: 두 라벨이 연속으로 오고 그 다음이 바로 지급여력기준금액.
    ("KR0074", "2024.4Q", 53), ("KR0074", "2024.4Q", 54),
    # BNP카디프 2023.2Q raw p13(텍스트레이어 2중 인쇄본): 두 라벨 다 값 없음.
    ("KR0075", "2023.2Q", 53), ("KR0075", "2023.2Q", 54),
    # AIA 2023.2Q raw p9 · 2024.2Q raw p16: 두 라벨 다 값 없음(2024.2Q 는 TFI=X 각주도 있다).
    ("KR0080", "2023.2Q", 53), ("KR0080", "2023.2Q", 54),
    ("KR0080", "2024.2Q", 53), ("KR0080", "2024.2Q", 54),
    # 처브라이프 2023.2Q raw p12: 두 라벨 다 값 없음.
    ("KR0100", "2023.2Q", 53), ("KR0100", "2023.2Q", 54),
})

# **로더의 텍스트 스캐너가 이 버킷의 TFI 표를 아예 못 읽었다** (parser iter-10 §4, 20버킷).
# 47/48/49/50/51 은 과거 세션의 vision 판독 백필로 들어와 있어서 "표를 읽었다" 처럼 보이지만
# 메모행은 그 백필의 스코프 밖이었다. 결측 사유가 발행사가 아니라 **우리 쪽 backlog** 이므로
# 발행사 공란과 같은 색으로 찍으면 안 된다 — 별도 사유로 세서 매 실행 눈앞에 남긴다.
_TFI_MEMO_TABLE_NOT_SCANNED: frozenset[tuple[str, str]] = frozenset({
    ("KR0010", "2024.1Q"), ("KR0010", "2024.3Q"), ("KR0010", "2025.1Q"),
    ("KR0010", "2025.3Q"), ("KR0010", "2025.4Q"), ("KR0010", "2026.1Q"),
    ("KR0080", "2024.4Q"), ("KR0080", "2025.1Q"), ("KR0080", "2025.2Q"),
    ("KR0080", "2025.3Q"), ("KR0080", "2025.4Q"), ("KR0080", "2026.1Q"),
    ("KR1098", "2024.2Q"), ("KR1098", "2024.3Q"), ("KR1098", "2024.4Q"),
    ("KR0005", "2024.4Q"), ("KR0071", "2024.4Q"), ("KR0079", "2023.3Q"),
    ("KR0087", "2026.1Q"), ("KR0097", "2024.2Q"),
})

# 보완자본 인정한도 = 지급여력기준금액 × 50% (K-ICS 자본 tiering). 원문 대조로 백만원 단위까지
# 확인: 푸본현대 2026.1Q 1,392,520×0.5=696,260 · IBK연금 2026.1Q 719,585×0.5=359,792.
TIER2_LIMIT_RATIO = 0.5

# "사실상 0" 판정 임계 (억원 단위 저장). 47/48/49 는 소수 둘째자리까지 저장되므로 0.5 미만은
# 인쇄값 0 또는 대시("-", "ㅡ")로 본다.
TIER2_ZERO_EPS = 0.5

# 자릿수 sanity 상한 — 값 > item14 × 이 배수면 단위스케일 오류로 본다.
# 근거: 원문 대조된 실측 item47/item14 비율의 최대가 1.04(KB손해 2025.1Q 66,274.84/63,515.4)로
# **1 을 넘을 수 있다** — 상한을 1 이나 2 로 잡으면 정상 필링을 오탐한다. 10 이면 실측 최대의
# 약 10배 여유를 두면서, 이 표의 문서화된 실패양식인 100배(비율 ~13 이상)·100만배는 반드시
# 걸린다. 실패양식 이력: 2026-07-07 백만원 표를 억원 스키마에 그대로 넣은 100배 사고 3사,
# 2026-08-21 교보생명 홀수분기 5건 100배 · DB생명 2026.1Q item48 100만배.
TIER2_SCALE_CEILING = 10.0

# 적용후 항등식은 **아직 확립되지 않았다** — 그래서 적용후 축의 불일치는 RED 가 아니라 YELLOW 다.
#
# 이건 "적용후를 안 본다"가 아니다. 적용후도 똑같이 계산해서 리포트에 싣고, 결측·부호·자릿수는
# 적용후에서도 RED 로 막는다(그건 스코프와 무관하므로). 다만 **값 항등식을 위반이라고 단정하지
# 않는다** — 그 항등식이 적용후 컬럼에서 성립한다는 근거가 없고, 오히려 반증이 있기 때문이다:
#
#   한화손해(KR0002) 2023.2Q raw p11(단어 좌표 판독):
#     보완자본 한도 적용 전   1,022,151 / 11,442      ← 적용후가 적용전의 1/89 (진짜 그렇게 인쇄됨)
#     보완자본 한도           1,674,297 / 1,674,297
#     보완자본               3,073,003 / 2,649,511
#   적용전: min(10,221.51, 16,742.97) + 20,508.52 = 30,730.03 = 공시 보완자본 ✅ 정확
#   적용후: min(   114.42, 16,742.97) + 20,508.52 = 20,622.94 ≠ 공시 26,495.11 ❌ (잔차 5,872.17)
#
# 즉 **추출은 옳은데 식이 적용후에서 안 닫힌다.** TFI(공통적용 경과조치)가 기본자본↔보완자본
# 사이를 재분류하면서 '한도 적용 전' 의 의미가 바뀌는 것으로 보이나, 정확한 적용후 관계식은
# 원문 근거로 확정하지 못했다. 확정 못 한 것을 RED 로 단정하면 220칸이 전부 오탐이 된다
# (같은 실수를 이 축에서 한 번 더 할 뻔했다 — item14_적용후를 분모로 쓰면 241칸 오탐이었다).
#
# **확립되면 YELLOW → RED 로 승격하라.** 그 전까지는 review 로 남되 조용하지는 않다.
_POST_UNESTABLISHED = (
    " ※ POST_IDENTITY_UNESTABLISHED: 적용후 관계식 미확립 → review(YELLOW), blocking 아님. "
    "반증 실측: 한화손해 2023.2Q 는 적용전에서 정확히 닫히는데 적용후에서만 잔차 5,872.17 이고 "
    "raw 대조 결과 추출은 정확하다. 확립되면 RED 로 승격할 것."
)

# 갈래 → status 매핑. **축 B(item3)와 축 F(item51)가 이 상수를 공유한다.**
# 갈래 정의(`_tier2_branch`)만 공유하고 매핑을 각자 두면, 같은 갈래가 한 축에서는 통과이고
# 다른 축에서는 RED 인 상태가 조용히 생긴다. 정의와 판정을 한 군데 묶어 그걸 막는다.
_COMPOSITION_RED_BRANCHES = frozenset({"NEITHER", "TFI_NA_RED"})
_COMPOSITION_SKIP_BRANCHES = frozenset({"INPUT_MISSING", "TFI_NA_NO_INPUT"})

# 19_market 부모-자식 완전성 면제: item19 공시인데 36-40 분해가 진짜 미공시인 (회사,분기).
# raw MD/PDF에 분해표가 실제로 없음을 교차검증한 케이스만 등록(문서화 면제). 기본 비어있음
# = "부모 공시면 분해도 있어야 한다"가 기본, 빠지면 RED(parser gap 추정).
MARKET_BREAKDOWN_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# 36_irr 시나리오 완전성 면제: item36 공시인데 41-46(금리위험 순자산가치 6시나리오)이 진짜 미공시인
# (회사,분기). 41-46은 **짝수분기(2Q/4Q) 서식에만** 존재 — 홀수분기(1Q/3Q)는 시나리오표가 서식에
# 원천부재라 SKIP이 정당(RED 아님). 짝수분기인데 item36 공시·41-46 결측이면 parser gap → RED.
# raw에 짝수분기에도 시나리오표 없음을 교차검증한 케이스만 등록(문서화 면제). 기본 비어있음.
IRR_SCENARIO_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# 36_irr 내부모형 면제. **2026-08-21 전건 해제 — 등재사유가 raw 대조에서 거짓으로 확인됐다.**
#
# 종전 사유: "내부모형사 — 회사가 시나리오별 금리위험액을 **직접 공시**하고 그 값을 같은 식에 넣으면
# 공시총액과 정확 일치(KR0094 2025.4Q=578,999 검증)". validation 이 2026-08-21 에 다섯 건의 raw 를
# 전부 열어(fitz 텍스트 + 240dpi 렌더링 육안) 확인한 결과 **두 전제가 모두 사실이 아니었다**:
#
#   ① 다섯 건 모두 표준서식 [② 금리위험액 현황] 표를 그대로 싣는다 — 충격 전 + 충격후 5시나리오
#      (평균회귀·금리상승·금리하락·금리평탄·금리경사) 열에 `Ⅲ. 순자산가치` 행이 완비돼 있다.
#      즉 항목 41-46 의 원천은 실재하고, 마스터에 없는 것은 **추출갭**이지 원천부재가 아니다.
#        KR0073 2025.2Q  FY2025_Q2 raw p21   (Ⅳ.금리위험액 459,988 = 마스터 item36 4,599.88)
#        KR0094 2024.2Q  FY2024_Q2 raw p22   (750,104 = 7,501.04)
#        KR0094 2024.4Q  FY2024_Q4 raw p144  (633,214 = 6,332.14)
#        KR0094 2025.2Q  FY2025_Q2 raw p28   (931,833 = 9,318.33)
#        KR0094 2025.4Q  FY2025_Q4 raw p131  (578,999 = 5,789.99)
#   ② `Ⅳ. 금리 위험액` 은 표 전체 폭을 덮는 **단일 병합셀**이다 — 시나리오별로 쪼개져 있지 않다.
#      "회사가 시나리오별 금리위험액을 직접 공시" 는 어느 페이지에서도 성립하지 않는다.
#   ③ 결정적으로 KR0094 는 스스로 **표준모형사**라고 적는다: FY2025_Q4 raw p135 "회사는
#      보험업감독업무시행세칙 [별표22] … 기준에 따라 시장위험액을 측정하고 있습니다" + 표준식
#      "금리위험액 = √max(금리상승, 금리하락)² + √max(금리평탄, 금리경사)² + 평균회귀금액".
#      '내부모형사' 라는 면제 이름 자체가 원문과 어긋난다.
#
# 해제하면 다섯 건 전부 36_irr RED("even quarter 인데 41-46 결측 = parser gap")가 된다. 그게 참이다 —
# 표는 원천에 있고 우리가 안 읽었을 뿐이다. **표준식이 공시총액을 재현하지 못하는 것은 별개의 미해결
# 질문**이고(추출 후 교보 25.2Q +5.5% · 신한 +8~34%), 그 건으로 새 면제를 만들려면 owner 승인이
# 필요하다. 검증 stage 는 반증된 면제를 지울 수 있을 뿐 새 면제를 만들지 않는다.
INTERNAL_MODEL_36IRR_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# ---------------------------------------------------------------------------
# 36_irr documented exception — **통째 skip 이 아니라 '잔차 박제'다** (owner 2026-08-21 승인)
# ---------------------------------------------------------------------------
# 대상은 아래 5개 (회사,분기)뿐이다. 이 다섯은 41-46 이 원문 그대로 적재돼 있는데도 표준 도출식이
# 공시 금리위험액(item36)을 재현하지 못한다. **데이터가 아니라 재현식이 이 회사들에 안 맞는다**:
#
#   ① item36 자체는 정상값이다 — 같은 item36 을 시장위험 축에 넣으면 닫힌다.
#      실측 `item19 == sqrt(item36~40 · MARKET_M)` 잔차: 교보 25.2Q −0.0042(−0.0000%) ·
#      신한 24.2Q −0.3312 · 24.4Q −0.2521 · 25.2Q −0.3338 · 25.4Q +0.4791 (전부 |rel| ≤ 0.0022%).
#      즉 공시 금리위험액은 **다른 축에서 검산되는 값**이고, 안 맞는 것은 41-46 부속표 재현뿐이다.
#   ② 41-46 은 원문 그대로다. raw 대조(fitz, 아래 provenance 원장의 present_markers 와 동일):
#      교보 25.2Q p21 Ⅲ.순자산가치 -5,667,711/-5,414,904/-6,352,338/-5,586,899/-5,463,138/-5,742,051,
#      Ⅳ.금리위험액 459,988 → 마스터 item41~46·item36 과 백만원↔억원 환산까지 정확 일치.
#      신한 24.2Q p22(750,104) · 24.4Q p144(633,214) · 25.2Q p28(931,833) · 25.4Q p131(578,999) 동일.
#   ③ **현행 식이 옳다 — 전사로 검증했다.** owner 가 "평균회귀 충격량도 0 으로 절단해야 하지
#      않냐"고 지적해 41-46 완비 226버킷 전수 재측정(validation 2026-08-21):
#         A 현행 signed 평균회귀 : 221/226 (97.8%)
#         B 평균회귀도 0 절단     : 123/226 (54.4%)
#      판정이 갈리는 102건 중 **100건이 A만 통과**(B-only 2건은 이 면제 대상인 신한 25.2Q·25.4Q).
#      A 는 소수점까지 맞는다(메리츠 23.4Q 공시 5,060.65 vs A 5,060.66 · 삼성화재 등).
#      **평균회귀 이익을 상계하는 것이 실제 서식이다 → 식은 건드리지 않는다.**
#   ④ 교보는 하한 자체를 못 지킨다. 25.2Q 금리상승 단일 충격량 684,627 백만원(= -5,667,711 −
#      (-6,352,338))이 공시 금리위험액 459,988 보다 크다. 어떤 합성식을 써도 최악 단일 시나리오보다
#      작아질 수 없다 → 표의 순자산가치와 공시 위험액이 같은 기준이 아니다.
#   ⑤ **원인 미규명(UNEXPLAINED).** 신한 24.4Q raw p144 주2 "2024년부터 금리위험액 현황의 자산 및
#      부채는 금리위험에 직·간접적으로 노출된 자산 및 부채를 대상으로 작성" 은 작성기준 변경을
#      명시하지만 **잔차를 설명하지 못한다** — 금리에 둔감한 항목은 모든 시나리오 열에 동일하게
#      들어가 열 간 차이(=충격량)에서 상쇄된다. 게다가 그 주2 는 25.2Q(p28)·25.4Q(p131)에는
#      아예 없는데 잔차는 그대로다(+7.5% · +14.9%). "스코프 때문"이라고 단정하지 말 것.
#
# 설계 원칙 — **통째 skip 금지**(_LIFE8_ISSUER_INCONSISTENT 와 동형). 기대잔차를 값으로 박제하고
# 매 실행 마스터에서 재계산한다. item36 이나 41-46 중 한 칸이라도 바뀌어 잔차가 박제값에서
# 벗어나면 면제가 깨지고 **다시 RED** 다. blanket skip 은 이 셀을 영구 사각지대로 만든다.
#
# **적용전·적용후 두 컬럼을 각각 박제한다.** 같은 미정합이 게이트에 RED 를 두 번 만든다:
# 룰엔진 `36_irr`(적용전) + 게이트 `_transition_irr_after` 축(적용후 = TRANSITION_AFTER_IRR_MISMATCH).
# 적용전만 면제하면 적용후가 그대로 막는다 — KR0079 8_life 때 실제로 그랬다.
# (이 다섯 건은 41-46 후 == 41-46 전 미러라 두 컬럼의 잔차가 같지만, 값이 아니라 **컬럼별로**
#  재계산·대조한다 — 미러가 깨지면 그것도 검출돼야 한다.)
#
# 잔차 부호 = item36(공시) − derive(41-46). 전부 양수(공시 > 도출).
IRR_DERIVE_ISSUER_INCONSISTENT: dict[tuple[str, str], dict[str, float]] = {
    ("KR0073", "2025.2Q"): {"적용전": 241.4373504145833, "적용후": 241.4373504145833},
    ("KR0094", "2024.2Q"): {"적용전": 1287.8295634268043, "적용후": 1287.8295634268043},
    ("KR0094", "2024.4Q"): {"적용전": 1622.0506399332953, "적용후": 1622.0506399332953},
    ("KR0094", "2025.2Q"): {"적용전": 698.1839921629144, "적용후": 698.1839921629144},
    ("KR0094", "2025.4Q"): {"적용전": 863.8221082879018, "적용후": 863.8221082879018},
}
# 박제 허용오차. 마스터 셀은 소수 2자리라 재계산이 결정론적이다 — 느슨하게 잡는 순간
# '박제'가 아니라 또 하나의 blanket skip 이 된다. (룰 허용오차는 손대지 않는다: 잔차가 5~26% 다.)
IRR_PIN_TOL = 0.01

# 36_irr 도출식 입력 항목. 41=충격 전 순자산 · 42=평균회귀 · 43=금리상승 · 44=금리하락 ·
# 45=금리평탄 · 46=금리경사. 게이트의 적용후 축이 **여기서 import** 한다(재타이핑 금지).
IRR_SCENARIO_ITEMS: tuple[int, ...] = (41, 42, 43, 44, 45, 46)


def irr_derive_expected(values: Mapping[int, Optional[float]]) -> Optional[float]:
    """금리위험액 = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀(signed).
    R = item41 − 시나리오 순자산가치. 입력 41-46 중 한 칸이라도 결측이면 None.

    적용전(룰엔진)·적용후(게이트) 두 축이 **이 함수 하나**를 쓴다 — 재구현하면 검증기가
    검증대상과 다른 식을 쓰게 된다."""
    if any(values.get(i) is None for i in IRR_SCENARIO_ITEMS):
        return None
    base = float(values[41])
    r_up = max(base - float(values[43]), 0.0)
    r_dn = max(base - float(values[44]), 0.0)
    r_flat = max(base - float(values[45]), 0.0)
    r_steep = max(base - float(values[46]), 0.0)
    r_mr = base - float(values[42])          # 평균회귀: signed (0 절단 금지 — 위 ③ 참조)
    return float(np.sqrt(max(r_up, r_dn) ** 2 + max(r_flat, r_steep) ** 2)) + r_mr


def irr_pin_verdict(
    code: str, quarter: str, column: str, values: Mapping[int, Optional[float]]
) -> tuple[str, Optional[float], Optional[float]]:
    """등재된 잔차 박제를 **매 실행 마스터에 대고 재검산**한다.

    반환 (verdict, pinned, actual):
      NOT_PINNED     이 (회사,분기,컬럼)은 면제 등재분이 아니다 → 평소 룰대로.
      MATCH          잔차가 박제값과 일치 → 이 셀에 한해 차단하지 않는다(SKIP).
      DRIFT          잔차가 박제값에서 이탈 → owner 판단의 전제가 바뀌었다 → RED.
      INPUT_MISSING  item36 또는 41-46 결측 → 박제 확인 불가 → **SKIP 이 아니라 RED**."""
    pins = IRR_DERIVE_ISSUER_INCONSISTENT.get((code, quarter))
    if not pins or column not in pins:
        return ("NOT_PINNED", None, None)
    pinned = pins[column]
    parent = values.get(36)
    expected = irr_derive_expected(values)
    if parent is None or expected is None:
        return ("INPUT_MISSING", pinned, None)
    actual = float(parent) - expected
    if abs(actual - pinned) > IRR_PIN_TOL:
        return ("DRIFT", pinned, actual)
    return ("MATCH", pinned, actual)


def parse_numeric(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    text = str(raw).strip()
    if not text or text in {"-", "—", "N/A", "n/a"}:
        return None
    text = text.replace(",", "")
    for ch in ("\u25b3", "\u25b2", "\u25bd", "\u25bc", "\u2212"):
        text = text.replace(ch, "-")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return float(text)
    except ValueError:
        return None


def classify_diff(diff: float, tolerance: float = 2.0) -> str:
    ad = abs(diff)
    if ad > tolerance:
        return STATUS_RED
    if ad >= 0.5:
        return STATUS_YELLOW
    return STATUS_GREEN


@dataclass(frozen=True)
class QuarterBucket:
    code: str
    name: str
    quarter: str
    values: dict[int, float]
    values_post: dict[int, float]

    @classmethod
    def from_records(cls, rows: Iterable[Mapping[str, Any]]) -> "QuarterBucket":
        rows = list(rows)
        if not rows:
            raise ValueError("empty bucket rows")
        code = str(rows[0].get(KEY_CODE, "")).strip()
        name = str(rows[0].get(KEY_NAME, "")).strip()
        quarter = str(rows[0].get(KEY_QUARTER, "")).strip()
        values: dict[int, float] = {}
        values_post: dict[int, float] = {}
        for row in rows:
            item_raw = row.get(KEY_ITEM)
            try:
                item_no = int(item_raw)
            except (TypeError, ValueError):
                continue
            val = parse_numeric(row.get(KEY_VALUE))
            if val is not None:
                values[item_no] = val
            if KEY_VALUE_POST in row:
                post = parse_numeric(row.get(KEY_VALUE_POST))
                if post is not None:
                    values_post[item_no] = post
        return cls(code=code, name=name, quarter=quarter, values=values, values_post=values_post)

    def get(self, item_no: int, *, post: bool = False) -> Optional[float]:
        if post and item_no in self.values_post:
            return self.values_post[item_no]
        return self.values.get(item_no)


def _group_records(records: Iterable[Mapping[str, Any]]) -> list[QuarterBucket]:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for rec in records:
        code = str(rec.get(KEY_CODE, "")).strip()
        quarter = str(rec.get(KEY_QUARTER, "")).strip()
        if not code or not quarter:
            continue
        groups.setdefault((code, quarter), []).append(rec)
    return [QuarterBucket.from_records(rows) for rows in groups.values()]


def _finding(
    bucket: QuarterBucket,
    rule_id: str,
    *,
    status: str,
    expected: Optional[float],
    actual: Optional[float],
    diff: Optional[float],
    detail: str = "",
) -> dict[str, Any]:
    return {
        "rule": rule_id,
        KEY_CODE: bucket.code,
        KEY_NAME: bucket.name,
        KEY_QUARTER: bucket.quarter,
        "status": status,
        "expected": expected,
        "actual": actual,
        "diff": diff,
        "detail": detail,
    }


def _check_numeric(
    bucket: QuarterBucket,
    rule_id: str,
    expected: float,
    actual: Optional[float],
    tolerance: float,
) -> dict[str, Any]:
    if actual is None:
        return _finding(
            bucket,
            rule_id,
            status=STATUS_RED,
            expected=expected,
            actual=None,
            diff=None,
            detail="missing actual item value",
        )
    diff = actual - expected
    return _finding(
        bucket,
        rule_id,
        status=classify_diff(diff, tolerance),
        expected=expected,
        actual=actual,
        diff=diff,
    )


def _sum_optional(bucket: QuarterBucket, item_nos: Iterable[int]) -> float:
    total = 0.0
    for n in item_nos:
        v = bucket.get(n)
        if v is not None:
            total += v
    return total


def _diversified_sqrt(vector: np.ndarray, matrix: np.ndarray) -> float:
    v = np.asarray(vector, dtype=float)
    m = np.asarray(matrix, dtype=float)
    inner = float(v @ m @ v)
    if inner < 0:
        inner = 0.0
    return float(np.sqrt(inner))


def _validate_market_irr(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    source_has_breakdown: Optional[frozenset],
    eff_tol: float,
) -> None:
    """Market-risk decomposition (19_market) and interest-rate-risk IRR (36_irr).
    Both are cadence-aware: a disclosed parent with the breakdown missing is RED on
    even quarters (full form) but a legit SKIP on odd quarters (간이공시), with
    per-(company,quarter) documented exemptions. Split out of _validate_bucket
    2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 19_market: 시장위험액(item19) = sqrt(V'·M·V), V=[36,37,38,39,40].
    # 8_life와 동형이나 부분결측 허용(부동산/자산집중 미보유 정상): 없는 하위=0.
    # 핵심(2026-06-12): 부모 item19 공시인데 36-40이 *전부* 결측이면 SKIP이 아니라 RED.
    #   부모를 공시한 회사가 표준모형 시장위험 분해(36-40)를 안 낼 수 없다 → parser gap
    #   (하나손해 2025.4Q: 표가 <!-- image -->로 분절 / 삼성생명: "1.금리위험액"+충격시나리오방식 라벨변형).
    #   진짜 미공시 legit 케이스만 MARKET_BREAKDOWN_EXEMPT에 (회사,분기) 문서화 면제.
    mkt_items = list(range(36, 41))
    mkt_present = [bucket.get(i) for i in mkt_items if bucket.get(i) is not None]
    cq = (bucket.code, bucket.quarter)
    if bucket.get(19) is not None and mkt_present:
        v = np.array([bucket.get(i) or 0.0 for i in mkt_items], dtype=float)
        expected = _diversified_sqrt(v, MARKET_M)
        mkt_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "19_market", expected, bucket.get(19), mkt_tol))
    elif bucket.get(19) is None or cq in MARKET_BREAKDOWN_EXEMPT:
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_SKIP, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 absent (nothing to check) or documented breakdown-exempt",
            )
        )
    elif (
        source_has_breakdown is not None
        and cq not in source_has_breakdown
        and not bucket.quarter.endswith(("2Q", "4Q"))
    ):
        # cadence-SKIP은 **홀수분기(1Q/3Q)만** — 간이공시라 세부표 원천부재(MD 키워드<3로 확인).
        # 짝수분기(2Q/4Q)는 반기/연간 full form이라 표가 반드시 있어야 함 → 결측은 아래 else에서 RED
        # (텍스트 스캔만으론 이미지/스캔표를 못 보므로, 짝수는 source 부재여도 숨기지 않음. 2026-06-13).
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_SKIP, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 present but breakdown 36-40 absent from odd-quarter source (abbreviated 1Q/3Q form / cadence) — legit absent",
            )
        )
    else:
        # 짝수분기 full form 결측, 또는 홀수분기인데 원천에 표 있음(MD 키워드>=3), 또는 source 확인불가 -> 파서갭. RED.
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_RED, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 present + breakdown 36-40 expected (even-qtr full form, or source has table) but missing in JSON — parser gap (image-split/label-variant/MD-truncation/OCR)",
            )
        )

    # Rule 36_irr: 금리위험액(item36) = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀.
    # R = base(item41) − 시나리오 순자산가치; 평균회귀는 signed(no max).
    # 핵심(2026-06-13, 19_market과 동형 SKIP맹점 폐쇄): 41-46(시나리오 순자산가치 6종)은
    #   **짝수분기(2Q/4Q) 서식에만** 존재. 홀수분기(1Q/3Q)는 서식 원천부재라 SKIP 정당.
    #   짝수분기인데 item36 공시·41-46 결측/불완전이면 SKIP 아니라 RED(parser gap). 진짜 부재만
    #   IRR_SCENARIO_EXEMPT 문서화 면제. 검증 empirics: 41-46은 전 분기 짝수에만 적재됨.
    irr_items = [36, 41, 42, 43, 44, 45, 46]
    is_even_q = bucket.quarter.endswith(("2Q", "4Q"))
    irr_vals = {i: bucket.get(i) for i in irr_items}
    # documented exception (owner 2026-08-21) — **잔차 박제**. 통째 skip 이 아니라
    # "이 잔차인 동안만 차단하지 않는다". 드리프트·결측은 둘 다 RED. 상세는
    # IRR_DERIVE_ISSUER_INCONSISTENT 주석 참조.
    pin_verdict, pinned_resid, actual_resid = irr_pin_verdict(
        bucket.code, bucket.quarter, "적용전", irr_vals)
    if (bucket.code, bucket.quarter) in INTERNAL_MODEL_36IRR_EXEMPT:
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP, expected=None,
                actual=bucket.get(36), diff=None,
                detail="internal-model insurer: 표준 derive식 불適用 (회사 시나리오별 금리위험액 직접공시) — owner-approved exempt (2026-06-14)",
            )
        )
    elif pin_verdict == "MATCH":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP,
                expected=irr_derive_expected(irr_vals), actual=bucket.get(36),
                diff=actual_resid,
                detail=f"documented exception (owner 2026-08-21, 잔차 박제): 적용전 잔차 "
                       f"{actual_resid:.4f} == 박제 {pinned_resid:.4f} (tol {IRR_PIN_TOL}). "
                       "item36 은 19_market 축에서 닫히고 41-46 은 원문 그대로 — 재현식이 이 "
                       "회사에 안 맞는 것이며 원인 미규명(UNEXPLAINED). 잔차가 움직이면 RED 로 복귀",
            )
        )
    elif pin_verdict == "DRIFT":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED,
                expected=irr_derive_expected(irr_vals), actual=bucket.get(36),
                diff=actual_resid,
                detail=f"IRR_EXEMPTION_RESIDUAL_DRIFT — 박제 {pinned_resid:.4f} → 실측 "
                       f"{actual_resid:.4f} (Δ{actual_resid - pinned_resid:+.4f}, tol {IRR_PIN_TOL}). "
                       "owner 판단의 전제(item36·41-46 모두 원문 그대로)가 바뀌었다 — 면제 무효",
            )
        )
    elif pin_verdict == "INPUT_MISSING":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED, expected=None,
                actual=bucket.get(36), diff=None,
                detail=f"IRR_EXEMPTION_INPUT_MISSING — 면제 등재분인데 item36/41-46 [적용전]이 "
                       f"결측이라 박제잔차 {pinned_resid:.4f} 를 확인할 수 없다. 결측은 SKIP 이 아니라 RED",
            )
        )
    elif all(bucket.get(i) is not None for i in irr_items):
        expected = irr_derive_expected(irr_vals)
        irr_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "36_irr", expected, bucket.get(36), irr_tol))
    elif (bucket.get(36) is not None and is_even_q
          and (bucket.code, bucket.quarter) not in IRR_SCENARIO_EXEMPT):
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED, expected=None,
                actual=bucket.get(36), diff=None,
                detail="item36(금리위험액) present in even quarter but scenario table 41-46 missing/incomplete — parser gap, not legit (scenario table is in 2Q/4Q form)",
            )
        )
    else:
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP, expected=None,
                actual=bucket.get(36), diff=None,
                detail="item36 absent, or odd quarter (scenario table not in 1Q/3Q form), or documented scenario-exempt",
            )
        )


def _validate_transition_capital(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    eff_tol: float,
) -> None:
    """경과조치 monotonicity: 기본자본 적용후>=적용전 (rule 9, grandfathered 신종자본
    증권) and 지급여력기준금액 적용전>=적용후 (rule 10, risk-charge phase-in). Split out
    of _validate_bucket 2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 9: 기본자본 (item2) 적용후 >= 적용전.
    # Transitional grandfather: pre-2022 신종자본증권 fully recognized in basic capital
    # under 적용 후, but limit-deducted under 적용 전. So post should be >= pre (within tol).
    item2_pre = bucket.get(2)
    item2_post = bucket.get(2, post=True)
    if item2_pre is not None and item2_post is not None and item2_post != item2_pre:
        diff = item2_post - item2_pre  # should be >= -tol
        # 대형사 grandfather 미세감소 허용: 절대 2.0은 수조원대 기본자본에 과도하게 엄격.
        # 경과조치 2차효과(보완자본 한도 재계산 등)로 극소량 감소는 정상(한화손해 2024.2Q raw
        # 확인: 기본자본 2,638,159→2,637,797 백만 = −0.015%). rule 8_life 동적허용오차와 동일 발상.
        gf_tol = max(eff_tol, 0.0005 * abs(item2_pre))
        if diff >= -gf_tol:
            status = STATUS_GREEN
        else:
            status = STATUS_RED
        findings.append(_finding(
            bucket, "9",
            status=status,
            expected=item2_pre, actual=item2_post, diff=diff,
            detail="item2(기본자본) 적용후 >= 적용전 expected (transitional grandfather, dynamic tol)",
        ))
    else:
        findings.append(_finding(
            bucket, "9",
            status=STATUS_SKIP, expected=None, actual=item2_post, diff=None,
            detail="no post-transition item2 (or equal to pre)",
        ))

    # Rule 10: 지급여력기준금액 (item14) 적용전 >= 적용후.
    # Transitional risk-ramp: some risk charges phase in gradually, so SCR_post
    # (currently effective) typically <= SCR_pre (strict end-state). Pre >= post (within tol).
    item14_pre = bucket.get(14)
    item14_post = bucket.get(14, post=True)
    if item14_pre is not None and item14_post is not None and item14_post != item14_pre:
        diff = item14_pre - item14_post  # should be >= -tol
        if diff >= -eff_tol:
            status = STATUS_GREEN
        else:
            status = STATUS_RED
        findings.append(_finding(
            bucket, "10",
            status=status,
            expected=item14_post, actual=item14_pre, diff=diff,
            detail="item14(SCR) 적용전 >= 적용후 expected (transitional risk ramp)",
        ))
    else:
        findings.append(_finding(
            bucket, "10",
            status=STATUS_SKIP, expected=None, actual=item14_pre, diff=None,
            detail="no post-transition item14 (or equal to pre)",
        ))


def _validate_transition_basic(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    eff_tol: float,
) -> None:
    """경과조치 적용후 기본자본비율 (8_post, item2후/item14후) and 생명장기 R7 sub-risk
    diversification (8_life, item17 = sqrt(S·R7·S)). Both use a dynamic tolerance for
    sub-scale denominators / accumulated sqrt rounding. Split out of _validate_bucket
    2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 8_post: post-transition basic capital ratio.
    # expected = item2_post / item14_post * 100  (use POST values for both
    # numerator and denominator). bucket.get(..., post=True) falls back to
    # pre value when post is missing, which is correct: if pre==post then
    # ratio is unchanged. SKIP only when neither item2 nor item14 has any
    # post-transition data AND item28 has no post value either (no
    # transitional reported at all).
    post2 = bucket.get(2, post=True)
    post14 = bucket.get(14, post=True)
    has_any_post = (
        2 in bucket.values_post
        or 14 in bucket.values_post
        or 28 in bucket.values_post
    )
    # 분자(item2)와 분모(item14)가 반드시 같은 기준(둘 다 genuine post, 또는 둘 다
    # pre 폴백)이어야 한다. 한쪽만 post이면(예: item14후는 채워졌는데 item2후는 결측 →
    # pre로 폴백) expected = pre2/post14 라는 무의미값이 나와 spurious RED가 뜬다
    # (흥국생명 2024.4Q·에이비엘 2025.3Q·푸본 2023.1Q, 2026-07-07 validation 적발).
    # 기준이 어긋나면 SKIP — 진짜 결측은 transition-after-capture MISSING 체크가 별도로 잡음.
    same_basis = (2 in bucket.values_post) == (14 in bucket.values_post)
    if has_any_post and same_basis and post2 is not None and post14 is not None and post14 != 0:
        expected = post2 / post14 * 100.0
        actual = bucket.get(28, post=True)
        if actual is None:
            actual = bucket.get(28)
        # rule 8(적용전)과 동일한 dynamic tol: micro사(작은 item14후)는 억원-coarse 반올림으로
        # 산출비율이 공시비율과 어긋남(카카오 2023.4Q item14후=20 → 974/20=4870 vs 공시4777).
        # 8_post만 eff_tol 쓰던 불일치 교정(2026-07-12).
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / abs(post14) + 50.0 / abs(post14))
        findings.append(_check_numeric(bucket, "8_post", expected, actual, ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8_post",
                status=STATUS_SKIP,
                expected=None,
                actual=bucket.get(28, post=True),
                diff=None,
                detail="no post data or mixed pre/post basis for item2/14 (skip; MISSING caught by transition check)",
            )
        )

    sub_items = list(range(29, 36))
    if bucket.get(17) is not None and all(bucket.get(i) is not None for i in sub_items):
        s = np.array([bucket.get(i) for i in sub_items], dtype=float)
        expected = _diversified_sqrt(s, R7)
        # 8_life only: dynamic tolerance = max(eff_tol, 5% of expected).
        # Rationale: R7 diversified sqrt accumulates rounding from 7 sub-items,
        # so absolute 2.0 tol is too tight when expected is large (hundreds-thousands).
        life_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "8_life", expected, bucket.get(17), life_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8_life",
                status=STATUS_SKIP,
                expected=None,
                actual=bucket.get(17),
                diff=None,
                detail="missing item17 or any of items 29-35",
            )
        )


def _tier2_branch(
    bucket: QuarterBucket, post: bool, tol: float, target_item: int = 3
) -> tuple[str, Optional[float]]:
    """보완자본 관행 분류 → (branch, 한도초과액).

    `보완자본(target) = min(한도적용전, 한도) + 초과분` 이 **보편적이지 않다.** parser 가 원문
    대조로 반례를 보고했고(한화생명·BNP카디프·KB손해), 실측으로도 확인된다 — 이 회사들은
    `보완자본 = 한도적용전` 으로 한도에 잘리지 않는다. 그래서 관행을 분류한다:

      CAPPED     : target == min(item47, item48) + item49 → 한도초과액이 불인정항목에서 빠짐
      UNCAPPED   : target == item47                       → 한도로 안 자름, 초과액 개념 없음
      BOTH       : 둘 다 성립(초과액도 item49 도 0 인 경우) → 구분 불필요
      TFI_NA_OK  : TFI 표 자체가 미기재(아래) + 대체 항등식 `target == item13` 성립
      TFI_NA_RED : TFI 표 자체가 미기재인데 대체 항등식도 깨짐 → RED
      NEITHER    : 어느 쪽으로도 target 이 재현되지 않음     → RED

    ## `target_item` — 갈래 정의는 **하나뿐이다** (2026-08-22)

    47/48/49 를 부모로 갖는 "보완자본" 셀은 마스터에 둘 있다. `item3`(헤드라인 세부표)과
    `item51`(TFI 표 자신). 축 B 는 앞을, 축 F 는 뒤를 검산한다. **두 축이 각자 갈래를
    구현하면 같은 이름의 갈래가 서로 다른 뜻을 갖게 된다** — 이 저장소가 반복해서 당한
    실패양식이라, 갈래 판정은 이 함수 하나만 갖고 대상 셀만 인자로 받는다.

    이 인자가 없던 하루 동안 축 F 는 `min(47,48)+49` 만 무조건 검사했고, **적용전 67칸이
    RED** 였다. 전수 분해하니 UNCAPPED 50 · TFI_NA 12 · 발행사 불일치 5 로, 앞의 62칸은
    축 B 가 **이미 갖고 있던 갈래**를 안 가져와서 생긴 오탐이었다(축 F 설계 당시 데이터가
    코리안리 7버킷뿐이었고 그게 우연히 전부 CAPPED 계열이라 안 보였다).

    ## TFI_NA — "표가 없다"가 아니라 "표가 이 회사에 적용되지 않는다" (2026-08-22 신설)

    `47 == 48 == 49 == 0` 인데 `item14 > 0` 이면 **item48 이 SCR×50% 가 아니다.** 한도는
    공식으로 정해지는 값이라 SCR 이 양수인 한 0 일 수 없다 — 즉 그 행의 0 은 금액이 아니라
    "이 경과조치는 우리에게 해당사항 없음" 표시다. parser 가 원문으로 확인했다(메트라이프
    2023.1Q raw p11: `보완자본 한도 0 0` 바로 아래 `(기발행 신종자본증권) 0` ·
    `(기발행 후순위채무) 0`). 이 상태에서 `min(47,48)+49 = 0` 은 item3 을 재현할 수 없고,
    **재현 못 하는 게 정상**이다.

    **그러나 무검사로 넘기지 않는다.** 채무성 자본이 하나도 없으면 보완자본은 전액
    "Ⅲ. 보완자본으로 재분류하는 항목(item13)" 에서 온다 → 대체 항등식 `item3 == item13`
    을 대신 건다. 전수 실측(2026-08-22): 이 상태인 24칸 **전부** 이 항등식이 성립한다
    (메트라이프 10 · 카카오페이 8 · 신한이지 6). 깨지면 RED 다.

    판정이 **결정론적**이라는 점이 중요하다 — 회사 레지스트리도, owner 판단도 필요 없다.
    `item48 == 0 ∧ item14 > 0` 은 데이터만으로 정해지고, 그 조건이 곧 "item48 은 한도가
    아니다" 의 증명이다.

    **이 분류는 로더가 강제하지 않는다.** 로더의 스케일 앵커는 `item48 ≈ item14 × 50%` 인데
    여기 쓰이는 item3 은 **다른 표(경과조치 적용 전 지급여력비율 세부)** 에서 온 독립 추출값이다.
    즉 이 항등식이 348/416 칸에서 성립한다는 사실은 **로더의 배율 선택을 독립적으로 검증**한다 —
    배율이 100배 틀렸다면 item3 과 절대 안 맞는다. 이 저장소에서 47/48/49 스케일에 대한
    유일한 비순환 증거다.
    """
    src = bucket.values_post if post else bucket.values
    i3, i47, i48, i49 = (src.get(target_item), src.get(47), src.get(48), src.get(49))
    if None in (i3, i47, i48, i49):
        return "INPUT_MISSING", None
    capped = abs(i3 - (min(i47, i48) + i49)) <= tol
    uncapped = abs(i3 - i47) <= tol
    if capped and uncapped:
        return "BOTH", max(0.0, i47 - i48)
    if capped:
        return "CAPPED", max(0.0, i47 - i48)
    if uncapped:
        return "UNCAPPED", 0.0
    # TFI 표 미기재: 세 행이 전부 0 인데 SCR 이 양수 → item48 은 한도가 아니다.
    # 한도 메커니즘이 없으므로 한도초과액도 0 이고, 대체 항등식은 target == item13.
    # item51 을 대상으로 해도 같은 항등식이 성립한다 — 실측 12칸(메트라이프 10 ·
    # 카카오페이 2), 최대 |잔차| 0.47. 표가 미기재면 두 표의 보완자본이 같은 재분류항목
    # 하나에서 오므로 대상 셀이 무엇이든 같은 값을 재현해야 한다.
    v14_pre = bucket.values.get(14)
    if (
        max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS
        and v14_pre is not None
        and abs(v14_pre) > 1.0
    ):
        i13 = src.get(13)
        if i13 is None:
            # 대체 항등식의 입력이 없다 → 위반이라고 단정하지 않는다(없는 값과의 비교는
            # 통과도 실패도 무의미하다). 사유를 붙인 SKIP 으로 내보내 게이트가 세게 한다.
            return "TFI_NA_NO_INPUT", 0.0
        if abs(i3 - i13) <= tol:
            return "TFI_NA_OK", 0.0
        return "TFI_NA_RED", 0.0
    return "NEITHER", None


def _tier2_composition_finding(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    rule: str,
    branch: str,
    target_item: int,
    post: bool,
    col: str,
    src: Mapping[int, Optional[float]],
    *,
    skip_tag: str,
    neither_tag: str,
    na_break_tag: str,
    na_missing_tag: str,
    same_table_note: str,
) -> None:
    """`_tier2_branch` 판정 하나를 finding 으로 옮긴다 — 갈래→status 매핑의 단일 지점.

    축 F(`51_tfi_tier2_composition`)가 쓴다. 매핑은 `_COMPOSITION_RED_BRANCHES` /
    `_COMPOSITION_SKIP_BRANCHES` 상수에서 오므로 축 B 와 갈라질 수 없다.

    통과 사유에 반드시 `branch=<이름>` 을 박는다. 게이트 출력만 보고 "어떤 근거로 통과했는지"
    를 못 읽으면 갈래는 검사가 아니라 면제와 구별되지 않는다
    (`tests/test_rule_coverage_manifest.py::test_composition_branch_set_matches_manifest`
    가 이 문자열을 기계로 강제한다).
    """
    tgt = src.get(target_item)
    i47, i48, i49 = src.get(47), src.get(48), src.get(49)
    i13 = src.get(13)
    # **status 는 갈래 이름이 아니라 공유 상수에서 나온다.** 아래 분기는 detail 문구만 고른다.
    if branch in _COMPOSITION_SKIP_BRANCHES:
        status = STATUS_SKIP
    elif branch in _COMPOSITION_RED_BRANCHES:
        status = STATUS_YELLOW if post else STATUS_RED
    else:
        status = STATUS_GREEN
    post_note = _POST_UNESTABLISHED if post else ""

    if branch == "INPUT_MISSING":
        findings.append(_finding(
            bucket, rule, status=status, expected=None, actual=tgt, diff=None,
            detail=f"{skip_tag}: [{col}] item{target_item}/47/48/49 중 결측",
        ))
        return
    if branch == "TFI_NA_NO_INPUT":
        findings.append(_finding(
            bucket, rule, status=status, expected=None, actual=tgt, diff=None,
            detail=f"{na_missing_tag}: [{col}] 47/48/49 가 전부 0 이라 한도 항등식은 적용 "
                   f"대상이 아닌데, 대체 항등식의 입력인 item13(보완자본으로 재분류하는 "
                   "항목)도 결측이라 검산할 수가 없다 "
                   "— 없는 값과의 비교는 통과도 실패도 무의미하다",
        ))
        return
    if branch == "NEITHER":
        expected = min(i47, i48) + i49
        findings.append(_finding(
            bucket, rule, status=status,
            expected=expected, actual=tgt, diff=tgt - expected,
            detail=f"{neither_tag}: [{col}] 공시 보완자본 item{target_item} = {tgt:g} 이 "
                   f"min(47,48)+49 = {expected:g} 도, item47 = {i47:g} 도 재현하지 못한다 "
                   f"— {same_table_note}" + post_note,
        ))
        return
    if branch == "TFI_NA_RED":
        findings.append(_finding(
            bucket, rule, status=status, expected=i13, actual=tgt,
            diff=None if (tgt is None or i13 is None) else tgt - i13,
            detail=f"{na_break_tag}: [{col}] 47/48/49 가 전부 0 인데 "
                   f"item14={bucket.values.get(14)!r} > 0 → item48 은 한도가 아니다"
                   "(해당사항 없음 표시). 그러면 보완자본은 전액 재분류항목이어야 하는데 "
                   f"item{target_item} {tgt!r} ≠ 재분류항목 item13 {i13!r} 이다 "
                   "— 채무성 자본 없이 설명되지 않는 보완자본이 있다" + post_note,
        ))
        return
    if branch == "TFI_NA_OK":
        findings.append(_finding(
            bucket, rule, status=status, expected=i13, actual=tgt, diff=tgt - i13,
            detail=f"보완자본 전액 재분류 [{col}] branch=TFI_NA_OK — 47/48/49 가 전부 0 이고 "
                   f"item14 > 0 이라 한도 항등식은 적용 대상이 아니다. 대신 대체 항등식 "
                   f"item{target_item}({tgt:g}) == item13({i13:g}) 로 검산했다",
        ))
        return
    expected = min(i47, i48) + i49 if branch != "UNCAPPED" else i47
    findings.append(_finding(
        bucket, rule, status=status, expected=expected, actual=tgt,
        diff=None if tgt is None else tgt - expected,
        detail=f"보완자본 구성 재현 [{col}] branch={branch} — {same_table_note}",
    ))


def _validate_tier2_limit(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    eff_tol: float,
    tier2_seen_codes: Optional[frozenset] = None,
    tier2_stale_limit: Optional[frozenset] = None,
    tfi_applicability: Optional[Mapping[tuple[str, str], str]] = None,
    tier2_x_present_codes: Optional[frozenset] = None,
) -> None:
    """보완자본 한도 3줄(47·48·49) 축 — **적용전·적용후를 각각** 검산한다.

    2026-08-21, parser 가 이 세 항목을 1,299칸 적재했는데 **게이트는 exit 0 이었다.** 산수가
    틀렸는데도 통과한 게 아니라, 세 항목을 보는 룰이 **하나도 없어서** 통과했다. 이 절이 그
    구멍이고, 네 개의 축으로 나눠 건다.

    ## 축 A — `2_tier1_bridge` / `_post` (**주 룰, blocking**)

    `item2 = item4 − (item12 − 한도초과) − item13`. 발행사 각주가 정의를 써 놨다
    (미래에셋생명 2023.2Q p11 주2): *"기본자본은 … 순자산에서 지급여력금액 불인정 항목
    (단, 보완자본 한도를 초과한 금액을 제외) 및 보완자본으로 재분류하는 항목을 차감한 금액"*.
    `한도초과 = max(0, item47 − item48)` 이고, **CAPPED 관행일 때만** 더한다(위 `_tier2_branch`).

    **이 축이 주 룰인 이유는 로더가 강제하지 않기 때문이다.** item2·4·12·13 은 전부 별도
    추출값이고, 47/48/49 중에서는 한도초과 한 항만 들어온다. 실측(적용전): 검사 477 ·
    통과 462 · 잔차 15. 한도초과 항을 빼면 425/52, 조건 없이 넣으면 393/36 이라 **조건부가
    유일하게 맞다**(무조건 더하면 UNCAPPED 회사 32칸이 새로 깨진다).

    허용오차 `eff_tol`(2.0억): 억원 정수로 저장된 네 항목의 반올림 ±0.5 × 4 = ±2.0 이 상한이다.

    ## 축 B — `3_tier2_composition` / `_post` (blocking)

    위 분류가 `NEITHER` 면 RED. 두 관행 어느 쪽으로도 공시 보완자본이 재현되지 않는다는 뜻이라,
    47/48/49 의 값·스케일 또는 item3 중 하나가 틀렸다. **item47·item49 가 값 단위로 검사되는
    유일한 축**이다(축 A 는 item47 만, 그것도 CAPPED 일 때만 본다).

    ## 축 C — `47_tier2_census` / `_post` (blocking)

    셋은 같은 표의 연속 3행이다. 완전성(부분결측 = 행 유실) · 부호(금액이라 음수 불가) ·
    자릿수(|값| > item14 × `TIER2_SCALE_CEILING` = 단위스케일 오류)를 본다. 셋이 한 칸도
    없으면 SKIP 이되 **사유 문자열을 반드시 남긴다** — 게이트가 사유를 세어 인쇄하므로
    "1,299칸이 조용히 무검사" 상태가 다시 오면 SKIP 카운트로 드러난다.

    ## 축 D — `48_tier2_limit` / `_post` (**YELLOW, blocking 아님 — 통과가 증거가 아니다**)

    `item48 == item14_적용전 × 50%`.

    **이 축은 로더가 강제한다.** parser 가 100배 사고를 고치면서 스케일(÷1 vs ÷100) 판별
    앵커를 바로 이 항등식으로 바꿨다 — 즉 이 식을 가장 잘 만족하는 배율을 골라 저장한다.
    그러므로 **여기서 GREEN 이 나오는 것은 추출이 옳다는 증거가 아니다.** 축 A·B·C 와 달리
    blocking 으로 세면 안 되고, 그래서 불일치를 RED 가 아니라 YELLOW(review)로 낸다.
    남겨 두는 이유는 회귀 감시다 — 로더가 앵커를 또 바꾸면 이 축이 먼저 움직인다.

    **적용후 분모는 `item14_적용후` 가 아니라 `item14_적용전` 이다.** 이걸 틀리면 241칸이 전부
    오탐이 된다. 근거 둘:
      · 원문(한화손해 2023.1Q p9, 단어 좌표로 확인): `(1)공통적용 경과조치` 표의 **자기
        지급여력기준금액 행이 32,387 / 32,387 로 두 컬럼 동일**하고, 한도는 16,193 / 16,193
        = 32,387 × 50%. 같은 표의 `보완자본 30,385 / 26,150` 은 실제로 다르므로 두 컬럼을
        못 읽는 것이 아니다. TFI(공통적용 경과조치)는 가용자본만 움직이고 요구자본은 안 건드린다.
      · 전수 실측: item14 가 전≠후인 216칸에서 item48_적용후가 `item14_전×50%` 와 맞는 것이
        **215칸, `item14_후×50%` 와 맞는 것이 0칸.**
    마스터의 `item14_적용후` 는 선택 경과조치까지 합친 **전체결합 스코프**라 개념이 다르다.
    """
    strict_tol = eff_tol
    for post in (False, True):
        col = KEY_VALUE_POST if post else KEY_VALUE
        sfx = "_post" if post else ""
        src = bucket.values_post if post else bucket.values
        present = {i for i in TIER2_ITEMS if i in src}
        branch, excess = _tier2_branch(bucket, post, strict_tol)

        # --- 축 A: 기본자본 다리 -------------------------------------------
        rule_a = f"2_tier1_bridge{sfx}"
        i2, i4, i12, i13 = (src.get(2), src.get(4), src.get(12), src.get(13))
        # **폴백 금지.** 적용후가 없는 항목을 적용전으로 메우면 서로 다른 기준의 값을 한 식에
        # 섞게 되고, 그렇게 나온 통과·실패는 둘 다 무의미하다(rule 8_post 가 같은 이유로
        # mixed-basis 를 걷어낸다). 결측은 사유를 붙여 SKIP 하고 게이트가 사유별로 센다.
        missing_bridge = [n for n, v in ((2, i2), (4, i4), (12, i12), (13, i13)) if v is None]
        if missing_bridge:
            findings.append(_finding(
                bucket, rule_a, status=STATUS_SKIP, expected=None, actual=i2, diff=None,
                detail=f"BRIDGE_INPUT_MISSING: [{col}] item{missing_bridge} 결측 "
                       "(폴백 금지 — 적용전 값으로 메우면 혼합기준 무의미값이 된다)",
            ))
        else:
            raw_exc = excess if branch in ("CAPPED", "BOTH") else 0.0
            # **구조적 상한: 한도초과액 ≤ 불인정항목(item12).**
            #
            # 발행사 각주가 정의를 써 놨다(미래에셋생명 2023.2Q p11 주2): 기본자본은 순자산에서
            # "지급여력금액 불인정 항목(단, **보완자본 한도를 초과한 금액을 제외**)" 을 차감한다.
            # 즉 한도초과액은 불인정항목 **안에 들어 있는 한 구성요소**다 — 그것보다 클 수 없다.
            # `max(0, item47 − item48)` 은 그 구성요소의 근사치일 뿐이고, 근사치가 상한을
            # 넘으면 넘은 만큼은 다른 데서 온 것이므로 다리에 넣으면 안 된다.
            #
            # 이건 허용오차를 키운 게 아니라 **불가능한 값을 잘라낸 것**이다. 실측이 그걸
            # 확인해 준다(2026-08-22 전수): 클램프가 발동하는 10칸 중 9칸에서 다리가 오히려
            # **정확히 닫힌다**. 그중 셋은 근사치가 item12 와 소수점 반올림 차이(203.10 vs 203 ·
            # 2,015.35 vs 2,015 · 513.09 vs 513)라 "불인정항목 전액이 한도초과" 임을 직접 보여준다.
            # 실측 성적: 461/16 → **467/10**. 남은 1칸(한화생명 2025.2Q, 근사치가 item12 의
            # 2.3배)은 클램프로도 안 닫히고 그대로 RED 다 — 클램프는 실패를 지우지 않는다.
            exc = min(raw_exc, max(0.0, i12))
            expected = i4 - (i12 - exc) - i13
            f = _check_numeric(bucket, rule_a, expected, i2, strict_tol)
            f["detail"] = (
                f"item2 == item4 − (item12 − 한도초과) − item13 [{col}] "
                f"branch={branch} 한도초과={exc:g}"
                + (f" (근사치 {raw_exc:g} 를 item12={i12:g} 로 클램프 — "
                   "한도초과액은 불인정항목의 구성요소라 그보다 클 수 없다)"
                   if raw_exc > exc + 1e-9 else "")
                + ("" if branch not in ("NEITHER", "INPUT_MISSING", "TFI_NA_RED",
                                        "TFI_NA_NO_INPUT")
                   else f" (※ branch={branch} 라 한도초과를 0 으로 뒀다 — "
                        f"3_tier2_composition{sfx} 가 별도로 RED/SKIP)")
            )
            if post and f["status"] == STATUS_RED:
                f["status"] = STATUS_YELLOW
                f["detail"] += _POST_UNESTABLISHED
            findings.append(f)

        # --- 축 B: 보완자본 구성(관행 분류) --------------------------------
        rule_b = f"3_tier2_composition{sfx}"
        if branch == "INPUT_MISSING":
            findings.append(_finding(
                bucket, rule_b, status=STATUS_SKIP, expected=None,
                actual=src.get(3), diff=None,
                detail=f"COMPOSITION_INPUT_MISSING: [{col}] item3/47/48/49 중 결측",
            ))
        elif branch == "TFI_NA_NO_INPUT":
            findings.append(_finding(
                bucket, rule_b, status=STATUS_SKIP, expected=None,
                actual=src.get(3), diff=None,
                detail=f"COMPOSITION_TFI_NA_RECLASS_MISSING: [{col}] 47/48/49 가 전부 0 이라 "
                       "한도 항등식은 적용 대상이 아닌데, 대체 항등식의 입력인 item13"
                       "(보완자본으로 재분류하는 항목)도 결측이라 검산할 수가 없다 "
                       "— 없는 값과의 비교는 통과도 실패도 무의미하다",
            ))
        elif branch == "NEITHER":
            i3 = src.get(3)
            i47, i48, i49 = src.get(47), src.get(48), src.get(49)
            findings.append(_finding(
                bucket, rule_b,
                status=STATUS_YELLOW if post else STATUS_RED,
                expected=min(i47, i48) + i49, actual=i3,
                diff=i3 - (min(i47, i48) + i49),
                detail=f"COMPOSITION_NEITHER: [{col}] 공시 보완자본 {i3:g} 이 "
                       f"min(47,48)+49 = {min(i47, i48) + i49:g} 도, "
                       f"item47 = {i47:g} 도 재현하지 못한다 "
                       "— 47/48/49 의 값·스케일 또는 item3 중 하나가 틀렸다"
                       + (_POST_UNESTABLISHED if post else ""),
            ))
        elif branch == "TFI_NA_RED":
            # TFI 표가 미기재(47=48=49=0, SCR>0)라 한도 항등식은 적용 대상이 아니지만,
            # 그 상태에서 성립해야 할 **대체 항등식** item3 == item13 이 깨졌다.
            # 무검사로 넘기지 않는다 — 갈래를 나눈 것이 면제가 되지 않게 하는 장치가 이 가지다.
            i3, i13 = src.get(3), src.get(13)
            findings.append(_finding(
                bucket, rule_b,
                status=STATUS_YELLOW if post else STATUS_RED,
                expected=i13, actual=i3,
                diff=None if (i3 is None or i13 is None) else i3 - i13,
                detail=f"COMPOSITION_TFI_NA_RECLASS_BREAK: [{col}] 47/48/49 가 전부 0 인데 "
                       f"item14={bucket.values.get(14)!r} > 0 → item48 은 한도가 아니다"
                       "(해당사항 없음 표시). 그러면 보완자본은 전액 재분류항목이어야 하는데 "
                       f"공시 보완자본 {i3!r} ≠ 재분류항목 item13 {i13!r} 이다 "
                       "— 채무성 자본 없이 설명되지 않는 보완자본이 있다"
                       + (_POST_UNESTABLISHED if post else ""),
            ))
        elif branch == "TFI_NA_OK":
            i3, i13 = src.get(3), src.get(13)
            findings.append(_finding(
                bucket, rule_b, status=STATUS_GREEN, expected=i13, actual=i3,
                diff=i3 - i13,
                detail=f"보완자본 전액 재분류 [{col}] branch=TFI_NA_OK — 47/48/49 가 전부 0 이고 "
                       f"item14 > 0 이라 한도 항등식은 적용 대상이 아니다. 대신 대체 항등식 "
                       f"item3({i3:g}) == item13({i13:g}) 로 검산했다 "
                       "(전수 24/24 성립, 2026-08-22)",
            ))
        else:
            findings.append(_finding(
                bucket, rule_b, status=STATUS_GREEN, expected=None,
                actual=src.get(3), diff=None,
                detail=f"보완자본 구성 재현 [{col}] branch={branch} "
                       "(로더가 강제하지 않는 축 — 배율 선택의 독립 검증)",
            ))

        # --- 축 C: census (완전성 · 부호 · 자릿수) --------------------------
        rule_c = f"47_tier2_census{sfx}"
        v14_pre = bucket.values.get(14)
        if not present:
            # **SKIP 사유를 두 갈래로 쪼갠다.** "한 칸도 없다" 는 사유가 아니라 현상이다.
            # 같은 회사가 다른 분기에서는 이 표를 공시했다면 원천부재가 아니라 **추출갭**이다
            # **판정 근거를 추론에서 실측으로 바꿨다 (2026-08-22, iter-5).**
            #
            # 그 전까지는 "같은 회사가 다른 분기엔 공시했나"(INTERMITTENT)로 갈라 RED 를 냈다.
            # **그 기준이 틀렸다.** 47/48/49 는 [지급여력비율의 경과조치 적용에 관한 사항]
            # (1) 공통적용 경과조치 표의 행이고, TFI(제도시행 前 기발행 자본증권 인정범위 확대)는
            # 그 자본증권이 상환·만기되면 적용이 끝난다. **분기마다 켜졌다 꺼지는 것이 정상**이고,
            # 적용하지 않는 분기엔 발행사가 근거표 자체를 안 그린다. 원문으로 확인했다:
            #   · 교보라이프플래닛 2023.1Q(TFI=O) MD 에 `보완자본 한도` 3회 + 표 존재 →
            #     2023.2Q 이후(TFI=X) 같은 키워드 **0회**. 12분기 전부 원천부재다.
            #     INTERMITTENT 규칙은 이 12버킷 × 2컬럼 = 24칸을 추출갭으로 오판하고 있었다.
            #
            # 그래서 이 버킷 **자신의 TFI 실측값**으로 판정한다
            # (`data/_derived/kics_transition_applicability.json`, 494버킷 전수, 95.1% 확정):
            #   O       → 발행사가 적용했는데 표가 없다 = **진짜 추출갭** → RED (parser 발주)
            #   X       → 적용 안 해서 안 그린 것 = 정상 부재 → SKIP + 사유
            #   NA      → 원문이 `-` 를 인쇄 = 적용여부 **미기재**. X 와 같게 보지 않는다 —
            #             `-` 는 "적용 안 함"의 진술이 아니라 진술의 부재다. UNKNOWN 과 같이
            #             review 로 낸다(실측상 NA 8버킷은 전부 47/48/49 가 **있어서** 이
            #             가지에 도달하지 않는다 = 엄격하게 잡아도 비용 0).
            #   UNKNOWN → 우리가 못 읽었다. **통과가 아니다** → review 로 인쇄하고 센다.
            #   사이드카 없음 / 키 없음 → UNKNOWN 과 동일. 파일이 사라지면 조용히 통과하는
            #             퇴화를 막는다(이 저장소의 stale 사이드카 전례 — `_source_readability`
            #             가 같은 이유로 디스크와 대조해 UNMEASURED 로 강등한다).
            #
            # **X 를 무조건 면죄부로 쓰지는 않는다.** 전수 실측: TFI=X 108버킷 중 93버킷이
            # 47/48/49 를 **갖고 있다**(P(부재|X)=13.9%). 즉 X 는 "표를 안 그린다"를 함의하지
            # 않는다 — 하나손해는 13분기 전부 TFI=X 인데 12분기가 표를 인쇄한다(2023.2Q raw:
            # "해당사항 없음" 문장 **뒤에** 적용전 컬럼만 채운 표를 그린다). 그러므로 같은 회사에
            # **다른 TFI=X 분기에서는 행이 있는데** 이 분기만 없으면, X 는 이 부재를 설명하지
            # 못한다 → SKIP 이 아니라 review 로 내린다. 갈래가 면제가 되지 않게 하는 장치가
            # 이 가지다. (해당 1버킷 = 하나손해 2023.1Q 는 원문 대조로 원천부재 확인 완료.)
            #
            # 해제 조건: RED 는 해당 (회사,분기)의 47/48/49 가 적재되면 사라진다 — 면제가 아니라
            # **작업 큐**다. review 는 사이드카의 UNKNOWN 이 확정되면 자동으로 갈래가 정해진다.
            tfi = (None if tfi_applicability is None
                   else tfi_applicability.get((bucket.code, bucket.quarter)))
            intermittent = (
                tier2_seen_codes is not None and bucket.code in tier2_seen_codes
            )
            hint = ("; 같은 회사의 다른 분기에는 이 표가 있다 → 추출갭 유력(parser 우선순위)"
                    if intermittent else
                    "; 이 회사는 전 분기에서 이 표가 없다")
            if tfi == "O":
                status, tag = STATUS_RED, "TIER2_TABLE_ABSENT_BUT_TFI_APPLIED"
                why = ("적용여부 실측 TFI=O — 발행사가 공통적용 경과조치를 **적용했다**. "
                       "적용했으면 (1)공통적용 경과조치 표가 실제 숫자와 함께 존재해야 하므로 "
                       "이 부재는 원천부재가 아니라 **추출갭**이다 (parser 발주 대상)")
            elif tfi == "X" and bucket.code in (tier2_x_present_codes or frozenset()):
                status, tag = STATUS_YELLOW, "TIER2_TABLE_ABSENT_TFI_X_INCONSISTENT"
                why = ("적용여부 실측 TFI=X 지만 **같은 회사의 다른 TFI=X 분기에는 47/48/49 가 "
                       "있다** — 이 발행사는 미적용 분기에도 표를 그리므로 X 가 이 부재를 "
                       "설명하지 못한다. 정상 부재로 단정하지 않고 원문 대조 대기로 둔다")
            elif tfi == "X":
                status, tag = STATUS_SKIP, "TIER2_TABLE_ABSENT_TFI_NOT_APPLIED"
                why = ("적용여부 실측 TFI=X — 공통적용 경과조치를 적용하지 않아 발행사가 "
                       "(1)공통적용 경과조치 표를 그리지 않았다. **정상 부재**이고 추출갭이 "
                       "아니다 (같은 회사의 다른 TFI=X 분기에도 이 표가 없다)")
            else:
                status, tag = STATUS_YELLOW, "TIER2_TABLE_ABSENT_APPLICABILITY_UNKNOWN"
                src_why = {
                    "NA": "원문이 적용여부에 `-` 를 인쇄했다(미기재) — `-` 는 미적용의 진술이 "
                          "아니라 진술의 부재라 X 와 같게 보지 않는다",
                    "UNKNOWN": "적용여부표를 우리가 못 읽었다(사이드카 UNKNOWN)",
                }.get(str(tfi), (
                    "이 버킷의 적용여부 실측값이 없다 — 사이드카 파일이 없거나 "
                    "(회사,분기) 키가 없거나 원본 MD 가 사라져 강등됐다"))
                why = (f"적용여부 미확정({tfi!r}): {src_why}. **통과가 아니다** — "
                       "부재가 정상인지 추출갭인지 판정할 근거가 없다는 뜻이라 "
                       "review 로 세어 남긴다" + hint)
            findings.append(_finding(
                bucket, rule_c, status=status,
                expected=len(TIER2_ITEMS), actual=0, diff=None,
                detail=f"{tag}: 47/48/49 가 [{col}] 에 한 칸도 없다 — {why}",
            ))
        else:
            problems: list[str] = []
            missing = [i for i in TIER2_ITEMS if i not in present]
            if missing:
                problems.append(
                    f"TIER2_PARTIAL_ROWS: {sorted(present)} 는 있는데 {missing} 결측 "
                    "— 같은 표의 연속 3행이라 부분결측은 행 유실 신호"
                )
            for i in sorted(present):
                if src[i] < 0:
                    problems.append(f"TIER2_NEGATIVE: item{i}={src[i]:g} — 금액 항목이 음수")
            if v14_pre is not None:
                ceiling = abs(v14_pre) * TIER2_SCALE_CEILING
                for i in sorted(present):
                    if abs(src[i]) > ceiling:
                        problems.append(
                            f"TIER2_SCALE: item{i}={src[i]:g} > item14_적용전 × "
                            f"{TIER2_SCALE_CEILING:g} (={ceiling:g}) — 단위스케일 오류 의심"
                        )
            # 중복행: `한도 적용 전(47)` 과 `한도(48)` 가 소수점까지 **정확히** 같다.
            #
            # ⚠️ **2026-08-22 정정 — 원래 붙어 있던 사유가 원문에 반증됐다.** 어제 이 자리엔
            # "48 은 SCR×50% 공식값이고 47 은 독립 합계라 2자리까지 우연히 같을 수 없다 →
            # **같은 셀을 두 번 읽은 지문**" 이라고 써 있었다. raw PDF 를 단어 좌표로 직접
            # 읽어 보니 **발행사가 두 행에 같은 숫자를 인쇄한다**:
            #   · BNP카디프 FY2024_Q3 p16 — `보완자본 한도 적용 전 31,614` / `보완자본 한도
            #     31,614` 두 행이 서로 다른 y 에 각자의 라벨을 달고 같은 값(2024_Q4 p50 은
            #     34,678/34,678). 우리 추출은 원문대로다.
            #   · 동양생명 FY2025_Q2 p16 — 적용전 컬럼이 1,210,705/1,210,705. 같은 표의
            #     적용후 컬럼은 866,138/1,210,705 로 **다르다** → 두 컬럼을 못 읽는 것이 아니다.
            # 그러니 이 지문은 "우리 파서의 중복 읽기" 가 아니라 **"이 표가 자기 공식으로
            # 안 닫힌다"** 는 신호로 읽어야 한다(원인은 발행사일 수도, 우리일 수도 있다).
            #
            # 그래도 검사는 남긴다 — 실제로 우리 결함을 하나 잡았다. 하나생명 2024.4Q 는
            # 47 = 48 = 51 = item3 = 3452.36 으로 **전부 item3 값이 복사**돼 있고, 그 분기
            # raw 는 347p 번들 문서라 (1)공통적용 경과조치 표가 아예 없다(MD 에도 `보완자본
            # 한도 적용 전` 0회). 그 복사 때문에 `3_tier2_composition` 은 branch=UNCAPPED 로
            # **GREEN 이 된다** — 즉 이 한 줄이 없으면 그 버킷은 통째로 false-green 이다.
            if (
                47 in present and 48 in present
                and src[47] == src[48] and abs(src[47]) > TIER2_ZERO_EPS
            ):
                problems.append(
                    f"TIER2_DUPLICATE_ROW: item47 == item48 == {src[47]:g} 이 소수점까지 동일 "
                    "— item48 은 SCR×50% 공식값이고 item47 은 독립 합계라 둘이 정확히 같으면 "
                    "한도 항등식 min(47,48)+49 가 성립할 수 없다. **원인을 단정하지 말 것**: "
                    "발행사가 실제로 같은 값을 인쇄한 사례(BNP카디프·동양생명, raw 좌표 확인)와 "
                    "우리가 item3 을 복사해 넣은 사례(하나생명 2024.4Q)가 둘 다 있다 "
                    "— raw 대조 전에는 어느 쪽인지 알 수 없다"
                )
            # 전기 한도 잔존: 당분기 SCR×50% 와는 안 맞는데 **직전분기** SCR×50% 와는 맞는다.
            # 롯데손해 2026.1Q 실측 — 47/48/49 적용전 3칸이 2025.4Q 와 바이트까지 동일하고
            # item48(10,335.34)은 2025.4Q SCR×50%(10,335.50)와 일치, 당분기(10,216)와는 119.34
            # 어긋난다. 산수가 맞는데 **소스가 직전분기**인 전형적 false-green 이라 RED 다.
            if tier2_stale_limit and (bucket.code, bucket.quarter, post) in tier2_stale_limit:
                problems.append(
                    f"TIER2_LIMIT_STALE: [{col}] item48 이 당분기 item14_적용전×50% 와 어긋나는데 "
                    "**직전분기** item14_적용전×50% 와는 일치한다 — 전기 값이 그대로 남아 있는 "
                    "것으로 본다 (47/48/49 3칸이 직전분기와 동일한지 같이 확인할 것)"
                )
            findings.append(_finding(
                bucket, rule_c,
                status=STATUS_RED if problems else STATUS_GREEN,
                expected=len(TIER2_ITEMS), actual=len(present), diff=None,
                detail="; ".join(problems) if problems
                       else f"47/48/49 완비 · 부호·자릿수 정상 [{col}]",
            ))

        # --- 축 D: 한도 = SCR × 50% (로더 강제 → YELLOW) ---------------------
        rule_d = f"48_tier2_limit{sfx}"
        v48 = src.get(48)
        if v48 is None or v14_pre is None:
            findings.append(_finding(
                bucket, rule_d, status=STATUS_SKIP, expected=None, actual=None, diff=None,
                detail=(f"TIER2_TABLE_ABSENT: 47/48/49 가 [{col}] 에 한 칸도 없다"
                        if not present else
                        f"TIER2_LIMIT_INPUT_MISSING: [{col}] item48 또는 item14_적용전 결측"),
            ))
        else:
            expected = v14_pre * TIER2_LIMIT_RATIO
            diff = v48 - expected
            findings.append(_finding(
                bucket, rule_d,
                # 불일치를 RED 가 아니라 YELLOW 로 내는 것은 임계를 느슨하게 잡은 게 아니라
                # **이 축의 통과가 증거가 아니기 때문**이다(로더가 이 식으로 배율을 골랐다).
                # 증거력 없는 축을 blocking 으로 세면 게이트 전체의 RED=0 이 오염된다.
                status=STATUS_GREEN if abs(diff) <= eff_tol else STATUS_YELLOW,
                expected=expected, actual=v48, diff=diff,
                detail=f"item48 == item14_적용전 × {TIER2_LIMIT_RATIO:g} [{col}] "
                       "※ LOADER_ENFORCED(동어반복): parser 가 이 식으로 스케일 배율을 "
                       "골라 저장한다 — 통과는 추출 정확성의 증거가 아니다. 회귀 감시용.",
            ))


def _validate_tfi_tier_rows(
    bucket: QuarterBucket, findings: list[dict[str, Any]], eff_tol: float
) -> None:
    """TFI 표 자신의 기본자본·보완자본(50·51) 축 — **적용전·적용후를 각각** 검산한다.

    ## 축 E 적용전 — `50_tfi_tier_split` (blocking RED)

    `item50 + item51 == item1_적용전`. TFI 표의 "적용 전" 컬럼은 경과조치를 하나도 안 쓴
    상태라 헤드라인 적용전과 같은 기준이다. 전수 실측 431칸 중 **429칸 성립**, 어긋나는
    2칸은 둘 다 이미 원문 대조로 확정된 롯데손해 발행사 불일치다(2023.1Q +18 · 2026.1Q
    −896.51). **item50 이 값 단위로 검사되는 유일한 축**이다.

    ⚠️ **이 축의 GREEN 은 절반만 증거다** — 로더가 같은 식을 쓴다. parser 의 백필 스크립트
    (`fix_20260822_tfi_tier_full_scan.py`)가 50/51 배율(÷1 vs ÷100)을 `50+51 ≈ item1_적용전`
    2% 밴드로 고르고, 나아가 잔차가 `max(5%, 5.0억)` 을 넘으면 **아예 안 쓴다**. 그래서
    이 축은 그 밴드 밖의 오류를 구조적으로 못 본다(안 쓰인 버킷은 아래 census 의
    `TFI_TIER_ROWS_ABSENT_BACKLOG` 로 세어진다 — 그쪽이 그 오류의 출구다). 다만 밴드가
    허용오차(2.0억)보다 훨씬 넓어 축 D 처럼 완전한 동어반복은 아니고, 실제로 RED 2 를 낸다.

    ## 축 E — 2026-08-24 **등식 승격**: comparand 가 item52(같은 표 지급여력금액 행)다

    아래 두 절(적용전=item1 / 적용후=범위검사)은 **item52 가 마스터에 없던 동안의 설계**다.
    parser iter-10 이 428버킷에 item52 를 실었으므로, 그 값이 있는 버킷에서는 적용전·적용후
    **둘 다** `item50 + item51 == item52` 로 검산한다. 같은 표·같은 컬럼이라 스코프 차이가
    개입할 수 없고, item52 는 로더가 배율 선택에 쓰지 않는 행이라 비순환이다. 아래 두 절은
    item52 결측 38버킷(적용전 30 · 적용후 30 + 표부재)의 **폴백**으로 그대로 살아 있다
    (`TFI_TOTAL_ROW_ABSENT` 사유로 매 실행 세어진다).

    승격 실측(2026-08-24): 적용후 YELLOW 70 → **69칸이 등식으로 닫힌다**(나머지 1칸은 item52
    결측). 그리고 **GREEN 이던 6칸이 RED 로 뒤집혔다** — 카카오페이 5버킷 item52 100배 +
    삼성화재 2025.3Q 적용후 발행사 자릿수 전치. 승격의 값어치는 닫힌 69칸이 아니라 이 6칸이다.

    ## 축 E 적용후 — `50_tfi_tier_split_post` (item52 결측 시 폴백: 범위검사)

    **원래 여기 있던 식 `50후 + 51후 == item1_적용후` 는 틀렸고, `== item1_적용전` 도 틀리다.**
    두 전제 모두 원문으로 반증됐다. IBK연금 FY2026_Q1 raw **p17** `1) 공통적용 경과조치 관련`
    (단위 백만원):

        지급여력비율(%)      119.24 /   130.46
        지급여력금액        857,997 /  938,740   ← **표 자신의 합계 행이 움직인다**
          기본자본          157,463 /  157,463
          보완자본          700,535 /  781,277
        지급여력기준금액    719,585 /  719,585   ← 요구자본은 안 움직인다(축 D 의 근거)

    · `== item1_적용후` 가 틀린 이유: 마스터의 item1_적용후(10,526억)는 TFI + 선택 경과조치를
      합친 **전체결합** 스코프인데 이 표의 50/51 은 TFI **단독**이다. 축 D 가 겪은 것과 같은
      스코프 실수다. 이 오류만으로 적용후 60칸이 RED 였다.
    · `== item1_적용전` 도 틀린 이유: 위 표의 합계 행 857,997 → 938,740 이 **실제로 움직인다.**
      "공통적용 경과조치는 재분류라 합계 불변" 은 코리안리 한 회사에서만 참이었다(그 회사는
      기본자본 +983 / 보완자본 −983 로 정확히 상쇄된다). 전수 실측: 합계가 움직이는 버킷이
      **49개 / 11개사**. 한 회사로 일반화한 전제였다.

    올바른 비교 대상은 **표 자신의 지급여력금액 적용후 행**인데 마스터에 항목이 없다
    (parser 발주 — item52). 없는 값을 다른 값으로 대신하지 않고, 그때까지 **범위검사**를 건다:

        min(item1_전, item1_후) − tol  ≤  50후 + 51후  ≤  max(item1_전, item1_후) + tol

    근거: TFI 단독 합계는 "경과조치 없음"(=item1_전)에서 출발해 TFI 효과만 더한 값이고,
    헤드라인 적용후는 거기에 선택 경과조치까지 더한 값이다. 두 경과조치 모두 가용자본을
    깎지 않으므로 TFI 단독값은 그 사이에 있어야 한다(실측: item1_후 < item1_전 인 버킷 0).

    **이 범위검사는 비어 있지 않다.** 431칸 중 426 통과 · **5 RED**, 그리고 그 5칸은 전부
    실제 결함이다(교보생명 4칸은 item51_적용후 가 0.10~0.15 로 읽혔다 — 같은 버킷 적용전이
    41,915.04 이고 47/48/49 적용후로 재현해도 41,915.04 다 · 롯데손해 2026.1Q 는 이미 확정된
    전기표 재게시). 그리고 `item1_전 == item1_후` 인 **362칸(84%)에서는 범위가 한 점으로
    붕괴해 등식과 같은 강도**로 검사된다 — 느슨해진 것은 나머지 69칸뿐이다.

    범위 안에 있지만 등식이 아닌 55칸은 GREEN 이 아니라 **YELLOW** 로 낸다. "검사했는데
    깨끗하다" 와 "약한 검사만 통과했다" 를 같은 색으로 찍으면 item52 발주가 조용히 사라진다.

    ## 축 F — `51_tfi_tier2_composition` / `_post` (적용전 RED · 적용후 YELLOW)

    `item51` 을 대상으로 **축 B 와 같은 `_tier2_branch` 를 돌린다**(CAPPED / UNCAPPED /
    BOTH / TFI_NA_*). 네 항목이 **전부 같은 표 · 같은 컬럼**에서 오므로 두 표 사이 스코프
    차이가 개입할 수 없다는 점만 축 B 와 다르다.

    갈래 없이 `min(47,48)+49` 만 검사하던 하루 동안 적용전 **67칸이 RED** 였고, 전수 분해
    결과 UNCAPPED 50 · TFI_NA 12 · 발행사 불일치 5 였다 — 즉 62칸이 축 B 가 이미 갖고 있던
    갈래를 안 가져와서 생긴 오탐이다. 갈래 이식 후 **RED 5**, 그 5칸은 (회사,분기)가
    `3_tier2_composition` 의 기존 RED 목록과 정확히 일치한다(BNP카디프 3 · 롯데손해 1 ·
    NH농협손해 1) — 두 표가 같은 방향으로 어긋난다는 뜻이라 서로를 확증한다.

    적용후는 YELLOW 다 — 축 B 와 **같은 미확립 사유**이고 같은 크기의 반증이 있다:
    코리안리 2023.2Q 적용후 min(581.39, 9832.38)+24.99 = 606.38 ≠ item51_후 5,209.20.
    한화손해 2023.2Q 반증(적용전 정확·적용후 잔차 5,872.17)과 같은 양식이라, 확립 못 한
    것을 위반으로 단정하지 않는다. **확립되면 RED 로 승격하라.**

    ## census — 결측을 통과로 세지 않는다

    50·51 은 같은 표의 연속 2행이라 **한쪽만 있으면 행 유실**이다(RED).
    둘 다 없는데 47/48/49 는 있으면, 그건 같은 표의 부모행을 안 읽은 것이므로
    `TFI_TIER_ROWS_ABSENT_BACKLOG` 사유를 붙여 SKIP 한다 — 게이트가 사유별로 세므로
    실측 430버킷이 매 실행 눈앞에 찍힌다(2026-08-22 기준, parser 백필 발주 대상).
    **RED 승격은 하지 않았다.** 47/48/49 의 `..._INTERMITTENT` 와 달리 50/51 은 어제 만든
    스키마라 기대 그리드가 아직 확정되지 않았고, 430버킷을 blocking 으로 올리는 것은
    orchestrator/owner 판단 사항이다. 다만 **조용하지는 않다.**
    """
    for post in (False, True):
        col = KEY_VALUE_POST if post else KEY_VALUE
        sfx = "_post" if post else ""
        src = bucket.values_post if post else bucket.values
        present = {i for i in TFI_TIER_ITEMS if i in src}
        i50, i51 = src.get(50), src.get(51)
        i1 = src.get(1)

        # --- 축 E: TFI 표의 tier 분할 합 == 지급여력금액 ----------------------
        rule_e = f"50_tfi_tier_split{sfx}"
        if not present:
            has_tier2 = any(i in src for i in TIER2_ITEMS)
            tag = ("TFI_TIER_ROWS_ABSENT_BACKLOG" if has_tier2
                   else "TFI_TIER_ROWS_ABSENT_NO_TABLE")
            why = ("47/48/49 는 있는데 같은 표의 부모행 50/51 이 없다 — 같은 표를 반쯤만 읽었다 "
                   "(parser 백필 발주 대상)" if has_tier2
                   else "이 버킷에는 TFI 표 자체가 [{}] 에 없다".format(col))
            findings.append(_finding(
                bucket, rule_e, status=STATUS_SKIP,
                expected=len(TFI_TIER_ITEMS), actual=0, diff=None,
                detail=f"{tag}: 50/51 이 [{col}] 에 한 칸도 없다 — {why}",
            ))
        elif len(present) < len(TFI_TIER_ITEMS):
            missing = [i for i in TFI_TIER_ITEMS if i not in present]
            findings.append(_finding(
                bucket, rule_e, status=STATUS_RED,
                expected=len(TFI_TIER_ITEMS), actual=len(present), diff=None,
                detail=f"TFI_TIER_PARTIAL_ROWS: [{col}] {sorted(present)} 는 있는데 "
                       f"{missing} 결측 — 같은 표의 연속 2행이라 부분결측은 행 유실 신호",
            ))
        elif src.get(TFI_TOTAL_ITEM) is not None:
            # **2026-08-24 승격**: comparand 를 같은 표·같은 컬럼의 지급여력금액 행(item52)으로
            # 바꾼다. 적용전·적용후 **둘 다** 같은 식이라 이 축은 여기서 대칭이 된다.
            # 종전 comparand(적용전=item1 헤드라인 / 적용후=범위)는 item52 결측일 때만 쓴다.
            i52 = src[TFI_TOTAL_ITEM]
            f = _check_numeric(bucket, rule_e, i50 + i51, i52, eff_tol)
            f["detail"] = (
                f"item50 + item51 == item52 [{col}] — **같은 표·같은 컬럼**의 지급여력금액 "
                f"행과 대조한다(2026-08-24 등식 승격, 종전 적용전=item1 대조 / 적용후=범위검사). "
                f"50={i50:g} + 51={i51:g} = {i50 + i51:g} vs item52={i52:g}. "
                "비순환 축이다 — item52 는 로더가 47/48/49/51 배율 선택에 쓰지 않는 독립 행이고, "
                "그래서 카카오페이 5버킷의 item52 100배(ALL_ZERO_TRIVIAL 스케일 단축이 만든 구멍)를 "
                "이 축이 처음 잡았다"
            )
            findings.append(f)
        elif i1 is None or (post and bucket.values.get(1) is None):
            missing_col = "item1[값_적용후]" if i1 is None else "item1[값](범위 하한)"
            findings.append(_finding(
                bucket, rule_e, status=STATUS_SKIP, expected=None,
                actual=i50 + i51, diff=None,
                detail=f"TFI_TIER_SPLIT_INPUT_MISSING: [{col}] {missing_col} 결측 "
                       f"(item52 도 결측 — TFI_TOTAL_ROW_ABSENT) "
                       "— 없는 값과의 비교는 통과도 실패도 무의미하다 (폴백 금지)",
            ))
        elif not post:
            f = _check_numeric(bucket, rule_e, i50 + i51, i1, eff_tol)
            f["detail"] = (
                f"TFI_TOTAL_ROW_ABSENT(폴백): item52 결측이라 헤드라인 item1 과 대조한다 — "
                f"item50 + item51 == item1 [{col}] — TFI 표의 '적용 전' 컬럼은 경과조치를 "
                f"하나도 안 쓴 상태라 헤드라인 적용전과 같은 기준이다(실측 429/431). "
                f"50={i50:g} + 51={i51:g} vs item1={i1:g} "
                "※ 부분 LOADER_ENFORCED: 로더가 이 식의 2% 밴드로 배율을 고르고 잔차가 "
                "max(5%, 5.0억) 을 넘으면 아예 적재하지 않는다 — 그 밖의 오류는 이 축이 "
                "아니라 census 의 TFI_TIER_ROWS_ABSENT_BACKLOG 로 드러난다"
            )
            findings.append(f)
        else:
            # 적용후: TFI 표 자신의 지급여력금액 행(item52)이 마스터에 없다. 없는 값을 다른
            # 값으로 대신하지 않는다 — item1_적용후(전체결합)도, item1_적용전(TFI 효과 무시)도
            # 둘 다 원문으로 반증됐다(docstring 축 E 적용후, IBK연금 FY2026_Q1 p17).
            # 그때까지 **범위검사**만 건다. item1 전==후 인 362칸에서는 범위가 한 점으로
            # 붕괴해 등식과 같은 강도가 되고, 나머지 69칸에서만 느슨하다.
            i1_pre = bucket.values.get(1)
            total = i50 + i51
            lo, hi = min(i1_pre, i1), max(i1_pre, i1)
            below, above = lo - total, total - hi
            worst = max(below, above)
            collapsed = abs(hi - lo) <= eff_tol
            if worst > eff_tol:
                status = STATUS_RED
                verdict = (f"TFI_TIER_SPLIT_OUT_OF_RANGE: 범위를 "
                           f"{'아래로' if below > above else '위로'} {worst:g} 벗어났다")
            elif collapsed:
                status = STATUS_GREEN
                verdict = ("item1 적용전==적용후 라 범위가 한 점으로 붕괴 — 등식과 같은 강도로 "
                           "검사됐다")
            else:
                status = STATUS_YELLOW
                verdict = ("TFI_TIER_SPLIT_RANGE_ONLY: 범위 안이지만 등식은 못 걸었다 — "
                           "TFI 표 자신의 지급여력금액 행(item52)이 **이 버킷에서** 결측이다 "
                           "(TFI_TOTAL_ROW_ABSENT, parser 백필 대상). GREEN 으로 찍으면 "
                           "그 발주가 조용히 사라진다")
            findings.append(_finding(
                bucket, rule_e, status=status,
                expected=None if not collapsed else lo, actual=total,
                diff=None if not collapsed else total - lo,
                detail=("TFI_TOTAL_ROW_ABSENT(폴백): item52 결측이라 범위검사만 건다. "
                        f"min(item1_전, item1_후) ≤ item50_후 + item51_후 ≤ max(item1_전, item1_후) "
                        f"[{col}] — TFI 단독 합계는 경과조치 없음(={i1_pre:g})에서 TFI 효과만 "
                        f"더한 값이라 전체결합 적용후(={i1:g}) 를 넘을 수 없다. "
                        f"50={i50:g} + 51={i51:g} = {total:g}, 범위 [{lo:g}, {hi:g}] → {verdict}"),
            ))

        # --- 축 F: TFI 표 안에서 닫는 보완자본 구성 --------------------------
        # **축 B 와 같은 `_tier2_branch` 를 쓴다** (target_item=51). 재구현하지 않는 이유는
        # 위 함수 docstring 에 있다 — 두 축이 각자 갈래를 구현하면 같은 이름이 다른 뜻을 갖는다.
        rule_f = f"51_tfi_tier2_composition{sfx}"
        i47, i48, i49 = src.get(47), src.get(48), src.get(49)
        branch51, _exc51 = _tier2_branch(bucket, post, eff_tol, target_item=51)
        _tier2_composition_finding(
            bucket, findings, rule_f, branch51, 51, post, col, src,
            skip_tag="TFI_COMPOSITION_INPUT_MISSING",
            neither_tag="TFI_COMPOSITION_NEITHER",
            na_break_tag="TFI_COMPOSITION_TFI_NA_RECLASS_BREAK",
            na_missing_tag="TFI_COMPOSITION_TFI_NA_RECLASS_MISSING",
            same_table_note=("네 항목 전부 같은 표·같은 컬럼이라 두 표 사이 스코프 차이가 "
                             "개입할 수 없다"),
        )

        # --- 축 G: 기발행 자본증권 메모행 53/54 (census · 부호 · 포함관계) ------
        _validate_tfi_memo_rows(bucket, findings, eff_tol, post, col, src)


def _validate_tfi_memo_rows(
    bucket: QuarterBucket, findings: list[dict[str, Any]], eff_tol: float,
    post: bool, col: str, src: Mapping[int, float],
) -> None:
    """축 G — `53_tfi_memo_rows{sfx}`: 기발행 신종자본증권(53)·후순위채무(54).

    ## 왜 관계식이 아니라 census + 포함관계인가

    이 두 행은 **메모행**이다. `min(47,48)+49` 같은 항등식의 항이 아니다 —
    parser iter-10 이 전수로 쟀다: `item51 == min(47,48) + 49 + item54` 를 전 버킷에
    강제하면 **새로 닫힘 1건(NH농협 2025.4Q) · 새로 깨짐 214건**(현대해상 12분기 전부 ·
    한화생명 12분기 등, item47 이 이미 후순위채무를 포함해 보고되는 회사가 대다수).
    내(validation) 독립 재현도 같다: 450버킷 검사 · +54 로 새로 닫힘 1 · 새로 깨짐 218.
    **그래서 등식으로 승격하지 않는다.** NH농협 1버킷은 잔차 박제형 documented exception 이다.

    관계식이 없다고 무방비로 두지는 않는다. 걸 수 있는 것 셋:

    ### 1. census — TFI 표 본문(47/48/49)을 읽었으면 메모행도 읽었어야 한다

    **적용전 컬럼만** 센다. 적용후는 raw 상 컬럼 자체가 대부분 없다(parser iter-10 §3:
    관측 12개사 전부 메모행은 적용전 칸에만 인쇄, 유일 반례가 신한라이프 2023.1Q). 460버킷
    중 적용후에 53/54 가 있는 것은 60/59 뿐이라, 적용후에 census 를 걸면 376칸이 통째로 오탐이다.
    **적용후의 미러는 census 가 아니라 아래 2·3(부호·포함관계)** 이고 그건 실제로 적용후에서도 돈다.

    결측 사유는 셋인데 **색이 달라야 한다** — 셋을 한 색으로 찍으면 우리 backlog 가
    발행사 탓으로 박제된다:
      · 발행사가 라벨만 찍고 값을 안 넣음 → `_TFI_MEMO_ISSUER_BLANK` 등재분, SKIP.
        (대시 "-" 는 다르다 — 그건 0 으로 적재되므로 결측이 아니다.)
      · 로더의 텍스트 스캐너가 이 버킷 표를 못 읽음 → `_TFI_MEMO_TABLE_NOT_SCANNED`, SKIP.
      · **그 외 전부 RED.** 미등재 결측을 SKIP 하면 검증 무력화다.

    실측 RED 5칸(전부 raw 대조 확정, parser 발주):
      · 롯데손해 2026.1Q item53 — raw p22 는 `(기발행 신〮자본증권) 45,370` 을 인쇄한다.
        라벨이 `신종`이 아니라 `신〮`(U+302E 혼입)이라 로더 라벨매칭이 통과 못 했다.
      · 하나생명 2025.2Q item53 — raw p20 은 `-`(대시) 다. 0 이 정답인데 결측이다.
      · 동양생명 2024.1Q item53·54 — raw p14 `(기발행 신종자본증권) 344,567` /
        `(기발행 후순위채무) 0`. 둘 다 인쇄돼 있는데 둘 다 결측이다.
      · 푸본현대 2024.3Q item53·54 — raw p15 는 **적용전** 칸에 40,000 / 505,185 를 찍는데
        마스터는 적용전이 결측이고 적용후에 400.00 / 5,051.85 가 들어가 있다(컬럼 오배정).
      · 동양생명 2024.3Q item54 — raw p13 이 `(기발행 신종자본증권) 344,567` 에서 끝나
        후순위채무 행의 유무를 페이지 텍스트만으로 확정 못 했다. **확정 못 한 것을 공란으로
        등재하지 않는다** — 등재는 "확인했다"는 뜻이라, 여기선 RED 로 남겨 parser 에 넘긴다.

    ### 2. 부호 — 발행잔액은 음수일 수 없다

    실측 위반 0. 변이시험이 발화를 증명한다(`tests/test_tfi_memo_rows.py`).

    ### 3. 포함관계 `item53 + item54 ≤ item51` (같은 표·같은 컬럼)

    두 메모행은 TFI 로 인정범위가 넓어진 **기발행 자본증권 잔액**이고, 그 인정분이 들어가는
    자리가 같은 표의 보완자본(item51)이다. 실측: 적용전 420검사/1위반 · 적용후 58검사/1위반.
    두 위반 다 raw 로 결함임을 확인했다 —
      · 처브라이프 2023.1Q item54 = 840.06 인데 raw p6 는 두 메모행 다 `-`(대시)다.
        **원문에 없는 값**이다(그 페이지의 다른 숫자를 집었다). item51 = 704.65.
      · 농협생명 2024.3Q **적용후** 53=37,913.42 · 54=19,008.63 인데 raw p8 은 메모행을
        적용전 칸에만 250,000 / 939,171(=2,500.00 / 9,391.71) 로 인쇄한다. 적용후 값은
        원문에 존재하지 않는다.

    **더 좁은 후보 `53+54 ≤ item47` 은 원문으로 반증됐다** — DB생명 2025.2Q raw p19 가
    `보완자본 한도 적용 전 300,748` 과 `(기발행 후순위채무) 301,919` 를 그대로 인쇄한다
    (4분기 연속). 그래서 47 이 아니라 51 을 쓴다. `≤ item52`(지급여력금액)도 반증됐다 —
    푸본현대 2025.3Q 는 기본자본이 △619,866 이라 지급여력금액(387.08억)이 후순위채무
    잔액(3,522.10억)보다 작다. **자본잠식사를 카테고리로 단정하면 여기서 틀린다.**
    """
    rule_g = f"53_tfi_memo_rows{'_post' if post else ''}"
    key = (bucket.code, bucket.quarter)
    body = [i for i in TIER2_ITEMS if i in src]
    present = [i for i in TFI_MEMO_ITEMS if i in src]
    missing = [i for i in TFI_MEMO_ITEMS if i not in src]

    if len(body) < len(TIER2_ITEMS) and not present:
        findings.append(_finding(
            bucket, rule_g, status=STATUS_SKIP, expected=len(TFI_MEMO_ITEMS), actual=0,
            diff=None,
            detail=f"TFI_MEMO_NO_TABLE: [{col}] 47/48/49 가 다 있지 않고 53/54 도 없다 — "
                   "이 버킷에는 공통적용 경과조치 표 자체가 이 컬럼에 없다",
        ))
        return

    if missing:
        blanks = [i for i in missing if (bucket.code, bucket.quarter, i) in _TFI_MEMO_ISSUER_BLANK]
        if post:
            status, tag, why = STATUS_SKIP, "TFI_MEMO_POST_COLUMN_ABSENT", (
                "대다수 필링이 메모행을 적용전 칸에만 인쇄한다(관측 12개사, 유일 반례 "
                "신한라이프 2023.1Q). 적용후 결측을 RED 로 세면 376칸이 오탐이라 "
                "**적용후 census 는 안 건다** — 적용후 미러는 부호·포함관계로 돈다")
        elif set(blanks) == set(missing):
            status, tag, why = STATUS_SKIP, "TFI_MEMO_ISSUER_BLANK", (
                "발행사가 라벨만 찍고 값을 안 넣었다(raw 직접 판독 등재분). 대시와 다르다 — "
                "대시는 0 으로 적재된다. 0 으로 메우면 없는 값을 지어내는 것이다")
        elif not post and all(i in bucket.values_post for i in missing):
            # **컬럼 배치 변형** — 이 컬럼엔 없는데 반대 컬럼(적용후)엔 두 메모행이 다 있다.
            # 발행사가 메모행을 한 번만 인쇄하고, 그게 어느 컬럼에 실리는지가 필링마다 다르다.
            # 실측(2026-08-24 전수): 이 조건에 걸리는 버킷은 **푸본현대 2024.3Q 단 1개**이고
            # 그 회사의 다른 12분기는 모두 적용전 칸에 있다. parser 가 raw 를 dpi=400 으로
            # 확대해 확인한 결과 그 분기 **적용전 칸에는 대각선 취소선**이 그어져 있다
            # (적용후 컬럼 우측 앵커와 좌표가 거의 정확히 일치) — 발행사가 그 칸을 무효 표시한
            # 것이고, 값을 적용후에만 실은 것이 원문 그대로다. 취소선은 기계로 못 읽으므로
            # **"반대 컬럼에 값이 있다"** 를 대리 근거로 쓴다. 값을 지어내지도, 0 으로 메우지도
            # 않는다. 이 조건이 넓어지면(1개를 넘어서면) 그 자체가 조사 신호다.
            status, tag, why = STATUS_SKIP, "TFI_MEMO_COLUMN_VARIANT", (
                "이 컬럼엔 없고 적용후 컬럼에 두 행이 다 있다 — 발행사가 메모행을 한 번만 "
                "인쇄하고 컬럼 배치가 필링마다 다르다(실측 1버킷: 푸본현대 2024.3Q, 적용전 칸에 "
                "대각선 취소선). 결측이 아니라 배치 변형이다")
        elif key in _TFI_MEMO_TABLE_NOT_SCANNED:
            status, tag, why = STATUS_SKIP, "TFI_MEMO_TABLE_NOT_SCANNED", (
                "로더 텍스트 스캐너가 이 버킷 TFI 표를 못 읽었다(parser iter-10 §4 의 20버킷). "
                "47-51 은 과거 vision 백필로 들어와 있어 표를 읽은 것처럼 보이지만 메모행은 "
                "그 백필 스코프 밖이었다 — **우리 backlog** 이지 발행사 공란이 아니다")
        else:
            status, tag, why = STATUS_RED, "TFI_MEMO_ROW_MISSING", (
                "TFI 표 본문(47/48/49)은 읽었는데 같은 표의 메모행이 없다 — 행 유실이다. "
                "발행사 공란이면 raw 근거와 함께 `_TFI_MEMO_ISSUER_BLANK` 에 등재하라. "
                "확인 못 한 결측을 SKIP 으로 내리는 것이 검증 무력화다")
        labels = ", ".join(f"item{i}{_TFI_MEMO_ITEM_LABEL[i]}" for i in missing)
        findings.append(_finding(
            bucket, rule_g, status=status,
            expected=len(TFI_MEMO_ITEMS), actual=len(present), diff=None,
            detail=f"{tag}: [{col}] {labels} 결측 (본문 47/48/49 = {body}) — {why}",
        ))
        return

    i53, i54 = src[53], src[54]
    neg = [i for i in TFI_MEMO_ITEMS if src[i] < -eff_tol]
    if neg:
        findings.append(_finding(
            bucket, rule_g, status=STATUS_RED, expected=None,
            actual=min(src[i] for i in neg), diff=None,
            detail=f"TFI_MEMO_NEGATIVE: [{col}] "
                   + " · ".join(f"item{i}={src[i]:g}" for i in neg)
                   + " — 기발행 자본증권 **잔액**이라 음수일 수 없다",
        ))
        return

    i51 = src.get(51)
    if i51 is None:
        findings.append(_finding(
            bucket, rule_g, status=STATUS_SKIP, expected=None, actual=i53 + i54, diff=None,
            detail=f"TFI_MEMO_PARENT_MISSING: [{col}] 부모행 item51(보완자본) 결측이라 "
                   "포함관계를 검산할 대상이 없다 (폴백 금지)",
        ))
        return

    over = (i53 + i54) - i51
    if over > eff_tol:
        findings.append(_finding(
            bucket, rule_g, status=STATUS_RED, expected=i51, actual=i53 + i54, diff=over,
            detail=(f"TFI_MEMO_EXCEEDS_TIER2: [{col}] item53({i53:g}) + item54({i54:g}) = "
                    f"{i53 + i54:g} > item51(보완자본, 같은 표·같은 컬럼) {i51:g} — 초과 {over:g}. "
                    "TFI 로 인정범위가 넓어진 기발행 자본증권 잔액이 그 인정분이 들어가는 "
                    "보완자본보다 클 수 없다. 실측 적용전 420검사/1위반 · 적용후 58검사/1위반이고 "
                    "두 위반 다 raw 로 결함 확정(처브라이프 2023.1Q 는 원문이 대시 · "
                    "농협생명 2024.3Q 적용후는 원문에 그 컬럼이 없다)"),
        ))
        return

    findings.append(_finding(
        bucket, rule_g, status=STATUS_GREEN, expected=i51, actual=i53 + i54, diff=over,
        detail=(f"53/54 census OK · 부호 OK · item53({i53:g}) + item54({i54:g}) ≤ "
                f"item51({i51:g}) [{col}]. 관계식(등식)은 걸지 않는다 — "
                "`item51 == min(47,48)+49+item54` 는 전사 공식이 아니다"
                "(전수 시뮬: 새로 닫힘 1 · 새로 깨짐 218)"),
    ))


def _tier2_cross_bucket_context(
    buckets: list["QuarterBucket"], tolerance: float,
    tfi_applicability: Optional[Mapping[tuple[str, str], str]] = None,
) -> tuple[frozenset, frozenset, frozenset]:
    """버킷 하나만 봐서는 못 잡는 세 가지를 미리 계산한다.

    1. `tier2_seen_codes` — 47/48/49 표를 **한 분기라도** 공시한 회사 코드. 2026-08-22 까지는
       이것이 RED/SKIP 의 **판정 근거**였는데 그게 틀렸다(TFI 는 분기마다 꺼졌다 켜진다).
       지금은 판정에서 빠지고 **triage 힌트**로만 쓴다 — 적용여부가 UNKNOWN 인 버킷에서
       "다른 분기엔 있다"는 parser 우선순위 신호이기 때문이다.
    2. `tier2_stale_limit` — item48 이 당분기 `item14×50%` 와는 어긋나는데 **직전분기**
       `item14×50%` 와는 맞는 (회사, 분기). 전기 값 잔존(stale copy) 지문이다.
       분기 순서는 `YYYY.nQ` 문자열에서 (연도, 분기) 로 파싱해 정렬한다.
    3. `tier2_x_present_codes` — **TFI=X 인데도 47/48/49 를 인쇄하는** 회사 코드.
       TFI=X 를 정상 부재의 근거로 쓰려면 그 회사에서 X 가 실제로 표를 없애는지 확인해야
       한다. 전수 실측으로 그렇지 않은 발행사가 있다(하나손해: 13분기 전부 X 인데 12분기가
       표를 인쇄 — "해당사항 없음" 문장 뒤에 적용전 컬럼만 채운 표를 그린다). 그런 회사에서는
       X 가 부재를 설명하지 못하므로 SKIP 대신 review 로 내린다.
    """
    seen: set[str] = set()
    x_present: set[str] = set()
    by_code: dict[str, list[QuarterBucket]] = {}
    for b in buckets:
        if any(i in b.values for i in TIER2_ITEMS):
            seen.add(b.code)
            if tfi_applicability is not None and (
                tfi_applicability.get((b.code, b.quarter)) == "X"
            ):
                x_present.add(b.code)
        by_code.setdefault(b.code, []).append(b)

    def _qkey(q: str) -> tuple[int, int]:
        try:
            year, part = q.split(".")
            return int(year), int(part[0])
        except (ValueError, IndexError):
            return (0, 0)

    # 적용전·적용후를 **각각** 판정한다. 한 컬럼만 보면 다른 컬럼의 전기 잔존이 그대로 통과한다
    # (이 저장소의 반복 사고형태). 적용후 한도의 분모도 `item14_적용전` 이다 — 실측 215:0.
    stale: set[tuple[str, str, bool]] = set()
    for code, bs in by_code.items():
        bs = sorted(bs, key=lambda b: _qkey(b.quarter))
        for prev, cur in zip(bs, bs[1:]):
            i14_cur, i14_prev = cur.values.get(14), prev.values.get(14)
            if i14_cur is None or i14_prev is None:
                continue
            if abs(i14_cur - i14_prev) <= tolerance:
                continue  # SCR 이 사실상 안 변했으면 구분이 불가능하다 — 판정하지 않는다
            for is_post in (False, True):
                src = cur.values_post if is_post else cur.values
                i48 = src.get(48)
                if i48 is None:
                    continue
                if (abs(i48 - i14_cur * TIER2_LIMIT_RATIO) > tolerance
                        and abs(i48 - i14_prev * TIER2_LIMIT_RATIO) <= tolerance):
                    stale.add((cur.code, cur.quarter, is_post))
    return frozenset(seen), frozenset(stale), frozenset(x_present)


def _validate_bucket(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    tolerance: float,
    source_has_breakdown: Optional[frozenset],
    tier2_seen_codes: Optional[frozenset] = None,
    tier2_stale_limit: Optional[frozenset] = None,
    tfi_applicability: Optional[Mapping[tuple[str, str], str]] = None,
    tier2_x_present_codes: Optional[frozenset] = None,
) -> None:
    """Apply all 14 rules to one (company, quarter) bucket, appending to `findings`.

    Split verbatim out of run_validation's per-bucket loop 2026-07-22; behaviour
    pinned by tests/test_kics_rules_golden.py."""
    eff_tol = (
        IMAGE_OCR_TOLERANCE
        if bucket.code in IMAGE_OCR_COMPANIES
        else tolerance
    )
    if all(bucket.get(i) is not None for i in (1, 2, 3)):
        expected = (bucket.get(2) or 0) + (bucket.get(3) or 0)
        findings.append(_check_numeric(bucket, "1", expected, bucket.get(1), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "1",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(1),
                diff=None,
                detail="missing items 1-3",
            )
        )

    if bucket.get(4) is not None:
        expected = _sum_optional(bucket, range(5, 12))
        findings.append(_check_numeric(bucket, "2", expected, bucket.get(4), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "2",
                status=STATUS_RED,
                expected=None,
                actual=None,
                diff=None,
                detail="missing item4",
            )
        )

    findings.append(
        _finding(
            bucket,
            "3",
            status=STATUS_SKIP,
            expected=None,
            actual=bucket.get(1),
            diff=None,
            detail="deferred: item4-item12+item13 bridge unreliable vs disclosure; rule 1 is authoritative for item1",
        )
    )

    if all(bucket.get(i) is not None for i in (15, 17, 18, 19, 20, 21)):
        v = np.array(
            [bucket.get(17), bucket.get(18), bucket.get(19), bucket.get(20)],
            dtype=float,
        )
        expected = _diversified_sqrt(v, R4) + float(bucket.get(21))
        findings.append(_check_numeric(bucket, "4", expected, bucket.get(15), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "4",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(15),
                diff=None,
                detail="missing items for R4 (15,17-21)",
            )
        )

    if all(bucket.get(i) is not None for i in (14, 15, 22)):
        item23 = bucket.get(23)
        if item23 is None:
            item23 = 0.0
        expected = (bucket.get(15) or 0) - (bucket.get(22) or 0) + item23
        findings.append(_check_numeric(bucket, "5", expected, bucket.get(14), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "5",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(14),
                diff=None,
                detail="missing items 14,15,22",
            )
        )

    if all(bucket.get(i) is not None for i in (15, 16, 17, 18, 19, 20, 21)):
        expected = (
            (bucket.get(17) or 0)
            + (bucket.get(18) or 0)
            + (bucket.get(19) or 0)
            + (bucket.get(20) or 0)
            + (bucket.get(21) or 0)
            - (bucket.get(15) or 0)
        )
        findings.append(_check_numeric(bucket, "6", expected, bucket.get(16), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "6",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(16),
                diff=None,
                detail="missing items for rule 6",
            )
        )

    if all(bucket.get(i) is not None for i in (1, 14, 27)) and bucket.get(14) != 0:
        expected = (bucket.get(1) or 0) / (bucket.get(14) or 1) * 100.0
        # ratio rule: integer-rounding of a tiny denominator (item14) swings the
        # recomputed ratio hugely (카카오페이손해 2023.4Q item14=20억 → ±~120%p),
        # while the disclosed item27 is exact. dynamic tol mirrors 8_life: propagate
        # ±0.5 rounding on denom (expected×0.5/|denom|) + num (50/|denom|). Negligible
        # for normal denominators; only loosens for sub-scale ones.
        d14 = abs(bucket.get(14))
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / d14 + 50.0 / d14)
        findings.append(_check_numeric(bucket, "7", expected, bucket.get(27), ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "7",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(27),
                diff=None,
                detail="missing items 1,14,27 or item14=0",
            )
        )

    if all(bucket.get(i) is not None for i in (2, 14, 28)) and bucket.get(14) != 0:
        expected = (bucket.get(2) or 0) / (bucket.get(14) or 1) * 100.0
        # same sub-scale denominator rounding as rule 7 (see note above).
        d14 = abs(bucket.get(14))
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / d14 + 50.0 / d14)
        findings.append(_check_numeric(bucket, "8", expected, bucket.get(28), ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(28),
                diff=None,
                detail="missing items 2,14,28 or item14=0",
            )
        )

    _validate_transition_basic(bucket, findings, eff_tol)

    _validate_market_irr(bucket, findings, source_has_breakdown, eff_tol)

    _validate_transition_capital(bucket, findings, eff_tol)

    _validate_tier2_limit(bucket, findings, eff_tol,
                          tier2_seen_codes, tier2_stale_limit,
                          tfi_applicability, tier2_x_present_codes)

    _validate_tfi_tier_rows(bucket, findings, eff_tol)


def run_validation(
    records: Iterable[Mapping[str, Any]], *, tolerance: float = 2.0,
    source_has_breakdown: Optional[frozenset] = None,
    tfi_applicability: Optional[Mapping[tuple[str, str], str]] = None,
) -> dict[str, Any]:
    """`tfi_applicability` = (원보험사코드, 공시분기) -> 'O'|'X'|'NA'|'UNKNOWN'.

    `47_tier2_census` 가 47/48/49 **전부 부재**를 판정할 때 쓰는 유일한 근거다. 룰엔진은
    파일 I/O 를 하지 않으므로(순수 함수라야 골든이 성립한다) 호출자가 실어 준다 —
    게이트는 `validate_kics_disclosure._load_tfi_applicability()`, 골든·매니페스트 테스트도
    **같은 로더**를 쓴다. "게이트가 검사하는 것 = 테스트가 검사하는 것" 을 깨지 않기 위해서다.

    **None(또는 키 없음)은 통과가 아니다.** 근거가 없으면 부재를 정상이라고 말할 수 없으므로
    review(YELLOW)로 내려간다 — 사이드카가 사라지면 RED 가 조용히 0 이 되는 게 아니라
    review 카운트가 튄다."""
    buckets = _group_records(records)
    findings: list[dict[str, Any]] = []
    tier2_seen_codes, tier2_stale_limit, tier2_x_present_codes = (
        _tier2_cross_bucket_context(buckets, tolerance, tfi_applicability)
    )

    for bucket in buckets:
        _validate_bucket(bucket, findings, tolerance, source_has_breakdown,
                         tier2_seen_codes, tier2_stale_limit,
                         tfi_applicability, tier2_x_present_codes)

    summary_status: dict[str, int] = {
        STATUS_YELLOW: 0,
        STATUS_GREEN: 0,
        STATUS_SKIP: 0,
        STATUS_ERROR: 0,
    }
    by_rule: dict[str, dict[str, int]] = {}
    for f in findings:
        st = f.get("status", STATUS_ERROR)
        summary_status[st] = summary_status.get(st, 0) + 1
        rid = str(f.get("rule"))
        by_rule.setdefault(rid, {})
        by_rule[rid][st] = by_rule[rid].get(st, 0) + 1

    return {
        "summary": {
            "buckets": len(buckets),
            "findings": len(findings),
            "by_status": summary_status,
            "by_rule": by_rule,
            "tolerance": tolerance,
        },
        "findings": findings,
    }
