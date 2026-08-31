# -*- coding: utf-8 -*-
"""Patch data/_gold/user_csm_cells.json: fill `why` for the 44 provenance-less
gold overrides named in inbox/parser/20260825T2200Z (KR0079 27, KR0003 12,
KR0072 5). Values (값/was) are NEVER touched -- only `why` is added/set.
Matched by exact list-index captured from a fresh census run just before this
script (see scripts/_probes/probe_20260830_gold_provenance_census2.py output).
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "data/_gold/user_csm_cells.json"

WHY_KR0072_2023_1Q = (
    "raw 재확인(rcept 20230515002450, 1분기보고서). 2026-08-29 71st pass(commit 9a067dd)가 "
    "viz_build_csm_waterfall.py::extract_stages()의 null-흡수 버그(라벨매칭 실패 시 항목5가 "
    "None으로 남고 항목4 잔차식의 `... or 0`이 그걸 통째로 삼킴)를 고친 뒤, 현재 코드로 "
    "waterfall_for_dir()를 재실행(read-only)하면 원수 일반모형 CSM 측정요소표(combined-agn "
    "블록)에서 항목4=-833.3, 항목5=-111.2, 항목6=4727.2(억원)를 독립적으로 재현 — gold 값과 "
    "반올림오차(≤0.05) 내 완전 일치. 재현: scripts/_probes/probe_20260830_waterfall_recompute.py."
)
WHY_KR0072_2023_2Q = (
    "raw 재확인(rcept 20230814003052, 반기보고서). 위 2023.1Q와 동일 근거 — 현재(수정후) "
    "waterfall_for_dir()가 combined-agn 블록에서 항목4=-685.5, 항목5=-234.2(억원)를 독립 재현, "
    "gold 값(-685.55/-234.15)과 반올림오차(≤0.05) 내 일치. "
    "재현: scripts/_probes/probe_20260830_waterfall_recompute.py."
)

WHY_KR0079_2023_1Q = (
    "raw 직접 재구성(rcept 20230515002900, 1분기보고서, 노트 '14.보험계약 및 재보험계약'). "
    "자동추출기(extract_measurement_tables)가 이 표를 못 찾음(score 3 < threshold 5 — 상품별 "
    "로마숫자 캡션 표라 표준 CSM 측정요소 헤더 패턴과 불일치) → waterfall_for_dir()는 "
    "src=None(추출 완전 실패)이라 was=ROW_ABSENT였음. 원문엔 상품별(i)사망/ii)건강/iii)연금/"
    "iv)저축/v)기타) 5개 SEPARATE 블록(라인 15088/15755/16425/17092/17756)이 실재 — 각 블록 "
    "'당분기' 섹션의 '보험계약마진' 소계열(기초잔액/처음인식한계약의효과/당기손익인식보험금융손익/"
    "보험계약마진을조정하는변동/보험계약마진의당기인식분/기말잔액)을 5상품 합산한 결과: "
    "항목1=19794.95, 항목2=572.47, 항목3=116.00, 항목4=105.29(gold 105.28, 백만원 반올림 0.01 "
    "오차), 항목5=-520.14, 항목6=20068.56(억원) — gold와 사실상 완전 일치. "
    "재현: scripts/_probes/probe_20260830_kr0079_2023q1_sum5.py."
)

WHY_KR0079_2025_2Q_OK = (
    "raw 재확인(rcept 20250814003532, 반기보고서). 상품별 WIDE 표(사망/건강/연금/저축/기타 "
    "열그룹, header '계약의 유형' 확인)를 직접 5상품 합산한 값과 현재 코드(waterfall_for_dir, "
    "combined-agn 블록) 재계산 값이 모두 항목1=20782.12, 항목2=2451.95, 항목3=295.77, "
    "항목6=21852.27(억원)로 일치 — gold와 완전 일치(오차 0). was(20782.1/2451.9/295.8/21852.3)는 "
    "같은 값을 소수 1자리로 반올림한 것일 뿐 실제 값 차이 아님. 항목1=20782.12는 "
    "inbox/parser/20260825T2200Z §1이 이미 3중교차검증(FY2024.4Q 5블록합=2,078,212백만원="
    "FY2025.1Q기초=FY2025.2Q WIDE표 리터럴)한 바로 그 값과 동일. "
    "재현: scripts/_probes/probe_20260830_wide_product_sum.py."
)

WHY_KR0079_2025_2Q_MYSTERY = (
    "출처 불명, 재확인 필요 — 원문(rcept 20250814003532) WIDE 표를 직접 수동 재구성했으나 gold와 "
    "불일치. 원문 row '보험계약마진을 조정하는 변동'(항목4 해당) 5상품 CSM소계 합산 = -685.50억, "
    "row '보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진'(항목5=CSM상각 해당) 5상품 "
    "합산 = -992.07억(=-99,207,397,518원 — inbox/parser/20260825T2200Z가 'PL쪽 992.07(소수 6자리) "
    "파생값이라 원천 미확정'이라 적은 바로 그 수치. 실은 파생값이 아니라 CSM 측정요소표 원문의 "
    "직접값이었음, 다만 CSM 항목이 아니라 항목5 자체가 맞는지는 아래 참조). gold(항목4=-886.27, "
    "항목5=-791.3)와 각각 200.77억 어긋나되 부호가 반대(항목4는 +200.77, 항목5는 -200.77) — 두 "
    "항목의 합계는 raw(-1677.57)=was(-1677.6, 구코드 잔차흡수값)=gold(-886.27-791.3=-1677.57)로 "
    "동일해 폐쇄식(항목6=Σ항목1~5) 자체는 안 깨짐. 즉 gold는 '항목4/항목5 사이의 배분'만 raw 원문과 "
    "다르고 두 항목의 합계는 맞다 — 배분 오류 가능성이 있으나 이 티켓은 값 변경을 금지하므로 수정"
    "안 함(validation 재확인 필요). 같은 회사 2025.3Q·2026.1Q는 동일 방법으로 raw와 gold가 정확히 "
    "일치(아래 항목 참조) — 2025.2Q만 이례적으로 배분이 어긋남. "
    "재현: scripts/_probes/probe_20260830_wide_product_sum.py."
)

WHY_KR0079_2025_3Q = (
    "raw 직접 재구성(rcept 20251114002791, 3분기보고서). 상품별 WIDE 표 5상품 CSM소계 합산 — "
    "항목1=20782.12, 항목2=3962.89, 항목3=448.69, 항목4=-333.17, 항목5=-1531.21, "
    "항목6=23329.32(억원) — gold 값과 완전 일치(오차 0). 코드(waterfall_for_dir, "
    "src=wide-product)는 이 표는 찾지만 항목5(CSM상각) 행 라벨 매칭에 실패해 None을 반환하고, "
    "잔차식(build_csm_waterfall_master.py L1198 `... or 0`)이 항목5를 통째로 항목4에 흡수 "
    "(was=-1864.4 ≈ raw 항목4+항목5 = -333.17-1531.21 = -1864.38) — gold가 정답, was가 "
    "null-흡수 버그값. 재현: scripts/_probes/probe_20260830_wide_product_sum.py."
)

WHY_KR0079_2025_4Q = (
    "raw 직접 재구성(rcept 20260318001664, 사업보고서/연차). 상품별 WIDE 표 5상품 CSM소계 합산 — "
    "항목1=20782.12, 항목2=5398.78, 항목3=606.58, 항목4=-4144.94, 항목5=-2058.31, "
    "항목6=20584.23(억원) — gold 값과 완전 일치(오차 0). was(20775.6/5360.6/606.4/-4134.2/"
    "-2056.2/20552.3)는 현재 코드가 그대로 재현하는 값으로, pick_combined_agnostic()이 5번째 "
    "'기타' 상품 블록을 합산에서 누락시킨 결과(inbox/parser/20260825T2200Z §1이 지목한 바로 그 "
    "미해결 버그 — 항목1의 잔차 +6.52억이 '기타'의 기말잔액 몫). WIDE 표 직접 합산은 그 누락이 "
    "없어 6항목 전부 gold와 정확히 일치 — gold가 정답, was가 버그값. "
    "재현: scripts/_probes/probe_20260830_wide_product_sum.py."
)

WHY_KR0079_2026_1Q = (
    "raw 직접 재구성(rcept 20260529001897, 1분기보고서). 상품별 WIDE 표 5상품 CSM소계 합산 — "
    "항목1=20584.23, 항목4=-174.32, 항목5=-537.11(억원) — gold 값과 완전 일치(오차 0). 코드"
    "(waterfall_for_dir, src=wide-product)는 항목5(CSM상각) 라벨 매칭에 실패해 None, 잔차식이 "
    "통째로 항목4에 흡수(was=-711.4 ≈ raw 항목4+항목5 = -174.32-537.11 = -711.43) — gold가 "
    "정답, was가 null-흡수 버그값. 2025.3Q와 동일 결함 패턴. "
    "재현: scripts/_probes/probe_20260830_wide_product_sum.py."
)

WHY_KR0003_2023_1Q_ITEM1 = (
    "raw 교차확인 — 2023.1Q 자체 필링(rcept 20230515002687)엔 CSM 측정요소 노트가 없음(전체 "
    "162개 표 전수 스코어링 결과 '보험계약마진'/'측정요소'/'이행현금흐름'/'위험조정' 매칭 0건 — "
    "자동추출 실패가 아니라 이 필링 자체에 표가 없는 것으로 판단됨, K-IFRS 1분기보고서 특성). "
    "다만 항목1(기초 CSM)은 FY 내 상수이므로 2023.4Q(연차, rcept 20240321001822) 필링이 "
    "독립적으로 보고하는 FY2023 기초(=anchor)와 대조 가능 — 그 값이 16774.4로 gold(16774.38)와 "
    "일치(반올림오차 0.02). 항목2~6은 이 방법으로 확인 불가(아래 해당 항목 참조)."
)
WHY_KR0003_2023_1Q_REST = (
    "출처 불명, 재확인 필요 — 2023.1Q 필링(rcept 20230515002687)에 CSM 측정요소 노트 자체가 "
    "없음(전체 162개 표 스코어링 매칭 0건, 자동추출기 결함이 아니라 원문 미공시로 판단). gold "
    "row는 내부적으로는 완전히 닫힘(항목6=Σ항목1~5, 16774.38+1553.18+174.43-681.62-392.84="
    "17427.53 검산 일치)이고 항목1은 별도 확인됨(위 항목1 why 참조)이나, 항목2~6 자체가 어느 "
    "필링·어느 표에서 왔는지는 특정 못함. KR0003 2023.2Q(아래)가 '1년 뒤 필링의 전기 비교열'에서 "
    "복원됐던 것과 같은 재작성(restatement) 패턴일 가능성이 있으나, Q1 단독 비교열은 통상 반기/"
    "9개월 노트에 존재하지 않아 동일 방법을 적용할 수 없었음."
)

WHY_KR0003_2023_2Q = (
    "raw 확인 — 2023.2Q 자체 필링(rcept 20230814002928)의 '<제79(당)기 반기>' 표 자체 값"
    "(was: 18004.6/2651.0/377.9/-556.7/-843.4/19633.5)은 현재 코드가 그대로 재현하지만, 이후 "
    "재작성(restate)된 것으로 보임: **1년 뒤 반기보고서인 2024.2Q(rcept 20240814002875)가 비교열 "
    "'<제79(전)기 반기>'로 보고하는 복원값**이 gold와 완전 일치 — 항목1=16774.38, 항목2=2654.34, "
    "항목3=358.76, 항목4=-361.99(=항목6-(1+2+3+5) 검산 일치), 항목5=-807.85, "
    "항목6=18617.64(억원), 오차 0. 즉 gold는 원 필링이 아니라 '차기 반기보고서의 전기 비교 "
    "재작성치'를 채택한 것 — 2023.2Q 원 필링(기초 18004.63)과 2023.4Q 연차 필링(기초 16774.4)의 "
    "기초 CSM 불일치가 그 사이 정정/재작성됐고, gold가 최신(재작성 후) 수치를 우선 채택. "
    "재현: scripts/_probes/probe_20260830_kr0003_2024q2_prior_half.py."
)

# idx -> why text, keyed by the exact list-index from the fresh census run
PATCH = {}
for i in (12, 16):
    PATCH[i] = WHY_KR0072_2023_1Q
PATCH[14] = WHY_KR0072_2023_1Q
for i in (13, 15):
    PATCH[i] = WHY_KR0072_2023_2Q

for i in (17, 22, 26, 30, 35, 40):
    PATCH[i] = WHY_KR0079_2023_1Q
for i in (18, 23, 27, 41):
    PATCH[i] = WHY_KR0079_2025_2Q_OK
for i in (31, 36):
    PATCH[i] = WHY_KR0079_2025_2Q_MYSTERY
for i in (19, 24, 28, 32, 37, 42):
    PATCH[i] = WHY_KR0079_2025_3Q
for i in (20, 25, 29, 33, 38, 43):
    PATCH[i] = WHY_KR0079_2025_4Q
for i in (21, 34, 39):
    PATCH[i] = WHY_KR0079_2026_1Q

PATCH[0] = WHY_KR0003_2023_1Q_ITEM1
for i in (2, 4, 6, 8, 10):
    PATCH[i] = WHY_KR0003_2023_1Q_REST
for i in (1, 3, 5, 7, 9, 11):
    PATCH[i] = WHY_KR0003_2023_2Q

assert len(PATCH) == 44, f"expected 44 patched cells, got {len(PATCH)}"

# ---- apply, with strict pre-checks (code/item/quarter/값/was must be unchanged) ----
EXPECTED = {
    17: ("KR0079", 1, "2023.1Q", 19794.95, "ROW_ABSENT"),
    22: ("KR0079", 2, "2023.1Q", 572.47, "ROW_ABSENT"),
    26: ("KR0079", 3, "2023.1Q", 116.0, "ROW_ABSENT"),
    30: ("KR0079", 4, "2023.1Q", 105.28, "ROW_ABSENT"),
    35: ("KR0079", 5, "2023.1Q", -520.14, "ROW_ABSENT"),
    40: ("KR0079", 6, "2023.1Q", 20068.56, "ROW_ABSENT"),
    18: ("KR0079", 1, "2025.2Q", 20782.12, 20782.1),
    23: ("KR0079", 2, "2025.2Q", 2451.95, 2451.9),
    27: ("KR0079", 3, "2025.2Q", 295.77, 295.8),
    31: ("KR0079", 4, "2025.2Q", -886.27, -1677.6),
    36: ("KR0079", 5, "2025.2Q", -791.3, None),
    41: ("KR0079", 6, "2025.2Q", 21852.27, 21852.3),
    19: ("KR0079", 1, "2025.3Q", 20782.12, 20782.1),
    24: ("KR0079", 2, "2025.3Q", 3962.89, 3962.9),
    28: ("KR0079", 3, "2025.3Q", 448.69, 448.7),
    32: ("KR0079", 4, "2025.3Q", -333.17, -1864.4),
    37: ("KR0079", 5, "2025.3Q", -1531.21, None),
    42: ("KR0079", 6, "2025.3Q", 23329.32, 23329.3),
    20: ("KR0079", 1, "2025.4Q", 20782.12, 20775.6),
    25: ("KR0079", 2, "2025.4Q", 5398.78, 5360.6),
    29: ("KR0079", 3, "2025.4Q", 606.58, 606.4),
    33: ("KR0079", 4, "2025.4Q", -4144.94, -4134.2),
    38: ("KR0079", 5, "2025.4Q", -2058.31, -2056.2),
    43: ("KR0079", 6, "2025.4Q", 20584.23, 20552.3),
    21: ("KR0079", 1, "2026.1Q", 20584.23, 20584.2),
    34: ("KR0079", 4, "2026.1Q", -174.32, -711.4),
    39: ("KR0079", 5, "2026.1Q", -537.11, None),
    0: ("KR0003", 1, "2023.1Q", 16774.38, "ROW_ABSENT"),
    2: ("KR0003", 2, "2023.1Q", 1553.18, "ROW_ABSENT"),
    4: ("KR0003", 3, "2023.1Q", 174.43, "ROW_ABSENT"),
    6: ("KR0003", 4, "2023.1Q", -681.62, "ROW_ABSENT"),
    8: ("KR0003", 5, "2023.1Q", -392.84, "ROW_ABSENT"),
    10: ("KR0003", 6, "2023.1Q", 17427.53, "ROW_ABSENT"),
    1: ("KR0003", 1, "2023.2Q", 16774.38, 18004.6),
    3: ("KR0003", 2, "2023.2Q", 2654.34, 2651.0),
    5: ("KR0003", 3, "2023.2Q", 358.76, 377.9),
    7: ("KR0003", 4, "2023.2Q", -361.99, -556.7),
    9: ("KR0003", 5, "2023.2Q", -807.85, -843.4),
    11: ("KR0003", 6, "2023.2Q", 18617.64, 19633.5),
    12: ("KR0072", 4, "2023.1Q", -833.3, -944.6),
    14: ("KR0072", 5, "2023.1Q", -111.25, None),
    16: ("KR0072", 6, "2023.1Q", 4727.25, 4727.2),
    13: ("KR0072", 4, "2023.2Q", -685.55, -685.5),
    15: ("KR0072", 5, "2023.2Q", -234.15, -234.2),
}
assert set(EXPECTED) == set(PATCH), "index set mismatch between EXPECTED and PATCH"

raw = GOLD_PATH.read_text(encoding="utf-8")
d = json.loads(raw)
s = d["set"]

for idx, exp in EXPECTED.items():
    e = s[idx]
    got = (e.get("원보험사코드"), e.get("항목번호"), e.get("공시분기"), e.get("값"), e.get("was"))
    if got != exp:
        raise SystemExit(f"MISMATCH at idx={idx}: expected {exp}, got {got} -- ABORTING, no write")
    cur_why = (e.get("why") or "").strip()
    cur_note = (e.get("note") or "").strip()
    if cur_why or cur_note:
        raise SystemExit(f"idx={idx} already has why/note set -- ABORTING, no write")

print(f"Pre-check OK: all {len(EXPECTED)} target cells verified (code/item/quarter/값/was unchanged, why/note still empty).")

for idx, why_text in PATCH.items():
    s[idx]["why"] = why_text

GOLD_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {GOLD_PATH} with {len(PATCH)} `why` fields filled.")
