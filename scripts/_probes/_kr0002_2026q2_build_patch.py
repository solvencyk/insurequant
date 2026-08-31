# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0002.json from source-verified values.
Read-only against kics_disclosure.json (only used earlier, via a separate probe, to
confirm existing labels/precedent) - this script just emits the patch file."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

COMMON = {
    "원보험사코드": "KR0002",
    "원수사명": "한화손해보험",
    "티커": "000370",
    "생손보여부": "손해보험",
    "공시분기": "2026.2Q",
}


def fmt(x):
    """Match existing string-number convention: no trailing .0 for integers,
    natural shortest-decimal repr otherwise (matches json.dumps(str(round(x,2)))."""
    r = round(float(x), 2)
    if r == int(r):
        return str(int(r))
    return str(r)


def cell(item_no, label, value, value_post=None, evidence="", bonus=False):
    c = dict(COMMON)
    c["항목번호"] = item_no
    c["항목명"] = label
    c["값"] = fmt(value)
    if value_post is not None:
        c["값_적용후"] = fmt(value_post)
    c["근거"] = ("[BONUS-not in original RED list] " if bonus else "") + evidence
    return c


cells = []

# ---------------------------------------------------------------------------
# PRIMARY: the 4 REDs
# ---------------------------------------------------------------------------

# RED #2/#3: item19 값_적용후 결측 (partial-fill / trailing gap)
cells.append(cell(
    19, "3. 시장위험액",
    value=13081,  # unchanged, already loaded correctly
    value_post=1308105 / 100,
    evidence=(
        "md_inbox/FY2026_Q2/KR0002_한화손해보험.md L380 [경과조치 적용전 지급여력비율 세부] "
        "'3. 시장위험액 | 13,081 | 13,320 | 12,079' (당분기/당분기-1/당분기-2, 억원) confirms 값=13081 unchanged. "
        "값_적용후: L444 [1) 공통적용 경과조치 관련, 단위 백만원] '시장위험액 | 1,308,105 | 1,308,105' "
        "(경과조치 적용전 = 적용후, 동일) -> /100 = 13081.05. "
        "L452 explicit disclaimer: '당사는 주식위험 및 금리위험 경과조치를 적용하지 않아 전·후 금액 및 비율이 동일함' "
        "confirms no market-risk transition applies to this company (TER=X, TIRR=X per "
        "kics_transition_applicability.json). Cross-check: derived sqrt(V'*MARKET_M*V) with V=[36-40] "
        "(see items below) = 13081.0549, matches both 13081 (전, rounded) and 13081.05 (후) almost exactly "
        "(residual 0.05, well within tolerance)."
    ),
))

# RED #3 (also item23): 기타요구자본 값_적용후 결측
cells.append(cell(
    23, "Ⅲ. 기타 요구자본(1+2+3)",
    value=0,  # unchanged, already loaded
    value_post=0,
    evidence=(
        "md_inbox MD L384 [경과조치 적용전 지급여력비율 세부] 'Ⅲ. 기타요구자본(1+2+3) | - | - | -' "
        "(all 3 quarter columns, dash=0). L448 [② 장수위험 등 경과조치, 전후 컬럼] "
        "'기타요구자본 | - | -' (both 전/후 = 0). Company has no 종속/관계회사 요구자본 환산치 "
        "(items 24/26 = 0 in all quarters on file) so item23 is structurally 0 in every quarter; "
        "값_적용후=0 mirrors 값=0, consistent with prior quarters 2025.4Q/2026.1Q which both had 값_적용후='0'."
    ),
))

# RED #1 + RED #4: items 36-40 (시장위험 subs) and 41-46 (금리위험 IRR) completely
# missing from the docling MD (localizer skipped Ch.VI §6-4 시장위험관리, pages 33-37 of
# the 316p raw PDF - docling MD jumps straight from 6-3 일반손해보험위험관리 to 6-7
# 유동성위험관리, i.e. 6-4/6-5/6-6 were never captured by run_harness --stage parse's
# keyword-page-window). Recovered directly from raw PDF via fitz (pdfplumber not even
# attempted - this is a localization/keyword-window gap, not a pdfplumber EOF).
raw_pdf_note = "raw PDF data/disclosure/FY2026_Q2/pdf/KR0002_한화손해보험.pdf p.33"

