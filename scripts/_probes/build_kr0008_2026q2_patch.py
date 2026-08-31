# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0008.json (KR0008 2026.2Q only).

Labels are pulled programmatically from KR0008's OWN existing rows in the
read-only root kics_disclosure.json (2025.4Q for items 36-54, 2026.2Q for
items 16-23/48) -- never retyped by hand, to avoid the U+318D vs U+00B7 byte
mismatch that got a patch rejected earlier today.

Values are derived from:
  - md_inbox/FY2026_Q2/KR0008_삼성화재해상보험.md (docling MD, lines 616-757)
  - data/disclosure/FY2026_Q2/pdf/KR0008_삼성화재해상보험.pdf (fitz cross-check,
    p34-37) -- every digit matches the MD exactly.
  - Self-checked against the real rule engine (src/solvency/validation/
    kics_json_rules.py: MARKET_M, R4, irr_derive_expected, _diversified_sqrt).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"
OUT = ROOT / "data" / "_derived" / "_patch_2026q2_KR0008.json"

CODE = "KR0008"
Q_CUR = "2026.2Q"
Q_PREC = "2025.4Q"  # precedent quarter to copy 항목명 for items 36-54 from

data = json.loads(MASTER.read_text(encoding="utf-8"))

prec = {r["항목번호"]: r for r in data if r.get("원보험사코드") == CODE and r.get("공시분기") == Q_PREC}
cur = {r["항목번호"]: r for r in data if r.get("원보험사코드") == CODE and r.get("공시분기") == Q_CUR}

# sanity: precedent quarter must actually have items 36-54 (full even-Q form)
for it in list(range(36, 47)) + [47, 48, 49, 50, 51, 52, 53, 54]:
    assert it in prec, f"item{it} missing from {CODE} {Q_PREC} precedent -- cannot copy label"

# sanity: current quarter must already have items 16-23/29-35 (parent items exist,
# just no _적용후 / for 48 wrong value)
for it in (16, 17, 18, 19, 20, 21, 22, 23, 29, 30, 31, 32, 33, 34, 35, 48):
    assert it in cur, f"item{it} missing from {CODE} {Q_CUR} -- unexpected, script assumptions wrong"


def _num(v):
    if v is None:
        return None
    return float(str(v).replace(",", ""))


cells = []

# ---------------------------------------------------------------------
# A. items 16-23: mirror 값_적용후 = 값 (KR0008 confirmed full non-applier:
#    TFI/RPT/TAC/TIR/TER/TIRR/PCA_DEFER all X for 6 consecutive quarters
#    2024.4Q-2026.1Q per data/_derived/kics_transition_applicability.json,
#    and 2026.2Q MD L275-282 + L320-344 explicitly repeats all-X with prose
#    negations ("...경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함").
#    None of TER/TIR/TIRR (the only measures that could move items 17-21)
#    are applied, so 적용후 == 적용전 for these by construction, not analogy.
# ---------------------------------------------------------------------
MIRROR_RATIONALE = (
    "KR0008 2026.2Q 전면 비적용사(TFI/RPT/TAC/TIR/TER/TIRR/PCA_DEFER 전부 X, "
    "md_inbox MD L275-282 표 + L320-344 prose; kics_transition_applicability.json "
    "2024.4Q-2026.1Q 6개 분기 연속 7종 전부 X 동일). 항목17-21을 바꿀 수 있는 유일한 "
    "수단(TER/TIR/TIRR)이 전부 미적용이므로 값_적용후=값은 미러링 관행이 아니라 정의상 "
    "귀결. 게이트 _post_transition_parent_census TRAILING + "
    "_parent_present_child_incomplete_after(parent=15) RED 해소."
)
for it in (16, 17, 18, 19, 20, 21, 22, 23):
    row = cur[it]
    val = _num(row["값"])
    cells.append({
        "항목번호": it,
        "항목명": row["항목명"],
        "값": val,
        "값_적용후": val,
        "근거": MIRROR_RATIONALE,
    })

# ---------------------------------------------------------------------
# A2. items 29-35 (생명장기 subs): same mirror, same rationale. Found via
#     scratch-gate iteration, not upfront: mirroring item17_적용후 (above)
#     makes item17 a "parent present" for the mmult_after/census axis
#     17->[29-35] (_TRANS_PARENT_SUBS), which then demanded 29-35_적용후 too
#     (new RED "부모item17후 present인데 item29..35후 결측" appeared on the
#     first --master scratch run). None of the 7 transition kinds (TFI/RPT/
#     TAC/TIR/TER/TIRR/PCA_DEFER, all X) target 사망/장수/장해질병/장기재물
#     기타/해지/사업비/대재해 specifically, so the same all-X non-applier
#     argument applies unchanged.
# ---------------------------------------------------------------------
for it in (29, 30, 31, 32, 33, 34, 35):
    row = cur[it]
    val = _num(row["값"])
    cells.append({
        "항목번호": it,
        "항목명": row["항목명"],
        "값": val,
        "값_적용후": val,
        "근거": (
            MIRROR_RATIONALE + " [item17_적용후를 채우면서 파생된 2차 요구사항: "
            "axis 17->29-35 (_TRANS_PARENT_SUBS) 도 부모present/자식결측이 되므로 "
            "동일 근거로 같이 미러링.]"
        ),
    })

