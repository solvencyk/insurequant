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
    _iter_tables_by_basis,
    _quarter_from_path,
    _quarter_sort_key,
    _tag_basis,
)
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402
from scripts.pl_breakdown.tier2 import (  # noqa: E402
    extract_tier2_abl,
    extract_tier2_life,
    extract_tier2_sonbo,
    extract_tier2_sonbo_structured,
)
from scripts.pl_breakdown.companies import (  # noqa: E402
    LIFE_HANDLERS,
    SONBO_HANDLERS,
    extract_tier2_aia,
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
    # 25-31: 총포괄손익 연장 (owner 티켓 inbox/parser/20260828T0113Z). sj_div=='CIS' 기반,
    # fetch_dart_fs.py::ACCT_OCI/_parse()가 채운다 — Tier-1(FS-API)에서만 오고 HTML fallback·
    # Tier-2 LOB 분해는 관여하지 않는다.
    25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)",
    28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
    30: "재보험금융손익(OCI)", 31: "총포괄손익",
    # 32: 기타 포괄손익(미분류) — catch-all residual (owner 티켓 inbox/parser/20260828T1600Z).
    # 이름은 IFRS17.html의 기존 클라이언트측 잔차 막대 라벨과 동일(plOciResidual, "기타 포괄
    # 손익(미분류)") — 일부러 맞췄다: item32는 그 잔차를 provenance 있는 서버측 필드로 정식화한
    # 것이다. 주의: norm()(공백 제거, validate_master_tables.py)이 "기타포괄손익(미분류)"로
    # 정규화되는데 item25("기타포괄손익")와 다른 문자열이라 충돌 없음 — "기타 포괄손익"(공백만
    # 다르고 접미사 없음)을 썼다면 item25와 정규화 후 동일 키가 되어 PL_EQS 등이 깨졌을 것.
    # fetch_dart_fs.py::_oci32_from_rows가 채운다 — 다른 25-31과 동일하게 FS-API 전용.
    32: "기타 포괄손익(미분류)",
}
OCI_ITEMS = (25, 26, 27, 28, 29, 30, 31, 32)


# --------------------------------------------------------------------------- #
# Assembly of the 24-item vector
# --------------------------------------------------------------------------- #
# Items whose "not extracted" is turned into a disclosed 0 by the owner rule of 2026-06-08
# ("미공시 시 0표시"): item6 원수 예실차 and item11 재보험 예실차.  See ZERO_FILL note below.
ZERO_FILL_ITEMS = frozenset({6, 11})