cells.append(cell(
    36, "3-1. 금리위험액",
    value=216050 / 100, value_post=216050 / 100,
    evidence=(
        f"{raw_pdf_note} '6-4. 시장위험 관리 (1) ... ② 금리위험액 현황' table, row 'Ⅳ. 금리 위험액 216,050' "
        "(단위: 백만원, 당기 26.2Q) -> /100 = 2160.50. Cross-check derive_irr(41-46) via "
        "src/solvency/validation/kics_json_rules.py:irr_derive_expected = 2160.5011 (residual 0.001, "
        "rounding-level). 값_적용후 = 값 per L452 disclaimer (no 금리위험 경과조치 applied)."
    ),
))
cells.append(cell(
    37, "3-2. 주식위험액",
    value=1212656 / 100, value_post=1212656 / 100,
    evidence=(
        "raw PDF p.35 '③ 주식위험액 현황' table, row 'Ⅲ. 합계주2)' col 당기(26.2Q) = 1,212,656 "
        "(단위: 백만원) -> /100 = 12126.56. Same page's 직전반기(25.4Q) column shows 'Ⅲ.합계 1,122,587' "
        "-> /100 = 11225.87, an EXACT match to the already-loaded 2025.4Q item37=11225.87 "
        "(confirms column mapping + unit). 값_적용후 = 값 per L452 disclaimer (no 주식위험 경과조치, TER=X)."
    ),
))
cells.append(cell(
    38, "3-3. 부동산위험액",
    value=122487 / 100, value_post=122487 / 100,
    evidence=(
        "raw PDF p.35 '④ 부동산위험액 현황' table, row 'Ⅲ. 합계' col 당기(26.2Q) 부동산위험액 = 122,487 "
        "(단위: 백만원) -> /100 = 1224.87. 직전반기(25.4Q) column 'Ⅲ.합계 189,489' -> /100=1894.89, "
        "EXACT match to already-loaded 2025.4Q item38=1894.89 (confirms mapping+unit). "
        "값_적용후 = 값 (부동산위험 not subject to any of this company's selected transitions)."
    ),
))
cells.append(cell(
    39, "3-4. 외환위험액",
    value=128065 / 100, value_post=128065 / 100,
    evidence=(
        "raw PDF p.36 '⑤ 외환위험액 현황' table, row '계' col 외환위험액, 당기(26.2Q) = 128,065 "
        "(단위: 백만원) -> /100 = 1280.65. 직전반기(25.4Q) row '계' 외환위험액 = 172,125 -> /100=1721.25, "
        "EXACT match to already-loaded 2025.4Q item39=1721.25. 값_적용후 = 값 (외환위험 not subject to "
        "any selected transition)."
    ),
))
cells.append(cell(
    40, "3-5. 자산집중위험액",
    value=0, value_post=0,
    evidence=(
        "raw PDF p.36 '⑥ 자산집중위험액 현황' table, row '계' 위험액 = '-' (dash=0) for both 당기(26.2Q) and "
        "직전반기(25.4Q, also '-'). Matches already-loaded 2025.4Q item40=0. 값_적용후=0 (no exposure -> "
        "no transition effect possible)."
    ),
))