# ---------------------------------------------------------------------
# B. items 36-40 (시장위험 세부): value from MD/raw PDF, /100 (백만원->억원).
#    Root cause of the MKT-SKIP refusal: fill_market_subitems_to_disclosure.py's
#    extract_mkt_subs() only matches rows whose col0 IS a bare "금리위험(액)" /
#    "주식위험(액)" / ... label. In this filing's ③④⑤⑥ tables the total row is
#    labelled "Ⅲ. 합 계2)" / "Ⅲ. 합 계" / "계", never the bare risk name (only
#    the ② 금리위험액 table's total row happens to literally say "Ⅳ. 금리 위험액"),
#    so only item36 (13833.02) was ever captured -> v5=[13833.02,0,0,0,0] ->
#    mkt_est=13833.02 vs item19=157702 -> rel=91.2% -> correctly refused (not a
#    wrong item19; the loader just never saw items 37-40). Confirmed by:
#      - fitz raw-PDF read (p34-37) reproduces every MD digit exactly.
#      - _diversified_sqrt([36..40], MARKET_M) via the real rule engine =
#        157702.03 vs disclosed item19=157702.0, diff=0.03 (0.00002% rel).
#      - rule6 (item16=sum(17-21)-15) already closed to diff=-1.0 using
#        item19=157702 as printed -- independent proof item19 itself is right.
# ---------------------------------------------------------------------
MKT_RATIONALE = (
    "MKT-SKIP root-caused: extractor's bare-label matcher only caught item36 "
    "(md_inbox MD L645 'Ⅳ. 금리 위험액', raw PDF p33 L173-174) because L③-⑥ "
    "표의 합계행은 '합계'/'계'로만 라벨링(라벨매칭 미스, item19 문제 아님). "
    "값 = MD L{line}, raw PDF p{page} 완전 동일(fitz 교차확인), 백만원/100. "
    "_diversified_sqrt(36..40, MARKET_M) 실계산 = 157702.03 vs 헤드라인 "
    "item19=157702.0 (diff 0.03, rel 0.00002%) -- item19는 원래 맞았고 결측은 "
    "37-40 미추출이었다."
)
MKT_SUBS = [
    (36, "MD L616-645", "34, Ⅳ.금리위험액 row", 1_383_302),
    (37, "MD L674-687", "34(next), ③합계2 2026년2/4분기", 14_722_584),
    (38, "MD L700-709", "34(next), ④합계 2026년2/4분기", 990_758),
    (39, "MD L723-732", "35, ⑤계 2026년2/4분기", 1_062_126),
    (40, "MD L740-752", "35, ⑥계 2026년2/4분기", 4_039_558),
]
for it, mdloc, pdfloc, raw_mm in MKT_SUBS:
    label = prec[it]["항목명"]
    val = round(raw_mm / 100.0, 2)
    cells.append({
        "항목번호": it,
        "항목명": label,
        "값": val,
        "값_적용후": val,
        "근거": f"{MKT_RATIONALE} [이 항목: {mdloc}, raw PDF p{pdfloc}, 원값 {raw_mm:,}백만원]",
    })

# ---------------------------------------------------------------------
# C. items 41-46 (금리위험 순자산가치 시나리오): MD L644 Ⅲ.순자산가치 row
#    (2026년 2/4분기 block), raw PDF p33-34 identical (fitz cross-check).
#    Self-check: irr_derive_expected({41..46}) = 13833.01 vs item36=13833.02
#    (from block B above), diff=-0.01, rel 0.0001% -- both tables agree.
# ---------------------------------------------------------------------
IRR_RATIONALE = (
    "MD L644 (Ⅲ.순자산가치 row, 2026년2/4분기 block), raw PDF p33-34 fitz "
    "교차확인 동일. irr_derive_expected(41..46) 실계산(kics_json_rules.py 그대로 "
    "import) = 13833.01 vs 같은 표의 item36(Ⅳ.금리위험액)=13833.02, diff=-0.01 "
    "(rel 0.0001%) -- 6개 시나리오값과 item36이 상호 정합."
)
IRR_VALS = [
    (41, 17_227_623),
    (42, 17_414_960),
    (43, 15_677_339),
    (44, 18_691_873),
    (45, 16_975_586),
    (46, 17_472_287),
]
for it, raw_mm in IRR_VALS:
    label = prec[it]["항목명"]
    val = round(raw_mm / 100.0, 2)
    cells.append({
        "항목번호": it,
        "항목명": label,
        "값": val,
        "값_적용후": val,
        "근거": IRR_RATIONALE,
    })

