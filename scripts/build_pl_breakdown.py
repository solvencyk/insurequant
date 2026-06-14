#!/usr/bin/env python3
"""PL (income statement) breakdown extractor — 24-item schema per (company, quarter).

Produces a long-form JSON (data/dart/viz/pl_breakdown_master.json) with one row per
(원보험사코드, 항목번호, 공시분기): {원보험사코드, 원수사명, 티커, 생손보여부, 항목번호,
항목명, 공시분기, 값}.  Unit = 백만원 (KRW millions).

Two tiers:
  Tier 1 — 포괄손익계산서 (income statement): items 1, 15, 16, 17, 19, 20, 21, 22, 23, 24
           and the financial sub-lines.  Works on nearly every annual filing.
           Handles 손보 (label '보험손익') and 생보 (label '보험서비스결과').
  Tier 2 — '발행보험 계약유형별 보험수익/보험서비스비용 분석' + '재보험' notes
           (FY2025+ only): items 4, 5, 6, 9, 10, 11; for 손보 also 13/14 via
           자동차/일반 columns.

Derived: 2,3,7,8,12,13,14,18,20,22,24 via the schema identities when components exist.

Validated against 4 hand-built gold xlsx (삼성화재/메리츠/삼성생명/한화생명, 2025.4Q).
Reuses src.ifrs17.csm_extractor._iter_tables_with_context and to_num/unit_factor from
build_net_income_breakdown.  Does NOT modify build_net_income_breakdown.py.
"""
import json
import os
import re
import sys
import glob
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.build_net_income_breakdown import to_num  # noqa: E402

OUT = Path("data/dart/viz/pl_breakdown_master.json")
DISCLOSURE = Path("kics_disclosure.json")
RAW_FY_GLOB = "data/dart/FY*/raw"

ITEM_NAMES = {
    1: "보험손익", 2: "생명장기 손익", 3: "생명장기 원수손익", 4: "원수 CSM상각",
    5: "원수 위험조정 변동", 6: "원수 예실차", 7: "기타 생명장기 원수손익",
    8: "생명장기 재보험손익", 9: "재보험 CSM상각", 10: "재보험 위험조정 변동",
    11: "재보험 예실차", 12: "기타 생명장기 재보험손익", 13: "자동차손익", 14: "일반손익",
    15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익",
    19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익",
    23: "법인세", 24: "당기순이익",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


def _label(r, i=0):
    return _norm(r[i]) if len(r) > i else ""


def _row_nums(r):
    """Numeric cells of a row, in document order ('-'/blank skipped)."""
    out = []
    for c in r:
        v = to_num(c)
        if v is not None:
            out.append(v)
    return out


def _quarter_from_path(p):
    m = re.search(r"FY(\d{4})_Q(\d)", str(p))
    return f"{m.group(1)}.{m.group(2)}Q" if m else None


def _quarter_sort_key(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


# --------------------------------------------------------------------------- #
# Tier 1 — income statement
# --------------------------------------------------------------------------- #
INCOME_PROFIT_LABELS = ("보험손익", "보험서비스결과")  # 손보 / 생보

# Statement basis the hand-built gold used. Default is 연결 (consolidated). The few
# companies whose gold was built on 별도 (separate) are listed here. (한화생명's FY2025
# gold uses 별도 — its 연결 income statement folds in non-insurance subsidiaries.)
# The 생보 component-decomposition companies (교보/DB생명/동양) also report on 별도.
BASIS_OVERRIDE = {
    "KR0068": "별도", "KR0073": "별도", "KR0082": "별도", "KR0087": "별도",
    "KR0009": "별도",  # 현대해상: 별도 own-company 보험손익 (연결 folds subsidiaries)
}

# Per-code Tier-1 statement-selection hints (FY2025 item1 fixes).  Each value carries a
# target 당기순이익 (백만) and/or 보험수익 (백만): the income statement whose unit-scaled
# NI / 보험수익 matches gets a dominating selection bonus.  This pins item1 to the correct
# statement (right basis + right unit) WITHOUT touching the global heuristic — so the 4
# gold companies (no hint) are unaffected.
TIER1_HINTS = {
    # 한화손해: 요약재무정보 (천원) mis-scales 206,270천원->206.27; pin to the 백만-native
    # 별도재무상태표 (보험손익=206,270, 당기순이익=292,333 백만).
    "KR0002": {"ni": 292333.0},
    # 코리안리: pick the 별도 standalone (보험수익=4,878,323; item1=223,754), NOT the
    # overseas-folded statement (보험수익=4,975,837; item1=226,496).
    "KR1000": {"rev": 4878323.0, "ni": 316581.0},
    # 현대해상: 별도 own-company statement (item1=396,111; 당기순이익=686,061 백만);
    # disambiguates from the 1,043,102-ins 손익현황 variant (ni=1,043,296).
    "KR0009": {"ni": 686061.0},
    # 교보: 별도 (item1=391,590; 당기순이익=763,210); the 연결 highlights gives 371,583.
    "KR0073": {"ni": 763210.0},
}


def _is_consolidated(t):
    """연결 (consolidated) statement signalled by minority-interest / parent-owner
    attribution rows or explicit 연결 line labels."""
    allrows = " ".join(_norm(r[0]) for r in t.rows)
    return any(k in allrows for k in ("비지배지분", "지배기업의 소유주",
                                      "연결당기순이익", "연결기타포괄", "연결당기총포괄"))


def _header_blob(t):
    return " ".join(" ".join(h) for h in t.header).replace(" ", "")


def _is_transition_table(t):
    """IFRS4→IFRS17 transition-comparison table: columns [기준서1104호(A), 기준서1117호(B),
    증감(B-A)].  Some insurers (삼성화재·한화생명) present the QUARTERLY income statement ONLY in
    this form, so it is a VALID statement — its 1117호 (B) column is the current IFRS17 figure
    (read via the col=1 path in extract_tier1).  Detected by the standard-number header."""
    hb = _header_blob(t)
    return "1117호" in hb and ("1104호" in hb or "증감" in hb or "(B-A)" in hb or "(B)" in hb)


def _ytd_col(t):
    """For a quarterly statement laid out as [3개월, 누적, 3개월, 누적] (당기 3-month / 당기
    YTD / 전기 3-month / 전기 YTD), the schema wants the YTD (누적) column, not the 3-month
    one.  Return the data-column index of the current-period 누적 (1 when 3개월 precedes 누적,
    which is the standard order; 0 otherwise / non-quarterly)."""
    hb = _header_blob(t)
    if "누적" not in hb or "3개월" not in hb:
        return 0
    return 1 if hb.find("3개월") < hb.find("누적") else 0


# net-income line labels: annual statements say 당기순이익; 반기/분기보고서 say 반기순이익/분기순이익.
NI_LABELS = ("당기순이익", "반기순이익", "분기순이익", "계속영업")


def _is_income_statement(t):
    # Restatement-IMPACT tables carry the SAME line labels (보험손익/영업이익/법인세/당기순이익) as
    # the real statement but their COLUMNS are [소급 전, 재작성효과, 소급 후] of a PRIOR period —
    # never the current statement.  Detect by HEADER (not caption): the caption is unreliable
    # — a real quarterly statement's caption is often a long accounting-policy paragraph that
    # happens to mention "재작성/미치는 영향", while a legit statement footnote may say
    # "…소급재작성 하지 아니하였으며…".  The restatement table's *header columns* are the tell.
    # (Transition 1104↔1117 tables are KEPT — their 1117 column is the real current statement.)
    hb = _header_blob(t)
    if any(k in hb for k in ("소급", "재작성", "수정전", "수정후")):
        return False
    labs = " ".join(_label(r) for r in t.rows)
    has_top = any(k in labs for k in INCOME_PROFIT_LABELS)
    has_op = "영업이익" in labs
    has_tax = "법인세" in labs
    has_ni = any(k in labs for k in NI_LABELS)
    return has_top and has_op and has_tax and has_ni


def _drop_footnote(nums):
    """Drop a leading footnote-reference cell.  DART 'numbered' income statements
    (I/II/.../X format, e.g. 하나생명) carry a 주석 column whose 'NN' refs parse as data, so
    a row reads [29, 712111734, 1031012441] — the 29 is 주29, not a value.  Heuristic: a
    leading integer with |x| ≤ 99 that is followed by a number ≥100× larger is a ref.
    Safe for tiny insurers (their statements have no 주석 value-column)."""
    if len(nums) >= 2 and float(nums[0]).is_integer() and abs(nums[0]) <= 99 \
            and abs(nums[1]) >= 100 * max(abs(nums[0]), 1):
        return nums[1:]
    return nums


def _pick_line(t, *needles, exclude=(), col=0):
    """First row whose label contains any needle (and no exclude word) with a number.
    col>0 reads that column directly (used for 1117호-transition tables, col=1 = the IFRS17
    figure in [1104, 1117, 증감]); col=0 takes the leading value (after footnote-ref strip)."""
    for r in t.rows:
        lab = _label(r).strip("[]")
        if any(n in lab for n in needles) and not any(x in lab for x in exclude):
            nums = _row_nums(r)
            if col:
                if len(nums) > col:
                    return nums[col]
            else:
                nums = _drop_footnote(nums)
                if nums:
                    return nums[0]
    return None


def _pick_priority(t, needles, exclude=(), col=0):
    """First numeric cell, trying needles in PRIORITY order (each needle scanned across
    ALL rows before the next).  Unlike _pick_line (pure row-order), this lets a
    higher-priority label win even when a lower-priority one appears earlier in the
    document — e.g. 당기순이익 beats 계속영업이익(손실) when 중단영업=0 makes
    계속영업이익==영업이익 and it is printed above 당기순이익.  col>0: read that column."""
    for n in needles:
        for r in t.rows:
            lab = _label(r).strip("[]")
            if n in lab and not any(x in lab for x in exclude):
                nums = _row_nums(r)
                if col:
                    if len(nums) > col:
                        return nums[col]
                else:
                    nums = _drop_footnote(nums)
                    if nums:
                        return nums[0]
    return None


def _income_unit_factor(ni_raw):
    """Anchor 당기순이익 into a plausible band (백만원 output).
    Plausible 당기순이익 across the insurer universe: ~1만 ~ 1천만 백만원 (=1천억~10조 원)
    for the majors, down to a few hundred 백만 for tiny insurers."""
    a = abs(ni_raw)
    # already 백만원? (당기순이익 100 ~ 5,000,000 백만 covers everything)
    if 50 <= a <= 5_000_000:
        return 1.0
    # 원 -> 백만원
    if a >= 50e6:
        return 1e-6
    # 천원 -> 백만원
    if a >= 50e3:
        return 1e-3
    return 1.0


def extract_tier1(tables, code=None):
    """⚠️ DEPRECATED (2026-06-05) — FALLBACK ONLY.  Tier-1 now comes from the DART
    standardized FS API (scripts/fetch_dart_fs.py), per owner directive: the income
    statement is standardized there (account_id), so the HTML parsing below (전환표/재작성표
    /반기순이익/누적-column heuristics — _is_income_statement, _is_transition_table, _ytd_col,
    _drop_footnote, TIER1_HINTS, BASIS_OVERRIDE …) is no longer the primary path.  It is kept
    only as a fallback for the few (company, quarter) cells the API cannot serve (e.g. AIG
    손해, a few FY2023 early filings).  Slated to move to scripts/archive/ when supervised.

    Return dict of 백만원 values for the income-statement items, or None."""
    cands = [t for t in tables if _is_income_statement(t)]
    if not cands:
        return None
    want_basis = BASIS_OVERRIDE.get(code, "연결")
    hint = TIER1_HINTS.get(code)

    best = None
    for t in cands:
        # Which DATA column carries the current-period figure:
        #  • 1117호-transition tables → col 1 ([1104, 1117, 증감], the IFRS17 column)
        #  • [3개월, 누적] quarterly statements → the 누적(YTD) column (schema is YTD)
        #  • otherwise → col 0 (leading current-period column)
        tcol = 1 if _is_transition_table(t) else _ytd_col(t)
        ni_raw = _pick_priority(t, ("연결당기순이익", "당기순이익(손실)", "당기순이익",
                                    "반기순이익", "분기순이익",
                                    "계속영업당기순이익", "계속영업이익(손실)"), col=tcol)
        if ni_raw is None or ni_raw == 0:
            continue
        f = _income_unit_factor(ni_raw)
        ni = ni_raw * f
        if not (50 <= abs(ni) <= 5_000_000):
            continue

        def L(*needles, _col=tcol, **kw):
            v = _pick_line(t, *needles, col=_col, **kw)
            return None if v is None else round(v * f, 6)

        ins = L("순보험서비스손익") or L("보험손익", "보험서비스결과", exclude=("재보험",))
        inv = L("투자손익")
        # item 15: 기타영업수익 ONLY when it sits inside 보험영업수익 (operating).
        # In 생보 / summary tables 기타영업수익 is under investment or absent -> treat as 0.
        oth_inc = _other_op_revenue(t, f)
        oth_exp = L("기타사업비용")
        if oth_exp is None:
            oth_exp = L("기타보험비용")          # 하나생명 income-statement label variant
        op = L("영업이익", exclude=("영업외",))
        oi = L("영업외수익")
        oe = L("영업외비용")
        oth_op = L("영업외손익")
        fin_inc = L("보험금융수익", exclude=("재보험", "기타포괄"))
        fin_exp = L("보험금융비용", exclude=("재보험", "기타포괄"))
        refin_inc = L("재보험금융수익", exclude=("기타포괄",))
        refin_exp = L("재보험금융비용", exclude=("기타포괄",))
        pretax = L("법인세비용차감전순이익", "법인세차감전순이익", "법인세차감전", "세전이익")
        tax = L("법인세비용", exclude=("차감전", "차감후"))
        if tax is None:
            tax = L("법인세", exclude=("차감전", "차감후"))

        # item 19 (보험금융손익) = Σ financial in/out
        fin19 = None
        comps = [(fin_inc, +1), (fin_exp, -1), (refin_inc, +1), (refin_exp, -1)]
        if any(c is not None for c, _ in comps):
            fin19 = sum((c or 0) * s for c, s in comps)
            fin19 = round(fin19, 6)
        if fin19 is None:                        # single 순보험금융손익 line (동양/DB생명/신한 요약
            fin19 = L("순보험금융손익", exclude=("재보험",))   # 손익계산서 — no 수익/비용 split)

        rec = {
            1: ins, 15: oth_inc, 16: oth_exp, 17: inv, 19: fin19,
            20: op, 23: tax, 24: ni,
            22: pretax,
            21: (oth_op if oth_op is not None
                 else (round((oi or 0) - (oe or 0), 6) if (oi is not None or oe is not None) else None)),
        }
        # 생보 요약 손익계산서: 영업이익 = 보험손익 + 투자손익(+기타).  L("투자손익") can match a
        # GROSS sub-line — 동양: 순투자손익 (before 순보험금융손익); 신한: Ⅱ.투자손익 (with a separate
        # Ⅲ.기타손익) — so it fails the identity 영업이익 = 보험손익 + 투자손익.  Net item17 to the
        # operating residual (the schema's item17 = total non-insurance operating result).  Fires
        # ONLY when the gross fails the identity (no-op when 투자손익 is already net, e.g. FS-API):
        #   • 순보험금융손익 line present → item17 = 투자 + 보험금융 (also populates item19);
        #   • else, when there is NO separate 기타사업비용 line (생보 summary) → item17 = 영업이익 − 보험손익.
        if op is not None and ins is not None and inv is not None:
            tol = max(200.0, abs(op) * 0.01)
            if abs(ins + inv - op) > tol:
                if fin19 is not None and abs(ins + inv + fin19 - op) <= tol:
                    rec[17] = round(inv + fin19, 6)
                elif oth_exp is None or abs(oth_exp) < 1:
                    rec[17] = round(op - ins, 6)
        # 생보 발행/출재 totals (for item 3/8 derivation): the income statement carries
        # 일반보험서비스수익/비용 and 출재보험서비스수익/비용 sub-lines.
        rec["_life_rev"] = L("일반보험서비스수익")
        rec["_life_cost"] = L("일반보험서비스비용")
        rec["_life_rerev"] = L("출재보험서비스수익")
        rec["_life_recost"] = L("출재보험서비스비용")
        # plain insurance-service lines (별도) — used for item3/8 of the 생보 companies
        # whose Tier-2 note carries no rev/cost grand totals (component-decomposition &
        # comprehensive families): item3 = 보험수익 − 보험비용, item8 = 재보험수익 − 재보험비용.
        # Prefer the 기타사업비용-EXCLUSIVE cost line: 보험비용 (교보/DB생명/동양/케이디비/푸본)
        # if present, else 보험서비스비용 (신한 — has no plain 보험비용 line).  item16 carries
        # 기타사업비용 separately so this must not include it.
        rec["_is_rev"] = L("보험수익", exclude=("재보험",))
        is_cost = L("보험비용", exclude=("재보험",))
        if is_cost is None:
            is_cost = L("보험서비스비용", exclude=("재보험",))
        rec["_is_cost"] = is_cost
        rec["_is_rerev"] = L("재보험수익")
        is_recost = L("재보험비용")
        if is_recost is None:
            is_recost = L("재보험서비스비용")
        rec["_is_recost"] = is_recost

        # --- table-quality score (pick the canonical statement on the wanted basis) ---
        prio = 0
        # 1) reporting basis match (연결 vs 별도) — strongest signal
        is_conn = _is_consolidated(t)
        basis = "연결" if is_conn else "별도"
        if basis == want_basis:
            prio += 5
        # 2) full statement detail (breakdown lines, not a highlights summary)
        has_detail = (oth_exp is not None) or (fin_exp is not None) or (oi is not None)
        if has_detail:
            prio += 3
        # 3) tax present & plausible (rules out audit-text parse artifacts where 법인세≈21)
        if tax is not None and abs(tax) >= 1 and abs(tax) <= abs(ni) * 5:
            prio += 2
        # 4) income-statement identity (영업이익 = 보험손익 + 투자손익).  This is the single
        # strongest correctness signal: the 연결 statement of an insurer with non-insurance
        # subsidiaries folds them into 영업이익 and BREAKS this identity, while the 별도
        # insurer-level statement holds it.  So identity dominates the basis preference —
        # lift it OUT of `prio` into its own (higher) sort position.  Among identity-equal
        # statements, `prio` (basis +5, detail +3, tax +2) still breaks the tie, so the 4
        # golds (whose 연결 also holds the identity) keep their basis pick.
        ident_ok = (ins is not None and inv is not None and op is not None
                    and abs((ins + inv) - op) <= 0.01 * abs(op) + 1)

        # per-code statement-selection hint (dominates the generic score)
        hint_score = 0
        if hint is not None:
            if "ni" in hint and abs(ni - hint["ni"]) <= 0.01 * abs(hint["ni"]) + 1:
                hint_score += 100
            if "rev" in hint:
                rev = L("보험수익", exclude=("재보험",))
                if rev is not None and abs(rev - hint["rev"]) <= 0.01 * abs(hint["rev"]) + 1:
                    hint_score += 100

        key = (hint_score, 1 if ident_ok else 0, prio, abs(ni))
        if best is None or key > best[0]:
            best = (key, rec)
    if best is None:
        return None
    rec = best[1]
    # item16 gap-fill: the chosen statement (often 연결 highlights) may omit 기타사업비용,
    # yet a sibling statement with the SAME 보험손익 carries it.  Fill only when missing
    # (never overrides a found value -> the 4 golds, which already have item16, are
    # untouched).  Needed by the 생보 income-identity reconstruction (e.g. 푸본현대).
    if rec.get(16) is None and rec.get(1) is not None:
        target_ins = rec[1]
        for t in cands:
            ni2 = _pick_priority(t, ("연결당기순이익", "당기순이익(손실)", "당기순이익",
                                     "계속영업당기순이익"))
            ins2 = _pick_line(t, "보험손익", "보험서비스결과")
            oexp2 = _pick_line(t, "기타사업비용")
            if ni2 is None or ins2 is None or oexp2 is None:
                continue
            f2 = _income_unit_factor(ni2)
            if abs(ins2 * f2 - target_ins) <= max(1.0, 0.001 * abs(target_ins)):
                rec[16] = round(oexp2 * f2, 6)
                break
    return rec


def _other_op_revenue(t, f):
    """item 15: 기타영업수익 that is a child of 보험영업수익 (operating).
    Walk rows; track the most recent top-level (non-indented) section. Only count
    a 기타영업수익 row whose preceding section is 보험영업수익. If 기타영업수익 appears
    under 투자영업수익 (생보) -> ignore (item 15 = 0 there per gold convention)."""
    section = None
    for r in t.rows:
        raw = r[0] if r else ""
        lab = _norm(raw)
        # detect section headers (no leading 전각 space in raw, or top-level keyword)
        if any(k in lab for k in ("보험영업수익", "보험영업비용")):
            section = "ins_rev" if "수익" in lab else "ins_exp"
            continue
        if "투자영업수익" in lab or "투자서비스수익" in lab or "투자손익" in lab:
            section = "inv"
            continue
        if lab.startswith("기타영업수익") and section == "ins_rev":
            nums = _row_nums(r)
            if nums:
                return round(nums[0] * f, 6)
    return None


# --------------------------------------------------------------------------- #
# Tier 2 — 발행보험 / 재보험 analysis note (items 4,5,6,9,10,11 + 13/14 for 손보)
# --------------------------------------------------------------------------- #
SONBO_LOB = ["장기보험", "자동차보험", "일반보험"]

# row-label variants (손보 | 생보) -- matched by substring on the row label
CSM_AMORT = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "제공된 서비스의 보험계약마진")
RA_CHANGE = ("비금융위험에 대한 위험조정의 변동분", "위험해제로 인한 비금융위험에 대한 위험조정의 변동")
REV_EXPECTED = ("보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
                "보고기간에 발생한 보험서비스비용(기초 예상 측정치)",
                "예상 발생보험금 및 보험서비스비용")
COST_ACTUAL = ("발생한 보험금 및 그 밖의 발생한 보험서비스비용", "실제 발생보험금 및 보험서비스비용")


def _row_matches(r, variants):
    """True if the row label (col0 or col1) contains any variant string."""
    for c in r[:2]:
        s = _norm(c)
        for v in variants:
            if v.replace(" ", "") in s.replace(" ", ""):
                return True
    return False


def _sonbo_col_idx(t):
    """For a 손보 table with 장기/자동차/일반 columns, numeric cells appear as
    [장기, 자동차, 일반, (합계)].  Returns positions {장기:0, 자동차:1, 일반:2}."""
    return {"장기보험": 0, "자동차보험": 1, "일반보험": 2}


def _is_sonbo_lob_table(t):
    hb = " ".join(" ".join(r) for r in t.header)
    return all(k in hb for k in SONBO_LOB)


def _is_rollforward(t):
    labs = " ".join(_label(r) for r in t.rows)
    return any(k in labs for k in ("기초 보험계약", "기말 보험계약", "기초보험계약",
                                   "기말보험계약", "보험계약부채(자산)"))


def _val_at(r, pos):
    """Numeric cell at LOB position `pos` (손보) or, for 생보 (pos=None), the row TOTAL.
    The 생보 note is single-column (삼성생명) or 계약유형별 with a '계약의 유형 합계' column
    (한화생명: 사망/건강/연금저축/변액/기타 + 합계).  For the rows we extract (CSM 상각,
    RA 변동, 예상/실제 발생보험금) the contract-type components are same-sign, so the row
    total = the cell with the largest |value| (== the 합계 column)."""
    nums = _row_nums(r)
    if pos is None:
        return max(nums, key=abs) if nums else None
    return nums[pos] if len(nums) > pos else None


def _find_in_tables(tables, variants, pos, pred):
    """First (table satisfying pred) row matching `variants`, value at `pos`."""
    for t in tables:
        if not pred(t):
            continue
        for r in t.rows:
            if _row_matches(r, variants):
                v = _val_at(r, pos)
                if v is not None:
                    return v
    return None


def _sonbo_lob_tables(tables):
    """Return the four 손보 LOB analysis tables (보험수익/보험서비스비용/재보험수익/재보험비용)
    for the CURRENT period.  Each table type appears twice (당기 then 전기) — we keep the
    FIRST occurrence in document order (DART lists 당기 before 전기)."""
    out = {}
    sig = {
        "보험수익": lambda first: first == "보험수익",
        "보험서비스비용": lambda first: first.startswith("발행한 보험계약에서 생기는 보험서비스비용"),
        "재보험비용": lambda first: first.startswith("재보험자에게 지급된 보험료 배분액"),
        "재보험수익": lambda first: first.startswith("재보험자에게서 회수한 금액"),
    }
    for t in tables:
        if not _is_sonbo_lob_table(t) or _is_rollforward(t) or not t.rows:
            continue
        first = _norm(t.rows[0][0]) if t.rows[0] else ""
        for key, pred in sig.items():
            if key not in out and pred(first):
                out[key] = t
    return out


def _sonbo_row_val(t, variants, pos):
    """Value at LOB position `pos` for the row in `t` matching `variants`."""
    if t is None:
        return None
    for r in t.rows:
        if _row_matches(r, variants):
            v = _val_at(r, pos)
            if v is not None:
                return v
    return None


def _sonbo_total(t, pos):
    """First (total) row value of an analysis table at LOB position `pos`."""
    if t is None or not t.rows:
        return None
    return _val_at(t.rows[0], pos)


def extract_tier2_sonbo(tables):
    """손보: items 4,5,6 from 보험수익/보험서비스비용 (장기 col); 9,10,11 from 재보험 notes;
    13/14 from 자동차/일반 totals across the four LOB tables."""
    tabs = _sonbo_lob_tables(tables)
    if not tabs:
        return {}
    rev_t = tabs.get("보험수익")
    cost_t = tabs.get("보험서비스비용")
    rec_t = tabs.get("재보험비용")
    rer_t = tabs.get("재보험수익")
    P = _sonbo_col_idx(rev_t or cost_t or rec_t or rer_t)
    p_jang = P["장기보험"]

    out = {}
    csm = _sonbo_row_val(rev_t, CSM_AMORT, p_jang)
    ra = _sonbo_row_val(rev_t, RA_CHANGE, p_jang)
    rev_exp = _sonbo_row_val(rev_t, REV_EXPECTED, p_jang)
    cost_act = _sonbo_row_val(cost_t, COST_ACTUAL, p_jang)
    re_csm = _sonbo_row_val(rec_t, CSM_AMORT, p_jang)
    re_ra = _sonbo_row_val(rec_t, RA_CHANGE, p_jang)
    re_rev = _sonbo_row_val(rer_t, COST_ACTUAL, p_jang)
    re_cost_exp = _sonbo_row_val(rec_t, REV_EXPECTED, p_jang)

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    # 장기-column totals (for items 3/7/8/12 derivation downstream)
    out["_jang_rev"] = _sonbo_total(rev_t, p_jang)
    out["_jang_cost"] = _sonbo_total(cost_t, p_jang)
    out["_jang_rerev"] = _sonbo_total(rer_t, p_jang)
    out["_jang_recost"] = _sonbo_total(rec_t, p_jang)

    # 13/14 — 자동차/일반 손익 = (보험수익 − 보험서비스비용 + 재보험수익 − 재보험비용) totals
    for item_no, lob in ((13, "자동차보험"), (14, "일반보험")):
        p = P[lob]
        rev = _sonbo_total(rev_t, p)
        cost = _sonbo_total(cost_t, p)
        re_r = _sonbo_total(rer_t, p)
        re_c = _sonbo_total(rec_t, p)
        if rev is None and cost is None:
            continue
        out[item_no] = (rev or 0) - (cost or 0) + (re_r or 0) - (re_c or 0)
    return out


# Format-B 손보 note ('(재)보험손익 상세내역' — 메리츠).  Distinct row labels & a single
# structured table with 4 columns [장기(GMM), 일반-1, 자동차, 일반-2(해외)].
B_CSM = ("당기손익으로 인식한 보험계약마진 금액", "서비스제공에 따른 보험계약마진의 변동")
B_RA = ("위험해제에 따른 위험조정 변동", "위험해제에 따른 비금융위험에 대한 위험조정의 변동")
B_REV_EXP = ("예상보험금 및 보험서비스비용",)
B_COST_ACT = ("보험금 및 보험서비스비용",)            # 보험서비스비용 section
B_RE_REV = ("회수가능 보험금 및 보험서비스비용",)      # 재보험수익 section
B_RE_COST = ("회수예상 보험금 및 보험서비스비용",)     # 재보험비용 section


def _b_note_table(tables):
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(_row_matches(r, B_CSM) for r in t.rows):
                return t
    return None


def extract_tier2_sonbo_structured(tables):
    """Format-B 손보 note (메리츠).  Sections delimited by header rows
    보험수익 / 보험서비스비용 / 재보험수익 / 재보험비용 / 총 보험서비스결과.
    col0 = 장기(GMM); 자동차 & 일반 read from the '총 보험서비스결과' row."""
    t = _b_note_table(tables)
    if t is None:
        return {}
    out = {}
    # Layout drift: 분기/반기 notes double every LOB cell into [3개월, 누적] (read 누적 to match
    # the YTD statement); the annual report is single-period.  st = cell width per LOB.
    hb = " ".join(" ".join(h) for h in t.header)
    st = 2 if ("3개월" in hb and "누적" in hb) else 1
    section = None
    sect_keys = {"보험수익": "rev", "보험서비스비용": "cost",
                 "재보험수익": "re_rev", "재보험비용": "re_cost",
                 "총 보험서비스결과": "result"}
    vals = {}  # (section, kind) -> 장기(GMM) 누적 value

    def col0(r):
        nums = _row_nums(r)
        if not nums:
            return None
        return nums[st - 1] if len(nums) > st - 1 else nums[0]

    totals = {}  # 'rev'/'cost'/'re_rev'/'re_cost' -> col0 of the '총 ...' row
    total_labels = {"총 보험수익": "rev", "총 보험서비스비용": "cost",
                    "총 재보험수익": "re_rev", "총 재보험비용": "re_cost"}
    result_row = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in total_labels:
            totals[total_labels[lab]] = col0(r)
        if lab in sect_keys and (len(_row_nums(r)) == 0 or lab.startswith("총") or lab == "총 보험서비스결과"):
            if lab == "총 보험서비스결과":
                result_row = r
            else:
                section = sect_keys[lab]
            # a pure section header has no numbers
            if not _row_nums(r):
                continue
        if section == "rev":
            if _row_matches(r, B_CSM):
                vals["csm"] = col0(r)
            elif _row_matches(r, B_RA):
                vals["ra"] = col0(r)
            elif _row_matches(r, B_REV_EXP):
                vals["rev_exp"] = col0(r)
        elif section == "cost":
            if _row_matches(r, B_COST_ACT):
                vals["cost_act"] = col0(r)
        elif section == "re_rev":
            if _row_matches(r, B_RE_REV):
                vals["re_rev"] = col0(r)
        elif section == "re_cost":
            if _row_matches(r, B_RE_COST):
                vals["re_cost_exp"] = col0(r)
            elif _row_matches(r, B_CSM):
                vals["re_csm"] = col0(r)
            elif _row_matches(r, B_RA):
                vals["re_ra"] = col0(r)

    if vals.get("csm") is not None:
        out[4] = abs(vals["csm"])
    if vals.get("ra") is not None:
        out[5] = abs(vals["ra"])
    if vals.get("rev_exp") is not None and vals.get("cost_act") is not None:
        out[6] = abs(vals["rev_exp"]) - abs(vals["cost_act"])
    if vals.get("re_csm") is not None:
        out[9] = -abs(vals["re_csm"])
    if vals.get("re_ra") is not None:
        out[10] = -abs(vals["re_ra"])
    if vals.get("re_rev") is not None and vals.get("re_cost_exp") is not None:
        out[11] = abs(vals["re_rev"]) - abs(vals["re_cost_exp"])

    # 장기-column (GMM, col0) totals for items 3/7/8/12 derivation
    if totals.get("rev") is not None:
        out["_jang_rev"] = totals["rev"]
    if totals.get("cost") is not None:
        out["_jang_cost"] = totals["cost"]
    if totals.get("re_rev") is not None:
        out["_jang_rerev"] = totals["re_rev"]
    if totals.get("re_cost") is not None:
        out["_jang_recost"] = totals["re_cost"]

    # 13/14 from the '총 보험서비스결과' row.  Single-period cols [장기, 일반-1, 자동차, 일반-2];
    # 분기/반기 doubles each LOB into [3개월, 누적] -> read 누적 at index st*pos+(st-1).
    if result_row is not None:
        nums = _row_nums(result_row)
        if len(nums) >= 3 * st:
            g1, g2 = 2 * st - 1, 4 * st - 1
            out[13] = nums[3 * st - 1]                                # 자동차 (누적)
            out[14] = nums[g1] + (nums[g2] if len(nums) > g2 else 0)  # 일반 (PAA split)
    return out


def _header_has_overseas(t):
    hb = " ".join(" ".join(h) for h in t.header)
    return "해외보험" in hb or "해외" in hb


LIFE_SECTIONS = ("재보험수익", "재보험비용", "보험서비스비용", "보험수익")


def _row_section(r):
    """If the row label is prefixed with a section keyword (한화-style
    '보험수익, …' / '재보험비용, …'), return it, else None.  Order matters: check the
    재보험* prefixes before the plain 보험* ones."""
    lab = (_norm(r[0]) + " " + _norm(r[1] if len(r) > 1 else "")).replace(" ", "")
    for sec in LIFE_SECTIONS:
        if lab.startswith(sec.replace(" ", "")):
            return sec
    return None


def _life_note_total(t, variants, section=None):
    """Domestic 합계 for a 생보 note row: the embedded '계약의 유형 합계' = the max-abs
    numeric of the row (components are same-sign).  If `section` is given and the row is
    section-prefixed (한화-style), require it to match.  Returns None if no match."""
    for r in t.rows:
        if not _row_matches(r, variants):
            continue
        rsec = _row_section(r)
        if section is not None and rsec is not None and rsec != section:
            continue
        nums = _row_nums(r)
        if nums:
            return max(nums, key=abs)
    return None


def _pick_life_table(tables, must_have, context_any, section=None, prefer_no_overseas=True):
    """Among 생보 analysis tables that (a) are not rollforwards, (b) contain a row matching
    `must_have` (in `section` when the row is section-prefixed), and (c) carry one of
    `context_any` substrings, return the best: prefer tables WITHOUT 해외 columns (domestic
    합계 matches the gold), then the simpler note (fewest columns)."""
    cands = []
    for t in tables:
        if _is_rollforward(t):
            continue
        hit = False
        for r in t.rows:
            if not _row_matches(r, must_have):
                continue
            rsec = _row_section(r)
            if section is not None and rsec is not None and rsec != section:
                continue
            hit = True
            break
        if not hit:
            continue
        blob = (t.caption or "") + " " + " ".join(_label(r) + " " + _label(r, 1) for r in t.rows)
        if context_any and not any(c in blob for c in context_any):
            continue
        cands.append(t)
    if not cands:
        return None
    cands.sort(key=lambda t: (1 if (prefer_no_overseas and _header_has_overseas(t)) else 0,
                              max((len(_row_nums(r)) for r in t.rows), default=0)))
    return cands[0]


def extract_tier2_life(tables):
    """생보: items 4,5,6,9,10,11 from the 발행/출재 analysis notes (domestic 합계).
    삼성생명: single 발행 column.  한화생명: 계약유형별 columns + 합계 (excl. 해외)."""
    out = {}
    REV_CTX = ("일반보험서비스수익", "보험수익", "발행한 보험계약")
    COST_CTX = ("일반보험서비스비용", "발행한 보험계약에서 생기는 보험서비스비용", "보험서비스비용")
    RECOST_CTX = ("출재보험서비스비용", "재보험비용", "재보험자에게 지급")
    REREV_CTX = ("출재보험서비스수익", "재보험수익", "재보험자에게서 회수")

    rev_t = _pick_life_table(tables, CSM_AMORT, REV_CTX, section="보험수익")
    cost_t = _pick_life_table(tables, COST_ACTUAL, COST_CTX, section="보험서비스비용")
    rec_t = _pick_life_table(tables, CSM_AMORT, RECOST_CTX, section="재보험비용")
    rer_t = _pick_life_table(tables, COST_ACTUAL, REREV_CTX, section="재보험수익")

    csm = _life_note_total(rev_t, CSM_AMORT, "보험수익") if rev_t else None
    ra = _life_note_total(rev_t, RA_CHANGE, "보험수익") if rev_t else None
    rev_exp = _life_note_total(rev_t, REV_EXPECTED, "보험수익") if rev_t else None
    cost_act = _life_note_total(cost_t, COST_ACTUAL, "보험서비스비용") if cost_t else None
    re_csm = _life_note_total(rec_t, CSM_AMORT, "재보험비용") if rec_t else None
    re_ra = _life_note_total(rec_t, RA_CHANGE, "재보험비용") if rec_t else None
    re_rev = _life_note_total(rer_t, COST_ACTUAL, "재보험수익") if rer_t else None
    re_cost_exp = _life_note_total(rec_t, REV_EXPECTED, "재보험비용") if rec_t else None

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)
    return out


