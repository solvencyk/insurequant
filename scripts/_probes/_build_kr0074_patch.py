# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0074.json -- 2026.2Q KR0074 라이나생명보험 fixes.
Diagnosis: 4 REDs assigned. Does NOT write kics_disclosure.json (patch-only, per ticket rule).
"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EV_NONAPPLIER = (
    "raw PDF p.18 [지급여력비율의 경과조치 적용에 관한 사항] 2) 선택적용 경과조치 관련: "
    "1)자본감소분, 2)장수/사업비/해지/대재해위험, 3)주식/금리위험 경과조치 모두 "
    "'적용하지 않아 경과조치 전ㆍ후 금액 및 비율이 동일함'. p.18 O/X표: "
    "TAC=TIR=TER=TIRR=PCA_DEFER=X (TFI만 O, 가용자본측 공통조치이며 그 수치효과도 0 -- "
    "1)공통적용표 지급여력비율/금액/기본자본/보완자본/지급여력기준금액 전후 완전동일). "
    "data/_derived/kics_transition_applicability.json: KR0074 13개 분기(2023.1Q-2026.1Q) "
    "전부 TAC/TIR/TER/TIRR/PCA_DEFER=X 일관. KR0074 자기 회사 과거 전체 분기에서 이 항목 "
    "값=값_적용후 100% 일치(예외 0) 실측 확인 -> 값을 값_적용후에 미러링."
)

cells = []


def add(item_no, label, val, val_post, evidence, fix_note=None):
    c = {
        "항목번호": item_no,
        "항목명": label,
        "값": val,
        "값_적용후": val_post,
        "근거": evidence,
    }
    if fix_note:
        c["_fix_note"] = fix_note
    cells.append(c)


# ---------------------------------------------------------------------
# Category B: mirror-fill 값_적용후 (값 already correct & already loaded;
# only 값_적용후 was missing). Source table for 값 = md_inbox/FY2026_Q2/
# KR0074_라이나생명보험.md L239-269 "[경과조치 적용 전 지급여력비율 세부]"
# (this table has NO 적용후 column at all -- confirms items 15-23 columns
# were never meant to show a distinct 적용후 figure this quarter).
# ---------------------------------------------------------------------