cells.append(cell(
    41, "3-1-0. 금리위험 순자산가치(충격전)",
    value=6129157 / 100,
    evidence=(
        f"{raw_pdf_note} 금리위험액 현황 table, row 'Ⅲ. 순자산가치' col '충격 전', 당기(26.2Q) = 6,129,157 "
        "(단위: 백만원) -> /100 = 61291.57. Same table's p.34 직전반기(25.4Q) '충격전' col = 5,022,854 -> "
        "/100=50228.54, EXACT match to already-loaded 2025.4Q item41=50228.54 (confirms row/col mapping). "
        "No 값_적용후 in source (single-column disclosure, matches schema convention where 41-46 never "
        "carry 값_적용후 in any prior quarter on file)."
    ),
))
cells.append(cell(
    42, "3-1-1. 금리위험 순자산가치(평균회귀)",
    value=6173625 / 100,
    evidence=(
        "same table as item41, row 'Ⅲ.순자산가치' col '평균회귀' = 6,173,625백만원 -> /100=61736.25. "
        "p.34 25.4Q '평균회귀' col = 5,055,472 -> /100=50554.72, EXACT match to loaded item42=50554.72."
    ),
))
cells.append(cell(
    43, "3-1-2. 금리위험 순자산가치(금리상승)",
    value=5874869 / 100,
    evidence=(
        "same table, row 'Ⅲ.순자산가치' col '금리상승' = 5,874,869백만원 -> /100=58748.69. "
        "p.34 25.4Q '금리상승' col = 5,011,600 -> /100=50116.00, EXACT match to loaded item43=50116."
    ),
))
cells.append(cell(
    44, "3-1-3. 금리위험 순자산가치(금리하락)",
    value=6356816 / 100,
    evidence=(
        "same table, row 'Ⅲ.순자산가치' col '금리하락' = 6,356,816백만원 -> /100=63568.16. "
        "p.34 25.4Q '금리하락' col = 4,976,418 -> /100=49764.18, EXACT match to loaded item44=49764.18."
    ),
))
cells.append(cell(
    45, "3-1-4. 금리위험 순자산가치(금리평탄)",
    value=6072524 / 100,
    evidence=(
        "same table, row 'Ⅲ.순자산가치' col '금리평탄' = 6,072,524백만원 -> /100=60725.24. "
        "p.34 25.4Q '금리평탄' col = 4,873,513 -> /100=48735.13, EXACT match to loaded item45=48735.13."
    ),
))
cells.append(cell(
    46, "3-1-5. 금리위험 순자산가치(금리경사)",
    value=6199850 / 100,
    evidence=(
        "same table, row 'Ⅲ.순자산가치' col '금리경사' = 6,199,850백만원 -> /100=61998.50. "
        "p.34 25.4Q '금리경사' col = 5,179,253 -> /100=51792.53, EXACT match to loaded item46=51792.53. "
        "Full 41-46 self-check: irr_derive_expected(41-46) = 2160.50 vs directly-disclosed item36 = "
        "2160.50 (residual 0.001) -- confirms all six values simultaneously."
    ),
))

# ---------------------------------------------------------------------------
# BONUS (NOT in the original 4-RED list) -- items 47-54 TFI-table cells found
# missing/wrong while reading the same source table for item19/23. Not covered
# by the standard rule engine (1-46 identities), so leaving them alone would
# NOT block the RED=0 gate -- flagged separately for the consuming process to
# decide whether to apply.
# ---------------------------------------------------------------------------