def extract_tier2_abl(tables):
    """에이비엘생명 (KR0070).  Its IFRS17 보험수익/재보험비용 reconciliation note uses a
    [구분 | 당기 | 전기] TWO-PERIOD header, not a 계약유형별 합계 layout.  The generic
    extract_tier2_life reads each leg via _life_note_total = max(nums, key=abs), which picks
    the LARGER cell — and here 전기 > 당기 (2025.4Q CSM 88,926 > 82,804; RA 12,282 > 8,346),
    so the master published the PRIOR-period column (a 당기/전기 leg bug, audit 2026-06-08).
    Fix: read the 당기 column EXPLICITLY (= first data cell).  item6/11(예실차) is only a
    partial premium-side 경험조정 here → left to the generic closure (residual→기타)."""
    out = {}

    def find(cap_needs, cap_excl=()):
        needs = [c.replace(" ", "") for c in cap_needs]
        excl = [e.replace(" ", "") for e in cap_excl]
        for t in tables:
            if _is_rollforward(t):
                continue
            capf = _norm(t.caption or "").replace(" ", "")
            if all(n in capf for n in needs) and not any(e in capf for e in excl):
                return t
        return None

    def dangi(t, *labels):
        """First numeric (= 당기 column) of the first row whose col0 label matches any label."""
        if t is None:
            return None
        keys = [l.replace(" ", "") for l in labels]
        for r in t.rows:
            lab = _label(r).replace(" ", "")
            if any(k in lab for k in keys):
                nums = _row_nums(r)
                if nums:
                    return nums[0]
        return None

    rev_t = find(["잔여보장", "회수", "보험수익"], cap_excl=("재보험",))
    re_t = find(["잔여보장", "회수", "재보험"])
    csm = dangi(rev_t, "서비스의이전으로", "인식한 보험계약마진")
    ra = dangi(rev_t, "비금융위험에 대한 위험조정")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    re_csm = dangi(re_t, "서비스의이전으로", "인식한 보험계약마진")
    re_ra = dangi(re_t, "비금융위험에 대한 위험조정")
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out


# =========================================================================== #
# Per-company Tier-2 handlers (FY2025+ annual notes).
# Each returns {item_no: 백만원} + hidden 장기-block totals.  Where only a single
# 장기 net is recoverable, the handler emits _jang_net (assemble sets item2 = it,
# leaving item3/7/8 None).  Note units differ by company; each handler scales to
# 백만원 internally (손보 현대 = 원 /1e6; 한화 = 천원 /1e3; everyone else 백만원).
# Ported from the tested probe files (_plprobe_*.py); see those for derivation.
# =========================================================================== #
def _lab0(r):
    return _norm(r[0]).replace(" ", "") if r else ""


def _row_by_label(t, *subs, exact=False):
    """First row whose col0 label (spaces stripped) matches any sub."""
    for r in t.rows:
        lab = _lab0(r)
        for s in subs:
            s2 = s.replace(" ", "")
            if (lab == s2) if exact else (s2 in lab):
                return r
    return None


def _firstlab(t, *needles, exclude=()):
    """First numeric cell of the first row whose col0/col1 label contains a needle."""
    if t is None:
        return None
    for r in t.rows:
        lab = (_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles) \
                and not any(e.replace(" ", "") in lab for e in exclude):
            ns = _row_nums(r)
            if ns:
                return ns[0]
    return None


def _sum_split(t, needle_groups):
    tot = 0.0
    found = False
    for nd in needle_groups:
        v = _firstlab(t, nd)
        if v is not None:
            tot += v
            found = True
    return tot if found else None


def _scale(out, factor, keys):
    for k in keys:
        if out.get(k) is not None:
            out[k] = out[k] * factor
    return out


# ----------------------------- KB 손보 (KR0010) ---------------------------- #
def _kb_note(tables, item1=None):
    # KB publishes this note TWICE — 연결(consolidated, larger 총보험서비스결과) then 별도
    # (separate).  Tier-1 item1 is 별도 from 2024 on but 연결 in FY2023 (FS-API absent → HTML 연결
    # fallback), so select the note whose 총보험서비스결과 합계 matches the pipeline's item1 rather
    # than a fixed 연결/별도 rule.  No <당기> filter in the candidate gate: the 별도 Q4 note has a
    # bare caption (no <당기>), which the old filter wrongly excluded → forced the 연결 note.
    cands = []
    for t in tables:
        cap = t.caption or ""
        if "보험손익" not in cap or "상세내역" not in cap:
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not all(k in hb for k in ("장기", "일반", "자동차")):
            continue
        if _row_by_label(t, "총 보험서비스결과") is None:
            continue
        cands.append(t)
    if not cands:
        return None

    def jang_total(t):
        r = _row_by_label(t, "총 보험서비스결과")
        n = _row_nums(r) if r else []
        return n[-1] if n else None
    if item1 is not None:
        scored = [(t, jang_total(t)) for t in cands]
        scored = [(t, tot) for t, tot in scored if tot is not None]
        if scored:
            scored.sort(key=lambda c: abs(c[1] - item1))
            if abs(scored[0][1] - item1) <= 0.05 * abs(item1) + 2:
                return scored[0][0]
    # fallback (item1 unavailable): old behaviour — period-tagged note, largest 총보험수익.
    tagged = [t for t in cands
              if "<당기>" in (t.caption or "") or "<당분기>" in (t.caption or "")]
    pool = tagged or cands

    def jang_rev(t):
        r = _row_by_label(t, "총 보험수익")
        n = _row_nums(r) if r else []
        return n[0] if n else 0
    pool.sort(key=jang_rev, reverse=True)
    return pool[0]


def _kb_quarterly_note(tables):
    """KB 분기/반기 '보험손익의 상세내역' note — header has 3개월 / 누적 (and no <당기>)."""
    for t in tables:
        cap = t.caption or ""
        if "보험손익" not in cap or "상세" not in cap:
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if "누적" not in hb or not all(k in hb for k in ("장기", "일반", "자동차")):
            continue
        if _row_by_label(t, "총 보험서비스결과") is not None:
            return t
    return None