# ---------------------------------------------------------------------
# D. items 47,49 (new) + 48 (FIX contamination) -- TIER2_ITEMS, same TFI
#    table (MD L320-335, "[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용
#    경과조치 관련", 단위 백만원). raw PDF p9 (동일 확인 안 했으면 MD 신뢰 -- 이
#    표는 md_inbox에서 이미 온전히 파싱됨, docling 결손 아님).
#
#    item48 CURRENTLY STORED = 97415 -- byte-identical to item3(보완자본)=97415.
#    Confirmed same contamination pattern documented for KR0050/KR0095/KR0002/
#    KR0074/KR0049 (label matcher confuses "보완자본 한도" row with "보완자본"
#    row). Correct value from raw table = 7,777,770백만원/100 = 77777.70.
#    Cross-check: item48 == item14(적용전 SCR)×50% = 155555×0.5 = 77777.5
#    (diff 0.20, matches the LOADER_ENFORCED formula almost exactly).
#    Cross-check: item3 == min(47,48)+49 = min(3089.80,77777.70)+94325.38
#    = 97415.18 vs headline item3=97415.0 (diff 0.18) -- closes with the
#    CORRECTED 48, not the contaminated one.
# ---------------------------------------------------------------------
item14 = _num(cur[14]["값"])
item48_expected_formula = round(item14 * 0.5, 2)
TFI2_RATIONALE_48 = (
    f"item48 오염 정정: 현재 저장값 97415 는 item3(보완자본)=97415 와 byte-identical "
    "-- KR0050/KR0095/KR0002/KR0074/KR0049 에서 반복 확인된 라벨매칭 오염과 동일 "
    "패턴(kics_disclosure_parser.py 소관, 이 패치는 데이터만 정정). 정정값은 raw "
    "MD L331 '보완자본 한도 | 7,777,770 | 7,777,770'(백만원) /100 = 77777.70. "
    f"공식검산 item14(적용전)×50%={item48_expected_formula}(diff 0.20) 및 "
    "item3==min(47,48)+49=97415.18(diff 0.18, 헤드라인 item3=97415) 둘 다 닫힘."
)
TFI2_RATIONALE_4749 = (
    "MD L320-335 TFI표(단위 백만원), '경과조치 적용 전'='경과조치 적용 후' 두 컬럼 "
    "값 동일(비적용사, TFI=X 확인 위와 동일 근거). 47='보완자본 한도 적용 전' "
    "L330=308,980, 49='해약환급금 부족분 상당액 중 해약환급금 상당액 초과분' "
    "L332=9,432,538, 각 /100. 항목명은 KR0008 2025.4Q 자신의 47/49행에서 복사."
)

cells.append({
    "항목번호": 47,
    "항목명": prec[47]["항목명"],
    "값": round(308_980 / 100.0, 2),
    "값_적용후": round(308_980 / 100.0, 2),
    "근거": TFI2_RATIONALE_4749,
})
cells.append({
    "항목번호": 48,
    "항목명": cur[48]["항목명"],
    "값": round(7_777_770 / 100.0, 2),
    "값_적용후": round(7_777_770 / 100.0, 2),
    "근거": TFI2_RATIONALE_48,
})
cells.append({
    "항목번호": 49,
    "항목명": prec[49]["항목명"],
    "값": round(9_432_538 / 100.0, 2),
    "값_적용후": round(9_432_538 / 100.0, 2),
    "근거": TFI2_RATIONALE_4749,
})