cells.append(cell(
    48, "보완자본 한도",
    value=1779833 / 100, value_post=1779833 / 100,
    evidence=(
        "md_inbox MD L407 [1) 공통적용 경과조치 관련] '보완자본 한도 | 1,779,833 | 1,779,833' "
        "(단위 백만원, 전=후 동일) -> /100 = 17798.33. CURRENTLY LOADED VALUE (41849) IS WRONG -- it "
        "silently duplicates item3(보완자본)=41849, not the cap. Confirmed via 보완자본한도=SCR(전)x50% "
        "identity (docs/agents/kics-json-validation-rules.md capital-tiering rule): item14(전)=35597 x "
        "0.5=17798.5 (matches 17798.33, rounding). Same identity holds exactly for the two prior quarters "
        "already in the master: 2026.1Q item14(전)=33944x0.5=16972.0 == loaded item48=16972.01; "
        "2025.4Q item14(전)=33787x0.5=16893.5 ~= loaded item48=16893.72. Those two are correct; only "
        "2026.2Q's currently-loaded 41849 breaks the pattern (looks like a copy-from-item3 cell-shift)."
    ),
    bonus=True,
))
cells.append(cell(
    47, "보완자본 한도 적용 전",
    value=1313825 / 100, value_post=831518 / 100,
    evidence=(
        "md_inbox MD L406 '보완자본 한도 적용 전 | 1,313,825 | 831,518' (백만원) -> /100 = "
        "13138.25(전) / 8315.18(후). 전-column self-check: item47(전)+item49(전) = 13138.25+28710.81 = "
        "41849.06 ~= item3(전)=41849 (매치, 소수점 반올림). CAUTION: 후-column historical pattern for "
        "this label in the two prior quarters is a ~100x drop (2026.1Q 13030.8->96.24, 2025.4Q "
        "13369.56->125.7), but this quarter's source table only shows a ~1.6x drop (13138.25->8315.18); "
        "I could not reconcile that discontinuity from the tables I read (item47후+item49후=37025.99 vs "
        "item3후=39508.01, off by ~2482 ~ item54). Read verbatim from source; recommend a human sanity "
        "check before trusting the 후-column specifically."
    ),
    bonus=True,
))
cells.append(cell(
    49, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    value=2871081 / 100, value_post=2871081 / 100,
    evidence=(
        "md_inbox MD L408 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 | 2,871,081 | 2,871,081' "
        "(백만원, 전=후 동일) -> /100 = 28710.81. Confirms via item47(전)+item49(전)=item3(전) identity "
        "above (41849.06 ~= 41849)."
    ),
    bonus=True,
))
cells.append(cell(
    50, "기본자본(TFI표, 공통적용경과조치)",
    value=2391443 / 100, value_post=2625548 / 100,
    evidence=(
        "md_inbox MD L404 '기본자본 | 2,391,443 | 2,625,548' (백만원) -> /100 = 23914.43(전) / "
        "26255.48(후). 후-value EXACTLY matches already-loaded item2 값_적용후='26255.48' for this same "
        "quarter (cross-validated, not just source-read)."
    ),
    bonus=True,
))
cells.append(cell(
    51, "보완자본(TFI표, 공통적용경과조치)",
    value=4184906 / 100, value_post=3950801 / 100,
    evidence=(
        "md_inbox MD L405 '보완자본 | 4,184,906 | 3,950,801' (백만원) -> /100 = 41849.06(전) / "
        "39508.01(후). Both EXACTLY match already-loaded item3 값='41849' (rounded) / 값_적용후='39508.01' "
        "for this same quarter (cross-validated)."
    ),
    bonus=True,
))
cells.append(cell(
    52, "지급여력금액(TFI표, 공통적용경과조치)",
    value=6576349 / 100, value_post=6576349 / 100,
    evidence=(
        "md_inbox MD L403 '지급여력금액 | 6,576,349 | 6,576,349' (백만원, 전=후 동일) -> /100 = 65763.49. "
        "CURRENTLY LOADED VALUE (65763, flat int, no 값_적용후) loses precision vs. the pattern in prior "
        "quarters (2026.1Q item52='62324.64', 2025.4Q item52='58948.29' both keep 2-decimal precision). "
        "This corrects precision + adds the missing 값_적용후, matching item1 값='65763'/값_적용후='65763' "
        "(item1 is separately rounded-to-int by the core 1-28 extractor per convention, item52 in the "
        "TFI-table historically was not)."
    ),
    bonus=True,
))
cells.append(cell(
    53, "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    value=234105 / 100,
    evidence=(
        "md_inbox MD L409 '(기발행 신종자본증권) | 234,105 |' (백만원, 적용후 column blank in source, "
        "matches schema convention -- item53 has no 값_적용후 in either prior quarter on file) -> "
        "/100 = 2341.05. EXACTLY unchanged from both 2026.1Q item53=2341.05 and 2025.4Q item53=2341.05 "
        "(this is an outstanding-issuance balance, plausibly static quarter to quarter). Also matches "
        "narrative text L58: '신종자본증권 2,341억원'."
    ),
    bonus=True,
))
cells.append(cell(
    54, "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
    value=248202 / 100,
    evidence=(
        "md_inbox MD L410 '(기발행 후순위채무) | 248,202 |' (백만원, 적용후 blank per schema convention) "
        "-> /100 = 2482.02. CAUTION: this is a large drop vs. 2026.1Q item54=10593.5 and 2025.4Q "
        "item54=10902.81 (roughly -76% QoQ). I found no contradicting source in this MD (only one "
        "'후순위' hit in the whole file, this table row) and no corroborating one either -- the capital "
        "narrative paragraph (L58) lists only 신종자본증권 among capital instruments, subordinated debt "
        "is a liability so it wouldn't appear there. A sharp single-quarter drop in the K-ICS-recognized "
        "balance is structurally possible (call-date haircut mechanics per "
        "[[reference_capital_securities_utilization]] -- recognized amount can step down hard when a "
        "call-option effective date passes, independent of actual redemption) but I cannot confirm which "
        "explanation applies from the sources I have. Read verbatim; recommend a human check against the "
        "company's 신종자본증권/후순위채 발행현황 (DART 사업보고서 XML) before trusting this one."
    ),
    bonus=True,
))

