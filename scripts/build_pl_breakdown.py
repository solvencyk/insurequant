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
from scripts.pl_breakdown.common import (  # noqa: E402
    _quarter_from_path,
    _quarter_sort_key,
)
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402
from scripts.pl_breakdown.tier2 import (  # noqa: E402
    extract_tier2_life,
    extract_tier2_sonbo,
    extract_tier2_sonbo_structured,
)
from scripts.pl_breakdown.companies import (  # noqa: E402
    LIFE_HANDLERS,
    SONBO_HANDLERS,
    extract_tier2_kb,
    extract_tier2_life_comprehensive,
    extract_tier2_life_old,
    extract_tier2_old,
    extract_tier2_sonbo_component,
)

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
    # 하나생명 KR0097 2025.4Q (비상장·감사보고서만): 투자를 단일 "투자손익" 행이 아니라
    # II.투자수익 / III.투자비용 2개 번호행으로 공시 → L275 단일 L("투자손익") 룩업이 미스해
    # item17/18만 null로 떨어짐(나머지 셀은 정상). round3 검증(20260616, 별도 00760, 단위 원):
    # II.투자수익 669,653,289,200 − III.투자비용 351,762,230,334 = 투자이익 317,891.06백만;
    # item17 = 18 + 19(순보험금융손익 −317,069.65) = 821.41; 영업이익 = item1(33,699.87) +
    # item17 = 34,521.27 = 재무제표 Ⅴ.영업이익 일치(gap 0). (owner P3 disposition = parse_miss)
    ("KR0097", "2025.4Q"): {18: 317891.058866, 17: 821.407415},
    # IBK연금보험 KR1011 (비상장·감사보고서만, 단위 천원): tier2 주석 [166][167]에서 직접 계산.
    # item3 = 보험수익합계 − 보험서비스비용합계; item4=CSM상각, item5=RA변동,
    # item6=예상발생 − 실제발생(예실차), item7=잔차(손실부담계약 등).
    # item8-12=0(재보험없음), item13-14=0(자동차/일반없음). closure OK all 3Y.
    ("KR1011", "2023.4Q"): {
        2: 24523.813, 3: 24523.813, 4: 26151.758, 5: 3078.527, 6: -6745.186, 7: 2038.714,
        8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0,
    },
    ("KR1011", "2024.4Q"): {
        2: 27402.597, 3: 27402.597, 4: 35111.633, 5: 2162.61, 6: -5855.725, 7: -4015.921,
        8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0,
    },
    ("KR1011", "2025.4Q"): {
        2: 50472.844, 3: 50472.844, 4: 44027.788, 5: 2878.019, 6: 2508.072, 7: 1058.965,
        8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0,
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