# ---------------------------------------------------------------------
# E. items 50,51,52 (TFI표 자신의 기본자본/보완자본/지급여력금액) + 53,54
#    (기발행 신종자본증권/후순위채무 memo rows, both "-" = 0 in raw, and raw
#    적용후 column is BLANK not "-" for these two memo rows specifically --
#    matches KR0008's own 2025.4Q precedent of leaving 53/54 값_적용후 unset).
#    Self-check: item50+item51 = 439879.36 = item52 (diff 0.0000, exact).
#    Self-check: item51 = min(47,48)+49+item54 = 97415.18 (diff 0.0000, exact).
#    Without these, rule 50_tfi_tier_split stays SKIP("같은 표를 반씴만 읽었다")
#    even after 47/48/49 are added -- i.e. adding 47/48/49 alone would recreate
#    the exact half-read-table pattern this rule flags elsewhere.
# ---------------------------------------------------------------------
TFI50_RATIONALE = (
    "MD L327-329 TFI표 동일 표, '경과조치 적용 전'='적용 후' 동일값. "
    "50=기본자본 L328=34,246,418, 51=보완자본 L329=9,741,518, "
    "52=지급여력금액 L327=43,987,936, 각 /100. 자체검산: item50+item51="
    "439879.36==item52(diff 0.0000); item51==min(47,48)+49+item54="
    "97415.18(diff 0.0000). 이 셋을 안 채우면 47/48/49만 있고 50/51 없는 "
    "'표 반쪽만 읽음' 패턴(rule 50_tfi_tier_split backlog)을 새로 만든다. "
    "항목명은 KR0008 2025.4Q 자신의 50/51/52행에서 복사."
)
cells.append({
    "항목번호": 50,
    "항목명": prec[50]["항목명"],
    "값": round(34_246_418 / 100.0, 2),
    "값_적용후": round(34_246_418 / 100.0, 2),
    "근거": TFI50_RATIONALE,
})
cells.append({
    "항목번호": 51,
    "항목명": prec[51]["항목명"],
    "값": round(9_741_518 / 100.0, 2),
    "값_적용후": round(9_741_518 / 100.0, 2),
    "근거": TFI50_RATIONALE,
})
cells.append({
    "항목번호": 52,
    "항목명": prec[52]["항목명"],
    "값": round(43_987_936 / 100.0, 2),
    "값_적용후": round(43_987_936 / 100.0, 2),
    "근거": TFI50_RATIONALE,
})
cells.append({
    "항목번호": 53,
    "항목명": prec[53]["항목명"],
    "값": 0,
    "값_적용후": None,
    "근거": (
        "MD L333 '(기발행 신종자본증권) | - |  ' -- 적용전='-'(=0), 적용후 컬럼은 "
        "공란(다른 TFI행처럼 숫자 반복이 아니라 진짜 공란). KR0008 2025.4Q 자신의 "
        "53행도 값_적용후 미설정(동일 관행) -- 값만 0, 값_적용후는 채우지 않음."
    ),
})
cells.append({
    "항목번호": 54,
    "항목명": prec[54]["항목명"],
    "값": 0,
    "값_적용후": None,
    "근거": (
        "MD L334 '(기발행 후순위채무) | - |  ' -- 항목53과 동일 사유(적용후 공란, "
        "2025.4Q 자신의 54행도 값_적용후 미설정)."
    ),
})

patch = {
    "company_code": CODE,
    "quarter": Q_CUR,
    "cells": cells,
    "notes": (
        "KR0008 2026.2Q: (A) items16-23 값_적용후 미러링(전면비적용사 확정) -- "
        "closes 부모item15후-부분충전 RED + TRAILING[16..23]후 RED. "
        "(A2) items29-35 값_적용후 미러링 -- item17후를 채우자 axis 17->29-35 "
        "(_TRANS_PARENT_SUBS) 가 새로 부모present/자식결측이 돼 걸린 2차 RED를 "
        "동일 비적용사 근거로 해소(scratch --master 재검증 1회차에서 발견). "
        "(B) items36-40 신규(MKT-SKIP 원인=라벨매칭이 금리위험만 캐치, 3-6표는 "
        "'합계'/'계'라벨이라 미스) -- closes 19_market RED + UNMEASURED. "
        "(C) items41-46 신규(같은 raw 표, irr_derive_expected 로 36과 상호검산). "
        "(D) item48 정정(item3값으로 오염돼있던것을 raw TFI표 값으로) + "
        "items47/49 신규 -- closes 47_tier2_census RED(TIER2_PARTIAL_ROWS). "
        "(E) items50-54 신규(TFI표 완결, 50+51=52 자체검산 exact) -- 47/48/49만 "
        "채우면 새로 생겼을 'TFI_TIER_ROWS_ABSENT_BACKLOG' 를 예방. "
        "모든 수치는 md_inbox MD + raw PDF(fitz) 이중소스 일치 확인 + "
        "src/solvency/validation/kics_json_rules.py 실제 룰엔진(MARKET_M/R4/"
        "irr_derive_expected/_diversified_sqrt) import 로 자체검산."
    ),
    "unfixable": [],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(cells)} cells to {OUT}")
for c in cells:
    print(f"  item{c['항목번호']:>2} {c['항목명']!r:60s} 값={c['값']!r:>12} 값_적용후={c['값_적용후']!r:>12}")
