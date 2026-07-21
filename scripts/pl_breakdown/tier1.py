"""Tier-1: 포괄손익계산서 (income statement) extraction."""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
from .common import _label, _norm, _row_nums


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
NI_LABELS = ("당기순이익", "반기순이익", "분기순이익", "계속영업", "당기순손익")


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
    has_op = "영업이익" in labs or "영업손익" in labs
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
                                    "반기순이익", "분기순이익", "당기순손익",
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
        op = L("영업이익", "영업손익", exclude=("영업외",))
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