mirror_items = [
    (4, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", 71251),
    (5, "1. 보통주", 698),
    (6, "2. 자본항목 중 보통주 이외의 자본증권", 0),
    (7, "3. 이익잉여금", 58442),
    (8, "4. 자본조정", 0),
    (9, "5. 기타포괄손익누계액", -108),
    (10, "6. 비지배지분", 0),
    (11, "7. 조정준비금", 12219),
    (12, "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)", 0),
    (13, "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)", 18652),
    (16, "- 분산효과 : (1+2+3+4+5) - Ⅰ", 6314),
    (17, "1. 생명장기손해보험위험액", 20210),
    (18, "2. 일반손해보험위험액", 0),
    (19, "3. 시장위험액", 8193),
    (20, "4. 신용위험액", 2350),
    (21, "5. 운영위험액", 2475),
    (22, "Ⅱ. 법인세조정액", 6523),
    (23, "Ⅲ. 기타 요구자본(1+2+3)", 0),
    (29, "1-1. 사망위험액", 1552.02),
    (30, "1-2. 장수위험액", 6.56),
    (31, "1-3. 장해ㆍ질병위험액", 5679.8),
    (32, "1-4. 장기재물ㆍ기타위험액", 0),
    (33, "1-5. 해지위험액", 15881.68),
    (34, "1-6. 사업비위험액", 4219.11),
    (35, "1-7. 대재해위험액", 359.84),
]
for item_no, label, val in mirror_items:
    add(item_no, label, val, val, "md L239-269 값 항목(이미 적재됨, 불변). 미러 근거: " + EV_NONAPPLIER)

# ---------------------------------------------------------------------
# Category A: confirmed parser bugs -- fix existing wrong 값, add 값_적용후.
# ---------------------------------------------------------------------

# item48: currently stored 18652 == item3(보완자본) exactly -- a row-adjacent
# mis-map (matches KR0050 precedent failure mode: label matcher confuses
# "보완자본 한도" row with the "보완자본" row directly above it). True value
# from raw PDF p.18 TFI table row "보완자본 한도 | 1,019,519 | 1,019,519"
# (백만원) = 10,195.19억. Self-check: item51 == min(47,48)+49+54 ->
# 18651.61 == min(0, 10195.19) + 18651.61 + 0 == 18651.61 (exact).
add(
    48, "보완자본 한도", 10195.19, 10195.19,
    "raw PDF p.18 row '보완자본 한도 | 1,019,519 | 1,019,519' (백만원, both columns identical). "
    "CONFIRMED BUG: previously-stored 값=18652 exactly equals item3(보완자본)=18652 -- a "
    "row-adjacent mis-map (matches precedent: scripts/fix_20260829_kr0050_2026q2_onboarding.py "
    "section B, '라벨 매처가 보완자본 한도와 보완자본을 혼동'). Self-check: item51(18651.61) == "
    "min(item47=0, item48=10195.19) + item49(18651.61) + item54(0) == 0 + 18651.61 + 0 = "
    "18651.61 == item51 exactly.",
    fix_note="FIX: 18652 (wrong, = item3 leaked) -> 10195.19 (raw p.18 보완자본 한도 row)",
)

# item52: currently stored 71251 == item1 exactly (int, no independent
# precision) -- historical convention for this item ALWAYS keeps the TFI
# table's own 2-decimal precision (e.g. 2026.1Q item52=72599.59 != item1=
# 72600). True value from raw PDF p.18 row "지급여력금액 | 7,125,084 |
# 7,125,084" (백만원) = 71,250.84억. Self-check: item52 == item50+item51 ->
# 71250.84 == 52599.23 + 18651.61 == 71250.84 (exact).
add(
    52, "지급여력금액(TFI표, 공통적용경과조치)", 71250.84, 71250.84,
    "raw PDF p.18 row '지급여력금액 | 7,125,084 | 7,125,084' (백만원, both columns identical). "
    "Previously-stored 값=71251 loses this table's native 2-decimal precision (매 분기 관례는 "
    "item1과 다른 독립 정밀도 유지 -- 2026.1Q item52=72599.59 vs item1=72600). Self-check: "
    "item52(71250.84) == item50(52599.23) + item51(18651.61) == 71250.84 exactly.",
    fix_note="FIX: 71251 (rounded/copied from item1) -> 71250.84 (raw p.18 native precision)",
)

# ---------------------------------------------------------------------
# Category C: items entirely absent this quarter -- extracted fresh from
# raw PDF (docling MD dropped this content; see notes). Text-verified
# non-scanned pages (fitz text density check: pp.25-29 NOT in the <200-char
# low-density list -- this is a docling table-conversion drop, not OCR/scan).
# ---------------------------------------------------------------------

CROSSCHECK_19 = (
    " Cross-check via MARKET_M [src/solvency/validation/kics_json_rules.py], V=[36,37,38,39,40]: "
    "sqrt(V'MV) = 8193.02 vs stored item19=8193.0, diff 0.02 (rel 0.0002%, tol 1%) -- GREEN."
)

add(
    36, "3-1. 금리위험액", 4093.59, 4093.59,
    "raw PDF p.25 '② 금리위험액 현황' row 'Ⅳ. 금리 위험액 | 409,359' (백만원, 당기 26.2Q) "
    "= 4093.59억. Cross-check via irr_derive_expected(41-46) [src/solvency/validation/"
    "kics_json_rules.py]: derived 4093.5825 vs printed 4093.59, diff -0.0075 (rel 0.0002%, "
    "tol 5%) -- GREEN. " + EV_NONAPPLIER,
)
add(
    37, "3-2. 주식위험액", 5564.55, 5564.55,
    "raw PDF p.27 '③ 주식위험액 현황' row 'Ⅲ. 합계주2) | 556,455' (백만원, 당기 26.2Q) "
    "= 5564.55억. " + EV_NONAPPLIER + CROSSCHECK_19,
)
add(
    38, "3-3. 부동산위험액", 1048.26, 1048.26,
    "raw PDF p.27 '④ 부동산위험액 현황' row 'Ⅲ. 합계 | 104,826' (백만원, 당기 26.2Q) "
    "= 1048.26억. " + EV_NONAPPLIER + CROSSCHECK_19,
)
add(
    39, "3-4. 외환위험액", 1469.82, 1469.82,
    "raw PDF p.28 '⑤ 외환위험액 현황' row '계 | 441,169 | - | 108,188 | 38,794 | 146,982' "
    "(백만원, 당기 26.2Q, last col=외환위험액) = 1469.82억. This table WAS present in "
    "md_inbox MD (L435-452) but never reached kics_disclosure.json -- fill_market_subitems "
    "pipeline gap, not a docling drop for this specific sub-item. " + EV_NONAPPLIER,
)
add(
    40, "3-5. 자산집중위험액", 60.78, 60.78,
    "raw PDF p.28 '⑥ 자산집중위험액 현황' row '계 | 33,263 | 6,078' (백만원, 당기 26.2Q, "
    "last col=위험액) = 60.78억. This table WAS present in md_inbox MD (L456-471) but never "
    "reached kics_disclosure.json -- fill_market_subitems pipeline gap, not a docling drop "
    "for this specific sub-item. " + EV_NONAPPLIER,
)

# 41-46: IRR shock scenarios, raw PDF p.25 "② 금리위험액 현황" table, 당기(26.2Q) column
# order confirmed [충격전, 평균회귀, 금리상승, 금리하락, 금리평탄, 금리경사] by matching
# "Ⅳ.금리위험액=409,359" against irr_derive_expected() (diff -0.0075, see item36 evidence).
IRR_SRC = (
    "raw PDF p.25 '② 금리위험액 현황' table, row 'Ⅲ. 순자산가치', 당기(26.2Q) column "
    "[충격전, 평균회귀, 금리상승, 금리하락, 금리평탄, 금리경사] = "
    "[7,125,084, 7,152,196, 6,704,049, 7,575,156, 7,010,037, 7,252,962] (백만원). "
    "Column order confirmed by irr_derive_expected(41-46) reproducing the page's own printed "
    "'Ⅳ. 금리 위험액 = 409,359' to within 0.0075억 (rel 0.0002%). MD dropped this entire table "
    "(6-4 시장위험 관리 section jumps from 6-3 header straight to ⑤외환위험액, skipping "
    "①개념/②금리위험액/③주식위험액/④부동산위험액) despite p.25-26 having dense, non-scanned "
    "text (fitz text-density check: not in the <200-char low-density page list) -- docling "
    "table-conversion drop, NOT an OCR/scan issue. " + EV_NONAPPLIER
)
add(41, "3-1-0. 금리위험 순자산가치(충격전)", 71250.84, 71250.84, IRR_SRC)
add(42, "3-1-1. 금리위험 순자산가치(평균회귀)", 71521.96, 71521.96, IRR_SRC)
add(43, "3-1-2. 금리위험 순자산가치(금리상승)", 67040.49, 67040.49, IRR_SRC)
add(44, "3-1-3. 금리위험 순자산가치(금리하락)", 75751.56, 75751.56, IRR_SRC)
add(45, "3-1-4. 금리위험 순자산가치(금리평탄)", 70100.37, 70100.37, IRR_SRC)
add(46, "3-1-5. 금리위험 순자산가치(금리경사)", 72529.62, 72529.62, IRR_SRC)

# 47/49/50/51: TFI memo items, raw PDF p.18 (= md L281-292, already correctly
# converted -- these were simply never UPSERTed by fill_period this quarter,
# unlike 48/52 which loaded but with the item48 bug above).
add(
    47, "보완자본 한도 적용 전", 0, 0,
    "raw PDF p.18 row '보완자본 한도 적용 전 | - | -' (dash=0, matches KR0074's own last-3-"
    "quarter trend 2025.3Q/2025.4Q/2026.1Q all =0). " + EV_NONAPPLIER,
)
add(
    49, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분", 18651.61, 18651.61,
    "raw PDF p.18 row '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 | 1,865,161 | "
    "1,865,161' (백만원) = 18651.61억. Self-check: item51 == min(item47,item48)+item49+item54 "
    "-> 18651.61 == min(0,10195.19) + 18651.61 + 0 == 18651.61 (exact -- structurally requires "
    "item49==item51 exactly when item47=item54=0, confirms both readings independently). "
    + EV_NONAPPLIER,
)
add(
    50, "기본자본(TFI표, 공통적용경과조치)", 52599.23, 52599.23,
    "raw PDF p.18 row '기본자본 | 5,259,923 | 5,259,923' (백만원) = 52599.23억 "
    "(cf. item2=52599, TFI표 own precision kept per historical convention). " + EV_NONAPPLIER,
)
add(
    51, "보완자본(TFI표, 공통적용경과조치)", 18651.61, 18651.61,
    "raw PDF p.18 row '보완자본 | 1,865,161 | 1,865,161' (백만원) = 18651.61억. "
    "Self-check: item52 == item50+item51 -> 71250.84 == 52599.23+18651.61 (exact). "
    + EV_NONAPPLIER,
)

# 53/54: 값 only (0), NO 값_적용후 -- 12/12 prior quarters (2023.1Q-2026.1Q)
# never populate 값_적용후 for these two rows (raw p.18 shows 적용후 column as
# a blank ideographic-space cell, not even a "-", for these two rows only --
# a consistent, deliberate distinction in the filing itself, not a gap).
add(
    53, "(기발행 신종자본증권)(TFI표, 공통적용경과조치)", 0, None,
    "raw PDF p.18 row '(기발행 신종자본증권) | - | [blank]' (적용전=dash=0; 적용후 cell is a "
    "blank ideographic space, not '-', in BOTH this quarter's raw text and all 12 prior "
    "quarters -- KR0074 has NEVER populated 값_적용후 for item53/54 in its full disclosed "
    "history; treated as a deliberate source convention, not a gap, so 값_적용후 left null "
    "per precedent rather than force-mirrored.",
)
add(
    54, "(기발행 후순위채무)(TFI표, 공통적용경과조치)", 0, None,
    "raw PDF p.18 row '(기발행 후순위채무) | - | [blank]' (same pattern/rationale as item53).",
)

patch = {
    "company_code": "KR0074",
    "company_name": "라이나생명보험",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "UNMEASURED verdict root cause: NOT OCR/scan (fitz text-density check confirms raw PDF "
        "pp.25-29 are dense, non-scanned text -- none appear in the <200-char/page low-density "
        "list that flags KICS-IMG-style scans elsewhere in this repo). NOT a legitimate "
        "non-applier absence either (that only explains 적용전==적용후, not the items being "
        "missing outright). Root cause = a docling MD conversion drop: md_inbox/FY2026_Q2/"
        "KR0074_라이나생명보험.md's '6-4. 시장위험 관리' section jumps directly from the "
        "'6-3. 일반손해보험위험 관리(해당사항 없음)' header to '⑤ 외환위험액 현황', skipping "
        "the '6-4' header, '①개념', '②금리위험액 현황' (raw p.25-26, contains ALL of items "
        "41-46 plus the printed item36 total), and '③주식위험액 현황'/'④부동산위험액 현황' "
        "(raw p.27, items 37/38). Separately, items 39(외환)/40(자산집중) DID survive into the "
        "MD (L435-471) but never made it into kics_disclosure.json either -- so "
        "fill_market_subitems_to_disclosure.py appears to have skipped this company/quarter's "
        "market-risk section as a unit (plausibly because its phase-0 localizer anchors on "
        "section-header text that is absent from the MD, so it never found a market_pages span "
        "for this company/quarter at all -- even the 2 sub-items whose source text survived in "
        "the MD (39,40) never got read). All 6 IRR items (41-46) plus market subs (36-40) were "
        "extracted directly from raw PDF text via fitz (not rendering/OCR -- the text layer is "
        "intact) and cross-verified against the live rule-engine formulas (irr_derive_expected, "
        "MARKET_M, imported directly from src/solvency/validation/kics_json_rules.py, not "
        "hand-arithmetic) with sub-0.001% residuals -- see per-cell 근거. "
        "Separately found + fixed 2 pre-existing data bugs while covering the TFI memo table "
        "(items 47-54, raw PDF p.18): item48 had item3's value leaked into it (row-adjacent "
        "mis-map, same failure mode as the documented KR0050 precedent), and item52 had lost "
        "the TFI table's native 2-decimal precision (was silently copied from item1 instead). "
        "Both confirmed via the table's own algebraic identities (item51==min(47,48)+49+54; "
        "item52==item50+item51), both exact to the cent once corrected. "
        "SCOPE NOTE -- deliberately NOT included: (1) item15's 값_적용후 (existing stored value "
        "26913 vs disclosed 값=26914, diff 0.19 -- investigated and found to be explainable as "
        "a rule4-derived value (sqrt(V'R4V)+item21 = 26913.81, likely int-truncated by an "
        "earlier fill pass) rather than a random error; it is within GREEN tolerance either way "
        "and not one of the 4 named REDs, so left untouched to avoid overwriting a possibly-"
        "intentional legacy convention on a field outside this ticket's scope). (2) items 24-26 "
        "(종속/관계회사 요구자본 환산치ㆍ대응치, always-0 optional items) -- present as '-' "
        "(=0) in the raw 적용전 detail table same as every prior quarter, but entirely absent "
        "from kics_disclosure.json this quarter (2026.1Q had them as 0); left out because they "
        "gate no validation rule (informational only) and are outside the 4 named REDs -- "
        "flagged here for visibility, not fixed."
    ),
    "unfixable": [],
}

out_path = "data/_derived/_patch_2026q2_KR0074.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(patch, f, ensure_ascii=False, indent=2)

print("wrote " + out_path + ": " + str(len(cells)) + " cells")
for c in cells:
    tag = " [FIX]" if "_fix_note" in c else ""
    print("  item" + str(c["항목번호"]) + tag + ": 값=" + str(c["값"]) + " 값_적용후=" + str(c["값_적용후"]))