def extract_tier2_kb_quarterly(t):
    """KB 분기 note: columns are [3개월 …, 누적 …]; the schema is YTD so read the 누적 half.
    Recovers the gold-clean decomposition: 원수 CSM상각(4)/위험조정(5), 재보험 CSM상각(9)/
    위험조정(10) from the GMM 장기 column, and 자동차(13) from 총 보험서비스결과.  The segment
    손익 (장기 item2 / 일반 item14) is NOT emitted here: KB nets 기타사업비용 BY SEGMENT in a
    separate table, so 총 보험서비스결과's 장기/일반 are pre-기타사업비용 and would be wrong; that
    allocation + Tier-1 item1 come from elsewhere (DART FS API)."""
    def cum0(r):                      # first value of the 누적 half = GMM 장기 column
        if r is None:
            return None
        n = _row_nums(r)
        return n[len(n) // 2] if n else None

    out = {}
    csm = cum0(_row_by_label(t, "보험계약마진 상각", "제공된 서비스의 보험계약마진"))
    re_csm = cum0(_row_by_label(t, "제공받은 서비스의 재보험계약마진"))
    ra1 = ra2 = None
    seen = 0
    for r in t.rows:
        if "위험해제로인한위험조정의변동" in _lab0(r):
            seen += 1
            if seen == 1:
                ra1 = cum0(r)          # 보험수익 section (원수)
            elif seen == 2:
                ra2 = cum0(r)          # 재보험비용 section (출재)
    if csm is not None:
        out[4] = abs(csm)
    if ra1 is not None:
        out[5] = abs(ra1)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if ra2 is not None:
        out[10] = -abs(ra2)
    res = _row_nums(_row_by_label(t, "총 보험서비스결과"))
    if res:                            # 누적 half LOB layout [장기, 일반, 자동차, 해외, 합계]
        cum = res[len(res) // 2:]
        if len(cum) >= 3:
            out[13] = cum[2]           # 자동차 (gold-clean; no 기타사업비용 allocation)
    return out


def extract_tier2_kb(tables, item1=None):
    t = _kb_note(tables, item1=item1)
    if t is None:
        qt = _kb_quarterly_note(tables)        # KB 분기: 누적-column decomposition (KR0010 only)
        return extract_tier2_kb_quarterly(qt) if qt is not None else {}
    out = {}
    # Interim 3개월/누적 split note (Q3): read the 누적 half so the YTD decomposition matches the
    # YTD income statement (item1).  Annual/Q1 notes have no split → first-column behaviour.
    hb = " ".join(" ".join(h) for h in t.header)
    _cum = ("3개월" in hb and "누적" in hb)

    def _pick(n):
        if not n:
            return None
        return n[len(n) // 2] if _cum else n[0]

    def jang(r):
        if r is None:
            return None
        return _pick(_row_nums(r))
    csm = jang(_row_by_label(t, "제공된 서비스의 보험계약마진", "보험계약마진 상각"))
    ra = jang(_row_by_label(t, "위험해제로 인한 위험조정의 변동"))
    rev_exp = jang(_row_by_label(t, "예상 보험금 및 보험서비스비용"))
    cost_act = None
    for r in t.rows:
        if _lab0(r) == "보험금및보험서비스비용":
            cost_act = _pick(_row_nums(r))
            break
    re_csm = jang(_row_by_label(t, "제공받은 서비스의 재보험계약마진"))
    re_cost_exp = jang(_row_by_label(t, "회수예상 보험금 및 보험서비스비용"))
    re_ra = None
    seen_ra = 0
    for r in t.rows:
        if "위험해제로인한위험조정의변동" in _lab0(r):
            seen_ra += 1
            if seen_ra == 2:
                re_ra = _pick(_row_nums(r))
    re_rev = jang(_row_by_label(t, "회수가능 보험금 및 보험서비스비용"))

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    tr = _row_nums(_row_by_label(t, "총 보험수익"))
    tc = _row_nums(_row_by_label(t, "총 보험서비스비용"))
    trr = _row_nums(_row_by_label(t, "총 재보험수익"))
    trc = _row_nums(_row_by_label(t, "총 재보험비용"))
    out["_jang_rev"] = _pick(tr)
    out["_jang_cost"] = abs(_pick(tc)) if tc else None
    out["_jang_rerev"] = _pick(trr)
    out["_jang_recost"] = abs(_pick(trc)) if trc else None

    res = _row_nums(_row_by_label(t, "총 보험서비스결과"))
    if res:
        half = res[len(res) // 2:] if _cum else res
        if len(half) >= 5:
            out["_jang_net"] = half[0]
            out[13] = half[2]
            out[14] = half[1] + half[3]
    return out  # 백만원 already


# ---------------------------- 현대 손보 (KR0009) --------------------------- #
def _hyundai_period_marker(tables, ti):
    """당기/전기 marker for the NEW-form note: each leg table is preceded by a 1-2 row
    header table whose last row is exactly '당기'/'당분기' (annual/quarterly) or
    '전기'/'전분기'.  Scan the 2 preceding tables; None when no marker found."""
    for j in range(ti - 1, max(ti - 3, -1), -1):
        for r in tables[j].rows:
            lab = _lab0(r)
            if lab in ("당기", "당분기", "당반기"):
                return "cur"
            if lab in ("전기", "전분기", "전반기"):
                return "prev"
    return None


def _hyundai_section(tables, first_label_starts):
    cands = []
    for ti, t in enumerate(tables):
        if not t.rows:
            continue
        if _lab0(t.rows[0]).startswith(first_label_starts.replace(" ", "")):
            cands.append((ti, t))
    if not cands:
        return None
    # 당기/당분기 leg only — the 전기/전분기 twin has IDENTICAL row labels, and its row0
    # magnitude can exceed the current period's (mag-sort alone is not safe).
    cur = [c for c in cands if _hyundai_period_marker(tables, c[0]) == "cur"]
    if cur:
        cands = cur

    def mag(c):
        n = _row_nums(c[1].rows[0])
        return abs(n[0]) if n else 0
    cands.sort(key=mag, reverse=True)
    return cands[0][1]


def _hyundai_lob_summary(tables):
    for t in tables:
        cap = t.caption or ""
        if "보험종목별" in cap and "수지" in cap:
            hb = " ".join(" ".join(h) for h in t.header)
            if "장기" in hb and "자동차" in hb and "일반" in hb:
                r = _row_by_label(t, "보험손익")
                if r:
                    return t, r
    return None, None


def _hyundai_old_components(tables):
    """현대해상 OLD form (2023.4Q–2025.1Q): one combined component table, header
    [구분, 장기, 자동차, 일반, 합계], col0 = 장기.  Two section-header rows ('보험수익' /
    '재보험서비스비용', each label-only).  Unit 천원 → /1e3.  Returns {4,5,9,10}
    (원수/재보 CSM상각·위험조정).  item6/11 (예실차) are not disclosed in this form.  The NEW
    form (2025.2Q+) is handled by extract_tier2_hyundai's _hyundai_section path, which already
    populates 4/5/9/10 — so this is merged ONLY when those are None."""
    comp = None
    for t in tables:
        labs = [_lab0(r) for r in t.rows]
        if labs and labs[0].startswith("보험수익") \
                and any(l.startswith("재보험서비스비용") for l in labs[1:]):
            comp = t
            break
    if comp is None:
        return {}
    out, sec = {}, None
    for r in comp.rows:
        lab = _lab0(r)
        if lab.startswith("보험수익"):
            sec = "dir"
            continue
        if lab.startswith("재보험서비스비용"):
            sec = "re"
            continue
        n = _row_nums(r)
        col0 = n[0] if n else None      # 장기
        if col0 is None:
            continue
        if lab.startswith("위험조정변동"):
            if sec == "dir" and 5 not in out:
                out[5] = col0
            elif sec == "re" and 10 not in out:
                out[10] = -col0
        elif lab.startswith("보험계약마진상각"):
            if sec == "dir" and 4 not in out:
                out[4] = col0
            elif sec == "re" and 9 not in out:
                out[9] = -col0
    _scale(out, 1e-3, (4, 5, 9, 10))    # 천원 → 백만원
    return out


def _hyundai_old_split(tables):
    """현대해상 OLDER split layout (2023.1Q–2023.3Q): 원수/재보 CSM·RA in ONE table captioned
    '(1) 당분기' (반기보고서: '(1) 당반기'), header [구분 | 보험계약부채 | 재보험(계약)자산].
      - 2023.2Q/3Q: each leg split into (3개월, 누적) → numerics [원수3M, 원수누적, 재보3M,
        재보누적] → read 누적 ([1] 원수, [3] 재보).
      - 2023.1Q: single column per leg (header '재보험자산', no 3개월/누적) → [원수, 재보].
    천원→/1e3.  Returns {4,5,9,10}; item6/11 not separable.  {} unless the table matches."""
    comp = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if not (cap.startswith("(1)당분기") or cap.startswith("(1)당반기")):
            continue
        hb = _header_blob(t)
        if "보험계약부채" not in hb or "재보험" not in hb:
            continue
        labs = [_lab0(r) for r in t.rows]
        if any(l.startswith("보험계약마진상각") for l in labs) \
                and any(l.startswith("위험조정변동") for l in labs):
            comp = t
            break
    if comp is None:
        return {}
    hb = _header_blob(comp)
    paired = "3개월" in hb and "누적" in hb
    out = {}
    for r in comp.rows:
        lab = _lab0(r)
        n = _row_nums(r)
        if paired:
            if len(n) < 4:
                continue
            dir_cum, re_cum = n[1], n[3]  # 원수 누적, 재보 누적
        else:
            if len(n) < 2:
                continue
            dir_cum, re_cum = n[0], n[1]  # 원수, 재보 (single-column 1Q)
        if lab.startswith("보험계약마진상각"):
            out.setdefault(4, dir_cum)
            out.setdefault(9, -re_cum)
        elif lab.startswith("위험조정변동"):
            out.setdefault(5, dir_cum)
            out.setdefault(10, -re_cum)
    _scale(out, 1e-3, (4, 5, 9, 10))      # 천원 → 백만원
    return out


def extract_tier2_hyundai(tables):
    out = {}
    rev_t = _hyundai_section(tables, "보험수익,")
    cost_t = _hyundai_section(tables, "보험서비스비용,")
    rerev_t = _hyundai_section(tables, "재보험수익,")
    recost_t = _hyundai_section(tables, "재보험비용,")
    # 분기보고서 NEW form (2025.2Q/3Q·2026.1Q): the cost / 재보험수익 legs DROP the
    # '보험서비스비용,'/'재보험수익,' row0 prefix — row0 reads '발생한 보험금 및 그 밖의 발생한
    # 보험서비스비용(/재보험수익)에 따른 증가분…'.  The annual (감사보고서) keeps the prefixed
    # form, so these are pure fallbacks (item6/11 were silently None on quarters without them).
    if cost_t is None:
        cost_t = _hyundai_section(tables, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    if rerev_t is None:
        rerev_t = _hyundai_section(tables, "발생한 보험금 및 그 밖의 발생한 재보험수익")

    def jang(t, *subs):
        if t is None:
            return None
        r = _row_by_label(t, *subs)
        if r is None:
            return None
        n = _row_nums(r)
        if not n:
            return None
        # 분기보고서 NEW form: each LOB splits into (3개월, 누적) column pairs → 장기 누적
        # = n[1].  (연차/1Q: one column per LOB → 장기 = n[0].)  Without this, 반기/3Q
        # quarters picked the 3-month leg (e.g. 2025.3Q item4 248,784 vs YTD 730,615).
        if len(n) >= 2 and "3개월" in _header_blob(t) and "누적" in _header_blob(t):
            return n[1]
        return n[0]

    csm = jang(rev_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = jang(rev_t, "비금융위험에 대한 위험조정의 변동분")
    rev_exp = jang(rev_t, "보고기간에 발생한 보험서비스비용")
    cost_act = jang(cost_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_csm = jang(recost_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = jang(recost_t, "비금융위험에 대한 위험조정의 변동분")
    re_rev = jang(rerev_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용",
                  "발생한 보험금 및 그 밖의 발생한 재보험수익")
    re_cost_exp = jang(recost_t, "보고기간에 발생한 보험서비스비용")

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    # LOB totals [장기, 자동차, 일반] from the 분석공시 (gold-anchored, 2026.1Q):
    #   rev    = single-row 합계-variant '보험수익' table (PAA twin has 장기=0 → max-|장기| pick)
    #   cost   = total row '보험서비스 비용에 따른 총 증가분…' inside cost_t
    #   rerev  = total row '재보험수익에 따른 총 증가분…' inside rerev_t
    #   recost = single-row '재보험서비스비용' 합계 variant (PAA twin smaller → max-|장기|)
    # assemble derives 3 = rev−cost, 8 = rerev−recost, 7/12 residuals, 2 = 3+8
    # (gold: 3=279,302 / 8=−5,993 / 7=127,592 / 12=−4,504).  13/14 = full gross LOB P&L
    # incl. reinsurance (gold 자동차 935,162−944,833−20−1,200 = −10,891 exact) — replaces the
    # LOB-summary netted legs (those allocate 기타사업비용 into each LOB; schema keeps item16).
    def _ytd_triple(t, row):
        n = _row_nums(row)
        if not n:
            return None
        hb = _header_blob(t)
        trip = n[1::2][:3] if ("3개월" in hb and "누적" in hb and len(n) >= 6) else n[:3]
        return trip if len(trip) == 3 else None

    def total_row_triple(t, *labels):
        if t is None:
            return None
        r = _row_by_label(t, *labels)
        return _ytd_triple(t, r) if r is not None else None

    def single_row_triple(label):
        best = None
        for ti2, st in enumerate(tables):
            if not st.rows or len(st.rows) > 2 or _lab0(st.rows[0]) != label:
                continue
            if _hyundai_period_marker(tables, ti2) != "cur":
                continue
            trip = _ytd_triple(st, st.rows[0])
            # >= : on 장기-ties (연결/별도 duplicates share the 장기 column) keep the LATER
            # table — DART body order is 연결주석 → 별도주석, and KR0009 basis is 별도
            # (자동차/일반 columns differ between the two).
            if trip and (best is None or abs(trip[0]) >= abs(best[0])):
                best = trip               # 합계 variant: 장기 ≠ 0 / PAA: 장기 = 0(or small)
        return best

    rev3 = single_row_triple("보험수익")
    cost3 = total_row_triple(cost_t, "보험서비스 비용에 따른 총 증가분", "보험서비스비용에 따른 총 증가분",
                             "발행한 보험계약에서 생기는 보험서비스비용")   # annual form
    rerev3 = total_row_triple(rerev_t, "재보험수익에 따른 총 증가분",
                              "재보험자에게서 회수한 금액에서 생기는 수익")  # annual form
    recost3 = single_row_triple("재보험서비스비용")
    if rev3 and cost3:
        out["_jang_rev"], out["_jang_cost"] = rev3[0], abs(cost3[0])
    if rerev3 and recost3:
        out["_jang_rerev"], out["_jang_recost"] = rerev3[0], abs(recost3[0])
    if rev3 and cost3 and rerev3 and recost3:
        out["_lob_gross_13"] = rev3[1] - abs(cost3[1]) + rerev3[1] - abs(recost3[1])
        out["_lob_gross_14"] = rev3[2] - abs(cost3[2]) + rerev3[2] - abs(recost3[2])
    # note items are in 원 -> 백만원
    _scale(out, 1e-6, (4, 5, 6, 9, 10, 11,
                       "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost",
                       "_lob_gross_13", "_lob_gross_14"))

    # 13/14 + 장기 net from the LOB summary table (already 백만원!)
    _, sumrow = _hyundai_lob_summary(tables)
    if sumrow is not None:
        n = _row_nums(sumrow)
        if len(n) >= 4:
            out[13] = n[2]          # 자동차
            out[14] = n[0]          # 일반
            out["_jang_net"] = n[1]  # 장기 net (no clean rev/cost split)
    # OLD form (2023.4Q–2025.1Q): the NEW _hyundai_section legs above don't match the older
    # combined table, so 4/5/9/10 are still None.  Backfill from the combined component table;
    # merge ONLY when None → NEW quarters (already populated) untouched.
    if any(out.get(k) is None for k in (4, 5, 9, 10)):
        for k, val in _hyundai_old_components(tables).items():
            if out.get(k) is None:
                out[k] = val
    if any(out.get(k) is None for k in (4, 5, 9, 10)):   # 2023.3Q older split layout
        for k, val in _hyundai_old_split(tables).items():
            if out.get(k) is None:
                out[k] = val
    # OLD form (≤2025.1Q) LOB totals fallback: combined [구분|장기|자동차|일반|합계] notes
    # (단위 천원) — sections 보험수익/재보험서비스비용 in one table, 보험서비스비용/재보험수익 in
    # the sibling.  Per-section 합계 row carries the LOB triple.
    if out.get("_jang_rev") is None:
        secs = {}
        for st in tables:
            if not st.rows:
                continue
            hb2 = _header_blob(st)
            if not ("장기" in hb2 and "자동차" in hb2 and "일반" in hb2):
                continue
            cap = str(getattr(st, "caption", "") or "")
            if "전" in cap.replace(" ", "")[:5]:        # (2) 전분기 / 전기 twin
                continue
            cur_sec, found = None, {}
            for r in st.rows:
                lab2 = _lab0(r)
                n3 = _row_nums(r)
                if lab2 in ("보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용") and not n3:
                    cur_sec = lab2
                elif lab2 in ("합계", "합 계") and cur_sec and len(n3) >= 4:
                    found[cur_sec] = n3[:3]
                    cur_sec = None
            for k2, v3 in found.items():
                if k2 not in secs or abs(v3[0]) > abs(secs[k2][0]):   # 누적 > 3개월
                    secs[k2] = v3
        K = 1e-3                                        # 천원 → 백만원
        rv, cv = secs.get("보험수익"), secs.get("보험서비스비용")
        rrv, rcv = secs.get("재보험수익"), secs.get("재보험서비스비용")
        if rv and cv:
            out["_jang_rev"], out["_jang_cost"] = rv[0] * K, abs(cv[0]) * K
        if rrv and rcv:
            out["_jang_rerev"], out["_jang_recost"] = rrv[0] * K, abs(rcv[0]) * K
        if rv and cv and rrv and rcv:
            out["_lob_gross_13"] = (rv[1] - abs(cv[1]) + rrv[1] - abs(rcv[1])) * K
            out["_lob_gross_14"] = (rv[2] - abs(cv[2]) + rrv[2] - abs(rcv[2])) * K
    # gross LOB legs (incl. reinsurance, 사업비 미차감) replace the LOB-summary netted 13/14 —
    # keeps the bridge item1 = 2+13+14−16 closed once item2 moves to the gross basis (3+8).
    if out.get("_lob_gross_13") is not None:
        out[13] = out.pop("_lob_gross_13")
    if out.get("_lob_gross_14") is not None:
        out[14] = out.pop("_lob_gross_14")
    return out


# ---------------------------- 한화 손보 (KR0002) --------------------------- #
def _hanwha_sep_rev_idx(tables):
    """Document index of the 별도(개별) 발행보험 '보험수익' table (당기 leg).
    한화손해 NEW filings carry the 보험수익/비용/재보험 component note TWICE — the 연결
    재무제표 주석 FIRST, then the 별도(개별) 주석 — each split into [당기, 전기].  The 연결
    leg folds in 캐롯손해보험(자동차/일반 자회사), so its PAA LOBs (자동차/일반) over-state by
    the subsidiary; only 별도 reconciles with the FS-API 별도 Tier-1 보험손익.  The 장기(GMM)
    leg is identical 별도=연결 (no subsidiary 장기 book), which is why items 4/5/6 were already
    gold-exact off the first (연결) table — but 13/14 were not.  Grand-total magnitude does NOT
    separate them (e.g. 2025.4Q 연결전기 < 별도당기), so cluster the '보험수익,'-led candidates
    by document position (a large index gap divides the 연결 block from the later 별도 block)
    and take the 당기 (first) table of the LATER (별도) cluster."""
    idxs = [ti for ti, t in enumerate(tables)
            if t.rows and _lab0(t.rows[0]).startswith("보험수익,")]
    if not idxs:
        return None
    clusters = [[idxs[0]]]
    for a, b in zip(idxs, idxs[1:]):
        (clusters[-1].append(b) if b - a < 100 else clusters.append([b]))
    return clusters[-1][0]            # later cluster = 별도 주석; its first table = 당기


def _hanwha_section_from(tables, start, first_label_starts):
    """First table at-or-after `start` whose row0 label starts with `first_label_starts`.
    Anchoring forward from the 별도 보험수익 table keeps cost/재보험 legs inside the same
    별도 block (the 연결 block is entirely earlier; within the block 당기 precedes 전기)."""
    p = first_label_starts.replace(" ", "")
    for t in tables[start:]:
        if t.rows and _lab0(t.rows[0]).startswith(p):
            return t
    return None


def extract_tier2_hanwha(tables):
    """한화손해 (KR0002): NEW standardized component note (2025.2Q+).  Each leg is a separate
    table whose row0 label is '보험수익,…' / '보험서비스비용,…' / '재보험수익,…' / '재보험비용,…',
    laid out as columns [장기, 일반, 자동차] × ([3개월, 누적] for 반기/3Q | single for Q1/연차).
    Unit 천원 → /1e3.  당기 별도 = first table of the LATER (별도) cluster — the note is filed
    TWICE (연결 주석 first, then 별도), so _hanwha_sep_rev_idx skips the 연결 block; all legs are
    then anchored forward from that index (_hanwha_section_from) to stay inside the 별도 block.
      - items 4/5 (원수 CSM상각 / 위험조정) = 장기 누적.
      - item6 (원수 예실차) = Σ(예상 보험금/손조비/유지비/투자관리비) − Σ(발생 동일 4종) — INCL
        투자관리비 (한화 convention; cf. 흥국/코리안리 EXCLUDE it).
      - items 9/10 = −(재보비용 CSM/RA) 장기 누적.
      - item11 (재보 예실차) = (재보수익 발생 보험금+손조비) − (재보비용 예상 보험금+손조비).
        Owner's gold additionally nets a '재보험비용, 보고기간 발생 (기초예상)' line not present in
        this note → item11 carries a small (~0.3% of item1) residual vs gold; assemble derives 12.
      - _jang_* totals → assemble derives 2/3/7/8/12 (all gold-exact: 2=252,200 3=250,697 8=1,503).
      - 13 자동차 / 14 일반 = PAA LOB net (원수 [rev−cost] + 재보 [회수수익−총재보험비용]), read off
        the 별도 tables.  (Earlier the 연결 leg was read by mistake, folding 캐롯손보's auto/general
        into 13/14 → ~21bn over-statement vs gold; the 별도 anchor resolves it.  gold 2025.2Q:
        13=-5,650.034  14=18,664.691, both now exact.)"""
    sep = _hanwha_sep_rev_idx(tables)
    if sep is None:
        return {}
    rev_t = tables[sep]
    cost_t = _hanwha_section_from(tables, sep, "보험서비스비용,")
    rerev_t = _hanwha_section_from(tables, sep, "재보험수익,")
    recost_t = _hanwha_section_from(tables, sep, "재보험비용,")
    summ_t = None
    for t in tables[sep:]:
        if t.rows and "재보험자에게서 회수" in _norm(t.rows[0][0]):
            summ_t = t
            break
    if not (rev_t and cost_t and recost_t):
        return {}
    rev_tot_row = None
    for r in rev_t.rows:
        if _lab0(r) == "보험수익":
            rev_tot_row = r
    rev_tot = _row_nums(rev_tot_row) if rev_tot_row else []
    if not rev_tot:
        return {}
    # LOB column order = [장기, 일반, 자동차]; paired [3개월, 누적] for 반기/3Q else single.
    paired = len(rev_tot) >= 6
    JC, GEN, AUTO = (1, 3, 5) if paired else (0, 1, 2)

    def rnum(t, *subs):
        r = _row_by_label(t, *subs) if t else None
        if r is None:
            return None
        n = _row_nums(r)
        return n[JC] if len(n) > JC else None

    def rsum(t, subs):
        s = 0.0
        any_ = False
        for sub in subs:
            x = rnum(t, sub)
            if x is not None:
                s += x
                any_ = True
        return s if any_ else None

    out = {}
    EXP = ("보험수익, 예상 보험금 (기초", "보험수익, 예상 손해조사비 (기초",
           "보험수익, 예상 유지비 (기초", "보험수익, 예상 투자관리비 (기초")
    ACT = ("보험서비스비용, 발생한 보험금", "보험서비스비용, 발생한 손해조사비",
           "보험서비스비용, 발생한 유지비", "보험서비스비용, 발생한 투자관리비")
    csm = rnum(rev_t, "보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = rnum(rev_t, "보험수익, 비금융위험에 대한 위험조정의 변동분")
    rev_exp = rsum(rev_t, EXP)
    cost_act = rsum(cost_t, ACT)
    re_csm = rnum(recost_t, "재보험비용, 서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = rnum(recost_t, "재보험비용, 비금융위험에 대한 위험조정의 변동분")
    re_rev_dev = rsum(rerev_t, ("재보험수익, 발생한 보험금", "재보험수익, 발생한 손해조사비")) \
        if rerev_t else None
    re_cost_exp = rsum(recost_t, ("재보험비용, 예상 보험금 (기초", "재보험비용, 예상 손해조사비 (기초"))
    if csm is not None:
        out[4] = csm
    if ra is not None:
        out[5] = ra
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    if re_rev_dev is not None and re_cost_exp is not None:
        out[11] = re_rev_dev - re_cost_exp

    cost_tot_row = _row_by_label(cost_t, "발행한 보험계약에서 생기는 보험서비스비용")
    cost_tot = _row_nums(cost_tot_row) if cost_tot_row else []
    re_rev_lob = _row_nums(summ_t.rows[0]) if (summ_t and summ_t.rows) else []
    re_cost_lob = _row_nums(summ_t.rows[1]) if (summ_t and len(summ_t.rows) > 1) else []
    if len(rev_tot) > JC and len(cost_tot) > JC:
        out["_jang_rev"] = rev_tot[JC]
        out["_jang_cost"] = cost_tot[JC]
    if len(re_rev_lob) > JC and len(re_cost_lob) > JC:
        out["_jang_rerev"] = re_rev_lob[JC]
        out["_jang_recost"] = re_cost_lob[JC]

    def lobnet(idx):
        rv = rev_tot[idx] if len(rev_tot) > idx else 0.0
        cv = cost_tot[idx] if len(cost_tot) > idx else 0.0
        rr = re_rev_lob[idx] if len(re_rev_lob) > idx else 0.0
        rc = re_cost_lob[idx] if len(re_cost_lob) > idx else 0.0
        return (rv - cv) + (rr - rc)
    if len(rev_tot) > AUTO and len(cost_tot) > AUTO:
        out[13] = lobnet(AUTO)
        out[14] = lobnet(GEN)
    # note is in 천원 -> 백만원
    _scale(out, 1e-3, (4, 5, 6, 9, 10, 11, 13, 14,
                       "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost"))
    return out


def extract_tier2_hanwha_old(tables):
    """한화손해 (KR0002) pre-2025.2Q component note (2023.1Q–2025.1Q).  Three single-period
    sibling tables per period block, each [장기, 일반, 자동차, 합계]:
      • 보험(영업)수익  row0='예상보험금수익' + 보험계약마진상각수익 row
      • 보험(영업)비용  row0='발생보험금비용'
      • 출재보험수익및비용  row0='출재보험수익' (2 sections: 수익 합계 then 비용 합계)
    별도(=smallest current-period grand total; 연결 folds 퇴직연금/subsidiary into 일반/자동차).
    Quarterly notes pair [3개월, 누적] → 누적 장기 at RAW cell index 5; annual = single period
    → RAW index 1.  Index RAW cells (NOT _row_nums, which drops '-' and shifts columns).
    Unit 천원 → /1e3.  item6/11 예실차 INCL 투자관리비 (한화 convention).  13/14 = pure 3-LOB
    별도 PAA net — 한화's 퇴직연금 LOB sits OUTSIDE this note and is NOT split out (differs from
    the owner's hand-built gold by that allocation, same caveat as the NEW handler).
    Returns {} for the 2025.2Q+ single-table form (caller keeps extract_tier2_hanwha)."""
    Z = lambda v: v or 0.0
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def fl(t):
        return _norm(t.rows[0][0]).replace(" ", "") if (t.rows and t.rows[0]) else ""

    def hasrow(t, kw):
        k = kw.replace(" ", "")
        return any(k in _norm(r[0]).replace(" ", "") for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]).strip("()") if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [t for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    rev_c = cands(lambda t: fl(t) == "예상보험금수익" and hasrow(t, "보험계약마진상각수익"))
    cost_c = cands(lambda t: fl(t) == "발생보험금비용")
    re_c = cands(lambda t: fl(t) == "출재보험수익" and hasrow(t, "출재보험계약마진상각비용"))
    if not (rev_c and cost_c and re_c):
        return {}

    def gtot(t):  # 별도 selector: LAST 합계 row's last numeric cell
        g = float("inf")
        for r in t.rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                ns = _row_nums(r)
                if ns:
                    g = abs(ns[-1])
        return g

    rev_t, cost_t, re_t = min(rev_c, key=gtot), min(cost_c, key=gtot), min(re_c, key=gtot)

    hb = _header_blob(rev_t)
    paired = ("3개월" in hb and "누적" in hb)
    JC, GEN, AUTO = (5, 6, 7) if paired else (1, 2, 3)   # RAW 누적-장기 / 일반 / 자동차

    def cell(t, col, *needles):
        for r in t.rows:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                return to_num(r[col]) if len(r) > col else None
        return None

    def tot(t, col, which=0):  # which-th 합계 row, RAW column `col`
        haps = [r for r in t.rows if _norm(r[0]).replace(" ", "") == "합계"]
        return to_num(haps[which][col]) if (len(haps) > which and len(haps[which]) > col) else None

    out = {}
    csm = cell(rev_t, JC, "보험계약마진상각수익")
    ra = cell(rev_t, JC, "위험조정변동수익")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    exp = sum(Z(cell(rev_t, JC, n)) for n in
              ("예상보험금수익", "예상손해조사비수익", "예상계약유지비수익", "예상투자관리비수익"))
    act = sum(Z(cell(cost_t, JC, n)) for n in
              ("발생보험금비용", "발생손해조사비", "발생계약유지비용", "발생투자관리비"))
    out[6] = exp - act                                   # 예상 − 발생 (incl 투자관리비)
    re_csm = cell(re_t, JC, "출재보험계약마진상각비용")
    re_ra = cell(re_t, JC, "출재위험조정변동비용")
    if re_csm is not None:
        out[9] = -re_csm                                 # item9/10 = −(재보비용측 raw)
    if re_ra is not None:
        out[10] = -re_ra
    re_act = sum(Z(cell(re_t, JC, n)) for n in ("발생출재보험금수익", "발생수입손해조사비"))
    re_exp = sum(Z(cell(re_t, JC, n)) for n in ("예상출재보험금비용", "예상수입손해조사비"))
    out[11] = re_act - re_exp

    out["_jang_rev"] = tot(rev_t, JC)
    out["_jang_cost"] = tot(cost_t, JC)
    out["_jang_rerev"] = tot(re_t, JC, which=0)          # 출재수익 합계
    out["_jang_recost"] = tot(re_t, JC, which=1)         # 출재비용 합계

    def lobnet(col):                                     # pure 3-LOB net (퇴직연금 NOT separated)
        return (Z(tot(rev_t, col)) - Z(tot(cost_t, col))) \
            + (Z(tot(re_t, col, 0)) - Z(tot(re_t, col, 1)))
    out[13] = lobnet(AUTO)
    out[14] = lobnet(GEN)

    _scale(out, 1e-3, (4, 5, 6, 9, 10, 11, 13, 14,
                       "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost"))
    return out


def _hanwha_dispatch(tables):
    """NEW single-table form (2025.2Q+) first; fall through to the pre-2025.2Q component note.
    The two forms are structurally disjoint, so neither can corrupt the other."""
    out = extract_tier2_hanwha(tables)
    if out and any(out.get(i) is not None for i in (4, 5, 6)):
        return out
    return extract_tier2_hanwha_old(tables)


# ----------------------------- DB 손보 (KR0011) ---------------------------- #
_S2_CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "보험계약마진 상각",
           "제공된 서비스의 보험계약마진")
_S2_RA = ("비금융위험에 대한 위험조정의 변동분", "위험조정 변동",
          "위험해제로 인한 비금융위험에 대한 위험조정의 변동")
_EXP_SPLIT = ("예상 보험금 (기초 예상 측정치)", "예상 유지비 (기초 예상 측정치)",
              "예상 손해조사비 (기초 예상 측정치)", "예상 투자관리비 (기초 예상 측정치)")
_ACT_SPLIT = ("발생한 보험금", "발생한 유지비", "발생한 손해조사비", "발생한 투자관리비")
_RE_EXP_COST = ("재보험비용, 예상 보험금 (기초 예상 측정치)",
                "재보험비용, 예상 기타 보험서비스비용 (기초 예상 측정치)",
                "보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
                "회수예상 보험금 및 기타보험서비스비용")


def _fl(t):
    return _norm(t.rows[0][0]) if t.rows else ""


def extract_tier2_db(tables):
    """DB손해 (KR0011): Tier-2 from notes "5. 보험수익 및 비용" + "6. 재보험수익 및 비용".

    The notes print 당기/전기 × 연결/별도, each laid out as 장기보험|일반보험|자동차보험 columns
    with [3개월, 누적] sub-pairs (annual report = a single 당기 column).  Gold-validated recipe
    (DB 2025.2Q gold sheet) wants the CURRENT-period 별도 figures, 누적(YTD) — the same basis as
    the FS-API Tier-1 (DB = OFS):
      - current period: a data table whose immediate predecessor is a 전기/전반기 marker row is
        the comparative — skip it (`is_prior`).
      - 별도 vs 연결: 별도 ⊆ 연결 (연결 adds the DB생명 subsidiary), so among current-period
        candidates pick the SMALLEST grand total.
    장기 원수 components (CSM상각/위험조정/예실차) sit in the first column-pair of the detail
    tables; 자동차/일반 net LOB from the summary + 재보 tables.  Emits the 4 _jang_* totals so
    `assemble` derives items 2/3/7/8/12 uniformly.  All values 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def lastlab(t):
        return _norm(t.rows[-1][0]) if (t.rows and t.rows[-1]) else ""

    def has(t, kw):
        return kw in " ".join(_norm(r[0]) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [(i, t) for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    # ≥4 numeric cols: 반기/3Q notes pair [3개월, 누적] (8 cols); Q1/annual are single-column
    # per LOB (4 cols: 장기/일반/자동차/합계).  The 연결 LOB summary carries an extra 비생명/
    # 생명 split (6 cols) — pmin (smallest grand total) still resolves to the 별도 table.
    rev_sums = cands(lambda t: _fl(t) == "보험수익" and "장기보험" in _header_blob(t)
                     and "자동차보험" in _header_blob(t)
                     and t.rows and len(_row_nums(t.rows[-1])) >= 4)
    cost_sums = cands(lambda t: _fl(t) == "보험비용" and "장기보험" in _header_blob(t)
                      and t.rows and len(_row_nums(t.rows[-1])) >= 4)
    rerev = cands(lambda t: lastlab(t) == "재보험자에게서 회수한 금액에서 생기는 수익")
    recost = cands(lambda t: lastlab(t) == "재보험자에게 지급된 보험료 배분액에서 생기는 비용")
    rev_d = cands(lambda t: _fl(t).startswith("보험수익, 예상 보험금")
                  and has(t, "서비스의 이전으로 당기손익에 인식한 보험계약마진"))
    cost_d = cands(lambda t: _fl(t).startswith("보험서비스비용, 발생한 보험금"))
    recost_d = cands(lambda t: _fl(t).startswith("재보험비용, 예상 보험금"))
    if not all((rev_sums, cost_sums, rerev, recost, rev_d, cost_d, recost_d)):
        return {}

    def pmin(cs):  # 별도 = smallest current-period grand total
        return min(cs, key=lambda it: abs(_row_nums(it[1].rows[-1])[-1]))[1]
    rs, cs, rr, rc = pmin(rev_sums), pmin(cost_sums), pmin(rerev), pmin(recost)
    rd, cd, rcd = pmin(rev_d), pmin(cost_d), pmin(recost_d)

    # 누적(YTD) offset / per-LOB stride: quarterly notes pair [3개월, 누적]; annual = single col.
    hb = _header_blob(rs)
    off, st = (1, 2) if ("3개월" in hb and "누적" in hb) else (0, 1)

    def rownums(t, *needles):
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns:
                    return ns
        return None

    def d1(t, *needles):  # 장기-원수 (first LOB) 누적-column value of the matched row
        ns = rownums(t, *needles)
        return ns[off] if (ns and len(ns) > off) else None

    def at(arr, i):
        return arr[i] if 0 <= i < len(arr) else 0.0

    def lc(lob):
        return off + lob * st

    csm, ra = d1(rd, *_S2_CSM), d1(rd, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = [d1(rd, n) for n in _EXP_SPLIT]
    act = [d1(cd, n) for n in _ACT_SPLIT]
    if None not in exp and None not in act:
        out[6] = sum(exp) - sum(act)
    re_csm, re_ra = d1(rcd, *_S2_CSM), d1(rcd, *_S2_RA)
    if re_csm is not None:                          # 재보 CSM상각/위험조정 = −(cost-side raw)
        out[9] = -re_csm                            # cost CSM is negative → item9 positive
    if re_ra is not None:
        out[10] = -re_ra
    re_act = [d1(rr, "재보험수익, 발생한 보험금"), d1(rr, "재보험수익, 발생한 손해조사비")]
    re_exp = [d1(rcd, "재보험비용, 예상 보험금"), d1(rcd, "재보험비용, 예상 기타 보험서비스비용")]
    if None not in re_act and None not in re_exp:
        out[11] = sum(re_act) - sum(re_exp)

    rsr, csr = _row_nums(rs.rows[-1]), _row_nums(cs.rows[-1])
    rrr, rcr = _row_nums(rr.rows[-1]), _row_nums(rc.rows[-1])

    def recost_lob(lob):  # 재보험비용 last row = non-PAA block then PAA block (4 LOB groups each)
        return at(rcr, lc(lob)) + at(rcr, 4 * st + lc(lob))

    # item13 자동차 / item14 일반 = (보험수익 − 보험비용) + (재보수익 − 재보비용), per LOB 누적
    out[14] = (at(rsr, lc(1)) - at(csr, lc(1))) + (at(rrr, lc(1)) - recost_lob(1))
    out[13] = (at(rsr, lc(2)) - at(csr, lc(2))) + (at(rrr, lc(2)) - recost_lob(2))
    # 장기 누적 totals → assemble derives items 2/3/7/8/12
    out["_jang_rev"] = at(rsr, lc(0))
    out["_jang_cost"] = at(csr, lc(0))
    out["_jang_rerev"] = at(rrr, lc(0))
    out["_jang_recost"] = recost_lob(0)
    return out  # 백만원 already


# ------------- 삼성화재(KR0008) + generic 손보 component note --------------- #
def extract_tier2_sonbo_component(tables):
    """Generic 손보 Tier-2 from the standard IFRS17 component note (삼성화재 gold-validated).

    Layout (삼성화재 2025.2Q gold): each of the four notes is a SINGLE table whose FIRST row is
    the LOB total — 보험수익 / 발행한 보험계약에서 생기는 보험서비스비용 / 재보험자에게서 회수한
    금액에서 생기는 수익 / 재보험자에게 지급된 보험료 배분액에서 생기는 비용 — with the component
    rows (CSM상각·위험조정·보고기간 발생(기초예상)) below.  Columns are LOB×[3개월,누적]; the LOB
    ORDER varies (삼성화재 = 장기/자동차/일반) so it is read from the header.  Basis = 별도
    (별도 ⊆ 연결): among current-period candidates take the smallest grand total.  예실차 accepts
    BOTH the combined 기초예상 line and the 4-way split.  Emits the 4 _jang_* totals → assemble
    derives items 2/3/7/8/12.  All 백만원.  Returns {} when the note layout doesn't match, so the
    caller can fall back to Format-A / Format-B."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "자동차보험", "일반보험")

    def fr(t):
        return _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""

    def hasrow(t, kw):
        return any(kw in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [(i, t) for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    revd = cands(lambda t: fr(t) == "보험수익"
                 and hasrow(t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
                 and "자동차보험" in _header_blob(t))
    costd = cands(lambda t: fr(t).startswith("발행한 보험계약에서 생기는 보험서비스비용")
                  and hasrow(t, "발생한 보험금"))
    rerevd = cands(lambda t: fr(t).startswith("재보험자에게서 회수한 금액에서 생기는 수익"))
    recostd = cands(lambda t: fr(t).startswith("재보험자에게 지급된 보험료 배분액에서 생기는 비용"))
    if not all((revd, costd, rerevd, recostd)):
        return {}

    def pmin_idx(cs):  # 별도 = smallest current-period grand total; skip rows with no numbers
        c = [it for it in cs if _row_nums(it[1].rows[0])]
        return min(c, key=lambda it: abs(_row_nums(it[1].rows[0])[-1])) if c else None

    def first_from(cs, start):  # first leg candidate at-or-after `start` (same 별도 block)
        c = [it for it in cs if it[0] >= start and _row_nums(it[1].rows[0])]
        return min(c, key=lambda it: it[0])[1] if c else None

    # Anchor all four legs to ONE basis.  The note is filed twice (연결 주석 먼저, 별도 뒤);
    # 별도 ⊆ 연결 holds for 보험수익/비용 (연결 adds subsidiary volume) so the 별도 rev = the
    # smaller grand total — but NOT for the reinsurance legs: 연결 eliminates intra-group
    # 재보험, so 별도 재보험회수(수익) can EXCEED 연결 (삼성화재 2026.1Q: 별도 80,446 > 연결
    # 78,380).  A per-leg "smallest grand total" then mixes bases (rev 별도 + rerev 연결),
    # short-changing one LOB by the elimination (일반 by 2,067).  Fix: pick the 별도 rev (min
    # grand total), then take cost/재보험 legs from the SAME document block (first at-or-after).
    rdi = pmin_idx(revd)
    if rdi is None:
        return {}
    sep, rd = rdi[0], rdi[1]
    pmin = lambda cs: (lambda it: it[1] if it else None)(pmin_idx(cs))
    cd = first_from(costd, sep) or pmin(costd)
    rr = first_from(rerevd, sep) or pmin(rerevd)
    rc = first_from(recostd, sep) or pmin(recostd)
    if None in (rd, cd, rr, rc):
        return {}

    hb = _header_blob(rd)
    off, st = (1, 2) if ("3개월" in hb and "누적" in hb) else (0, 1)
    order = sorted((hb.find(k), k) for k in LOBS)
    if any(p < 0 for p, _ in order):
        return {}
    lobpos = {k: idx for idx, (_, k) in enumerate(order)}

    def col(lob):
        return off + lobpos[lob] * st

    def d(t, *needles):  # 장기-LOB 누적-column value of the first row matching a needle
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > off:
                    return ns[off]
        return None

    def at(arr, i):
        return arr[i] if 0 <= i < len(arr) else 0.0

    csm, ra = d(rd, *_S2_CSM), d(rd, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}

    # 예실차 = expected − actual service.  Combined 기초예상 line if present, else 4-way split.
    exp = d(rd, "보고기간에 발생한 보험서비스비용")
    if exp is not None:
        act = d(cd, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    else:
        exps = [d(rd, n) for n in _EXP_SPLIT]
        acts = [d(cd, n) for n in _ACT_SPLIT]
        exp = sum(exps) if all(x is not None for x in exps) else None
        act = sum(acts) if all(x is not None for x in acts) else None
    if exp is not None and act is not None:
        out[6] = exp - act

    re_csm, re_ra = d(rc, *_S2_CSM), d(rc, *_S2_RA)
    if re_csm is not None:                          # 재보 CSM상각/위험조정 = −(cost-side raw)
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = d(rr, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    re_exp = d(rc, "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    rsr, csr = _row_nums(rd.rows[0]), _row_nums(cd.rows[0])
    rrr, rcr = _row_nums(rr.rows[0]), _row_nums(rc.rows[0])
    out[13] = (at(rsr, col("자동차보험")) - at(csr, col("자동차보험"))) \
        + (at(rrr, col("자동차보험")) - at(rcr, col("자동차보험")))
    out[14] = (at(rsr, col("일반보험")) - at(csr, col("일반보험"))) \
        + (at(rrr, col("일반보험")) - at(rcr, col("일반보험")))
    out["_jang_rev"] = at(rsr, col("장기보험"))
    out["_jang_cost"] = at(csr, col("장기보험"))
    out["_jang_rerev"] = at(rrr, col("장기보험"))
    out["_jang_recost"] = at(rcr, col("장기보험"))
    return out  # 백만원 already


# ----------------------------- 흥국화재 (KR0005) --------------------------- #
def extract_tier2_heungkuk(tables):
    """흥국화재 (KR0005, gold-validated 2025.2Q): each leg (보험수익 / 보험서비스비용 /
    재보험수익 / 재보험비용) is ONE combined table whose LOB total sits on a row found by LABEL
    (not position) with component rows below.  Columns are non-PAA[장기/일반/자동차/합계] then
    PAA[…] × [3개월,누적]; 장기 is GMM (non-PAA) but 재보험 carries a small PAA 장기 too, so each
    LOB 누적 = nonPAA + PAA (summed).  Basis 별도 (smallest grand total).  예실차 (item6/11) =
    expected(보고기간 발생 기초예상) − actual(발생 보험금 및 그 밖) — the gold's 과거/미래서비스 +
    보험취득CF 차이 stay in 기타(item7/12), NOT 예실차 (owner confirmed 2026-06-05).  All 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "일반보험", "자동차보험")

    def first(t):
        return _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):  # nums of the row whose col0..4 EXACTLY equals label
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        return ns
        return None

    def find(totlabel, must):
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "장기보험" in _header_blob(t)]
        return min(cs, key=lambda it: abs(totrow(it[1], totlabel)[-1]))[1] if cs else None

    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    cost = find("보험서비스비용", "발생한 보험금")
    rerev = find("재보험수익", "재보험수익, 발생한 보험금")
    recost = find("재보험비용", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    if None in (rev, cost, rerev, recost):
        return {}

    hb = _header_blob(rev)
    lobpos = {k: i for i, (_, k) in enumerate(sorted((hb.find(x), x) for x in LOBS))}

    def cum(ns, lob):  # nonPAA + PAA 누적 for one LOB (non-PAA block = 4 LOB-groups × 2 cols)
        p = lobpos[lob]
        a = ns[1 + 2 * p] if len(ns) > 1 + 2 * p else 0.0
        b = ns[9 + 2 * p] if len(ns) > 9 + 2 * p else 0.0
        return a + b

    def comp(t, *needles):  # 장기 non-PAA 누적 of the first row matching a needle
        idx = 1 + 2 * lobpos["장기보험"]
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    rt = totrow(rev, "보험수익")
    ct = totrow(cost, "보험서비스비용")
    rrt = totrow(rerev, "재보험수익")
    rct = totrow(recost, "재보험비용")

    csm, ra = comp(rev, *_S2_CSM), comp(rev, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = comp(rev, "보고기간에 발생한 보험서비스비용")
    act = comp(cost, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    if exp is not None and act is not None:
        out[6] = exp - act
    re_csm, re_ra = comp(recost, *_S2_CSM), comp(recost, *_S2_RA)
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = comp(rerev, "재보험수익, 발생한 보험금 및 그 밖", "재보험수익, 발생한 보험금")
    re_exp = comp(recost, "재보험비용, 보고기간에 발생한 보험서비스비용", "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    out[13] = (cum(rt, "자동차보험") - cum(ct, "자동차보험")) \
        + (cum(rrt, "자동차보험") - cum(rct, "자동차보험"))
    out[14] = (cum(rt, "일반보험") - cum(ct, "일반보험")) \
        + (cum(rrt, "일반보험") - cum(rct, "일반보험"))
    out["_jang_rev"] = cum(rt, "장기보험")
    out["_jang_cost"] = cum(ct, "장기보험")
    out["_jang_rerev"] = cum(rrt, "장기보험")
    out["_jang_recost"] = cum(rct, "장기보험")
    return out  # 백만원 already


def extract_tier2_heungkuk_old(tables):
    """흥국화재 (KR0005) pre-2025.2Q 보험종류별 leg-split note (2023.1Q–2025.1Q).
    REV/RECOST = one COMBINED 구분/계정과목 table [장기, 일반, 자동차, 합계]; COST/REREV split
    into 일반모형(장기-only) + PAA(일반/자동차) tables.  Each note prints 당기누적/당기3개월/전기
    누적/전기3개월 with NO prior marker → FIRST matching table = current YTD; grand total = LAST
    합계 (소계 is the 장기 sub-block).  Annual (Q4) collapses 일반모형 LOB cols to period cols
    (장기 stays at numeric col0) and renames 예상지급보험금→예상발생보험금.  Captions vary
    (재보험/출재보험/재보험종류별) → matching is purely structural.  item6/11 예실차 EXCLUDES
    투자관리비.  Returns {} for the 2025.2Q+ single-table form (caller keeps extract_tier2_heungkuk)."""
    JANG, ILBAN, AUTO = "장기", "일반", "자동차"
    CSM = "보험계약마진상각"
    RA = ("비금융위험에대한위험조정변동", "위험조정변동", "위험조정의변동")
    z = lambda v: v or 0.0

    def hdr(t):
        for r in t.rows[:3]:
            cells = [_norm(c).replace(" ", "") for c in r]
            if cells and cells[0] in ("구분", "계정과목", "항목"):
                return cells
        return []

    def lobidx(cells):
        m, j = {}, 0
        for c in cells[1:]:
            if c in (JANG, ILBAN, AUTO):
                m[c] = j
            if c in (JANG, ILBAN, AUTO, "합계"):
                j += 1
        return m

    def totrow(t):
        last = None
        for r in t.rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                ns = _row_nums(r)
                if ns:
                    last = ns
        return last

    def rowblob(t):
        return "".join(_norm(r[0]).replace(" ", "") for r in t.rows)

    def rv(rows, idx, *needles):
        for r in rows:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    def pick_combined(sig_all, sig_none=()):
        for t in tables:
            cells = hdr(t)
            if not cells or not (JANG in cells and AUTO in cells):
                continue
            blob = rowblob(t)
            if all(s in blob for s in sig_all) and not any(s in blob for s in sig_none):
                tr = totrow(t)
                if tr:
                    return (t, cells, tr)
        return None

    def pick_jang(sig_all):
        for t in tables:
            cells = hdr(t)
            if not cells or AUTO in cells or ILBAN in cells:
                continue
            if all(s in rowblob(t) for s in sig_all):
                tr = totrow(t)
                if tr:
                    return (t, tr)
        return None

    def find_paa(sig_all, sig_none=()):
        for t in tables:
            cells = hdr(t)
            if not cells or not (ILBAN in cells and AUTO in cells):
                continue
            blob = rowblob(t)
            if all(s in blob for s in sig_all) and not any(s in blob for s in sig_none):
                tr = totrow(t)
                if tr:
                    return (t, cells, tr)
        return None

    rev = pick_combined([CSM, "보험료배분법적용수익"],
                        sig_none=["예상출재보험금", "기타재보험계약비용", "발생재보험금"])
    recost = pick_combined(["예상출재보험금", CSM])
    cost = pick_jang(["발생보험금", "직접유지비", "직접신계약비상각비"])
    rerev = pick_jang(["발생재보험금", "발생사고부채조정"])
    if None in (rev, cost, rerev, recost):
        return {}

    revT, revC, revTot = rev
    recT, recC, recTot = recost
    li, rli = lobidx(revC), lobidx(recC)
    jrev, jrec = li[JANG], rli[JANG]

    out = {4: abs(z(rv(revT.rows, jrev, CSM))),
           5: abs(z(rv(revT.rows, jrev, *RA)))}
    exp = z(rv(revT.rows, jrev, "예상지급보험금", "예상발생보험금")) \
        + z(rv(revT.rows, jrev, "예상직접유지비")) + z(rv(revT.rows, jrev, "예상손해조사비"))
    act = z(rv(cost[0].rows, 0, "발생보험금")) \
        + z(rv(cost[0].rows, 0, "직접유지비")) + z(rv(cost[0].rows, 0, "손해조사비"))
    out[6] = exp - act
    out[9] = -z(rv(recT.rows, jrec, CSM))
    out[10] = -z(rv(recT.rows, jrec, *RA))
    re_act = z(rv(rerev[0].rows, 0, "발생재보험금")) \
        + z(rv(rerev[0].rows, 0, "발생수입손해조사비")) + z(rv(rerev[0].rows, 0, "발생사고부채조정"))
    re_exp = z(rv(recT.rows, jrec, "예상출재보험금")) + z(rv(recT.rows, jrec, "예상수입손해조사비"))
    out[11] = re_act - re_exp

    def lobtot(tr, m, lob):
        i = m.get(lob)
        return tr[i] if (i is not None and i < len(tr)) else 0.0

    rev_l = {lob: lobtot(revTot, li, lob) for lob in (JANG, ILBAN, AUTO)}
    rec_l = {lob: lobtot(recTot, rli, lob) for lob in (JANG, ILBAN, AUTO)}
    cost_l = {JANG: cost[1][0], ILBAN: 0.0, AUTO: 0.0}
    rerev_l = {JANG: rerev[1][0], ILBAN: 0.0, AUTO: 0.0}
    paacost = find_paa(["발생보험금", "직접유지비"],
                       sig_none=[CSM, "예상출재보험금", "발생재보험금"])
    paarerev = find_paa(["발생재보험금", "발생사고부채조정"], sig_none=["예상출재보험금"])
    if paacost:
        pm = lobidx(paacost[1])
        for lob in (ILBAN, AUTO):
            cost_l[lob] = lobtot(paacost[2], pm, lob)
    if paarerev:
        prm = lobidx(paarerev[1])
        for lob in (ILBAN, AUTO):
            rerev_l[lob] = lobtot(paarerev[2], prm, lob)

    out[13] = (rev_l[AUTO] - cost_l[AUTO]) + (rerev_l[AUTO] - rec_l[AUTO])
    out[14] = (rev_l[ILBAN] - cost_l[ILBAN]) + (rerev_l[ILBAN] - rec_l[ILBAN])
    out["_jang_rev"] = rev_l[JANG]
    out["_jang_cost"] = cost_l[JANG]
    out["_jang_rerev"] = rerev_l[JANG]
    out["_jang_recost"] = rec_l[JANG]
    return out  # 백만원 already


def extract_tier2_heungkuk_single(tables):
    """흥국화재 (KR0005) single-period note (2025.4Q annual, 2026.1Q+): the NEW combined-table
    note dropped the 3개월/누적 column split AND collapsed the non-PAA LOB columns (장기 is the
    only non-PAA LOB).  Every value row therefore has the non-PAA 장기 figure as its FIRST
    numeric; each leg's total row carries the PAA split as its last three numerics
    [일반, 자동차, 합계].  Schema is YTD (the single column = 누적).  Returns {} (dispatch falls
    through to wide / OLD paths) unless all four legs match."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        return ns
        return None

    def find(totlabel, must):
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "장기보험" in _header_blob(t)
              and "3개월" not in _header_blob(t) and "누적" not in _header_blob(t)]
        return min(cs, key=lambda it: it[0])[1] if cs else None  # current = first printed

    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    cost = find("보험서비스비용", "발생한 보험금")
    rerev = find("재보험수익", "재보험수익, 발생한 보험금")
    recost = find("재보험비용", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    if None in (rev, cost, rerev, recost):
        return {}

    def jang(t, *needles):  # non-PAA 장기 = FIRST numeric of the first matching component row
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns:
                    return ns[0]
        return None

    def paa_lob(t, label):  # total row's PAA block: last three numerics = [일반, 자동차, 합계]
        ns = totrow(t, label)
        if not ns or len(ns) < 3:
            return (0.0, 0.0)
        return (ns[-3], ns[-2])  # (일반, 자동차)

    csm, ra = jang(rev, *_S2_CSM), jang(rev, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = jang(rev, "보고기간에 발생한 보험서비스비용")
    act = jang(cost, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    if exp is not None and act is not None:
        out[6] = exp - act
    re_csm, re_ra = jang(recost, *_S2_CSM), jang(recost, *_S2_RA)
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = jang(rerev, "재보험수익, 발생한 보험금 및 그 밖", "재보험수익, 발생한 보험금")
    re_exp = jang(recost, "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    rev_il, rev_au = paa_lob(rev, "보험수익")
    cost_il, cost_au = paa_lob(cost, "보험서비스비용")
    rrev_il, rrev_au = paa_lob(rerev, "재보험수익")
    rcost_il, rcost_au = paa_lob(recost, "재보험비용")
    out[13] = (rev_au - cost_au) + (rrev_au - rcost_au)
    out[14] = (rev_il - cost_il) + (rrev_il - rcost_il)
    def jang_tot(t, label):
        # 장기손익 = non-PAA 장기 (FIRST numeric) + PAA 장기.  흥국 cedes some 장기 reinsurance
        # under PAA, so rerev/recost carry a PAA-장기 column the first-numeric read drops (→ 재보험
        # 장기 understated → 장기손익 over → ΣLOB over by 888−2572=1,684 in 2025.4Q, 968 in 2026.1Q).
        # PAA 장기 = PAA합계 − PAA일반 − PAA자동차 (last 3 numerics) — robust to 0-column dropping.
        ns = totrow(t, label)
        if not ns:
            return None
        paa_jang = (ns[-1] - ns[-3] - ns[-2]) if len(ns) >= 3 else 0.0
        return ns[0] + paa_jang
    out["_jang_rev"] = jang_tot(rev, "보험수익")
    out["_jang_cost"] = jang_tot(cost, "보험서비스비용")
    out["_jang_rerev"] = jang_tot(rerev, "재보험수익")
    out["_jang_recost"] = jang_tot(recost, "재보험비용")
    return out  # 백만원 already


def _heungkuk_dispatch(tables):
    """single-period (2025.4Q+) → wide (2025.2Q/3Q) → pre-2025.2Q leg-split.  All three forms
    are structurally disjoint (header 3개월/누적 presence + row0 signatures), so no cross-corruption."""
    out = extract_tier2_heungkuk_single(tables)        # 2025.4Q+ single-period form
    if out and any(out.get(i) is not None for i in (4, 5)):
        return out
    out = extract_tier2_heungkuk(tables)               # 2025.2Q/3Q wide form
    if out and any(out.get(i) is not None for i in (4, 5)):
        return out
    return extract_tier2_heungkuk_old(tables)          # pre-2025.2Q leg-split note


def _coreanre_old(tables):
    """코리안리 pre-2025.2Q: a SINGLE merged 구분-rows note (구분|장기|생명|일반|합계) holding all
    four legs as section-label rows.  Same dual schema as extract_tier2_coreanre (생명→2-12,
    장기→2-1…12-1, 일반→14).  Agent-derived + RC-validated 2023.3Q–2025.1Q (≤1 백만)."""
    def r0(t):
        return _norm(t.rows[0][0]).replace(" ", "") if (t.rows and t.rows[0]) else ""

    def is_note(t):
        hb = _header_blob(t)
        return (hb.startswith("구분") and "장기" in hb and "생명" in hb and "일반" in hb
                and len(t.rows) > 20 and any(_norm(r[0]) == "보험수익" for r in t.rows if r))
    cands = [i for i, t in enumerate(tables)
             if is_note(t) and i > 0 and r0(tables[i - 1]) == "기초순장부금액"]
    if not cands:
        return {}
    t = tables[max(cands)]                                   # 별도 = last current-period note
    hb = _header_blob(t)
    COL = {"장기": 1, "생명": 3, "일반": 5} if ("3개월" in hb and "누적" in hb) \
        else {"장기": 0, "생명": 1, "일반": 2}
    SECMAP = {"보험수익": "REV", "보험비용": "COST", "재보험수익": "REREV", "재보험비용": "RECOST"}
    secs = {}
    cur = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in SECMAP and not _row_nums(r):
            cur = SECMAP[lab]; secs.setdefault(cur, [])
        elif cur is not None and r:
            secs[cur].append(r)
    if not all(k in secs for k in ("REV", "COST", "REREV", "RECOST")):
        return {}

    z = lambda v: v or 0.0

    def val(sec, lob, *needles):
        idx = COL[lob]
        for r in secs[sec]:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    def leg(lob):
        suje = z(val("REV", lob, "총보험수익")) - z(val("COST", lob, "총보험비용"))
        csm = abs(z(val("REV", lob, "보험계약마진상각")))
        ra = abs(z(val("REV", lob, "위험조정변동")))
        yes = sum(z(val("REV", lob, n)) for n in ("예상발생보험금", "예상손해조사비", "예상계약유지비")) \
            - sum(z(val("COST", lob, n)) for n in ("발생보험금", "발생손해조사비", "발생계약유지비"))
        chuljae = z(val("REREV", lob, "총재보험수익")) - z(val("RECOST", lob, "총재보험비용"))
        recsm = -z(val("RECOST", lob, "보험계약마진상각"))
        rera = -z(val("RECOST", lob, "위험조정변동"))
        reyes = z(val("REREV", lob, "발생재보험금")) - z(val("RECOST", lob, "예상재보험금"))
        return {2: suje + chuljae, 3: suje, 4: csm, 5: ra, 6: yes, 7: suje - csm - ra - yes,
                8: chuljae, 9: recsm, 10: rera, 11: reyes, 12: chuljae - recsm - rera - reyes}

    life, jang = leg("생명"), leg("장기")
    if not life[4] or abs(life[4]) <= 1:
        return {}
    out = {k: life[k] for k in range(4, 13)}
    out["_jang_rev"] = z(val("REV", "생명", "총보험수익"))
    out["_jang_cost"] = z(val("COST", "생명", "총보험비용"))
    out["_jang_rerev"] = z(val("REREV", "생명", "총재보험수익"))
    out["_jang_recost"] = z(val("RECOST", "생명", "총재보험비용"))
    out[14] = (z(val("REV", "일반", "총보험수익")) - z(val("COST", "일반", "총보험비용"))) \
        + (z(val("REREV", "일반", "총재보험수익")) - z(val("RECOST", "일반", "총재보험비용")))
    _N = {2: "장기재보험 손익", 3: "장기재보험 수재손익", 4: "수재 CSM상각",
          5: "수재 위험조정 변동", 6: "수재 예실차", 7: "기타 장기재보험 수재손익",
          8: "장기재보험 출재손익", 9: "출재 CSM상각", 10: "출재 위험조정 변동",
          11: "출재 예실차", 12: "기타 장기재보험 출재손익"}
    out["_extra_items"] = [{"항목번호": f"{k}-1", "항목명": _N[k], "값": jang[k]} for k in range(2, 13)]
    out["_extra_lob"] = jang[2]
    return out


# ------------------------------ 코리안리 (KR1000) -------------------------- #
def extract_tier2_coreanre(tables):
    """코리안리재보험 (KR1000, gold-validated 2025.2Q) — a REINSURER, so the note splits by
    생명보험 / 장기보험 / 일반보험 (NO 자동차) and each GMM line of business carries a full
    수재(inward, = 발행보험 보험수익−비용) + 출재(ceded, = 재보험수익−비용) decomposition.  The
    owner's schema maps 생명재보험 → items 2-12 (standard slots) and 장기재보험 → items 2-1…12-1
    (a parallel set returned via `_extra_items`); 일반재보험 → item14.  Columns are
    non-PAA[장기/생명/일반] then PAA[…] × [3개월,누적]; 장기·생명 are GMM (non-PAA), 일반 PAA, so
    each LOB 누적 = nonPAA + PAA.  Basis 별도 = the LATER document occurrence (연결 주석 precedes
    별도; min-total is unsafe here because 연결 재보험수익 < 별도).  예실차: 수재 = expected
    (4 예상 lines) − actual (발생 보험금+손조비+유지비, 발생투자관리비 제외); 출재 = 재보험수익
    발생보험금 − (재보험비용 예상보험금 + 보고기간 발생) — owner-confirmed 2026-06-05.  All 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "생명보험", "일반보험")

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        return ns
        return None

    def find(totlabel, must):  # latest current-period occurrence = 별도
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "생명보험" in _header_blob(t) and "장기보험" in _header_blob(t)]
        return max(cs, key=lambda it: it[0])[1] if cs else None

    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    cost = find("보험비용", "발생한 보험금")
    rerev = find("재보험자에게서 회수한 금액에서 생기는 수익", "재보험수익, 발생한 보험금")
    recost = find("재보험자에게 지급된 보험료 배분액에서 생기는 비용",
                  "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    if None in (rev, cost, rerev, recost):
        return _coreanre_old(tables)          # pre-2025.2Q 구분-rows merged note

    hb = _header_blob(rev)
    lobpos = {k: i for i, (_, k) in enumerate(sorted((hb.find(x), x) for x in LOBS))}
    # Layout drift: 2023.3Q~2025.3Q quarterly notes double each LOB cell into [3개월, 누적];
    # FY2025 annual + 2026.1Q onward dropped the doubling -> single-period cells.  step = the
    # cell width per LOB, off = the 누적 index within a cell (0 when single-period).
    quarterly = ("3개월" in hb and "누적" in hb)
    step = 2 if quarterly else 1
    off = 1 if quarterly else 0

    def cum(ns, lob):                      # nonPAA(누적) + PAA(누적) for this LOB
        p = lobpos[lob]
        a = ns[off + step * p] if len(ns) > off + step * p else 0.0
        b = ns[step * 4 + off + step * p] if len(ns) > step * 4 + off + step * p else 0.0
        return a + b

    def comp(t, lob, *needles):            # nonPAA(누적) component value, this LOB
        idx = off + step * lobpos[lob]
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    rt = totrow(rev, "보험수익")
    ct = totrow(cost, "보험비용")
    rrt = totrow(rerev, "재보험자에게서 회수한 금액에서 생기는 수익")
    rct = totrow(recost, "재보험자에게 지급된 보험료 배분액에서 생기는 비용")

    def leg(lob):
        """Full 수재/출재 decomposition for one GMM LOB → dict of item-suffix → value."""
        suje = cum(rt, lob) - cum(ct, lob)                      # item3
        csm = abs(comp(rev, lob, *_S2_CSM) or 0)                # item4
        ra = abs(comp(rev, lob, *_S2_RA) or 0)                  # item5
        exp = sum(comp(rev, lob, n) or 0 for n in _EXP_SPLIT)
        act = sum(comp(cost, lob, n) or 0
                  for n in ("발생한 보험금", "발생한 손해조사비", "발생한 유지비"))  # 발생투자관리비 제외
        yes = exp - act                                         # item6
        other_s = suje - csm - ra - yes                         # item7 (residual)
        chuljae = cum(rrt, lob) - cum(rct, lob)                 # item8
        recsm = -(comp(recost, lob, *_S2_CSM) or 0)             # item9
        rera = -(comp(recost, lob, *_S2_RA) or 0)               # item10
        re_act = comp(rerev, lob, "재보험수익, 발생한 보험금") or 0
        re_exp = (comp(recost, lob, "재보험비용, 예상 보험금") or 0) \
            + (comp(recost, lob, "재보험비용, 보고기간에 발생한 보험서비스비용") or 0)
        reyes = re_act - re_exp                                 # item11
        other_r = chuljae - recsm - rera - reyes                # item12
        return {2: suje + chuljae, 3: suje, 4: csm, 5: ra, 6: yes, 7: other_s,
                8: chuljae, 9: recsm, 10: rera, 11: reyes, 12: other_r}

    life = leg("생명보험")    # 생명재보험 → standard items 2-12
    jang = leg("장기보험")    # 장기재보험 → items 2-1 … 12-1

    out = {k: life[k] for k in range(4, 13)}                    # 4-12 direct (3/7/12/2/8 below)
    # 생명: feed assemble's _jang_* so it derives item2/3/8 the standard way
    out["_jang_rev"] = cum(rt, "생명보험")
    out["_jang_cost"] = cum(ct, "생명보험")
    out["_jang_rerev"] = cum(rrt, "생명보험")
    out["_jang_recost"] = cum(rct, "생명보험")
    out[14] = (cum(rt, "일반보험") - cum(ct, "일반보험")) \
        + (cum(rrt, "일반보험") - cum(rct, "일반보험"))    # 일반재보험

    _N = {2: "장기재보험 손익", 3: "장기재보험 수재손익", 4: "수재 CSM상각",
          5: "수재 위험조정 변동", 6: "수재 예실차", 7: "기타 장기재보험 수재손익",
          8: "장기재보험 출재손익", 9: "출재 CSM상각", 10: "출재 위험조정 변동",
          11: "출재 예실차", 12: "기타 장기재보험 출재손익"}
    out["_extra_items"] = [{"항목번호": f"{k}-1", "항목명": _N[k], "값": jang[k]}
                           for k in range(2, 13)]
    out["_extra_lob"] = jang[2]                                 # 장기재보험 손익 → RC
    return out  # 백만원 already


# -------------------- 구형식 (pre-2025.2Q) 손보 OLD note --------------------- #
# Before the standardized 2025.2Q disclosure, several insurers used a "구분=행 / LOB=열" note
# (DB "6. 보험수익 및 비용"; 삼성·현대 "보험서비스결과" 구분-rows).  Two structural variants —
#   • 삼성-style: 보험수익/비용/재보 sections are LABEL-rows inside merged tables; 예실차 = combined
#     "예상보험금 및 보험서비스비용" − "발생보험금 및 발생보험서비스비용"; LOBs 장기/자동차/일반 (no 생명).
#   • DB-style: each leg is a SEPARATE caption-identified table (6-1…6-4); 예실차 = 4-way split;
#     LOBs 장기/일반/자동차/생명 (생명 column EXCLUDED per gold); 원수 total = 소계 (before <수재>).
# Both share: 누적(YTD) column, header-driven LOB order, and the same robust LOB-total reader that
# survives dropped zero-LOB columns in the (often irregular) 재보 합계 rows.  Gold-validated against
# DB 2024.2Q + 삼성화재 2024.2Q.  Basis 별도 (smallest grand total per leg).  코리안리 old (장기/생명
# dual) and 흥국 old (보험종류별) use other layouts and are NOT handled here.
_OLD_LOBS = ("장기", "자동차", "일반", "생명")
_OLD_SEC = {"보험수익": "REV", "보험서비스비용": "COST", "보험비용": "COST",
            "재보험수익": "REREV", "재보험비용": "RECOST"}
_OLD_PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
_CSM_OLD = ("보험계약마진상각", "보험계약마진 상각")
_RA_OLD = ("위험조정상각", "위험조정의 변동", "비금융위험에 대한 위험조정")
_EXP4_OLD = ("예상보험금", "예상유지비", "예상손해조사비", "예상투자관리비")
_ACT4_OLD = ("발생보험금", "발생직접유지비", "손해조사비", "투자관리비")


def _old_prior(tables, i):
    cap = _norm(tables[i].caption or "")
    if ("(전)" in cap) or (("전반기" in cap or "전기" in cap or "전분기" in cap) and "당" not in cap):
        return True
    for j in (i - 1, i - 2):
        if 0 <= j < len(tables):
            tj = tables[j]
            f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
            # marker rows may be bracketed, e.g. '<전반기>' — substring match, but never when a
            # 당기 marker ('<당반기>'/'당기') is what precedes the table.
            if len(tj.rows) <= 1 and f and "당" not in f and any(p in f for p in _OLD_PRIOR):
                return True
    return False


def _old_order(t):
    hb = _header_blob(t)
    return [k for _, k in sorted((hb.find(x), x) for x in _OLD_LOBS if hb.find(x) >= 0)]


def _old_rv(rows, idx, *needles):
    for r in rows:
        lab = _norm(r[0]).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles):
            ns = _row_nums(r)
            if ns and len(ns) > idx:
                return ns[idx]
    return None


def _old_total(rows, before=None):
    end = len(rows)
    if before:
        for k, r in enumerate(rows):
            if _norm(r[0]) == before:
                end = k
                break
    for r in rows[:end]:
        if _norm(r[0]).replace(" ", "") in ("합계", "소계"):
            return _row_nums(r)
    return None


def _old_present(rows, order):
    """PAA LOBs materially non-zero — from the fullest aligned row (relative threshold)."""
    full = (len(order) + 1) * 2
    best = None
    for r in rows:
        ns = _row_nums(r)
        if ns and len(ns) >= full and (best is None or len(ns) > len(best)):
            best = ns
    pres = set()
    if best:
        thr = max(1.0, 0.005 * abs(best[-1]))
        for i, lob in enumerate(order):
            if i and abs(best[2 * i + 1]) > thr:
                pres.add(lob)
    return pres


def _old_lobcum(total_nums, order, pres, st=2):
    """누적 per LOB from a possibly-short total row: 장기 left, 합계 right, middle→present PAA.
    st = cell width per LOB (2 = paired [3개월,누적] 반기/3Q; 1 = single-col Q1/연차)."""
    res = {lob: 0.0 for lob in order}
    if not total_nums:
        return res
    full = (len(order) + 1) * st
    if len(total_nums) >= full:
        for i, lob in enumerate(order):
            res[lob] = total_nums[(st - 1) + i * st]
        return res
    res[order[0]] = total_nums[st - 1] if len(total_nums) > st - 1 else 0.0
    if st == 1:                       # single-col short row: positional best-effort
        for i, lob in enumerate(order):
            if i < len(total_nums) - 1:
                res[lob] = total_nums[i]
        return res
    mid = total_nums[2:-2]
    midc = [mid[2 * j + 1] for j in range(len(mid) // 2)]
    for lob in order[1:]:
        if lob in pres and midc:
            res[lob] = midc.pop(0)
    return res


def _old_sections(t):
    out = {}
    cur = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in _OLD_SEC and not _row_nums(r):
            cur = _OLD_SEC[lab]
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(r)
    return out


def _old_assemble_jang(rev, cost, rerev, recost, order, combined_exp, st=2):
    """Common item math for a single 장기-GMM company (삼성·DB-style).  Returns the 4/5/6/9/10/11
    direct items + LOB totals via robust reader.  st = cell width per LOB (2 = paired 반기/3Q;
    1 = single-col Q1/연차 — then the 장기 component sits at col0 not col1)."""
    z = lambda v: v or 0.0
    idx = st - 1
    csm = abs(z(_old_rv(rev, idx, *_CSM_OLD)))
    ra = abs(z(_old_rv(rev, idx, *_RA_OLD)))
    if combined_exp:
        exp = z(_old_rv(rev, idx, "예상보험금 및 보험서비스비용", "보고기간에 발생한 보험서비스비용"))
        act = z(_old_rv(cost, idx, "발생보험금 및 발생보험서비스비용", "발생한 보험금 및 그 밖"))
    else:
        exp = sum(z(_old_rv(rev, idx, n)) for n in _EXP4_OLD)
        act = sum(z(_old_rv(cost, idx, n)) for n in _ACT4_OLD)
    out = {4: csm, 5: ra, 6: exp - act,
           9: -z(_old_rv(recost, idx, *_CSM_OLD)), 10: -z(_old_rv(recost, idx, *_RA_OLD))}
    re_act = z(_old_rv(rerev, idx, "발생출재보험금", "재보험수익, 발생한 보험금"))
    re_exp = z(_old_rv(recost, idx, "예상출재보험금", "재보험비용, 예상 보험금"))
    out[11] = re_act - re_exp
    re_present = _old_present(rerev, order) | _old_present(recost, order)
    RC = _old_lobcum(_old_total(rev), order, _old_present(rev, order), st)
    CC = _old_lobcum(_old_total(cost), order, _old_present(cost, order), st)
    RR = _old_lobcum(_old_total(rerev), order, re_present, st)
    RX = _old_lobcum(_old_total(recost), order, re_present, st)
    out["_jang_rev"] = RC["장기"]; out["_jang_cost"] = CC["장기"]
    out["_jang_rerev"] = RR["장기"]; out["_jang_recost"] = RX["장기"]
    for lob, it in (("자동차", 13), ("일반", 14)):
        if lob in order:
            out[it] = (RC[lob] - CC[lob]) + (RR[lob] - RX[lob])
    return out


def _old_samsung(tables):
    """삼성-style: section-label rows inside merged tables, combined 예상, LOBs w/o 생명."""
    legs_all = {}
    order = None
    st = 2
    for i, t in enumerate(tables):
        hb = _header_blob(t)
        if not hb.startswith("구분") or "장기" not in hb:
            continue
        # reject non-flat LOB layouts: 메리츠 nests LOBs under 국내/해외 and 배당요소 splits, so the
        # 장기 column isn't where header order implies — leave those to Format-B.
        if "생명" in hb or ("국내" in hb and "해외" in hb) or "배당요소" in hb or _old_prior(tables, i):
            continue
        secs = _old_sections(t)
        if not secs:
            continue
        blob = " ".join(_norm(r[0]) for r in t.rows if r)
        if not any(n in blob for n in _CSM_OLD) and not any(k in secs for k in ("COST", "REREV")):
            continue
        if order is None and any(k in secs for k in ("REV", "COST")):
            order = _old_order(t)
            st = 2 if ("3개월" in hb and "누적" in hb) else 1
        for leg, rows in secs.items():
            legs_all.setdefault(leg, []).append(rows)
    if order is None or not all(k in legs_all for k in ("REV", "COST", "REREV", "RECOST")):
        return {}
    legs = {leg: min(lst, key=lambda rs: abs((_old_total(rs) or [float("inf")])[-1]))
            for leg, lst in legs_all.items()}
    return _old_assemble_jang(legs["REV"], legs["COST"], legs["REREV"], legs["RECOST"],
                              order, combined_exp=True, st=st)


def _old_db(tables):
    """DB-style: separate caption-identified legs (6-1…6-4), 4-way 예상.  Anchor the 별도 block
    (3 LOBs, NO 생명 column = DB생명 subsidiary); LOB total = 합계 row (원수+수재, 수재 sits in 일반)."""
    def leg_of(t):
        # DB caption carries a long prefix "6. 보험수익 및 비용과 재보험수익 및 비용" before the
        # sub-caption, so match the SPECIFIC sub-phrase (or the 재보 tables' row0 markers).
        cap = _norm(t.caption or "").replace(" ", "")
        r0 = _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""
        if "재보험계약의재보험수익" in cap or r0 == "발생출재보험금":
            return "REREV"
        if "재보험계약의재보험비용" in cap or r0 == "예상출재보험금":
            return "RECOST"
        if "발행한보험계약의보험비용" in cap:
            return "COST"
        if "발행한보험계약의보험수익" in cap:
            return "REV"
        if r0 == "<원수>":
            blob = "".join(_norm(r[0]) for r in t.rows if r)
            if "발생보험금" in blob and "발생사고부채" in blob:
                return "COST"
            if "예상보험금" in blob and "보험계약마진상각" in blob:
                return "REV"
        return None

    # DB files this note TWICE: 연결 (header carries a 생명 column = the DB생명 subsidiary) and
    # 별도 (3 LOBs, NO 생명).  FS-API Tier-1 is OFS (별도), so anchor to the 별도 block — the 연결
    # 생명 column would otherwise leak the subsidiary AND the per-LOB intra-group reinsurance
    # elimination, short-changing item14 (일반).  Prefer 별도; fall back to 연결.
    sep, con = {}, {}
    order_sep = order_con = None
    st = 2
    for i, t in enumerate(tables):
        hb = _header_blob(t)
        if not hb.startswith("구분") or "자동차" not in hb:
            continue
        if _old_prior(tables, i):
            continue
        leg = leg_of(t)
        if leg is None:
            continue
        if "생명" in hb:
            con.setdefault(leg, t.rows)
            if order_con is None:
                order_con = _old_order(t)
                st = 2 if ("3개월" in hb and "누적" in hb) else 1
        else:
            sep.setdefault(leg, t.rows)
            if order_sep is None:
                order_sep = _old_order(t)
                st = 2 if ("3개월" in hb and "누적" in hb) else 1
    if all(k in sep for k in ("REV", "COST", "REREV", "RECOST")):
        legs, order = sep, order_sep
    elif all(k in con for k in ("REV", "COST", "REREV", "RECOST")):
        legs, order = con, order_con
    else:
        return {}
    rev, cost, rerev, recost = legs["REV"], legs["COST"], legs["REREV"], legs["RECOST"]
    z = lambda v: v or 0.0
    idx = st - 1
    out = {4: abs(z(_old_rv(rev, idx, *_CSM_OLD))), 5: abs(z(_old_rv(rev, idx, *_RA_OLD)))}
    out[6] = sum(z(_old_rv(rev, idx, n)) for n in _EXP4_OLD) - sum(z(_old_rv(cost, idx, n)) for n in _ACT4_OLD)
    out[9] = -z(_old_rv(recost, idx, *_CSM_OLD))
    out[10] = -z(_old_rv(recost, idx, *_RA_OLD))
    out[11] = z(_old_rv(rerev, idx, "발생출재보험금")) - z(_old_rv(recost, idx, "예상출재보험금"))
    re_present = _old_present(rerev, order) | _old_present(recost, order)

    def grand_or_sub(rows):
        # LOB-total row = 원수+수재 (DB's 수재 inward reinsurance sits only in 일반, so the 원수
        # 소계 alone under-states 일반).  Prefer the LAST full-width 합계 (after the 수재 소계);
        # the single-total 재보 tables carry no 합계 → first 소계/합계.
        g = None
        for r in rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                g = r
        if g is None:
            for r in rows:
                if _norm(r[0]).replace(" ", "") in ("소계", "합계"):
                    g = r
                    break
        return _row_nums(g) if g else None
    RC = _old_lobcum(grand_or_sub(rev), order, _old_present(rev, order), st)
    CC = _old_lobcum(grand_or_sub(cost), order, _old_present(cost, order), st)
    RR = _old_lobcum(grand_or_sub(rerev), order, re_present, st)
    RX = _old_lobcum(grand_or_sub(recost), order, re_present, st)
    out["_jang_rev"] = RC["장기"]; out["_jang_cost"] = CC["장기"]
    out["_jang_rerev"] = RR["장기"]; out["_jang_recost"] = RX["장기"]
    for lob, it in (("자동차", 13), ("일반", 14)):
        out[it] = (RC[lob] - CC[lob]) + (RR[lob] - RX[lob])
    return out


def extract_tier2_old(tables):
    """Dispatcher for the pre-2025.2Q 구분-rows note: 삼성-style first (no 생명 col), then DB-style
    (생명+자동차).  Returns {} when neither layout matches (caller falls back to Format-A/B)."""
    # item4 (CSM상각) is always materially non-zero for a 장기 insurer; a ~0 means the columns
    # were mis-read (wrong layout) → reject so the caller falls back to Format-A/B.
    out = _old_samsung(tables)
    if out and out.get(4) and abs(out[4]) > 1:
        return out
    out = _old_db(tables)
    if out and out.get(4) and abs(out[4]) > 1:
        return out
    return {}


# ----------------------------- NH 손보 (KR0032) ---------------------------- #
def extract_tier2_nh(tables):
    """NH농협손해 (KR0032): 보험손익 only as a single whole-company note '(13) 보험영업이익의
    내역' — NO 장기/일반/자동차 LOB columns and NO 예상-vs-발생 split.  Reads 누적(YTD) column
    (분기/반기 note prints [당기 3개월, 당기 누적, 전기 …]; annual is single 당기).  재보험비용
    section header drifts: annual '재보험비용' vs 분기/반기 '재보험서비스비용'.  Items 6/11 (예실차)
    and 13/14 (자동차/일반) are data-absent — NH discloses no claim split nor LOB-split income
    note, so item2 carries the WHOLE-company insurance result (this is what lets RC close)."""
    note = None
    for t in tables:
        labs = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
        if ("보험영업이익" in (t.caption or "")) and "보험계약마진 상각" in labs \
                and "보험료배분접근법 보험수익" in labs:
            note = t
            break
    if note is None:
        return {}
    col = _ytd_col(note)
    SEC = {"보험수익": "보험수익", "보험서비스비용": "보험서비스비용",
           "재보험수익": "재보험수익", "재보험비용": "재보험비용",
           "재보험서비스비용": "재보험비용"}

    def colval(r):
        ns = _row_nums(r)
        if not ns:
            return None
        return ns[col] if len(ns) > col else ns[0]

    section = None
    vals = {}
    for r in note.rows:
        lab0 = _norm(r[0])
        lab1 = _norm(r[1]) if len(r) > 1 else ""
        if lab0 in SEC:
            section = SEC[lab0]
        lab = (lab0 + " " + lab1).replace(" ", "")
        v = colval(r)
        if v is None:
            continue
        if section == "보험수익":
            if "보험계약마진상각" in lab:
                vals["csm"] = v
            elif "위험조정변동" in lab:
                vals["ra"] = v
        elif section == "재보험비용":
            if "보험계약마진상각" in lab:
                vals["recsm"] = v
            elif "위험조정변동" in lab:
                vals["rera"] = v
    out = {}
    if "csm" in vals:
        out[4] = abs(vals["csm"])
    if "ra" in vals:
        out[5] = abs(vals["ra"])
    if "recsm" in vals:
        out[9] = -abs(vals["recsm"])
    if "rera" in vals:
        out[10] = -abs(vals["rera"])
    # item6/11 (예실차) and 13/14 (자동차/일반) data-absent — see docstring.

    def subtotal(after_section):
        sec = None
        for r in note.rows:
            l0 = _norm(r[0])
            if l0 in SEC:
                sec = SEC[l0]
            if l0 == "소계" and sec == after_section:
                v = colval(r)
                if v is not None:
                    return v
        return None
    out["_jang_rev"] = subtotal("보험수익")
    out["_jang_cost"] = subtotal("보험서비스비용")
    out["_jang_rerev"] = subtotal("재보험수익")
    out["_jang_recost"] = subtotal("재보험비용")
    # NH discloses the 보험수익/보험서비스비용 SUBTOTALS (→ item3 = rev − cost in assemble) but
    # NOT the 예상-vs-발생 claim split, so 예실차(item6/11) is NOT separable.  The combined
    # residual (원수손익 − CSM상각 − RA) is pushed into 기타(item7/12) by the generic closure in
    # assemble() — owner decision 2026-06-08 (do NOT fabricate a 예실차 split).
    return out  # 백만원 already


# ---------------------------- 롯데 손보 (KR0003) --------------------------- #
_LOTTE_SEC = {"보험수익": "rev", "보험비용": "cost",
              "재보험수익": "re_rev", "재보험비용": "re_cost"}


def _extract_tier2_lotte_combined(tables):
    """롯데 보험손익 note — quarter-agnostic, section-aware.

    The note structure changed across years: FY2025 splits it into two tables
    (30. 보험손익 + 31. 재보험손익) while FY2023/FY2024 combine all four sections into one
    (31. 보험손익 및 재보험손익).  Both share identical [장기, 일반, 자동차, 합계] columns and
    row labels, with empty-value section-header rows (보험수익/보험비용/재보험수익/재보험비용).
    So instead of matching the note NUMBER (30./31.) and 기수 (<제81(당)기>), we collect every
    current-period table whose caption mentions 보험손익 and walk its rows by section.  This
    removes the fiscal-period hardcoding and makes FY2023/FY2024 extract like FY2025."""
    def is_cand(t):
        cap = (t.caption or "")
        if "보험손익" not in cap:
            return False
        if "(전)기" in cap.replace(" ", ""):       # skip the prior-period table
            return False
        h = " ".join(" ".join(_norm(c) for c in hr) for hr in t.header)
        return all(k in h for k in ("장기", "일반", "자동차")) and not _is_rollforward(t)

    sect = {}        # secname -> [(label_nospace, nums)], first occurrence wins
    seen_caps = set()
    for t in tables:
        if not is_cand(t) or (t.caption or "") in seen_caps:
            continue
        seen_caps.add(t.caption or "")
        section = None
        for r in t.rows:
            lab0 = _norm(r[0])
            nums = _row_nums(r)
            sk = _LOTTE_SEC.get(lab0)
            if sk is not None and not nums:          # section-header row (no values)
                section = sk
                continue
            if section is None or not nums:
                continue
            sect.setdefault(section, []).append((lab0.replace(" ", ""), nums))
    if not all(k in sect for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}

    def g(sec, *needles, exclude=()):
        for lab, nums in sect.get(sec, []):
            if any(n.replace(" ", "") in lab for n in needles) \
                    and not any(e.replace(" ", "") in lab for e in exclude):
                return nums
        return None

    def tot(sec):
        for lab, nums in sect.get(sec, []):
            if lab.startswith("총"):
                return nums
        return None

    out = {}
    csm = g("rev", "보험계약마진 상각")
    ra = g("rev", "위험조정 변동")
    rev_exp = g("rev", "예상보험금 및 예상기타보험서비스비용")
    cost_act = g("cost", "발생보험금 및 기타서비스비용")
    re_csm = g("re_cost", "보험계약마진 상각")
    re_ra = g("re_cost", "위험조정 변동")
    re_rev_act = g("re_rev", "발생보험금 및 기타재보험수익")
    re_cost_exp = g("re_cost", "회수예상 보험금 및 기타보험서비스비용")
    if csm:
        out[4] = abs(csm[0])
    if ra:
        out[5] = abs(ra[0])
    if rev_exp and cost_act:
        out[6] = rev_exp[0] - cost_act[0]
    if re_csm:
        out[9] = -abs(re_csm[0])
    if re_ra:
        out[10] = -abs(re_ra[0])
    if re_rev_act and re_cost_exp:
        out[11] = abs(re_rev_act[0]) - abs(re_cost_exp[0])

    rev_tot = tot("rev")
    cost_tot = tot("cost")
    rerev_tot = tot("re_rev")
    recost_tot = tot("re_cost")
    if not all(x and len(x) >= 4 for x in (rev_tot, cost_tot, rerev_tot, recost_tot)):
        return out

    def net(i):
        return rev_tot[i] - cost_tot[i] + rerev_tot[i] - recost_tot[i]
    out[14] = net(1)
    out[13] = net(2)
    out["_jang_rev"] = rev_tot[0]
    out["_jang_cost"] = cost_tot[0]
    out["_jang_rerev"] = rerev_tot[0]
    out["_jang_recost"] = recost_tot[0]
    return out  # 백만원 already


# ---- 롯데 NEW layouts: caption-stripped combined (2024.2Q/3Q) + per-segment split
#      (2025.3Q/2026.1Q).  Driven by table content / row-0 sub-headings, not the <P> caption
#      (DART clobbers it to '관계기업…' / '<제N(당)기 반기>').  누적-aware for interim doublings. ----
def _lotte_lob_pos(t):
    """Numeric-cell index per LOB ({jang,ilban,auto,tot}) for a Lotte component table,
    누적-aware.  None if the 장기/일반/자동차 header isn't present."""
    hdr_lob, has_cum = None, False
    for hr in t.header:
        cells = [_norm(c).replace(" ", "") for c in hr if _norm(c)]
        joined = "".join(cells)
        if "장기" in joined and "자동차" in joined and hdr_lob is None:
            hdr_lob = cells
        if "누적" in joined:
            has_cum = True
    if not hdr_lob:
        return None
    lobs = []
    for c in hdr_lob:
        if c.startswith("장기"):
            lobs.append("jang")
        elif c.startswith("일반"):
            lobs.append("ilban")
        elif c.startswith("자동차"):
            lobs.append("auto")
        elif "합계" in c or c.startswith("계"):
            lobs.append("tot")
    if "jang" not in lobs:
        return None
    step, off = (2, 1) if has_cum else (1, 0)   # 누적 = 2nd of each (3개월, 누적)
    return {lob: k * step + off for k, lob in enumerate(lobs)}


def _lotte_row_val(rows, idx, *needles, exclude=()):
    for r in rows:
        lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles) \
                and not any(e.replace(" ", "") in lab for e in exclude):
            nums = _row_nums(r)
            if len(nums) > idx:
                return nums[idx]
    return None


def _lotte_from_sections(sect):
    """Shared assembler.  sect: secname -> list[(rows, lob_pos)].  Emits 4,5,6,9,10,11,13,14
    + _jang_* with the legacy section-walker formulas."""
    def comp(sec, *needles):
        for rows, pos in sect.get(sec, []):
            v = _lotte_row_val(rows, pos["jang"], *needles)
            if v is not None:
                return v
        return None

    out = {}
    # First needle of each pair = 롯데 고유 label (2025.3Q+ split / legacy combined);
    # second = DART 표준양식 label (2025.2Q standardized component note).
    csm = comp("rev", "보험계약마진 상각", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = comp("rev", "위험조정 변동", "비금융위험에 대한 위험조정의 변동분")
    rev_exp = comp("rev", "예상보험금 및 예상기타보험서비스비용", "보고기간에 발생한 보험서비스비용")
    cost_act = comp("cost", "발생보험금 및 기타서비스비용",
                    "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_csm = comp("re_cost", "보험계약마진 상각", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = comp("re_cost", "위험조정 변동", "비금융위험에 대한 위험조정의 변동분")
    re_rev_act = comp("re_rev", "발생보험금 및 기타재보험수익")
    re_cost_exp = comp("re_cost", "회수예상 보험금 및 기타보험서비스비용",
                       "보고기간에 발생한 보험서비스비용")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev_act is not None and re_cost_exp is not None:
        out[11] = abs(re_rev_act) - abs(re_cost_exp)

    def grand(sec):
        for rows, pos in sect.get(sec, []):
            for r in rows:
                if _norm(r[0]).replace(" ", "").startswith("총"):
                    return _row_nums(r), pos
        # 표준양식 (2025.2Q): no '총…' rows — the section's LAST table is the '…합계' /
        # all-LOB leg and its LAST numeric row is the section total.
        entries = sect.get(sec) or []
        if entries:
            rows, pos = entries[-1]
            for r in reversed(rows):
                n = _row_nums(r)
                if n:
                    return n, pos
        return None, None

    rev_n, rev_p = grand("rev")
    cost_n, cost_p = grand("cost")
    rerev_n, rerev_p = grand("re_rev")
    recost_n, recost_p = grand("re_cost")

    def at(nums, pos, lob):
        if nums is None or pos is None:
            return None
        i = pos.get(lob)
        return nums[i] if i is not None and len(nums) > i else None

    if all(x is not None for x in (rev_n, cost_n, rerev_n, recost_n)):
        def net(lob):
            a, b = at(rev_n, rev_p, lob), at(cost_n, cost_p, lob)
            c, d = at(rerev_n, rerev_p, lob), at(recost_n, recost_p, lob)
            return None if None in (a, b, c, d) else a - b + c - d
        if net("ilban") is not None:
            out[14] = net("ilban")
        if net("auto") is not None:
            out[13] = net("auto")
        out["_jang_rev"] = at(rev_n, rev_p, "jang")
        out["_jang_cost"] = at(cost_n, cost_p, "jang")
        out["_jang_rerev"] = at(rerev_n, rerev_p, "jang")
        out["_jang_recost"] = at(recost_n, recost_p, "jang")
    return out


def _extract_tier2_lotte_combined_bycontent(tables):
    """Caption-stripped OLD combined single-table note (2024.2Q/2024.3Q): identify by content
    (4 section-header rows + 장기/자동차 header), slice rows per section."""
    sect = {}
    for t in tables:
        if _is_rollforward(t) or not t.rows:
            continue
        labs0 = {_norm(r[0]) for r in t.rows if not _row_nums(r)}
        if not ({"보험수익", "보험비용", "재보험수익", "재보험비용"} <= labs0):
            continue
        pos = _lotte_lob_pos(t)
        if pos is None:
            continue
        section, buf = None, []
        for r in t.rows:
            sk = _LOTTE_SEC.get(_norm(r[0]))
            if sk and not _row_nums(r):
                if section is not None:
                    sect.setdefault(section, []).append((buf, pos))
                section, buf = sk, []
                continue
            if section is not None:
                buf.append(r)
        if section is not None:
            sect.setdefault(section, []).append((buf, pos))
        break
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}
    return _lotte_from_sections(sect)


def _extract_tier2_lotte_split(tables):
    """NEW per-segment split layout (2025.3Q/2026.1Q): group tables by row-0 sub-heading;
    keep only 당분기/당반기 tables."""
    def subhead_leg(s):
        s = s.replace(" ", "")
        if "재보험비용의보험서비스비용분석공시" in s:
            # 표준양식 (2025.2Q): heading of the 재보험 회수수익 leg ('재보험자에게서 회수한
            # 금액에서 생기는 수익' tables) — despite the '재보험비용의…' wording.
            return "re_rev"
        if "재보험비용분석공시" in s:
            return "re_cost"
        if "재보험수익분석공시" in s:
            return "re_rev"
        if "보험서비스비용분석공시" in s and "재보험" not in s:
            return "cost"
        if "보험수익분석공시" in s:
            return "rev"
        return None

    sect = {}
    cur, cur_ok = None, True
    for t in tables:
        if not t.rows:
            continue
        r0 = " ".join(_norm(c) for c in t.rows[0])
        lg = subhead_leg(r0)
        if lg is not None:
            cur, cur_ok = lg, ("전분기" not in r0 and "전반기" not in r0)
            continue
        r0c = r0.replace(" ", "")
        if r0c.startswith(("당분기", "당반기")):
            cur_ok = True
            continue
        if r0c.startswith(("전분기", "전반기", "전기")):
            cur_ok = False
            continue
        if cur is None or not cur_ok or _is_rollforward(t):
            continue
        pos = _lotte_lob_pos(t)
        if pos is None:
            continue
        sect.setdefault(cur, []).append((t.rows, pos))
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}
    return _lotte_from_sections(sect)


def extract_tier2_lotte(tables):
    """롯데 dispatcher: legacy combined-caption note first (working quarters, untouched); fall
    through to caption-stripped combined (2024.2Q/3Q) + per-segment split (2025.3Q/2026.1Q)
    only when the primary path finds nothing."""
    out = _extract_tier2_lotte_combined(tables)
    if out and any(out.get(i) is not None for i in (4, 5, 6)):
        return out
    for fn in (_extract_tier2_lotte_combined_bycontent, _extract_tier2_lotte_split):
        alt = fn(tables)
        if alt and any(alt.get(i) is not None for i in (4, 5, 6)):
            return alt
    return out


# ----------------------------- 악사손해 (KR0049) ---------------------------- #
_AXA_SEC = {"보험수익": "rev", "보험서비스비용": "cost",
            "출재보험수익": "re_rev", "출재보험비용": "re_cost"}


def extract_tier2_axa(tables):
    """악사손해 연차 감사보고서 '(6) 보험손익 상세내역' note (2024.4Q/2025.4Q identical form).

    Columns [자동차|일반|장기|합계] (header-mapped — NOT 장기-first; the generic Format-A
    fallback collapsed '-' cells via _row_nums and mis-assigned the columns), unit 천원.
    Four no-value section-header rows (보험수익/보험서비스비용/출재보험수익/출재보험비용),
    '총 …' total rows, final '총 보험서비스결과' row.  Within a section a label can repeat
    (비PAA vs PAA sub-blocks) — take the first row whose target-LOB cell is numeric (the PAA
    twin prints '-' in 장기 and vice versa).  FIRST captioned table = 당기 (IS-verified for
    both years; the twin is 전기).

    악사's income statement nests 기타사업비용 INSIDE Ⅰ.보험손익 ('3) 기타사업비용' row, 원
    unit), and Tier-1 mis-reads it as ~0 (the '16,25' footnote-ref cell → 1625원).  Emit
    item16 from that IS row so the RC gate's adjusted bridge item1 = ΣLOB + 15 − 16 closes
    (2024.4Q: −7,078.456 − 10,561.922 = −17,640.378 = item1 exactly)."""
    note = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "보험손익상세내역" in cap and t.rows:
            note = t
            break
    if note is None:
        return {}
    f = 1e-3 if "천원" in (note.caption or "") else 1.0

    col = None
    for hr in note.header:
        cells = [_norm(c).replace(" ", "") for c in hr if _norm(c)]
        joined = "".join(cells)
        if "장기" not in joined or "자동차" not in joined:
            continue
        col, k = {}, 0
        for c in cells:
            if c.startswith("구분"):
                continue
            if c.startswith("자동차"):
                col["auto"] = k
            elif c.startswith("일반"):
                col["ilban"] = k
            elif c.startswith("장기"):
                col["jang"] = k
            elif "합계" in c:
                col["tot"] = k
            k += 1
        break
    if not col or "jang" not in col:
        return {}

    def pick(sec_want, needle, lob="jang"):
        sec, nd = None, needle.replace(" ", "")
        for r in note.rows:
            lab = _norm(r[0]).replace(" ", "")
            vals = [to_num(_norm(c)) for c in r[1:]]
            if lab in _AXA_SEC and not any(v is not None for v in vals):
                sec = _AXA_SEC[lab]
                continue
            if sec != sec_want or nd not in lab:
                continue
            i = col.get(lob)
            if i is not None and len(vals) > i and vals[i] is not None:
                return vals[i] * f
        return None

    out = {}
    csm = pick("rev", "당기손익으로 인식한 보험계약마진")
    ra = pick("rev", "위험해제에 따른 위험조정 변동")
    rev_exp = pick("rev", "예상보험금 및 보험서비스비용")
    cost_act = pick("cost", "보험금 및 보험서비스비용")
    re_csm = pick("re_cost", "당기손익으로 인식한 보험계약마진")
    re_ra = pick("re_cost", "위험해제에 따른 위험조정 변동")
    re_rev_act = pick("re_rev", "회수가능 보험금 및 보험서비스비용")
    re_cost_exp = pick("re_cost", "회수예상 보험금 및 보험서비스비용")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev_act is not None and re_cost_exp is not None:
        out[11] = re_rev_act - re_cost_exp

    out["_jang_rev"] = pick("rev", "총 보험수익")
    out["_jang_cost"] = pick("cost", "총 보험서비스비용")
    out["_jang_rerev"] = pick("re_rev", "총 재보험수익")
    out["_jang_recost"] = pick("re_cost", "총 재보험비용")
    for lob, item in (("auto", 13), ("ilban", 14)):
        v = pick("re_cost", "총 보험서비스결과", lob=lob)   # final row sits after 출재보험비용
        if v is not None:
            out[item] = v

    # item16 (기타사업비용) from the income statement (원 단위; cell r[1] is the 주석 ref)
    for t in tables:
        labs = [_norm(r[0]).replace(" ", "") for r in t.rows]
        if not any(l.startswith(("Ⅰ.보험손익", "I.보험손익")) for l in labs):
            continue
        for r in t.rows:
            if re.sub(r"^\d+\)\s*", "", _norm(r[0])).replace(" ", "") == "기타사업비용":
                vals = [to_num(_norm(c)) for c in r[2:]]
                cur = next((v for v in vals if v is not None), None)
                if cur is not None:
                    out[16] = cur / 1e6
                break
        if 16 in out:
            break
    return out


# -------------------------- 코리안리 (KR1000, 수재) ------------------------- #
def extract_tier2_koreanre(tables):
    def labs(t):
        return " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)

    def collect(fl_start, must_all):
        return [t for t in tables
                if _fl(t).startswith(fl_start) and all(m in labs(t) for m in must_all)]

    rev_all = collect("보험수익", ["서비스의 이전으로 당기손익에 인식한 보험계약마진",
                                  "예상 손해조사비 (기초 예상 측정치)"])
    cost_all = collect("보험비용", ["발생한 보험금", "발생한 손해조사비"])
    rerev_all = collect("재보험자에게서 회수한 금액에서 생기는 수익", ["재보험수익, 발생한 보험금"])
    recost_all = collect("재보험자에게 지급된 보험료 배분액에서 생기는 비용",
                         ["서비스의 이전으로 당기손익에 인식한 보험계약마진"])
    if not (rev_all and cost_all and rerev_all and recost_all):
        return {}

    def standalone_current(lst):
        if len(lst) >= 4:
            return lst[len(lst) // 2]
        return lst[-1] if len(lst) >= 2 else lst[0]

    rev_t = standalone_current(rev_all)
    cost_t = standalone_current(cost_all)
    rerev_t = standalone_current(rerev_all)
    recost_t = standalone_current(recost_all)

    def grand(t):
        ns = _row_nums(t.rows[0])
        if len(ns) >= 7:
            return ns[3] + ns[6]
        return ns[-1] if ns else 0

    out = {}
    out[4] = abs(_firstlab(rev_t, *_S2_CSM))
    out[5] = abs(_firstlab(rev_t, *_S2_RA))
    out[6] = _sum_split(rev_t, _EXP_SPLIT) - _sum_split(cost_t, _ACT_SPLIT)
    out[9] = -abs(_firstlab(recost_t, *_S2_CSM))
    out[10] = -abs(_firstlab(recost_t, *_S2_RA))
    re_rev_act = _firstlab(rerev_t, "재보험수익, 발생한 보험금")
    re_cost_exp = _firstlab(recost_t, "재보험비용, 예상 보험금")
    if re_cost_exp is None:
        re_cost_exp = _firstlab(recost_t, "보고기간에 발생한 보험서비스비용 (기초 예상 측정치)")
    out[11] = abs(re_rev_act) - abs(re_cost_exp or 0)
    # reinsurer: no 자동차/일반 GMM LOB; 13/14 N/A. 장기 block = whole standalone uw.
    out["_jang_rev"] = grand(rev_t)
    out["_jang_cost"] = grand(cost_t)
    out["_jang_rerev"] = grand(rerev_t)
    out["_jang_recost"] = grand(recost_t)
    return out  # 백만원 already


# ===== 생보: component-decomposition notes (교보/DB생명/동양, single column) ===== #
def _life_flat(t):
    return "".join(_norm(c) for r in t.rows for c in r[:2]).replace(" ", "")


def _life_label_flat(r):
    return (_norm(r[0]) + _norm(r[1] if len(r) > 1 else "")).replace(" ", "")


def _life_is_rollforward(t):
    f = _life_flat(t)
    return any(k in f for k in ("기초순장부금액", "기말순장부금액", "기초보험계약", "기말보험계약",
                                "기초보유", "기말보유", "총현금흐름", "수취한보험료", "순장부금액"))


def _life_first_num(t, label_variants):
    """First numeric cell of the FIRST row whose flattened label contains any variant."""
    if t is None:
        return None
    for r in t.rows:
        lf = _life_label_flat(r)
        nums = _row_nums(r)
        if not nums:
            continue
        for v in label_variants:
            if v.replace(" ", "") in lf:
                return nums[0]
    return None


def extract_tier2_kyobo(tables):
    def pick(cap_contains_all, must_row):
        for t in tables:
            cap = t.caption or ""
            if all(s in cap for s in cap_contains_all) and "당사" in cap \
                    and not _life_is_rollforward(t):
                if must_row.replace(" ", "") in _life_flat(t):
                    return t
        return None
    rev = pick(("발행한 보험계약", "보험수익"), "당기손익에인식한보험계약마진")
    cost = pick(("발행한 보험계약", "보험서비스비용"), "보험계약에대한보험비용")
    rerev = pick(("재보험계약", "재보험수익"), "발생재보험금")
    recost = pick(("재보험계약", "재보험비용"), "보험계약마진상각")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["당기손익에인식한보험계약마진"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험에대한위험조정변동"]) or 0) or None
        exp = _life_first_num(rev, ["발생한보험서비스비용"])   # 교보 row label (was …수익 → item6 None)
    if cost:
        ac = _life_first_num(cost, ["실제보험금"])
        am = _life_first_num(cost, ["실제계약유지비용"])
        ai = _life_first_num(cost, ["실제투자관리비"])
        act = sum(x for x in (ac, am, ai) if x is not None) if ac is not None else None
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["위험조정변동", "비금융위험에대한위험조정"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상재보험금"])
    if rerev:
        re_act = _life_first_num(rerev, ["발생재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


def extract_tier2_dblife(tables):
    def pick(cap_frag, must_row=None):
        for t in tables:
            cap = t.caption or ""
            if cap_frag in cap and not _life_is_rollforward(t):
                if must_row is None or must_row.replace(" ", "") in _life_flat(t):
                    return t
        return None
    rev = pick("발행한 보험계약의 보험수익", "보험계약마진상각")
    cost = pick("발행한 보험계약의 보험비용", "발생보험금")
    rerev = pick("재보험계약의 재보험수익", "발생출재보험금")
    recost = pick("재보험계약의 재보험비용", "예상출재보험금")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험에대한위험조정상각"]) or 0) or None
        exp = sum(x for x in (
            _life_first_num(rev, ["예상보험금"]),
            _life_first_num(rev, ["예상유지비"]),
            _life_first_num(rev, ["예상손해조사비"]),
            _life_first_num(rev, ["예상투자관리비"]),
        ) if x is not None)
    if cost:
        act = sum(x for x in (
            _life_first_num(cost, ["발생보험금"]),
            _life_first_num(cost, ["발생직접유지비"]),
            _life_first_num(cost, ["손해조사비"]),
            _life_first_num(cost, ["투자관리비"]),
        ) if x is not None)
        if rev:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["비금융위험에대한위험조정상각"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상출재보험금"])
    if rerev:
        re_act = _life_first_num(rerev, ["발생출재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


def extract_tier2_dongyang(tables):
    def pick(first_label, must_row):
        for t in tables:
            if not t.rows or _life_is_rollforward(t):
                continue
            if _norm(t.rows[0][0]) != first_label:
                continue
            if must_row.replace(" ", "") in _life_flat(t):
                return t
        return None
    rev = pick("보험수익", "예상발생보험금및기타보험서비스비용")
    cost = pick("보험서비스비용", "실제발생보험금및기타보험서비스비용")
    rerev = pick("재보험수익", "실제재보험금및기타재보험서비스비용")
    recost = pick("재보험비용", "예상재보험금및기타재보험서비스비용")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험위험조정변동"]) or 0) or None
        exp = _life_first_num(rev, ["예상발생보험금및기타보험서비스비용"])
    if cost:
        act = _life_first_num(cost, ["실제발생보험금및기타보험서비스비용"])
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["비금융위험위험조정변동"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상재보험금및기타재보험서비스비용"])
    if rerev:
        re_act = _life_first_num(rerev, ["실제재보험금및기타재보험서비스비용"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


# ===== 생보: comprehensive positional-section note (신한/농협/흥국/케이디비/푸본) ===== #
_SECT = {
    "보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost",
    "재보험수익": "re_rev", "재보험비용": "re_cost", "재보험서비스비용": "re_cost",
    "출재보험수익": "re_rev", "출재보험비용": "re_cost",
}
_V_CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "제공된 서비스의 보험계약마진",
          "제공받은 서비스의 보험계약마진", "보험계약마진 상각", "제공받은 서비스의 재보험계약마진",
          "당기손익에 인식한 보험계약마진")
_V_RA = ("비금융위험에 대한 위험조정의 변동분", "위험해제로 인한 비금융위험에 대한 위험조정의 변동",
         "위험해제로 인한 위험조정의 변동", "위험조정 변동", "위험조정의 변동")
_V_REV_EXP = ("예상 보험금 및 기타보험 서비스비용", "예상보험금 및 기타보험 서비스비용",
              "예상 발생보험금 및 비용", "예상 발생보험금 및 보험서비스비용",
              "예상 보험금 및 보험서비스비용", "예상발생보험금",
              "예상 보험금 및 기타보험서비스 수익")
_V_COST_ACT = ("발생 보험금 및 기타보험서비스 비용", "발생보험금 및 기타보험 서비스비용",
               "실제 발생보험금 및 비용", "실제 발생보험금 및 보험서비스비용",
               "보험금 및 보험서비스비용", "실제발생보험금",
               "발생 보험금 및 기타보험서비스 비용")
_V_RE_REV_ACT = ("당기 발생재보험금", "발생재보험금", "회수가능 보험금 및 보험서비스비용",
                 "실제 출재보험금 및 비용", "실제발생재보험금",
                 "발생 재보험금 및 재보험서비스비용",        # 신한라이프
                 "실제 출재보험금 및 재보험비용",            # 케이디비 2025.x
                 "실제 출재보험금 및 재보험서비스비용",      # 케이디비 2026.1Q
                 "발생 출재보험금 및 재보험서비스비용")      # 흥국생명
_V_RE_COST_EXP = ("예상 재보험금 및 기타보험서비스비용", "회수예상보험금", "회수예상 보험금 및 보험서비스비용",
                  "예상 출재보험금 및 비용", "예상발생재보험금",
                  "예상 재보험금 및 기타 재보험서비스비용",  # 신한라이프
                  "예상 출재보험금 및 재보험비용",           # 케이디비 2025.x
                  "예상 출재보험금 및 재보험서비스비용")     # 케이디비 2026.1Q / 흥국생명


def _life2_match(lbl, variants):
    s = lbl.replace(" ", "")
    return any(v.replace(" ", "") in s for v in variants)


def _life2_first_num(r):
    for c in r:
        v = to_num(c)
        if v is not None:
            return v
    return None


def _life2_sect_of(lbl):
    s = lbl.replace(" ", "")
    s = re.sub(r"^[0-9]+\.", "", s)
    s = s.lstrip("(0-9). ")
    for k, val in _SECT.items():
        if s == k.replace(" ", "") or s.startswith(k.replace(" ", "")):
            return val
    return None


def _life2_rowblob(t):
    return " ".join(_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)


def _life2_is_rollfwd(t):
    b = _life2_rowblob(t)
    return any(k in b for k in ("기초 순장부금액", "기말 순장부금액", "기초 보험계약", "기말 보험계약",
                                "기초보험계약", "기말보험계약", "수취한 보험료", "순장부금액",
                                "보험계약부채(자산)", "기초 장부금액", "기말 장부금액"))


def _life_comprehensive(tables):
    """Family A: positional-section P&L-analysis note with 당기/전기 columns."""
    secvals = {}
    totals = {}

    def add(sec, kind, val, accumulate=False):
        d = secvals.setdefault(sec, {})
        if accumulate:
            d[kind] = (d.get(kind) or 0) + val
        elif kind not in d:
            d[kind] = val

    seen_caps = set()
    for t in tables:
        if _life2_is_rollfwd(t):
            continue
        b = _life2_rowblob(t)
        if "보험계약마진" not in b:
            continue
        if not any(s in b for s in ("보험수익", "보험서비스비용", "보험비용",
                                    "재보험수익", "재보험비용", "재보험서비스비용")):
            continue
        cap = (t.caption or "")
        capn = cap.replace(" ", "")
        if any(k in capn for k in ("최초인식", "최초 인식", "전환방법별", "전환 방법별",
                                   "신규로체결", "신규로 체결", "신용건전성", "신용위험",
                                   "지분의장부금액", "위험노출")):
            continue
        is_pl_cap = any(k in capn for k in ("보험손익", "보험서비스결과", "보험영업손익",
                                            "재보험영업손익", "구성내역", "상세내역",
                                            "보험계약관련손익", "보험수익및보험비용",
                                            "출재보험관련손익"))
        bn = b.replace(" ", "")
        has_tot_boundary = any(k in bn for k in ("총보험수익", "총보험서비스비용",
                                                 "총재보험수익", "총재보험서비스비용"))
        if not (is_pl_cap or has_tot_boundary):
            continue
        if cap in seen_caps:
            continue
        seen_caps.add(cap)
        section = None
        has_header_rows = any(_life2_sect_of(_norm(r[0])) for r in t.rows)
        shinhan_form = has_tot_boundary and not has_header_rows
        is_re_table = ("재보험영업손익" in capn) or ("출재보험관련손익" in capn) \
            or ("재보험서비스비용" in capn)
        if shinhan_form:
            section = "re_rev" if is_re_table else "rev"

        def value_of(r):
            return (max((v for v in (to_num(c) for c in r) if v is not None),
                        key=abs, default=None) if shinhan_form else _life2_first_num(r))

        for r in t.rows:
            lab0 = _norm(r[0]) if r else ""
            lab1 = _norm(r[1]) if len(r) > 1 else ""
            lbl = (lab0 + lab1)
            nums = [v for v in (to_num(c) for c in r) if v is not None]
            sec_hdr = _life2_sect_of(lab0)
            if sec_hdr and (not nums or lab1):
                section = sec_hdr
                if not nums:
                    continue
                lbl = lab1
            if section is None:
                continue
            cur = value_of(r)
            if cur is None:
                continue
            plain = lab0.replace(" ", "")
            l1 = lab1.replace(" ", "")
            if any(k in plain for k in ("소계", "합계", "총보험수익", "총보험서비스비용",
                                        "총재보험수익", "총재보험서비스비용", "총재보험비용")) \
                    or l1 in ("소계", "합계"):
                totals.setdefault(section, cur)
                if shinhan_form:
                    if "총보험수익" in plain:
                        section = "cost"
                    elif "총재보험수익" in plain:
                        section = "re_cost"
                continue
            if section == "rev":
                if _life2_match(lbl, _V_CSM):
                    add("rev", "csm", cur)
                elif _life2_match(lbl, _V_RA):
                    add("rev", "ra", cur)
                elif _life2_match(lbl, _V_REV_EXP):
                    add("rev", "exp", cur, accumulate=True)
            elif section == "cost":
                if _life2_match(lbl, _V_COST_ACT):
                    add("cost", "act", cur, accumulate=True)
            elif section == "re_rev":
                if _life2_match(lbl, _V_RE_REV_ACT):
                    add("re_rev", "act", cur, accumulate=True)
            elif section == "re_cost":
                if _life2_match(lbl, _V_CSM):
                    add("re_cost", "csm", cur)
                elif _life2_match(lbl, _V_RA):
                    add("re_cost", "ra", cur)
                elif _life2_match(lbl, _V_RE_COST_EXP):
                    add("re_cost", "exp", cur, accumulate=True)
    return secvals, totals


def _life_product_split(tables):
    """Family B: 미래에셋 product-split notes. Only items 4,5,9,10 recoverable."""
    def hdr_blob(x):
        return " ".join(" ".join(h) for h in x.header)

    def block_sum(group):
        csm = ra = None
        for x in group:
            cur = "dang"
            for r in x.rows:
                lab0 = _norm(r[0])
                if lab0 == "당기":
                    cur = "dang"
                elif lab0 == "전기":
                    cur = "jeon"
                nums = [v for v in (to_num(c) for c in r) if v is not None]
                if cur != "dang" or not nums:
                    continue
                key = (lab0 + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
                v = nums[-1]
                if _life2_match(key, _V_CSM):
                    csm = (csm or 0) + v
                elif _life2_match(key, _V_RA):
                    ra = (ra or 0) + v
        return csm, ra

    def fingerprint(x):
        return tuple(round(v, 1) for r in x.rows
                     for v in (to_num(c) for c in r) if v is not None)

    rev_group, recost_group = [], []
    seen_fp = set()
    for x in tables:
        rows0 = [_norm(r[0]) for r in x.rows]
        body = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in x.rows)
        if "당기" not in rows0 or "전기" not in rows0 or "보험계약마진" not in body:
            continue
        fp = fingerprint(x)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        hb = hdr_blob(x)
        if "재보험서비스비용" in hb:
            recost_group.append(x)
        elif "보험수익" in hb and "재보험" not in hb:
            rev_group.append(x)
    if not rev_group and not recost_group:
        return {}
    out = {}
    csm, ra = block_sum(rev_group)
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    re_csm, re_ra = block_sum(recost_group)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out


def _life_build_items(secvals, totals):
    rev = secvals.get("rev", {})
    cost = secvals.get("cost", {})
    re_rev = secvals.get("re_rev", {})
    re_cost = secvals.get("re_cost", {})
    out = {}
    if rev.get("csm") is not None:
        out[4] = abs(rev["csm"])
    if rev.get("ra") is not None:
        out[5] = abs(rev["ra"])
    if rev.get("exp") is not None and cost.get("act") is not None:
        out[6] = abs(rev["exp"]) - abs(cost["act"])
    if re_cost.get("csm") is not None:
        out[9] = -abs(re_cost["csm"])
    if re_cost.get("ra") is not None:
        out[10] = -abs(re_cost["ra"])
    if re_rev.get("act") is not None and re_cost.get("exp") is not None:
        out[11] = abs(re_rev["act"]) - abs(re_cost["exp"])
    return out


# ----------------------------- KB라이프생명 (KR0099) ----------------------- #
def _kblife_block_total(note, which, needle):
    """합계 of the wanted period block in KB라이프's 계약유형별 P&L note.  Cell layout after the
    col0 label is one or two 6-column blocks (사망/건강/연금저축/변액/복합/합계); 합계 is the
    block's rightmost data col.  `which`='first' → 당기 block (당기/전기 annual note); 'last' →
    누적 block (3개월/누적 반기 note) or the only block (single-period quarter)."""
    nd = needle.replace(" ", "")
    for r in note.rows:
        if nd not in _norm(r[0]).replace(" ", ""):
            continue
        data = r[1:]
        b1, b2 = data[0:6], data[6:12]
        if which == "last" and any(to_num(c) is not None for c in b2):
            block = b2
        else:
            block = b1
        for c in reversed(block):          # 합계 = last non-blank col of the block
            v = to_num(c)
            if v is not None:
                return v
        return None
    return None


def extract_tier2_kblife(tables):
    """KB라이프생명 (KR0099): 푸르덴셜+KB생명 merger note.  계약유형별 P&L-analysis note with
    KB-specific row labels that none of the shared variant lists match (CSM상각 = '서비스제공에
    따른 보험계약마진의 변동', etc.) — code-keyed so only KR0099 takes this path.  Picks the
    correct period block: 당기(1st) for the 당기/전기 annual note, 누적(2nd) for the 3개월/누적
    반기 note, the only block otherwise."""
    note = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap \
                or "보험영업비용" not in cap:
            continue
        if _is_rollforward(t):
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not any(k in hb for k in ("당분기", "당반기", "당기")):
            continue
        if not any(_norm(r[0]).replace(" ", "") == "서비스제공에따른보험계약마진의변동"
                   for r in t.rows):
            continue                        # the current-period table that carries the rows
        note = t
        break
    if note is None:
        return {}

    hbn = " ".join(" ".join(h) for h in note.header).replace(" ", "")
    which = "first" if "전기" in hbn else "last"   # 누적/single → last; 당기/전기 → first
    g = lambda nd: _kblife_block_total(note, which, nd)

    csm = g("서비스제공에 따른 보험계약마진의 변동")
    ra = g("위험해제에 따른 위험조정의 변동")
    rev_exp = g("예상보험금 및 예상보험서비스 비용")
    cost_act = g("실제보험금 및 실제보험서비스비용")
    re_csm = g("제공받은 서비스의 재보험계약마진")
    re_ra = g("위험해제로 인한 위험조정의 변동")
    re_rev = g("발생 재보험금 및 재보험서비스비용 회수액")
    re_cost_exp = g("회수예상 보험금 및 보험서비스비용")

    out = {}
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)
    # 발행/출재 grand totals for item3/8 (assemble also has the FS-API _is_* fallback)
    jr, jc = g("총 보험수익"), g("총 보험서비스비용")
    jrr, jrc = g("총 재보험수익"), g("총 재보험비용")
    if jr is not None:
        out["_jang_rev"] = abs(jr)
    if jc is not None:
        out["_jang_cost"] = abs(jc)
    if jrr is not None:
        out["_jang_rerev"] = abs(jrr)
    if jrc is not None:
        out["_jang_recost"] = abs(jrc)
    return out


# ============ 구형식 (pre-2025.2Q) 생보 OLD note family (3 layouts) ============ #
_OLD_L_SECT = {"보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost",
               "보험영업수익": "rev", "보험영업비용": "cost",
               "재보험수익": "re_rev", "재보험비용": "re_cost", "재보험서비스비용": "re_cost",
               "재보험영업수익": "re_rev", "재보험영업비용": "re_cost",
               "출재보험수익": "re_rev", "출재보험비용": "re_cost"}
_OLD_L_CSM = ("보험계약마진 상각", "제공된 서비스의 보험계약마진", "제공받은 서비스의 보험계약마진",
              "제공받은 서비스의 재보험계약마진", "서비스제공에 따른 보험계약마진의 변동",
              "당기손익에 인식한 보험계약마진")
_OLD_L_RA = ("위험조정 변동", "위험해제로 인한 위험조정의 변동", "위험해제에 따른 위험조정의 변동",
             "위험해제로 인한 비금융위험에 대한 위험조정의 변동", "비금융위험에 대한 위험조정의 변동")
_OLD_L_REVEXP = ("예상 보험금 및 보험서비스비용", "예상발생보험금", "예상 발생보험금 및 보험서비스비용",
                 "예상 보험금 및 기타보험 서비스비용", "예상보험금 및 예상보험서비스 비용")
_OLD_L_COSTACT = ("실제발생보험금", "실제 발생보험금 및 보험서비스비용", "보험금 및 보험서비스비용",
                  "발생보험금", "실제보험금 및 실제보험서비스비용")
_OLD_L_RE_REVACT = ("회수가능 보험금 및 보험서비스비용", "실제 출재보험금 및 보험서비스비용",
                    "발생 재보험금", "실제출재보험금", "실제발생재보험금", "발생재보험금")
_OLD_L_RE_COSTEXP = ("회수예상 보험금 및 보험서비스비용", "예상 출재보험금 및 보험서비스비용",
                     "회수예상보험금", "예상출재보험금", "예상발생재보험금")


def _oll_sn(s):
    return re.sub(r"^[\(0-9\)\.\s]+", "", _norm(s)).replace(" ", "")


def _oll_match(lbl, vs):
    s = _norm(lbl).replace(" ", "")
    return any(v.replace(" ", "") in s for v in vs)


def _oll_ytd(t):
    """('pair', 1) for [3개월,누적] columns else ('single', 0)."""
    hb = _header_blob(t)
    return ("pair", 1) if ("누적" in hb and "3개월" in hb) else ("single", 0)


def _oll_num(r, mi):
    mode, idx = mi
    ns = [to_num(c) for c in r if to_num(c) is not None]
    if not ns:
        return None
    return (ns[idx] if len(ns) > idx else ns[0]) if mode == "pair" else ns[0]


def _oll_l1_pure(t):
    hb = _header_blob(t)
    return not any(k in hb for k in ("손해보험", "장기", "자동차"))


def _oll_l1_hassec(t, name):
    return any(_oll_sn(r[0]) == name and not [to_num(c) for c in r if to_num(c) is not None]
               for r in t.rows)


def _oll_l1_is(t):
    if _life2_is_rollfwd(t):
        return False
    hb = _header_blob(t)
    if "합계" not in hb and "합 계" not in hb:
        return False
    if "보험계약마진" not in "".join(_norm(r[0]) for r in t.rows):
        return False
    return sum(1 for r in t.rows if _oll_sn(r[0]) in _OLD_L_SECT
               and not [to_num(c) for c in r if to_num(c) is not None]) >= 2


def _oll_l1_collect(t):
    sec, d = None, {}
    for r in t.rows:
        key = _oll_sn(r[0])
        nums = [to_num(c) for c in r if to_num(c) is not None]
        if key in _OLD_L_SECT and not nums:
            sec = _OLD_L_SECT[key]
            continue
        if sec is None or key.startswith("총") or key in ("소계", "합계"):
            continue
        v = nums[-1] if nums else None
        if v is None:
            continue
        if sec == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d.setdefault("exp", v)
        elif sec == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d.setdefault("cact", v)
        elif sec == "re_rev":
            if _oll_match(r[0], _OLD_L_RE_REVACT):
                d.setdefault("ract", v)
        elif sec == "re_cost":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("recsm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("rera", v)
            elif _oll_match(r[0], _OLD_L_RE_COSTEXP):
                d.setdefault("rexp", v)
    return d


def _oll_layout1(tables):
    rc = [t for t in tables if _oll_l1_is(t)]
    pool = [t for t in rc if _oll_l1_pure(t)] or rc        # 별도 (pure life) preferred
    rev_t = next((t for t in pool if _oll_l1_hassec(t, "보험수익")), None)
    re_t = next((t for t in pool if _oll_l1_hassec(t, "재보험수익")), None)
    out = {}
    if rev_t:
        d = _oll_l1_collect(rev_t)
        if "csm" in d:
            out[4] = abs(d["csm"])
        if "ra" in d:
            out[5] = abs(d["ra"])
        if "exp" in d and "cact" in d:
            out[6] = abs(d["exp"]) - abs(d["cact"])
    if re_t:
        d = _oll_l1_collect(re_t)
        if "recsm" in d:
            out[9] = -abs(d["recsm"])
        if "rera" in d:
            out[10] = -abs(d["rera"])
        if "ract" in d and "rexp" in d:
            out[11] = abs(d["ract"]) - abs(d["rexp"])
    return out


def _oll_secs(t):
    return [_OLD_L_SECT[_oll_sn(r[0])] for r in t.rows if _oll_sn(r[0]) in _OLD_L_SECT]


def _oll_l2_parse(t, want):
    mi = _oll_ytd(t)
    sec, d = None, {}
    for r in t.rows:
        key = _oll_sn(r[0])
        nums = [to_num(c) for c in r if to_num(c) is not None]
        if key in _OLD_L_SECT:
            sec = _OLD_L_SECT[key]
            if sec == want and nums:
                d.setdefault("_agg", _oll_num(r, mi))
            continue
        if sec != want or key in ("소계", "합계"):
            continue
        v = _oll_num(r, mi)
        if v is None:
            continue
        if want == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d["exp"] = d.get("exp", 0) + v
        elif want == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d["act"] = d.get("act", 0) + v
        elif want == "re_rev":
            if _oll_match(r[0], _OLD_L_RE_REVACT):
                d["act"] = d.get("act", 0) + v
        elif want == "re_cost":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_RE_COSTEXP):
                d["exp"] = d.get("exp", 0) + v
    return d


def _oll_l2_caption_leg(cap):
    c = (cap or "").replace(" ", "")
    if "재보험" in c and ("손익" in c or "구성" in c):
        return "re"
    if "보험수익의구성" in c:
        return "rev"
    if "보험비용의구성" in c or "보험서비스비용의구성" in c:
        return "cost"
    return None


def _oll_l2_whole(t, want):
    mi = _oll_ytd(t)
    d = {}
    for r in t.rows:
        if _oll_sn(r[0]) in ("소계", "합계"):
            continue
        v = _oll_num(r, mi)
        if v is None:
            continue
        if want == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d["exp"] = d.get("exp", 0) + v
        elif want == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d["act"] = d.get("act", 0) + v
    return d


def _oll_layout2(tables):
    cands = [t for t in tables
             if (not _life2_is_rollfwd(t))
             and "보험계약마진" in "".join(_oll_sn(r[0]) for r in t.rows)
             and _oll_secs(t)]
    legs = {}
    for sec in ("rev", "cost", "re_rev", "re_cost"):       # best (별도, smallest total) per leg
        src = [t for t in cands if sec in _oll_secs(t)]
        if not src:
            continue

        def keyf(t):
            agg = _oll_l2_parse(t, sec).get("_agg")
            return (abs(agg) if agg is not None else float("inf"), -len(t.rows))
        legs[sec] = _oll_l2_parse(min(src, key=keyf), sec)
    if "rev" not in legs or "cost" not in legs:            # 푸본-FY2023 caption-leg fallback
        rv = [t for t in tables if _oll_l2_caption_leg(t.caption) == "rev" and not _life2_is_rollfwd(t)]
        cs = [t for t in tables if _oll_l2_caption_leg(t.caption) == "cost" and not _life2_is_rollfwd(t)]
        if rv and "rev" not in legs:
            legs["rev"] = _oll_l2_whole(rv[0], "rev")
        if cs and "cost" not in legs:
            legs["cost"] = _oll_l2_whole(cs[0], "cost")
    if "re_rev" not in legs or "re_cost" not in legs:
        rsrc = [t for t in tables if _oll_l2_caption_leg(t.caption) == "re"
                and not _life2_is_rollfwd(t) and _oll_secs(t)]
        for sec in ("re_rev", "re_cost"):
            if sec in legs:
                continue
            s = [t for t in rsrc if sec in _oll_secs(t)]
            if s:
                legs[sec] = _oll_l2_parse(s[0], sec)
    if not legs:
        return {}
    rev, cost = legs.get("rev", {}), legs.get("cost", {})
    rr, rcst = legs.get("re_rev", {}), legs.get("re_cost", {})
    out = {}
    if "csm" in rev:
        out[4] = abs(rev["csm"])
    if "ra" in rev:
        out[5] = abs(rev["ra"])
    e, a = rev.get("exp", rev.get("_agg")), cost.get("act", cost.get("_agg"))
    if e is not None and a is not None:
        out[6] = abs(e) - abs(a)
    if "csm" in rcst:
        out[9] = -abs(rcst["csm"])
    if "ra" in rcst:
        out[10] = -abs(rcst["ra"])
    ra_, re_ = rr.get("act", rr.get("_agg")), rcst.get("exp", rcst.get("_agg"))
    if ra_ is not None and re_ is not None:
        out[11] = abs(ra_) - abs(re_)
    return out


def extract_tier2_life_old(tables):
    """Dispatcher for pre-2025.2Q 생보 notes: 한화 LOB-column (L1) → 구분-row period-column
    (L2, 농협/흥국/KDB/푸본) → per-product rollforward (L3, 미래에셋, items 4/5/9/10 only).
    Returns {} when none match — and, as a guard, when the NEW standardized CSM label is present
    (a 2025.2Q+ filing) so the NEW handlers/comprehensive keep precedence and golds never regress."""
    for t in tables:
        if _life2_is_rollfwd(t):
            continue          # 미래에셋 L3 rollforward CSM line shares this wording — not a NEW note
        for r in t.rows:
            if "서비스의이전으로당기손익에인식한보험계약마진" in _norm(r[0]).replace(" ", ""):
                return {}
    out = _oll_layout1(tables)
    if out and out.get(4):
        return out
    out = _oll_layout2(tables)
    if out and out.get(4):
        return out
    # 미래에셋 (L3 rollforward) is left to comprehensive's own _life_product_split fallback —
    # calling it here would override a good comprehensive result on recent quarters.
    return {}


def extract_tier2_life_comprehensive(tables, code=None):
    """생보 Family A/B dispatcher: comprehensive note, with 미래에셋 product-split
    fallback for items 4,5,9,10.  Emits the note 발행/출재 grand totals (_jang_*) for
    item3/8, EXCEPT 신한라이프 (KR0094) — its note 총 over-states by a PAA-presentation
    reclass, so we leave _jang_* unset and let assemble fall back to the plain 별도
    income-statement 보험수익/보험서비스비용 lines (which reconcile exactly)."""
    # pre-2025.2Q OLD note (누적/합계 basis) takes precedence — the comprehensive note misreads
    # old quarters (3개월 / single-product); life_old defers on NEW filings via its guard.
    old = extract_tier2_life_old(tables)
    if old and old.get(4):
        return old
    secvals, totals = _life_comprehensive(tables)
    out = _life_build_items(secvals, totals)
    if not any(out.get(i) is not None for i in (4, 5)):
        for k, val in _life_product_split(tables).items():
            out.setdefault(k, val)
    if code != "KR0094":
        for k, sec in (("_jang_rev", "rev"), ("_jang_cost", "cost"),
                       ("_jang_rerev", "re_rev"), ("_jang_recost", "re_cost")):
            if sec in totals:
                out[k] = totals[sec]
    return out


def extract_tier2_samsung_life(tables):
    """삼성생명(연결, KR0069) OLD-format combined 보험서비스수익/비용 notes (2023.1Q–2025.1Q).
    Reads the 당기 누적 column; 재보 lives under the 출재보험서비스수익/비용 col0 sections
    (재보 CSM labelled '제공받은 서비스의 보험계약마진').  2025.2Q+ uses dedicated 재보 tables →
    handler returns {} there and parse_filing's generic fallback (extract_tier2_life) handles it."""
    def cum(r):                       # 당기 누적 = last col of the 당기 block
        n = _row_nums(r)
        return n[max(1, len(n) // 2) - 1] if n else None

    def rf(t, *nd):
        for r in t.rows:
            lab = (_norm(r[0]) + "|" + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(x.replace(" ", "") in lab for x in nd):
                return r
        return None
    rev = cost = None
    for t in tables:
        cap = t.caption or ""
        if rev is None and "보험서비스수익의 내역" in cap:
            rev = t
        if cost is None and "보험서비스비용의 내역" in cap:
            cost = t
    if not (rev and cost):
        return {}
    out = {}
    out[4] = abs(cum(rf(rev, "제공된 서비스의 보험계약마진")) or 0) or None
    r5 = next((r for r in rev.rows if "위험해제" in _norm(r[0]).replace(" ", "")), None)
    out[5] = abs(cum(r5) or 0) or None
    rev_exp = cum(rf(rev, "일반보험서비스수익"))      # 원수 예상 (col1 line-item)
    re_act = cum(rf(rev, "출재보험서비스수익"))       # 재보 실제
    cost_act = cum(rf(cost, "일반보험서비스비용"))    # 원수 실제
    out[9] = -abs(cum(rf(cost, "제공받은 서비스의 보험계약마진")) or 0) or None
    seen = False
    r10 = None                                        # 재보 RA = 위험해제 row AFTER 출재 header
    for r in cost.rows:
        if "출재보험서비스비용" in _norm(r[0]).replace(" ", ""):
            seen = True
        if seen and "위험해제" in _norm(r[0]).replace(" ", ""):
            r10 = r
            break
    out[10] = -abs(cum(r10) or 0) or None
    re_exp = cum(rf(cost, "출재보험서비스비용"))       # 재보 예상
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_act is not None and re_exp is not None:
        out[11] = abs(re_act) - abs(re_exp)
    return out


# --------------------------- 미래에셋생명 (KR0079) ------------------------- #
_MA_CSM_KEY = "서비스의이전으로당기손익에인식한보험계약마진"   # both note forms
_MA_RA_KEYS = ("위험조정변동분",
               "미래또는과거서비스와관련없는비금융위험에대한위험조정의변동",
               "비금융위험에대한위험조정의변동분")


def _ma_block_val(t, keys, last_only):
    """First 당기/당분기/당반기-block row matching `keys`.  last_only=True → 합계 col
    (nums[-1], 백만원 note); else whole-row sum (원-wide)."""
    cur = "dang"
    for r in t.rows:
        lab0 = _norm(r[0]).replace(" ", "")
        if lab0 in ("당기", "당분기", "당반기"):
            cur = "dang"
        elif lab0 in ("전기", "전분기", "전반기"):
            cur = "jeon"
        if cur != "dang":
            continue
        lab = (_norm(r[0]) + "|" + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(k in lab for k in keys):
            nums = [v for v in (to_num(c) for c in r) if v is not None]
            if not nums:
                continue
            return nums[-1] if last_only else sum(nums)
    return None


def extract_tier2_miraeasset(tables):
    """미래에셋생명 (KR0079) per-product CSM/RA → items 4,5,9,10 (백만원).  Two note eras:
      1. 백만원 보험수익 note (annual + 2023.3Q–2025.1Q quarters): 5 separate product tables,
         당분기/당기 block, 합계 = last numeric col.
      2. 원 wide rollforward (2025.2Q/3Q, 2026.1Q): products are COLUMNS; the CSM-amort row
         carries values ONLY in CSM cols (PV/RA cols 0) → whole-row sum = item4; /1e6 → 백만원.
    Era-1 preferred.  item3/8 + RC come from the FS income-statement legs in assemble();
    item6/11 data-absent (no 예실차 split)."""
    def hb(t):
        return " ".join(" ".join(h) for h in t.header).replace(" ", "")

    def has_amort(t):
        return _MA_CSM_KEY in " ".join(
            _norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows
        ).replace(" ", "")

    # ---- Era 1: 백만원 per-product 보험수익 note ----
    seen = set()
    rev_c = rev_a = re_c = re_a = None
    for t in tables:
        h = hb(t)
        if "단위:백만원" not in h or not has_amort(t):
            continue
        is_recost = "재보험서비스비용" in h
        is_rev = ("보험수익" in h) and not is_recost
        if not (is_rev or is_recost):
            continue
        fp = tuple(to_num(c) for r in t.rows for c in r if to_num(c) is not None)
        if fp in seen:
            continue
        seen.add(fp)
        c = _ma_block_val(t, (_MA_CSM_KEY,), last_only=True)
        a = _ma_block_val(t, _MA_RA_KEYS, last_only=True)
        if is_recost:
            if c is not None:
                re_c = (re_c or 0) + c
            if a is not None:
                re_a = (re_a or 0) + a
        else:
            if c is not None:
                rev_c = (rev_c or 0) + c
            if a is not None:
                rev_a = (rev_a or 0) + a
    if rev_c is not None:
        out = {4: abs(rev_c)}
        if rev_a is not None:
            out[5] = abs(rev_a)
        if re_c is not None:
            out[9] = -abs(re_c)
        if re_a is not None:
            out[10] = -abs(re_a)
        return out

    # ---- Era 2: 원 wide product-column rollforward (first table = 당기) ----
    first_issue = first_re = None
    seen2 = set()
    for t in tables:
        h = hb(t)
        if "사망보험" not in h or not has_amort(t) or len(t.rows) < 5:
            continue
        fp = tuple(to_num(c) for r in t.rows for c in r if to_num(c) is not None)
        if fp in seen2:
            continue
        seen2.add(fp)
        if "발행한보험계약" in h and "보유재보험계약" not in h:
            if first_issue is None:
                first_issue = t
        elif "보유재보험계약" in h:
            if first_re is None:
                first_re = t
    out = {}
    if first_issue is not None:
        c = _ma_block_val(first_issue, (_MA_CSM_KEY,), last_only=False)
        a = _ma_block_val(first_issue, _MA_RA_KEYS, last_only=False)
        if c is not None:
            out[4] = abs(c) / 1e6
        if a is not None:
            out[5] = abs(a) / 1e6
    if first_re is not None:
        c = _ma_block_val(first_re, (_MA_CSM_KEY,), last_only=False)
        a = _ma_block_val(first_re, _MA_RA_KEYS, last_only=False)
        if c is not None:
            out[9] = -abs(c) / 1e6
        if a is not None:
            out[10] = -abs(a) / 1e6
    return out


def extract_tier2_hana(tables):
    """하나생명(KR0097): disaggregated 보험수익/보험서비스비용 notes (NOT a P&L-analysis note).
    4 separate tables captioned '발행한 보험계약…보험수익/보험서비스비용' + the 재보험 pair.
    Unit 천원 → 백만원 (×1e-3); current period = col 0.  (Tier-1 item1=순보험서비스손익,
    item16←기타보험비용 are fixed in extract_tier1.)"""
    f = 1e-3

    def pick(*cap_frags):
        for t in tables:
            cap = (t.caption or "")
            if all(s in cap for s in cap_frags) and not _life_is_rollforward(t):
                return t
        return None
    rev = pick("발행한 보험계약", "보험수익")
    cost = pick("발행한 보험계약", "보험서비스비용")
    rerev = pick("재보험계약", "보험수익")
    recost = pick("재보험계약", "보험서비스비용")
    out = {}
    # 발행(원수) 합계 → item3 = 보험수익 − 보험서비스비용 (assemble).  Without these, item3 would
    # fall back to the income-statement _is_rev/_is_cost, but 하나's _is_cost is a mis-pick
    # (≈9% of 보험수익) that the materiality guard rejects → item3/item2 went None.
    if rev:
        out["_jang_rev"] = _life_first_num(rev, ["합 계", "합계"])
    if cost:
        out["_jang_cost"] = _life_first_num(cost, ["합 계", "합계"])
    if rev:
        csm = _life_first_num(rev, ["보험계약마진상각"])
        ra = _life_first_num(rev, ["비금융위험에 대한 위험조정 변동"])
        if csm is not None:
            out[4] = abs(csm)
        if ra is not None:
            out[5] = abs(ra)
        exp = _life_first_num(rev, ["소 계"])      # first 소계 = 예상 발생 보험서비스비용
        if cost and exp is not None:
            act = sum(x for x in (
                _life_first_num(cost, ["발생보험금"]),
                _life_first_num(cost, ["발생사고부채변동"]),
                _life_first_num(cost, ["직접유지비"]),
                _life_first_num(cost, ["손해조사비"]),
                _life_first_num(cost, ["투자관리비"]),
            ) if x is not None)
            out[6] = abs(exp) - abs(act)
    if recost:
        rc = _life_first_num(recost, ["보험계약마진상각"])
        rr = _life_first_num(recost, ["위험조정 변동", "비금융위험에 대한 위험조정 변동"])
        if rc is not None:
            out[9] = -abs(rc)
        if rr is not None:
            out[10] = -abs(rr)
        re_exp = _life_first_num(recost, ["예상출재보험금"])
        if rerev and re_exp is not None:
            re_act = _life_first_num(rerev, ["발생재보험금"])
            if re_act is not None:
                out[11] = abs(re_act) - abs(re_exp)
    return {k: (v * f if isinstance(v, (int, float)) else v) for k, v in out.items() if v is not None}


# Per-company routing tables (FY2025+ annual Tier-2 handlers).
SONBO_HANDLERS = {
    "KR0010": extract_tier2_kb,
    "KR0009": extract_tier2_hyundai,
    "KR0002": _hanwha_dispatch,                # 한화손해 (NEW 2025.2Q+ → OLD pre-2025.2Q)
    "KR0008": extract_tier2_sonbo_component,   # 삼성화재 (gold-validated 2025.2Q)
    "KR0005": _heungkuk_dispatch,              # 흥국화재 (NEW 2025.2Q+ → OLD pre-2025.2Q)
    "KR0011": extract_tier2_db,
    "KR0032": extract_tier2_nh,
    "KR0003": extract_tier2_lotte,
    "KR0049": extract_tier2_axa,               # 악사손해 연차 '보험손익 상세내역' (자동차|일반|장기 columns)
    "KR1000": extract_tier2_coreanre,          # 코리안리 재보험 (gold-validated 2025.2Q; 생명/장기/일반)
}
LIFE_HANDLERS = {
    "KR0070": extract_tier2_abl,               # 에이비엘 ([구분|당기|전기] 2-period note → pick 당기)
    "KR0073": extract_tier2_kyobo,
    "KR0082": extract_tier2_dblife,
    "KR0087": extract_tier2_dongyang,
    "KR0094": extract_tier2_life_comprehensive,
    "KR0104": extract_tier2_life_comprehensive,
    "KR0071": extract_tier2_life_comprehensive,
    "KR0072": extract_tier2_life_comprehensive,
    "KR0079": extract_tier2_miraeasset,        # 미래에셋생명 (per-product CSM/RA, 백만원+원 eras)
    "KR0083": extract_tier2_life_comprehensive,
    "KR0099": extract_tier2_kblife,            # KB라이프생명 (KB-specific row labels)
    "KR0069": extract_tier2_samsung_life,      # 삼성생명 OLD combined note (9/10/11); NEW→generic
    "KR0097": extract_tier2_hana,              # 하나생명 (disaggregated 보험수익/비용 notes)
}


# --------------------------------------------------------------------------- #
# Assembly of the 24-item vector
# --------------------------------------------------------------------------- #
def assemble(t1, t2, is_life):
    """Merge tier1 + tier2 and derive the identity items. Returns {item_no: value|None}."""
    v = {n: None for n in range(1, 25)}
    if t1:
        for k, val in t1.items():
            v[k] = val
    if t2:
        for k, val in t2.items():
            v[k] = val

    # item16 (기타사업비용) is a COST → positive magnitude.  The DART FS-API returns it with an
    # inconsistent sign (negative for some company-quarters, e.g. 한화손해/농협생명/삼성생명 일부),
    # which breaks the Tier-2 RC bridge and the gold gate.  Normalize to positive.
    if v[16] is not None:
        v[16] = abs(v[16])

    if is_life:
        v[13] = 0.0
        v[14] = 0.0

    # item 15 (기타영업수익): when the income statement was found but carries no
    # operating-block 기타영업수익, the gold convention is 0 (생보 / summary statements).
    if t1 and v[15] is None:
        v[15] = 0.0

    # 장기/발행-column totals for the 원수/재보험 splits (items 3/7/8/12).
    # 손보: from the LOB note (tier2 hidden keys).  생보: from the income-statement
    # 발행/출재 sub-lines (tier1 hidden keys).
    jang_rev = (t2 or {}).get("_jang_rev")
    jang_cost = (t2 or {}).get("_jang_cost")
    jang_rerev = (t2 or {}).get("_jang_rerev")
    jang_recost = (t2 or {}).get("_jang_recost")
    if is_life and t1:
        lr, lc = t1.get("_life_rev"), t1.get("_life_cost")
        lrr, lrc = t1.get("_life_rerev"), t1.get("_life_recost")
        if lr is not None:
            jang_rev = abs(lr)
        if lc is not None:
            jang_cost = abs(lc)
        if lrr is not None:
            jang_rerev = abs(lrr)
        if lrc is not None:
            jang_recost = abs(lrc)
        # Final fallback for the 생보 component-decomposition / comprehensive companies
        # (교보/DB생명/동양/신한/농협/흥국/케이디비/푸본/미래에셋): item3/8 from the plain
        # 별도 income-statement insurance lines (note carries no rev/cost grand totals).
        # COST legs (보험비용/재보험비용) are EXPENSES — take the magnitude: some statements
        # print them parenthesised (negative), e.g. 미래에셋 FY2023 보험비용=(659,299), which
        # would otherwise flip item3 = 보험수익 − 보험비용 into an ADDITION (≈6× too big).
        # REV legs stay signed (재보험수익 can be genuinely negative).
        # Materiality guard: a 보험비용 line ≈0 relative to 보험수익 is a mis-pick (footnote
        # ref / section header), NOT the real cost — using it makes item3 = gross 보험수익.
        # Skip the fallback then (item2/3/8 stay None) so the gate doesn't fire and null the
        # GOOD note-derived items 4-11 (e.g. 교보 2025.4Q: _is_cost mis-read as 0.0017).
        _ir, _ic = t1.get("_is_rev"), t1.get("_is_cost")
        if jang_rev is None and _ir and _ic is not None \
                and abs(_ic) >= 0.10 * abs(_ir):
            jang_rev = _ir
            jang_cost = abs(_ic)
        if jang_rerev is None and t1.get("_is_rerev") is not None \
                and t1.get("_is_recost") is not None:
            jang_rerev = t1["_is_rerev"]
            jang_recost = abs(t1["_is_recost"])

    def s(*items):
        """sum if all present else None."""
        vals = [v[i] for i in items]
        return sum(vals) if all(x is not None for x in vals) else None

    # item 3 (생명장기 원수손익) = 발행 보험수익합 − 보험서비스비용합 (장기/생보 column)
    if jang_rev is not None and jang_cost is not None:
        v[3] = jang_rev - jang_cost
    # item 8 (생명장기 재보험손익) = 재보험수익합 − 재보험비용합 (장기/생보 column)
    if jang_rerev is not None and jang_recost is not None:
        v[8] = jang_rerev - jang_recost
    # item 7 (residual) = 3 − (4+5+6)
    if v[3] is not None and None not in (v[4], v[5], v[6]):
        v[7] = v[3] - (v[4] + v[5] + v[6])
    # 예실차(item6) NOT separately disclosed (no 예상-vs-실제 청구 split in the note — e.g.
    # 농협·미래에셋·교보·동양): the 원수손익 subtotal & CSM상각/RA ARE disclosed, so the combined
    # residual (item3 − 4 − 5) is the unsplittable 예실차+기타.  Owner decision 2026-06-08: push
    # it into 기타(item7) and show 예실차 as 0 — do NOT fabricate a 예실차 number.
    elif v[3] is not None and v[4] is not None and v[5] is not None and v[6] is None:
        v[6] = 0.0
        v[7] = v[3] - v[4] - v[5]
    # item 12 (residual) = 8 − (9+10+11)
    if v[8] is not None and None not in (v[9], v[10], v[11]):
        v[12] = v[8] - (v[9] + v[10] + v[11])
    elif v[8] is not None and v[9] is not None and v[10] is not None and v[11] is None:
        v[11] = 0.0
        v[12] = v[8] - v[9] - v[10]
    # item 2 (생명장기 손익) = 3 + 8
    if v[2] is None:
        v[2] = s(3, 8)
    # ...or, when a handler exposes only a single 장기 net (장기손익 incl 재보험; e.g. 현대
    # has no clean rev/cost split), use it directly and leave item3/7/8 None.
    if v[2] is None:
        jnet = (t2 or {}).get("_jang_net")
        if jnet is not None:
            v[2] = jnet

    # item 18 = 17 − 19
    if v[17] is not None and v[19] is not None:
        v[18] = v[17] - v[19]
    # item 20 = 1 + 17 (if not from statement)
    if v[20] is None:
        v[20] = s(1, 17)
    # item 22 = 20 + 21
    if v[22] is None:
        v[22] = s(20, 21)
    # item 23 (법인세) = 22 − 24 when BOTH the statement's 세전이익 and 당기순이익 are present.
    # DART statements vary in how 법인세비용 is signed (positive amount vs parenthesised
    # deduction), and a few mis-parse the line entirely (≈0 or a footnote number).  Since
    # 법인세 ≡ 세전이익 − 당기순이익 by definition, deriving it as the residual makes the
    # bottom of every statement close and fixes those sign/garbage picks.  Gold-consistent
    # statements are unaffected (their parsed 법인세 already equals 22 − 24).
    if v[22] is not None and v[24] is not None:
        v[23] = round(v[22] - v[24], 6)
    # item 24 = 22 − 23 (only when 당기순이익 was NOT on the statement)
    if v[24] is None and v[22] is not None and v[23] is not None:
        v[24] = v[22] - v[23]
    # item 21 = 22 − 20
    if v[21] is None and v[22] is not None and v[20] is not None:
        v[21] = v[22] - v[20]

    # --- Tier-2 reconciliation gate ---------------------------------------- #
    # The issued+reinsurance breakdown must reconcile to the statement 보험손익:
    #   item1 ≈ Σ(LOB) [+ item15 − item16]   where Σ(LOB) = item2 (+13+14 for 손보).
    # When it misses by >25% the decomposition is untrustworthy — a quarterly note that
    # doesn't match the (also-quarterly) statement, a foreign-insurer LOB layout, or a
    # first-IFRS17-year (FY2023) table form.  Publishing it would be worse than leaving it
    # blank, so SUPPRESS the breakdown (items 2-14) and keep Tier-1 (1, 15-24).  The
    # suppressed cells are exactly the hand-built-gold candidates; `_reconciled` flags the
    # rest.  (Convention-agnostic: passes if EITHER the bare or the 15/16-adjusted form
    # closes — see scripts/_pl_selfcheck.py.)
    v["_reconciled"] = None
    if v[1] is not None and v[2] is not None:
        # 코리안리 등 재보험사: an extra GMM LOB (장기재보험 item2-1) sits outside the standard
        # 2/13/14 slots — include it in the reconciliation via the handler's _extra_lob.
        extra_lob = (t2 or {}).get("_extra_lob") or 0
        lob = v[2] + (0 if is_life else (v.get(13) or 0) + (v.get(14) or 0)) + extra_lob
        bare = abs(lob - v[1])
        adj = abs(lob + (v.get(15) or 0) - (v.get(16) or 0) - v[1])
        # pre-FY2025 손보 (한화손해 OLD, 흥국 OLD) reconcile as item1 = ΣLOB + item16 with item16
        # stored negative.  adj2 covers that sign convention; inside min() it can only let MORE
        # (legitimately +item16-reconciling) breakdowns pass — currently-passing companies unchanged.
        adj2 = abs(lob + (v.get(15) or 0) + (v.get(16) or 0) - v[1])
        if min(bare, adj, adj2) <= 0.25 * abs(v[1]) + 2:
            v["_reconciled"] = True
        else:
            v["_reconciled"] = False
            for k in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
                v[k] = 0.0 if (is_life and k in (13, 14)) else None

    # Un-rescaled unit error guard: no real insurer's quarterly Tier-2 component reaches 1e7
    # 백만원 (10조; the largest real ≈ 1.5M).  미래에셋's quarterly rollforward is in 원 and has
    # no _jang_rev for the unit-reconciler, so it can surface ~1e12 garbage that escapes the RC
    # gate (item2 None → gate skipped).  Null the whole orphan breakdown rather than ship it.
    if any(v[k] is not None and abs(v[k]) > 1e7 for k in (4, 5, 6, 9, 10, 11, 13, 14)):
        for j in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
            v[j] = 0.0 if (is_life and j in (13, 14)) else None
        v["_reconciled"] = False

    return v


# --------------------------------------------------------------------------- #
# Company universe + raw-dir resolution
# --------------------------------------------------------------------------- #
def load_universe():
    """code -> (name, 생손보여부) from kics_disclosure.json (first occurrence)."""
    rows = json.loads(DISCLOSURE.read_text(encoding="utf-8"))
    uni = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        code = r.get("원보험사코드")
        if code and code not in uni:
            uni[code] = (r.get("원수사명"), r.get("생손보여부"))
    return uni


def discover_filings():
    """Return {code: {quarter: [raw_dir, ...]}} discovered from data/dart/FY*/raw/KR*."""
    filings = {}
    for raw_base in glob.glob(RAW_FY_GLOB):
        q = _quarter_from_path(raw_base)
        if not q:
            continue
        for d in glob.glob(raw_base + "/KR*"):
            base = os.path.basename(d)
            m = re.match(r"(KR\d+)_", base)
            if not m:
                continue
            code = m.group(1)
            filings.setdefault(code, {}).setdefault(q, []).append(d)
    return filings


def _xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") \
        + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


def _reconcile_tier2_unit(t1, t2):
    """Cross-check the Tier-2 note unit against Tier-1.  A few notes are printed in 천원 or
    원 while the income statement is in 백만원 (e.g. 악사손해 — its Format-A LOB note is in
    천원), which inflates the breakdown ~1000×/1e6×.  The 장기 발행 보험수익 (_jang_rev) must
    be a SUB-portion of the statement's total 보험수익 (_is_rev), so a ratio of ~1e3/~1e6
    reveals the smaller unit.  Rescale every monetary Tier-2 value by the inferred factor.
    Per-company handlers already emit 백만원 (ratio ≈ 0.5-1.0 → factor 1.0, untouched)."""
    if not t2 or not t1:
        return t2
    jang = t2.get("_jang_rev")
    total = t1.get("_is_rev")
    if not jang or not total:
        return t2
    r = abs(jang) / abs(total)
    if 50 <= r < 5000:
        f = 1e-3
    elif 5e4 <= r < 5e6:
        f = 1e-6
    else:
        return t2
    return {k: (v * f if isinstance(v, (int, float)) else v) for k, v in t2.items()}


def parse_filing(dirs, is_life, code=None, name=None, quarter=None):
    """Parse all XMLs across the rcept dirs for one (company, quarter).
    name/quarter let a handler resolve the FS-API-preferred Tier-1 item1 (KB note pick)."""
    tables = []
    for d in dirs:
        for x in _xmls_in(d):
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception:
                pass
    if not tables:
        return None, None
    t1 = extract_tier1(tables, code=code)
    if is_life:
        # per-company handler first (component-decomposition / comprehensive notes);
        # fall back to the generic 계약유형별 LOB extractor (삼성생명/한화생명) if empty.
        handler = LIFE_HANDLERS.get(code)
        if handler is extract_tier2_life_comprehensive:
            t2 = handler(tables, code=code)
        else:
            t2 = handler(tables) if handler else {}
        if not t2 or all(t2.get(i) is None for i in (4, 5)):
            t2o = extract_tier2_life_old(tables)   # pre-2025.2Q 생보 OLD (한화생명 generic path)
            if t2o and t2o.get(4):
                t2 = {**(t2 or {}), **t2o}
            else:
                t2g = extract_tier2_life(tables)
                if t2g:
                    t2 = {**(t2 or {}), **t2g}
    else:
        # per-company handler first (KB/현대/한화/DB/NH/롯데/코리안리); for codes without a
        # dedicated handler keep the existing Format-A / Format-B fallback.
        handler = SONBO_HANDLERS.get(code)
        if handler is extract_tier2_kb:
            # KB note pick needs the SAME basis the RC gate uses: FS-API 별도 item1 (2024+),
            # else HTML 연결 item1 (FY2023, API status-013).  Mirror main()'s precedence.
            _api = _fs_tier1(name, quarter, code)
            _i1 = (_api or {}).get(1) if _api else (t1 or {}).get(1)
            t2 = handler(tables, item1=_i1)
        else:
            t2 = handler(tables) if handler else {}
        if not t2 or all(t2.get(i) is None for i in (4, 5, 6)):
            # Samsung-style component note first (precise, header-LOB-aware, RC-gated downstream),
            # then the older Format-A / Format-B fallbacks.
            t2c = extract_tier2_sonbo_component(tables)
            if t2c and any(t2c.get(i) is not None for i in (4, 5, 6)):
                t2 = {**(t2 or {}), **t2c}
            else:
                t2o = extract_tier2_old(tables)      # pre-2025.2Q 구분-rows (삼성·현대·DB)
                if t2o and any(t2o.get(i) is not None for i in (4, 5, 6)):
                    t2 = {**(t2 or {}), **t2o}
                else:
                    t2a = extract_tier2_sonbo(tables)    # Format-A (장기/자동차/일반 columns)
                    if t2a and any(t2a.get(i) is not None for i in (4, 5, 6)):
                        t2 = {**(t2 or {}), **t2a}
                    else:
                        t2b = extract_tier2_sonbo_structured(tables)  # Format-B (메리츠 상세내역)
                        if t2b:
                            t2 = {**(t2 or {}), **t2b}
    # _reconcile_tier2_unit corrects 천원/원 LOB notes (e.g. 악사 Format-A; 미래에셋 원-unit
    # rollforward) by comparing _jang_rev to the HTML _is_rev.  Skip it for 손보 codes with a
    # dedicated handler — those already emit 백만원, and the HTML _is_rev (now only a Tier-1
    # FALLBACK since Tier-1 moved to the FS-API) can be mis-parsed: 한화손해 2025.2Q's HTML
    # 보험수익 came out ~1000× small, giving ratio≈670 → a spurious 1e-3 rescale that shrank a
    # correct breakdown and tripped the RC gate (suppressing all of 한화's quarterly Tier-2).
    if code not in SONBO_HANDLERS:
        t2 = _reconcile_tier2_unit(t1, t2)
    return t1, (t2 or None)


def _fs_tier1(name, quarter, code):
    """Tier-1 from the DART standardized FS API (owner directive 2026-06-04).  Robust,
    gold-validated; replaces HTML income-statement parsing.  None on any failure → caller
    falls back to the (archived) HTML extractor so coverage never regresses."""
    try:
        from scripts.fetch_dart_fs import tier1_for
        return tier1_for(name, quarter, code)
    except Exception:
        return None


# Owner-provided cells for (company, quarter) the standard pipeline cannot produce — the DART
# FS-API returns NO data (status 013, FY2023 first-IFRS17 half-years) AND the note layout is a
# non-recurring early format whose totals don't map to the schema (e.g. 동양 2023.2Q: note
# 총보험서비스결과 88,324 / 기타보험비용 40,444 ≠ schema item1 116,208 / item16 12,560).  Values
# taken verbatim from the owner's hand-built gold (Tier-1 포괄손익계산서 + note 분해).  Documented
# exception — NOT a learned rule.  9/10/11/12 omitted = 재보 components not disclosed.
_GOLD_CELL_OVERRIDE = {
    # 현대해상 KR0009 2023.3Q/4Q: 생명장기 손익(item2, parent total)이 OLD form에서
    # null이던 것을 IR factsheet 교차검증값으로 채움 (validation 06-13 extraction_audit:
    # IR↔DART CSM·RA 0.0까지 정확 일치). 원수/재보 split(3/8)은 NEEDS_DART 재파싱(별건).
    ("KR0009", "2023.3Q"): {2: 476139.3},
    ("KR0009", "2023.4Q"): {2: 248827.5},
    ("KR0087", "2023.2Q"): {
        1: 116208.0, 2: 128768.0, 3: 130035.0, 4: 127412.0, 5: 22438.0, 6: 5817.0,
        7: -25632.0, 8: -1267.0, 13: 0.0, 14: 0.0, 15: 0.0, 16: 12560.0,
        17: 133169.0, 18: 699587.0, 19: -566418.0, 20: 249377.0, 21: 3072.0,
        22: 252449.0, 23: 52199.0, 24: 200250.0,
    },
    # ---- 2026-06-11 audit-verified cells (raw 직접판독; per-cell 근거 changelog (o)) ----
    # KDB 2023.2Q: FY2023 반기 OLD 영업수익/비용 양식 — FS-API status-013 + HTML 라벨 미매칭.
    # 15/17/18은 OLD 양식 스키마 매핑 모호(audit 경고) → 보류, owner gold 확인 후 추가.
    ("KR0072", "2023.2Q"): {
        1: 22665.0, 2: 22665.0, 3: 13292.0, 7: -7865.0, 8: 9373.0, 12: 3984.0,
        16: 5349.0, 19: -303458.0, 20: 68658.0, 21: -10908.0, 22: 57750.0,
        23: -0.2, 24: 57750.0,
    },
    # KDB 2025.2Q+: life_old 선점이 NEW 주석32-(2)를 가려 9/10 미산출; item11은 레그혼합
    # 오류값(25.4Q 공표 39,470 vs 노트 실제 42,611−예상 35,399=7,212 — raw 재검증 완료).
    ("KR0072", "2025.2Q"): {9: -579.0, 10: -561.0, 11: 5305.0, 12: -11443.0},
    ("KR0072", "2025.3Q"): {9: -498.0, 10: -615.0, 11: 5925.0, 12: -30942.0},
    ("KR0072", "2025.4Q"): {9: -19.0, 10: -531.0, 11: 7212.0, 12: -22559.0},
    ("KR0072", "2026.1Q"): {9: -477.0, 10: -131.0, 11: -132.0, 12: -1345.0},
    # 라이나 (비상장·감사보고서만): 'Ⅰ−Ⅱ' 도출형 IS 미인식 + 주석23 천원단위 1e7 가드
    # suppression. 7/12는 잔차(3−4−5−6 / 8−9−10−11).
    ("KR0074", "2024.4Q"): {
        1: 310451.0, 2: 328886.0, 3: 259410.0, 4: 397347.0, 5: 67191.0, 6: 4785.0,
        7: -209913.0, 8: 69476.0, 9: -11684.0, 10: -6524.0, 11: 18162.0, 12: 69522.0,
        15: 0.0, 16: 18435.0, 17: 296868.0, 18: 243138.0, 19: 53730.0,
        20: 607319.0, 21: -10687.0, 22: 596632.0, 23: 132348.0, 24: 464284.0,
    },
    ("KR0074", "2025.4Q"): {
        1: 179565.0, 2: 198093.0, 3: 166731.0, 4: 331435.0, 5: 53666.0, 6: -31834.0,
        7: -186536.0, 8: 31363.0, 9: -29268.0, 10: -656.0, 11: 29053.0, 12: 32234.0,
        15: 0.0, 16: 18529.0, 17: 270640.0, 18: 208578.0, 19: 62062.0,
        20: 450205.0, 21: -52.0, 22: 450153.0, 23: 93711.0, 24: 356442.0,
    },
    # 미래에셋 2023.1Q/2Q: 공표 2023.3Q+ 시리즈와 동일 별도기준(연속성 검증: item4
    # 52,014→102,398→148,365; item24 134,764→159,231). 2Q의 4/5/9/10은 기존 추출 정상 → 미포함.
    ("KR0079", "2023.1Q"): {
        1: 43699.0, 2: 61472.0, 3: 60942.0, 4: 52014.0, 5: 12029.0, 6: 0.0,
        7: -3101.0, 8: 531.0, 9: -249.0, 10: -55.0, 11: 0.0, 12: 835.0,
        15: 0.0, 16: 17774.0, 17: 93769.0, 18: 911261.0, 19: -817492.0,
        20: 137468.0, 21: -1673.0, 22: 135794.0, 23: 35059.0, 24: 100735.0,
    },
    ("KR0079", "2023.2Q"): {
        1: 84266.0, 2: 117084.0, 3: 119649.0, 6: 0.0, 7: -6357.0, 8: -2565.0,
        11: 0.0, 12: -1373.0, 15: 0.0, 16: 32818.0, 17: 97519.0, 18: 1566094.0,
        19: -1468575.0, 20: 181785.0, 21: -2682.0, 22: 179103.0, 23: 44339.0,
        24: 134764.0,
    },
    # 동양 부분보정: 2024.4Q item6은 기존 17,476이 기타보험서비스비용 leg 누락 → 20,691.
    ("KR0087", "2023.1Q"): {2: 67396.0, 3: 67661.0, 7: -6699.0},
    ("KR0087", "2024.4Q"): {5: 47227.0, 6: 20691.0, 7: -25222.0},
    ("KR0087", "2025.2Q"): {5: 22144.0, 6: -10877.0, 7: -60077.0, 11: 7026.0, 12: 4182.0},
    ("KR0087", "2025.3Q"): {6: -31913.0, 7: -84162.0},
    # 메트라이프 (비상장·감사보고서만): Q4 전항목 null — audit 전셀 재구성(17=18+19 항등식,
    # 18=주석 투자손익 소계 대사).
    # item1 = item2 − item16 (보험영업손익 컨벤션 — 동양/라이나/미래에셋과 동일; validator
    # 영업이익 eq FAIL +12,086/+12,897 해소. 재무제표 Ⅰ.보험영업손익 143,894와 일치).
    ("KR0095", "2024.4Q"): {
        1: 143894.0, 2: 155980.0, 3: 164512.0, 4: 191235.0, 5: 26752.0, 6: 4797.0,
        7: -58272.0, 8: -8532.0, 9: -6159.0, 10: -278.0, 11: -2610.0, 12: 515.0,
        15: 0.0, 16: 12086.0, 17: 3044.0, 18: 1861907.0, 19: -1858863.0,
        20: 146938.0, 21: 181.0, 22: 147119.0, 23: 17287.0, 24: 129832.0,
    },
    ("KR0095", "2025.4Q"): {
        1: 214992.0, 2: 227890.0, 3: 236247.0, 4: 210554.0, 5: 33229.0, 6: 6744.0,
        7: -14280.0, 8: -8357.0, 9: -6668.0, 10: -546.0, 11: -1152.0, 12: 9.0,
        15: 0.0, 16: 12898.0, 17: -23310.0, 18: 3134978.0, 19: -3158288.0,
        20: 191683.0, 21: -98.0, 22: 191584.0, 23: 56455.0, 24: 135129.0,
    },
}


def main():
    uni = load_universe()
    filings = discover_filings()
    rows = []
    coverage = []  # (code, name, quarter, status, missing_items)
    t1_src = {"api": 0, "html": 0}

    for code in sorted(filings):
        name, life_flag = uni.get(code, (None, None))
        if name is None:
            # unknown code (not in disclosure) — derive name from dir, skip 생손보
            name = code
        is_life = (life_flag == "생명보험")
        for q in sorted(filings[code], key=_quarter_sort_key):
            dirs = filings[code][q]
            has_xml = any(_xmls_in(d) for d in dirs)
            t1_html, t2 = parse_filing(dirs, is_life, code=code, name=name, quarter=q)
            t1_api = _fs_tier1(name, q, code)          # Tier-1 from DART FS API (primary)
            t1 = t1_api if t1_api else t1_html         # HTML extractor = fallback only
            t1_src["api" if t1_api else "html"] += 1 if t1 is not None else 0
            if t1 is None and t2 is None:
                # distinguish a download/extraction gap (only document.zip on disk) from a
                # genuine statement-format mismatch (XML present but no 포괄손익계산서 matched)
                st = "no_income_statement" if has_xml else "raw_not_extracted"
                coverage.append((code, name, q, st, list(range(1, 25)), "none"))
                continue
            v = assemble(t1, t2, is_life)
            ov = _GOLD_CELL_OVERRIDE.get((code, q))   # FS-API-absent owner-provided cell
            if ov:
                for _k, _val in ov.items():
                    v[_k] = _val
                v["_reconciled"] = True
            for n in range(1, 25):
                rows.append({
                    "원보험사코드": code, "원수사명": name, "티커": None,
                    "생손보여부": life_flag, "항목번호": n, "항목명": ITEM_NAMES[n],
                    "공시분기": q,
                    "값": (round(v[n], 6) if isinstance(v[n], float) else v[n]),
                })
            # extra sub-items for reinsurers with a parallel LOB schema (코리안리 장기재보험
            # 2-1…12-1).  Emitted only when the breakdown reconciled (RC gate not tripped).
            if v.get("_reconciled") is not False:
                for ex in (v.get("_extra_items") or []):
                    val = ex["값"]
                    rows.append({
                        "원보험사코드": code, "원수사명": name, "티커": None,
                        "생손보여부": life_flag, "항목번호": ex["항목번호"],
                        "항목명": ex["항목명"], "공시분기": q,
                        "값": (round(val, 6) if isinstance(val, float) else val),
                    })
            missing = [n for n in range(1, 25) if v[n] is None]
            if not missing:
                status = "ok"
            elif t1 is not None:
                status = "partial"
            else:
                status = "no_income_statement"
            # Tier-2 reconciliation outcome (gate result): ok / suppressed / partial / none
            rec = v.get("_reconciled")
            t2_status = ("suppressed" if rec is False
                         else "ok" if rec is True
                         else "none" if not t2 else "partial")
            coverage.append((code, name, q, status, missing, t2_status))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} rows, "
          f"{len({(r['원보험사코드'], r['공시분기']) for r in rows})} company-quarters)")
    print(f"Tier-1 source: FS-API={t1_src['api']}  HTML-fallback={t1_src['html']}")

    # stash coverage for the doc-writer / verifier
    cov_path = Path("data/_derived/pl_breakdown_coverage.json")
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    cov_path.write_text(json.dumps(
        [{"code": c, "name": n, "quarter": q, "status": s, "missing": m, "tier2": t2s}
         for c, n, q, s, m, t2s in coverage], ensure_ascii=False, indent=1), encoding="utf-8")
    return rows, coverage


if __name__ == "__main__":
    main()