patch = {
    "company_code": "KR0002",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "PRIMARY (closes all 4 REDs from the task): items 19,23,36,37,38,39,40,41,42,43,44,45,46. "
        "Root cause of RED#1/RED#4: docling's --stage parse keyword-page-window localization skipped "
        "Ch.VI section 6-4 (시장위험 관리, PDF pages 33-37) entirely -- the docling MD "
        "(md_inbox/FY2026_Q2/KR0002_한화손해보험.md, 1105 lines) jumps directly from '6-3. "
        "일반손해보험위험 관리' (L623) to '6-7. 유동성위험 관리' (L767), i.e. 6-4/6-5/6-6 headers never "
        "appear at all. This is NOT a pdfplumber EOF (fitz was not even needed as a fallback -- the "
        "pages were simply never in the docling output to begin with) and NOT cadence (2026.2Q is an "
        "even quarter, full-form disclosure). All 36-40/41-46 values were recovered directly from the "
        "raw PDF (fitz) at data/disclosure/FY2026_Q2/pdf/KR0002_한화손해보험.pdf pages 33 (금리위험 + "
        "IRR scenarios), 35 (주식/부동산위험), 36 (외환/자산집중위험). Every recovered value "
        "cross-validates in one of two independent ways: (a) the identical page's 직전반기(25.4Q) "
        "comparison column reproduces the ALREADY-LOADED 2025.4Q master values to the exact 백만원 (all "
        "6 of items 41-46 plus 36-40, zero discrepancy), confirming column-order/unit mapping is exactly "
        "right; (b) the recovered 36-40 vector satisfies item19=sqrt(V'*MARKET_M*V) to residual 0.05 "
        "(13081.05 vs 13081), and the recovered 41-46 vector satisfies "
        "item36=irr_derive_expected(41-46) to residual 0.001 (2160.50 vs 2160.50) -- both formulas "
        "imported from src/solvency/validation/kics_json_rules.py, not retyped. "
        "item19/item23 값_적용후: this company applies TFI (공통, 가용자본) + TIR (선택, 신규위험) but "
        "explicitly does NOT apply TAC/TER/TIRR (자본감소분/주식위험/금리위험 경과조치 전부 X per "
        "kics_transition_applicability.json and the MD's own 적용여부 table L345-352) -- confirmed by an "
        "explicit disclaimer in the filing itself (L452: '당사는 주식위험 및 금리위험 경과조치를 "
        "적용하지 않아 전·후 금액 및 비율이 동일함'), so 값_적용후=값 for items 19/36-40 is not a guess, "
        "it is what the company states in its own filing, plus item19 후's precise value (13081.05) is "
        "directly given in the L444 TFI-table row. item23 (기타요구자본) is structurally 0 in every "
        "quarter on file for this company (no 종속/관계회사 요구자본 환산치), 값_적용후=0 mirrors that. "
        "BONUS (items 47-52 high confidence, 53 high confidence, 54 and 47's 후-column flagged "
        "uncertain): found while reading the same L398-411 TFI table for item19's 후-value. item48 was "
        "SILENTLY WRONG in the current master (holds item3's value, not the actual 보완자본 한도) -- "
        "confirmed via the SCR(전)x50%=한도 identity holding exactly for the two prior quarters already "
        "loaded but broken only in 2026.2Q's current bad value. Items 47/49/50/51/52 were completely "
        "missing (present in both 2025.4Q and 2026.1Q, gone in 2026.2Q) -- same table, recovered "
        "together. Item54 and item47's 값_적용후 specifically are read verbatim from source but their "
        "magnitude does not fit the historical pattern for this company well enough that I'm fully "
        "confident -- see each cell's 근거 for the specific discrepancy; flagged for human review rather "
        "than silently applied."
    ),
    "unfixable": [],
}

out_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0002.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {out_path} ({len(cells)} cells)")

# quick self-print for review
for c in cells:
    tag = "BONUS" if c["근거"].startswith("[BONUS") else "PRIMARY"
    vp = c.get("값_적용후", "<none>")
    print(f"  [{tag}] item{c['항목번호']:>3} {c['항목명'][:30]:30s} 값={c['값']:>10s} 값_적용후={vp:>10s}")