def assemble(t1, t2, is_life, zero_fill_ok=None):
    """Merge tier1 + tier2 and derive the identity items. Returns {item_no: value|None}.

    `zero_fill_ok` -- item numbers for which the owner's 2026-06-08 "미공시 시 0표시" rule may
    fire.  `None` (default) means "all of them", i.e. the pre-2026-08-30 behaviour; callers
    that know the company's whole time series pass the narrowed set (see main()).

    WHY this parameter exists (owner decision 2026-08-30, option 1 of the three proposed in
    inbox/parser/20260830T0000Z): the 0-fill branches below cannot tell "this company never
    discloses this item" from "this one quarter's extraction failed" -- both arrive as
    `v[n] is None`.  A single row proves they are different: 미래에셋생명 2025.4Q had item11
    correctly 0 (no extraction is wired for it at all) and item6 wrongly 0 (the 예실차 note's
    only 별도-basis rendering in that filing's raw XML is corrupted) at the same time.  A lone
    0.0 wedged into a series of real values reads as a disclosed fact and is not.  That case
    class showed up four times, and `PL_YTD_COLLAPSE_TO_ZERO` caught it only after the fact.
    """
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
    elif v[3] is not None and v[4] is not None and v[5] is not None and v[6] is None \
            and (zero_fill_ok is None or 6 in zero_fill_ok):
        v[6] = 0.0
        v[7] = v[3] - v[4] - v[5]
    # RESOLVED (2026-08-30, inbox/parser/20260830T0000Z; was a KNOWN GAP as of 2026-08-29,
    # inbox/parser/20260829T2330Z follow-up): this branch ALSO fires for 미래에셋생명(KR0079)
    # 2025.4Q, same as 농협/교보/동양, but for a different reason -- and the fix is a
    # `_GOLD_CELL_OVERRIDE` entry below, not a change to this elif.  `_ma_yesilcha_direct`'s
    # dual population-check gate self-aborts that quarter, but the root cause is one level
    # deeper than "picks the wrong candidate table": `_ma_find_product_table` now (as of this
    # fix) recognizes the tie is UNRESOLVABLE and returns None directly, because the 예실차
    # note's raw DART XML carries an intact 연결(CFS)-basis rendering AND a row-value-shifted
    # (corrupted) 별도(OFS)-basis rendering, and `_prefer_ofs` -- correctly, per this
    # project's 별도-only convention -- keeps only the corrupted one.  There is no clean OFS
    # table to prefer for this quarter; see that function's docstring for the raw-XML proof.
    # So item6 still lands here as None -> this elif still turns it into 0.0, EXACTLY like
    # 농협/교보/동양.  The difference from those 3 is that KR0079's OWN pipeline resolves
    # item6 to a real nonzero number in 2025.2Q/2025.3Q/2026.1Q/2026.2Q (same function,
    # confirmed unaffected by the tie-break fix via a 14-quarter regression sweep), so a lone
    # 0.0 wedged mid-series reads as dropped data, not a disclosed fact -- exactly what
    # validate_data_contract.py's PL_YTD_COLLAPSE_TO_ZERO flagged on 2026-08-29 (edb6b77).
    # The `_GOLD_CELL_OVERRIDE` entry for ("KR0079", "2025.4Q") below forces v[6] back to
    # None inside the deterministic build so a fresh rebuild reproduces the committed cell
    # instead of drifting back to 0.0 -- see that entry for the full explanation, and this
    # ticket's `assemble()`-rule review for why the elif itself still can't tell "genuinely
    # never disclosed" apart from "this one quarter's extraction failed" without one.
    # item 12 (residual) = 8 − (9+10+11)
    if v[8] is not None and None not in (v[9], v[10], v[11]):
        v[12] = v[8] - (v[9] + v[10] + v[11])
    elif v[8] is not None and v[9] is not None and v[10] is not None and v[11] is None \
            and (zero_fill_ok is None or 11 in zero_fill_ok):
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
                tables.extend(_tag_basis(
                    list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
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
        elif handler is extract_tier2_aia:
            # AIA has no table at all for this data (prose-only note) -- needs the raw
            # rcept dirs to re-read the XML text directly, not the parsed `tables`.
            t2 = handler(tables, dirs=dirs)
        elif handler is extract_tier2_abl:
            # note26 예실차 (item6) needs `quarter` to suppress ONE known-anomalous cell
            # (2024.4Q) whose note37 MD&A prose contradicts its own note26 table -- see
            # _ABL_ITEM6_SUPPRESS_QUARTERS in tier2.py.
            t2 = handler(tables, quarter=quarter)
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
    # KDB 2023.1Q: 같은 원인(FS-API 013 + IFRS17 최초도입분기 구양식, tier1 '보험손익' 행
    # 없음) — 2023.2Q 와 동일 메커니즘. rcept 20230515002450, note36 raw 직접판독
    # (inbox/parser/20260901T1630Z, 2026-09-12 처리). 3/4/5/8/13/14/16/19/20/21/22/23/24는
    # 원문 라인 직접값; 2/15/1/17/18은 2023.3Q/4Q 마스터가 이미 쓰는 항등식
    # (2=3+8, 15=0, 1=2+15-16, 17=20-1, 18=17-19)으로 파생. 6/7/9-12(재보험 분해·예실차)는
    # note36에 실제발생/재보험 분해가 없어 미기입 — 억지 추정 금지.
    ("KR0072", "2023.1Q"): {
        1: 7111.35, 2: 9457.51, 3: 8746.10, 4: 11125.0, 5: 3962.0, 8: 711.41,
        13: 0.0, 14: 0.0, 15: 0.0, 16: 2346.17, 17: 35986.75, 18: 200709.54,
        19: -164722.79, 20: 43098.09, 21: -5425.70, 22: 37672.40, 23: -0.209323,
        24: 37672.61,
    },
    # KDB 2025.2Q+: life_old 선점이 NEW 주석32-(2)를 가려 9/10 미산출; item11은 레그혼합
    # 오류값(25.4Q 공표 39,470 vs 노트 실제 42,611−예상 35,399=7,212 — raw 재검증 완료).
    ("KR0072", "2025.2Q"): {9: -579.0, 10: -561.0, 11: 5305.0, 12: -11443.0},
    ("KR0072", "2025.3Q"): {9: -498.0, 10: -615.0, 11: 5925.0, 12: -30942.0},
    ("KR0072", "2025.4Q"): {9: -19.0, 10: -531.0, 11: 7212.0, 12: -22559.0},
    ("KR0072", "2026.1Q"): {9: -477.0, 10: -131.0, 11: -132.0, 12: -1345.0},
    # 라이나 (비상장·감사보고서만): 'Ⅰ−Ⅱ' 도출형 IS 미인식 + 주석23 천원단위 1e7 가드
    # suppression. 7/12는 잔차(3−4−5−6 / 8−9−10−11).
    # 2023.4Q 신설(2026-09-22, owner 지시). 같은 회사 2024.4Q·2025.4Q 는 진작 override 로
    # 채워져 있었는데 2023.4Q 만 income_statement 블록이 통째 비어 있었다(provenance
    # source_id=DART · source_file=null · NO_PUBLISHED_VALUE_IN_BLOCK · published_items=0).
    # 원인은 같다 — FS-API 가 이 회사에 status 013(조회된 데이타 없음)을 돌려주고(전 연도 동일),
    # 'Ⅰ−Ⅱ' 도출형 IS 를 tier1 HTML 이 못 읽는다. 아무도 2023.4Q 만 손으로 안 넣었을 뿐이다.
    #
    # **기준 주의**: FY2023 은 FY2024 보고서에서 소급재작성됐다. 자기 보고서(제21기) 당기순이익
    # 463,997 vs FY2024 보고서 전기 비교컬럼 511,309 — 차이 47,312. 여기 값은 **후자(재작성)**다.
    # 이미 마스터에 있던 item4(443,127.76)·item9(-7,365.047)가 그 기준으로 들어가 있어
    # (data/_gold/user_pl_cells.json, inbox/parser/20260815T1400Z) 나머지를 같은 기준에 맞춘다.
    # 섞으면 item7/item12 잔차가 두 기준을 합산하게 된다.
    #
    # 근거: data/dart/FY2024_Q4/raw/KR0074_라이나생명보험_20250409002702/20250409002702_00760.xml
    #   포괄손익계산서 제21(전)기 + 주석23 전기 컬럼(단위 천원). 산식은 이 회사 2024.4Q·2025.4Q
    #   기존 override 로 역검증해 전부 재현됨:
    #     item5 = 주석23(1) 원수 '비금융위험에 대한 위험조정 변동분'      48,896,452
    #     item6 = 주석23(1) 예상발생 − 주석23(2) 실제발생  1,361,300,255−1,341,666,849 = 19,633,406
    #     item11 = 주석23(1) 출재 실제 − 주석23(2) 출재 예상  61,735,734−64,259,424 = -2,523,690
    #     item10 = 주석23(2) 출재 '위험조정 변동분' 인쇄부호 그대로 +1,120,058
    #              (2024.4Q -6,524 · 2025.4Q -656 이 둘 다 인쇄부호 그대로인 기존 관행)
    #     item7/item12 = 잔차(3−4−5−6 / 8−9−10−11)
    #   4·9 는 user_pl_cells.json 이 이미 upsert 하므로 여기 넣지 않는다(이중 소스 방지).
    ("KR0074", "2023.4Q"): {
        1: 404534.0, 2: 421600.0, 3: 431699.0, 5: 48896.0, 6: 19633.0,
        7: -79959.0, 8: -10098.0, 10: 1120.0, 11: -2524.0, 12: -1330.0,
        15: 0.0, 16: 17066.0, 17: 208810.0, 18: 145251.0, 19: 63559.0,
        20: 613344.0, 21: -220.0, 22: 613124.0, 23: 101815.0, 24: 511309.0,
    },
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
    # 신한이지손해보험 KR0051 2025.4Q (비상장·감사보고서만, FS-API 캐시 없음 -> HTML tier1
    # fallback): 포괄손익계산서 "(1)보험금융수익/(2)재보험금융수익/(1)보험금융비용/(2)재보험금융비용"
    # 행의 주석열이 복수참조("13, 24" / "14, 24")라 to_num()의 콤마+공백 제거로 "1324"/"1424"로
    # 뭉개짐 -> _drop_footnote()의 abs<=99 문턱을 피해 각 행 nums[0]으로 오채택됨. 수익/비용 행이
    # 같은 주석번호를 인용해 오채택값이 동일(1324 vs 1324, 1424 vs 1424)하므로 fin19=Σ(±)가 정확히
    # 0으로 상쇄되는 결정론적 버그(우연한 진짜 0 아님). raw 직접판독(2026-08-03, 00760.xml, 단위 원,
    # 제23(당)기 포괄손익계산서): 보험금융수익 36,452,010 + 재보험금융수익 3,149,145,386 −
    # 보험금융비용 5,458,298,595 − 재보험금융비용 14,105,522 = −2,286,806,721원 = −2286.806721
    # 백만원(item19). item17(투자손익, 정상추출) −3890.709458 − item19 = item18(투자이익)
    # −1603.902737. 근본원인은 scripts/pl_breakdown/common.py::to_num 콤마/공백 처리 +
    # tier1.py::_drop_footnote 문턱값 — "NN, MM" 형태 복수주석을 쓰는 다른 회사·분기 행도 영향
    # 가능한 범용 버그이므로 별도 조사 필요 (이 override는 KR0051 2025.4Q 셀 하나만 대증).
    ("KR0051", "2025.4Q"): {18: -1603.902737, 19: -2286.806721},
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
    # 디비생명보험 KR0082 2023.1Q/2Q (FS-API status-013 -> HTML tier1.extract_tier1()
    # fallback, DEPRECATED): the fallback's needle list for item1 is ("보험손익",
    # "보험서비스결과") — neither is a substring of THIS company's parent-line label
    # "보험서비스손익" (보험 + 서비스 + 손익, "서비스" sits between 보험 and 손익 so
    # "보험손익" does not match it), so _pick_line's single-pass row scan walks PAST the
    # parent row "I. 보험서비스손익" (no needle match) and stops at the very next row,
    # child sub-line "1. 보험손익" (DOES match), silently returning ~1.6~5.9십억원 too
    # little (raw '(2) 요약포괄손익계산서' 표: parent = child["1.보험손익"] +
    # child["2.재보험손익"]). Root cause is general (any HTML-fallback company/quarter
    # whose parent line reads "보험서비스손익" verbatim would trip the same needle gap) but
    # only these 2 cells currently hit it (KR0082 is the only code with both an FS-API gap
    # here AND this exact parent-label spelling); scoped per-cell rather than widening the
    # needle list, to avoid re-verifying every OTHER company's already-correct HTML-fallback
    # row-scan order (see the identical scoping precedent 3 entries up: KR0051 2025.4Q's
    # to_num/_drop_footnote root-cause note "범용 버그... 이 override는 셀 하나만 대증").
    # Both cells raw-confirmed 2026-08-25 (inbox/parser/20260825T1120Z iter2 + independent
    # re-verification, parser-ifrs17): identity item1 = item2(생명장기손익, Tier-2-sourced,
    # already correct) + item13 + item14 + item15 − item16 closes to EXACT 0.000 residual
    # both quarters once item1 uses the parent row (was: the mis-picked child row).
    # 2023.1Q: raw data/dart/FY2023_Q1/raw/KR0082_디비생명보험/20230515002932.xml
    #   '(2) 요약포괄손익계산서' 제35(당)기1분기: 'I. 보험서비스손익' 24,548,248,470원 (parent,
    #   correct item1) vs '1. 보험손익' 22,946,356,594원 (child, mis-picked old item1).
    #   item16(기타사업비용)=2,577.053702 already raw-confirmed in a prior pass (2026-08-25,
    #   user_pl_cells.json). Check: 27125.302172(item2)+0+0+0-2577.053702(item16) =
    #   24548.24847 = item1 below, diff 0.000.
    ("KR0082", "2023.1Q"): {1: 24548.24847},
    #   NOTE: item16 for this quarter is NOT in _GOLD_CELL_OVERRIDE — it was fixed earlier
    #   via the data/_gold/user_pl_cells.json overlay (applied downstream in
    #   build_root_masters.py::build_pl, after this module's pl_breakdown_master.json).
    # 2023.2Q: raw data/dart/FY2023_Q2/raw/KR0082_DB생명보험/20230814002739.xml '(2)
    #   요약포괄손익계산서' 제35(당)기반기 누적열: 'I. 보험서비스손익' 59,719,308,746원 (parent,
    #   correct item1) vs '1. 보험손익' 60,174,304,424원 (child, mis-picked old item1);
    #   '(3) 기타사업비' 5,850,450,986원 (item16, was missing entirely — same row-scan gap,
    #   needle "기타사업비용" doesn't match label "기타사업비" either, no trailing 용).
    #   Check: 65569.759732(item2)+0+0+0-5850.450986(item16 below) = 59719.308746 = item1
    #   below, diff 0.000.
    ("KR0082", "2023.2Q"): {1: 59719.308746, 16: 5850.450986},
    # 푸본현대생명 KR0083 2024.3Q: DART API 부호반전 결함(원문·캐시 대조는 51st/52nd pass,
    # orchestrator 티켓 inbox/_resolved/20260828T1200Z에서 확인·수정 완료). item27(보험계약
    # 금융손익 OCI)·28(위험회피 파생상품평가손익)·30(재보험금융손익 OCI) 세 값 다 |캐시|=|raw|
    # 이고 부호만 반대. 이 항목들은 24가 아니라 25-31(OCI 확장) 슬롯이라 이 override 루프의
    # 원래 사용례(item1-24 결측 보정)와 다르지만, 적용 메커니즘 자체(아래 main()의
    # `for _k, _val in ov.items(): v[_k] = _val`)는 항목번호에 무관하게 동작한다 — 검증
    # 완료(inbox/parser/20260828T1600Z, item32 신설 작업의 부산물). 이 셀은 이미
    # data/_gold/user_pl_cells.json(gold-overlay, build_root_masters.build_pl()이 최종
    # UPSERT)로 루트 PL_breakdown.json이 보호되고 있었으나, pl_breakdown_master.json
    # 자체는 그 보호 밖이었다(참고용 파일이라 "검사 대상 아님"으로 문서화돼 있었지만, 이
    # 빌더를 향후 raw가 복구된 뒤 통짜 재실행하면 이 3셀만 다시 틀린 부호로 채워짐 — 그 잠재
    # 불일치를 메우는 belt-and-suspenders). `v["_reconciled"] = True` 부작용 확인: 이 회사·
    # 분기는 items 2-14가 이미 전부 non-null(Tier-2 RC 게이트 기존 통과, 이 override 이전에도
    # True)이므로 이 대입은 상태를 바꾸지 않는 no-op — 순수 OCI 항목 3개만 영향받는다.
    ("KR0083", "2024.3Q"): {27: -265226.939791, 28: -5322.135208, 30: -536.616012},
    # 미래에셋(KR0079) 2025.4Q item6 은 여기 있던 `{6: None}` 박제로 버티고 있었는데,
    # owner 가 2026-08-30 에 option 1 을 승인하면서 구조적으로 해결돼 **지웠다** — 이제
    # assemble() 의 0-fill 억제가 그 칸을 스스로 None 으로 남긴다(이 회사는 2025.2Q·3Q·
    # 2026.1Q·2Q 에서 item6 을 실제로 뽑는다). 박제를 남겨두면 그 규칙이 나중에 회귀해도
    # 이 한 칸만은 계속 옳아 보여서 아무도 모른다 — 오늘 gold 오버레이 축에서 확인한 바로
    # 그 false-green 형태다. 근거·raw 증거는 inbox/parser/20260830T0000Z 참조.
    # 교보라이프플래닛(KR1010) 2023.4Q: FS-API 013, tier1/tier2 매칭기가 아무 표도 못 찾음.
    # 연결본(20240328001012_00761) 채택 -- 기존 마스터 2024.4Q item24(-26035.169735)가 별도
    # (-25624.45)가 아니라 연결본 값과 일치해 시계열 basis 일관성상 연결을 택함. item1/2 는
    # 포괄손익계산서 Ⅲ.영업손실-item17(top-down), item3~12 는 주석18-4/18-5/18-9/18-10
    # 측정요소별 변동내역(bottom-up, CSM_waterfall item5 -44.1억 <-> item4 44.06억 억원단위
    # 교차확인). item25-31 OCI는 정책상 FS-API CIS 전용이라 미기입.
    # (inbox/parser/20260901T1630Z, 2026-09-12 parser/ifrs17)
    #
    # 2026-09-12 후속(같은 티켓 Q2) -- item2(장기손익=3+8)와 item16(기타사업비용)의 근본원인을
    # raw 로 규명해 정정. 이전 값은 item2=item1(-19236.643649, "원인 미규명"으로 병기됐던
    # 임시값)·item16=1933.610508("3.기타사업비용"만) 이었다. 원인: 연결 포괄손익계산서
    # (data/dart/FY2023_Q4/raw/KR1010_.../20240328001012_00761.xml, table '연결포괄손익계산서')
    # 의 Ⅱ.영업비용 은 7개 하위행인데 그중 "7.기타영업비용"(4,691,303,769원=4691.303769백만원)
    # 이 "3.기타사업비용"(1,933,610,508원) 과 별개 행으로 존재 -- 이 회사는 2024/2025.4Q 와
    # 통계서 레이아웃이 달라(그 두 해는 "1.보험영업수익/2.보험서비스비용" 2행 구조로 기타비용이
    # 전부 한 줄 안에 있음, data/_gold/pl_bridge_baseline.json `_round_20260826b` 참조) 별도
    # 하위행을 놓치고 있었다. item16 을 3.기타사업비용+7.기타영업비용=6624.914277(원 단위까지
    # 합산 확인)로 고치면 item1(=item20-item17, top-down, 불변) = item2(=item3+item8, canonical
    # 공식) + item15 - item16 이 **잔차 0.000000 으로 정확히 닫힌다**(재현:
    # scripts/_probes/probe_20260912_kr1010_2023q4_bridge_verify.py). item2 도 그 canonical
    # 공식(=3+8)으로 정정 -- KR0008/KR0032 등 이 항등식이 정확히 닫히는 다른 회사들과 동일
    # 관례가 된다. item7/12는 여전히 3-12 부분계 안에서만 플러그로 역산(3=4+5+6+7,
    # 8=9+10+11+12, item16 변경과 무관, 둘 다 닫힘 유지). `data/_gold/pl_bridge_baseline.json`
    # 의 "교보라이프플래닛생명보험|2023.4Q|생명장기손익 = 원수손익+재보험손익" known-gap 등재는
    # 이 정정으로 항등식이 자연히 닫혀 삭제한다.
    #
    # 참고(정정 대상 아님): 2024.4Q 도 마스터 item2=item1(-26015.543184) 이지만, 이건 owner
    # xlsx fill(data/_gold/user_pl_cells.json, review-loop 2026-06-19/20)이고 그 해 필링의
    # "Ⅰ.보험손익" 원문 헤드라인 자체가 item3+item8-item16(기존 값, 하위행 누락 없음) 과 원
    # 단위까지 일치한다고 validation 이 별도로 raw 확인했다(pl_bridge_baseline.json
    # `_round_20260826b`, 2026-08-26) -- 그 해는 "기타사업비용"이 보험손익 라인 밖이 아니라
    # 안에서 원수·재보험과 나란한 세 번째 다리라 item1=item2 가 그 해의 진짜 구조다. 서로 다른
    # 필링 연도의 서로 다른 표 레이아웃이라 같은 패턴이 아니므로 owner 셀은 손대지 않는다.
    ("KR1010", "2023.4Q"): {
        1: -19236.643649, 2: -14538.659979, 3: -15897.504305, 4: 4406.389869,
        5: 968.792670, 6: -5330.868887, 7: -15941.817957, 8: 1358.844326,
        9: 667.916775, 10: 380.844373, 11: 395.662716, 12: -85.579538,
        13: 0.0, 14: 0.0, 15: 1926.930607, 16: 6624.914277, 17: -2857.722895,
        18: 18360.523970, 19: -21218.246865, 20: -22094.366544, 21: -162.071424,
        22: -22256.437968, 23: -219.962159, 24: -22036.475809,
    },
    # 롯데손해(KR0003) 2023.1Q: IFRS17 최초도입분기, "4.재무제표"~"5.주석" 사이가 원문 자체
    # 공백(rcept 20230515002687 L4816-5242 확인, FS-API 013). "1.요약재무정보 > 나.요약
    # 손익계산서" 표만 존재 -- item20-24 만 채운다(항목1-19는 원문 부재, 억지 추정 금지).
    # item25(-15699)/item31(63676)은 다른 2023 분기가 OCI를 안 채워 일관성 판단 보류,
    # 미기입. item24 는 22-23=79374 인데 원문 헤드라인은 79375(반올림 1원) -- 공시치 채택.
    ("KR0003", "2023.1Q"): {20: 105030.0, 21: -1628.0, 22: 103402.0, 23: 24028.0, 24: 79375.0},
    # 삼성화재(KR0008) 2023.1Q: `pl_breakdown_coverage.json`에 이미 no_income_statement로
    # 기록됨. tier1 '보험손익' 행 없음(이 필링 특유 표 구조, 최초도입분기 전용) + tier2
    # sonbo_component 헤더에 '자동차'가 없어 매칭 실패. 주석20(전체 보험계약/출재보험계약)
    # 직접판독으로 24항목. item1=2+13+14-16(660,154-92,608=567,546, 원문 567,547과 1 이내
    # 정합) · item7/12 는 3-12 부분계 플러그(각각 내부 검산 exact) · item17 은 원 단위 계산
    # 시 241,422~241,423 사이(±1 반올림, 241,422 채택). item15(기타영업수익)는 주석20 표에
    # 별도 라인이 없어 처음엔 N/A 로 뒀으나, assemble() 의 기존 관례("if t1 and v[15] is None:
    # v[15]=0.0" -- 이 회사는 t1=None 경로라 그 기본값이 못 걸림)와 PL_BRIDGE 보험손익(dual)
    # 검사가 item15/16 둘 다 있어야 item1=2+13+14+15-16 항등식을 도는 것(2026-09-12 실측,
    # 없으면 bare=2+13+14 만 보고 92,607 잔차로 오탐)을 확인해 0.0 명시(다른 항목13/14 의
    # "미해당=N/A" 와는 성격이 다른, 캐치올 소액 라인의 통상 0-기본값).
    ("KR0008", "2023.1Q"): {
        1: 567547.0, 2: 459817.0, 3: 457815.0, 4: 376038.0, 5: 32999.0,
        6: 21083.0, 7: 27695.0, 8: 2001.0, 9: -2249.0, 10: -4174.0, 11: 469.0,
        12: 7955.0, 13: 134513.0, 14: 65824.0, 15: 0.0, 16: 92608.0, 17: 241422.0,
        18: 598506.0, 19: -357084.0, 20: 808970.0, 21: 6906.0, 22: 815876.0,
        23: 235737.0, 24: 580138.0,
    },
    # NH농협손해(KR0032) 2023.1Q: `extract_tier2_nh` 캡션 매칭 실패(1Q 는 "보험영업이익"
    # 대신 "보험손익", "보험료배분접근법을적용하지않는" 대신 "을" 빠진 변형 사용 -- 이 필링
    # 전용, 코드 일반화는 후속). 노트14(보험계약 및 재보험계약) + MD&A 직접판독 22항목
    # (item13/14 는 "보험업 단일부문"이라 LOB 분리 미공시, 빈칸 유지). item2=3+8(76083 exact)
    # · item20=1+17(109496 exact) · item22=20+21(103625 exact) · item24=22-23(78945 exact)
    # 전부 내부 항등식 닫힘 확인(KR1010 과 달리 이 회사는 완전 정합). CSM_waterfall item5
    # -604.6억 <-> item4 60459백만원 억원단위 교차확인 일치.
    ("KR0032", "2023.1Q"): {
        1: 54280.0, 2: 76083.0, 3: 55622.0, 4: 60459.0, 5: 6161.0, 6: 1017.0,
        7: -12015.0, 8: 20461.0, 9: -1778.0, 10: -143.0, 11: -1357.0, 12: 23739.0,
        15: 0.0, 16: 21803.0, 17: 55216.0, 18: 111812.0, 19: -56596.0,
        20: 109496.0, 21: -5871.0, 22: 103625.0, 23: 24680.0, 24: 78945.0,
    },
    # 서울보증(KR0150) 2024.4Q: tier1 이 '보험손익' 단일행을 못 찾음(이 필링은
    # Ⅰ.영업수익/Ⅱ.영업비용/Ⅲ.영업이익 구조라 '1.보험수익'/'1.보험비용' 하위행에서 손계산
    # 필요). item13/14(LOB)는 extract_tier2_sgi 의 라벨변형 수정(_sgi_re_legs, 2026-09-12)으로
    # 코드가 직접 뽑는다 -- 이 override 는 건드리지 않음. item2(생명장기손익)도 이 회사
    # 전 분기 관례대로 None 유지(추가 안 함). rcept 20250324000440, 별도(OFS).
    # 검산: item1(146,226.527456) ~= item13+item14+item15-item16(잔차 0.000346, "사업의 개황"
    # 서술표 종목별 보험손익 합계와도 독립 일치). inbox/parser/20260901T1630Z(2026-09-12 처리).
    ("KR0150", "2024.4Q"): {
        1: 146226.527456, 15: 0.0, 16: 39313.675890, 17: 128210.284631,
        18: 248210.084756, 19: -119999.800125, 20: 274436.812087, 21: 5670.223745,
        22: 280107.035832, 23: 69152.035251, 24: 210955.000581,
    },
}


def main():
    uni = load_universe()
    filings = discover_filings()
    rows = []
    coverage = []  # (code, name, quarter, status, missing_items)
    oci32_prov = []  # item32 catch-all provenance: which account_id fed each (code, quarter)
    # (code, quarter, item) whose null is a DELIBERATE judgement, not a missing source:
    # the owner's 0-fill was suppressed because this company extracts the item for real in
    # some other quarter (option 1, 2026-08-30).  build_root_masters._additive_merge must
    # not resurrect the previously committed 0 over these -- it cannot tell the two kinds of
    # null apart from the value alone, so the builder states which ones it meant.
    intentional_nulls = []
    t1_src = {"api": 0, "html": 0}

    for code in sorted(filings):
        name, life_flag = uni.get(code, (None, None))
        if name is None:
            # unknown code (not in disclosure) — derive name from dir, skip 생손보
            name = code
        is_life = (life_flag == "생명보험")
        # Two passes over this company's quarters (owner decision 2026-08-30, option 1).
        # Pass A parses every quarter once and asks assemble() with the 0-fill switched off
        # entirely: whatever comes back non-None for items 6/11 was genuinely EXTRACTED.
        # Pass B then allows the 0-fill only for the items this company never extracts in
        # ANY quarter -- 농협/교보/동양 keep their 0 exactly as before, while a company that
        # normally reports the item keeps a null for the quarter whose source broke, instead
        # of a 0 that reads as a disclosed fact.  Parsing (the expensive part: parse_filing +
        # the FS API) happens once and is reused; the second assemble() call is pure dict
        # arithmetic.  This is the "분기간 대조를 assemble() 안으로 당기기" option -- it moves
        # the judgement PL_YTD_COLLAPSE_TO_ZERO already makes after the fact to before the
        # value is written, so a rebuild reproduces it instead of drifting back to 0.0.
        parsed = {}
        for q in sorted(filings[code], key=_quarter_sort_key):
            dirs = filings[code][q]
            has_xml = any(_xmls_in(d) for d in dirs)
            t1_html, t2 = parse_filing(dirs, is_life, code=code, name=name, quarter=q)
            t1_api = _fs_tier1(name, q, code)          # Tier-1 from DART FS API (primary)
            t1 = t1_api if t1_api else t1_html         # HTML extractor = fallback only
            t1_src["api" if t1_api else "html"] += 1 if t1 is not None else 0
            parsed[q] = (t1, t2, has_xml)
        ever_extracted = set()
        for q, (t1, t2, _hx) in parsed.items():
            if t1 is None and t2 is None:
                continue
            probe = assemble(t1, t2, is_life, zero_fill_ok=frozenset())
            for _n in ZERO_FILL_ITEMS:
                if probe[_n] is not None:
                    ever_extracted.add(_n)
        zero_fill_ok = ZERO_FILL_ITEMS - ever_extracted

        for q in sorted(parsed, key=_quarter_sort_key):
            t1, t2, has_xml = parsed[q]
            # KR0072(KDB생명) 2023.1Q: t1=t2=None(FS-API 013 + IFRS17 최초도입분기 구양식이라
            # tier1/tier2 매칭기가 아무 표도 못 찾는다) 인데도 raw 원문 직접판독으로 확인된
            # _GOLD_CELL_OVERRIDE 셀이 있다 -- 예전엔 여기서 무조건 skip 돼 그 override 가
            # 절대 적용되지 못했다(2026-09-12 실측: probe_20260912_pl_scoped_build_kr0072_
            # kr0150.py 로 재현, KR0072 2023.1Q 만 유일하게 SKIP 되고 KR0150 2024.4Q(t2 有)는
            # 정상 적용됨을 대조 확인). 등재된 override 가 있는 (회사,분기)만 예외적으로
            # 통과시킨다 -- 등재 없는 나머지 전부는 기존 동작(skip) 그대로.
            has_override = (code, q) in _GOLD_CELL_OVERRIDE
            if t1 is None and t2 is None and not has_override:
                # distinguish a download/extraction gap (only document.zip on disk) from a
                # genuine statement-format mismatch (XML present but no 포괄손익계산서 matched)
                st = "no_income_statement" if has_xml else "raw_not_extracted"
                coverage.append((code, name, q, st, list(range(1, 25)), "none"))
                continue
            v = assemble(t1, t2, is_life, zero_fill_ok=zero_fill_ok)
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
            # items 25-31 (총포괄손익 연장): only ever come from t1 (FS-API CIS rows) — never
            # pre-initialized by assemble() the way 1-24 are, so v.get(n) (not v[n]) and an
            # explicit None row when the filing's CIS section lacks them (audit-only companies,
            # or the pre-2025.4Q filings that disclose OCI totals but not the sub-line
            # breakdown, e.g. 삼성화재 2023.3Q-2025.3Q) — an explicit null row keeps the gap
            # visible to the coverage census instead of silently omitting it (SKIP-on-missing
            # is forbidden; see artifacts/parser/oci_label_census_pass2.json for the full grid).
            for n in OCI_ITEMS:
                val = v.get(n)
                rows.append({
                    "원보험사코드": code, "원수사명": name, "티커": None,
                    "생손보여부": life_flag, "항목번호": n, "항목명": ITEM_NAMES[n],
                    "공시분기": q,
                    "값": (round(val, 6) if isinstance(val, float) else val),
                })
            # item32 provenance (owner ticket inbox/parser/20260828T1600Z): catch-all, so record
            # which account_id/account_nm rows fed the sum for this (code, quarter) — otherwise
            # "what's in 기타" is unanswerable later.  fetch_dart_fs._oci32_from_rows stashes
            # this as a hidden t1 key; assemble() passes it through into v untouched.
            prov32 = v.get("_oci32_src")
            if prov32:
                oci32_prov.append({"원보험사코드": code, "원수사명": name, "공시분기": q,
                                    "구성": prov32})
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
            # items 7/12 are the residuals of 6/11 (7 = 3-4-5-6, 12 = 8-9-10-11); when the
            # 0-fill is suppressed they are unknowable too, and that null is equally deliberate.
            # Record ONLY the nulls the suppression itself created -- i.e. the exact
            # precondition of the 0-fill elif (its three inputs present, the item absent).
            # A blanket "item is null" test would also cover cells that are null because
            # their source is simply not on disk right now, and turning OFF the additive
            # fallback for those is precisely the cell-loss bug that merge exists to prevent.
            for _n, _dep, _pre in ((6, 7, (3, 4, 5)), (11, 12, (8, 9, 10))):
                if (_n in ever_extracted and v[_n] is None
                        and all(v[_p] is not None for _p in _pre)):
                    intentional_nulls.append([code, q, _n])
                    if v[_dep] is None:
                        intentional_nulls.append([code, q, _dep])
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

    # item32 (기타 포괄손익(미분류)) provenance — which account_id/account_nm rows were summed
    # into each (code, quarter)'s catch-all, so "what's actually in 기타" stays answerable.
    prov_path = Path("data/_derived/pl_oci_item32_provenance.json")
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    prov_path.write_text(json.dumps(oci32_prov, ensure_ascii=False, indent=1), encoding="utf-8")
    nulls_path = Path("data/_derived/pl_intentional_nulls.json")
    nulls_path.parent.mkdir(parents=True, exist_ok=True)
    nulls_path.write_text(json.dumps(
        {"_what": "0-fill 을 일부러 건너뛴 칸 (owner 결정 2026-08-30, option 1). "
                  "이 회사가 다른 분기에서는 이 항목을 실제로 뽑으므로, 이번 분기의 0 은 "
                  "공시된 사실이 아니라 유실이다. build_root_masters._additive_merge 가 "
                  "예전 0 을 되살리지 못하게 하는 목록.",
         "_items": {"6": "원수 예실차", "7": "기타 생명장기 원수손익(6의 잔차)",
                    "11": "재보험 예실차", "12": "기타 생명장기 재보험손익(11의 잔차)"},
         "cells": intentional_nulls}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"intentional nulls (0-fill suppressed): {len(intentional_nulls)} cells "
          f"-> {nulls_path}")
    print(f"item32 provenance: {len(oci32_prov)} company-quarters -> {prov_path}")
    return rows, coverage


if __name__ == "__main__":
    main()
