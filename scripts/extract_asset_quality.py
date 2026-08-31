"""Extract K-ICS disclosure Chapter III (자산의 건전성) into asset_quality.json.

  3-1. 자산건전성(부실자산비율) -- 3-row identity table (가중부실자산 / 분류대상자산 / 비율)
  3-2. 유가증권투자 및 평가손익 -- fixed 27-row regulatory template (공정가액 + 평가손익
       per security sub-type, under 일반계정 A/B/C/D categories + 특별계정 + 소계/합계)

SOURCE DECISION -- read before touching this file
-------------------------------------------------
This extractor reads the RAW PDF directly via fitz (PyMuPDF) as the PRIMARY source,
not docling MD. Census taken 2026-08-31 across all 36 FY2026_Q2 companies: docling's
keyword-window localizer drops Chapter III text entirely for 13/36 companies (36%) --
the *same* bug flagged in
inbox/parser/20260831T0700Z__orchestrator__MULTI_2026.2Q__docling_window_drops_market_section.md
for Chapter 6-4 (시장위험). The raw PDF text layer is intact for 11 of those 13
(verified via scripts/_probes/probe_asset_quality_pages.py) -- only KR0087(동양생명)
and KR0079(미래에셋생명) are genuinely scanned PDFs with no usable text layer (see
SCAN_ONLY_EXCEPTIONS below). Going PDF-direct avoids depending on a fix to that bug
and matches the established repo pattern (scripts/fill_market_subs_from_pdf.py).

Raw PDFs are on disk for ALL quarters 2023.1Q-2026.2Q under
data/disclosure/<period>/{raw,pdf}/ (confirmed 2026-08-31; not gitignored away
historically) -- newer quarters keep them under pdf/, older under raw/; this
extractor checks both.

FALLBACK: when the PDF text layer for a company/quarter is empty or the anchors
aren't found (e.g. KR0010 2026.2Q -- its pdf/ file on disk was overwritten today by
a concurrent process with a broken 0-byte-text "Microsoft: Print To PDF" artifact,
confirmed via fitz metadata: producer="Microsoft: Print To PDF", all pages 0 chars,
even though its docling MD -- generated earlier from the real PDF -- has valid
table text), this extractor falls back to parsing the docling MD pipe-table for the
same section. Both backends feed the SAME line-based state machine (see
_parse_31_lines / _parse_32_lines) so behavior is identical regardless of source.

SCHEMA (mirrors IFRS17_BS.json -- 10 fields, single 값 column, no 값_적용후 since
Chapter III has no 경과조치 concept):
  원보험사코드 · 원수사명 · 티커 · 생손보여부 · 항목번호 · 항목명 · 섹션 · 레벨 · 공시분기 · 값

ITEM NUMBER MAP (defined here, not in source -- source only has row labels):
  섹션="자산건전성" (from 3-1):
    1  가중부실자산(A)                       레벨=2  단위=억원
    2  자산건전성 분류대상자산(B)              레벨=2  단위=억원
    3  부실자산비율(A/B)                      레벨=1  단위=%  (derived ratio row)

  섹션="유가증권평가손익" (from 3-2, fixed 27-row template x 2 measures):
    항목번호 = 100 + row  -> 공정가액(fair value), 억원
    항목번호 = 200 + row  -> 평가손익(valuation P&L), 억원
    row  leaf (항목명 suffix)
    ---  --------------------------------------------------------------
     1   일반계정_당기손익공정가치측정유가증권(A)_주식
     2   일반계정_당기손익공정가치측정유가증권(A)_출자금
     3   일반계정_당기손익공정가치측정유가증권(A)_채권
     4   일반계정_당기손익공정가치측정유가증권(A)_수익증권
     5   일반계정_당기손익공정가치측정유가증권(A)_외화표시유가증권
     6   일반계정_당기손익공정가치측정유가증권(A)_기타유가증권
     7   일반계정_기타포괄손익공정가치측정유가증권(B)_주식
     8   일반계정_기타포괄손익공정가치측정유가증권(B)_출자금
     9   일반계정_기타포괄손익공정가치측정유가증권(B)_채권
    10   일반계정_기타포괄손익공정가치측정유가증권(B)_수익증권
    11   일반계정_기타포괄손익공정가치측정유가증권(B)_외화표시유가증권
    12   일반계정_기타포괄손익공정가치측정유가증권(B)_기타유가증권
    13   일반계정_상각후원가측정유가증권(C)_채권
    14   일반계정_상각후원가측정유가증권(C)_수익증권
    15   일반계정_상각후원가측정유가증권(C)_외화표시유가증권
    16   일반계정_상각후원가측정유가증권(C)_기타유가증권
    17   일반계정_관계종속기업투자주식(D)_주식
    18   일반계정_관계종속기업투자주식(D)_출자금
    19   일반계정_관계종속기업투자주식(D)_기타
    20   일반계정_소계(A+B+C+D)                                  레벨=1
    21   특별계정_주식
    22   특별계정_채권
    23   특별계정_수익증권
    24   특별계정_외화유가증권
    25   특별계정_기타유가증권
    26   특별계정_소계                                          레벨=1
    27   합계                                                레벨=1
    (all other rows 레벨=2)

  Row order is FIXED by regulation (표준 경영공시 서식) -- confirmed identical across
  36 companies incl. tiny/zero-book insurers (KR1098 카카오페이손해보험 shows all 27
  rows with "-" placeholders). A disclosed "-" in this table means "held none of this
  security type" (a real disclosed zero), NOT a missing/undisclosed cell -- so "-" is
  mapped to 0.0, distinct from a row whose LABEL never appears at all (genuine gap,
  left out of the master, not zero-filled). See _NUM_RE / _parse_amount.

Usage:
  venv python scripts/extract_asset_quality.py --period FY2026_Q2 --dry-run
  venv python scripts/extract_asset_quality.py --period FY2026_Q2
  venv python scripts/extract_asset_quality.py --all-periods --dry-run
  venv python scripts/extract_asset_quality.py --period FY2026_Q2 --company KR0011
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "asset_quality.json"
KICS_JSON_PATH = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"
MD_INBOX = REPO / "md_inbox"
DIAG_PATH = REPO / "data" / "_derived" / "asset_quality_diagnostics.json"

_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")

# ---------------------------------------------------------------------------
# item schema
# ---------------------------------------------------------------------------

SEC_31 = "자산건전성"
SEC_32 = "유가증권평가손익"

ITEM_31 = {
    1: ("가중부실자산(A)", 2),
    2: ("자산건전성 분류대상자산(B)", 2),
    3: ("부실자산비율(A/B)", 1),
}

# canonical 27-row leaf schema for 3-2, in disclosed order.
# (category_prefix, leaf_keyword_compact, level)
ROW32 = [
    ("일반계정_당기손익공정가치측정유가증권(A)", "주식", 2),
    ("일반계정_당기손익공정가치측정유가증권(A)", "출자금", 2),
    ("일반계정_당기손익공정가치측정유가증권(A)", "채권", 2),
    ("일반계정_당기손익공정가치측정유가증권(A)", "수익증권", 2),
    ("일반계정_당기손익공정가치측정유가증권(A)", "외화표시유가증권", 2),
    ("일반계정_당기손익공정가치측정유가증권(A)", "기타유가증권", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "주식", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "출자금", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "채권", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "수익증권", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "외화표시유가증권", 2),
    ("일반계정_기타포괄손익공정가치측정유가증권(B)", "기타유가증권", 2),
    ("일반계정_상각후원가측정유가증권(C)", "채권", 2),
    ("일반계정_상각후원가측정유가증권(C)", "수익증권", 2),
    ("일반계정_상각후원가측정유가증권(C)", "외화표시유가증권", 2),
    ("일반계정_상각후원가측정유가증권(C)", "기타유가증권", 2),
    ("일반계정_관계종속기업투자주식(D)", "주식", 2),
    ("일반계정_관계종속기업투자주식(D)", "출자금", 2),
    ("일반계정_관계종속기업투자주식(D)", "기타", 2),
    ("", "일반계정_소계(A+B+C+D)", 1),          # row 20 (checkpoint #1)
    ("특별계정", "주식", 2),
    ("특별계정", "채권", 2),
    ("특별계정", "수익증권", 2),
    ("특별계정", "외화유가증권", 2),
    ("특별계정", "기타유가증권", 2),
    ("특별계정", "기타", 2),                     # row 26, OPTIONAL -- only AIA생명(KR0080)
                                                #   2026.2Q discloses this 6th 특별계정 leaf
                                                #   (reconciles into 소계 exactly: 6937+3253+
                                                #   1050+2412+0+0=13652=소계 공정가액). Most
                                                #   companies stop at 5 (기타유가증권); when
                                                #   absent this row is simply not emitted.
    ("", "특별계정_소계", 1),                    # row 27 (checkpoint #2, FIXED regardless of
                                                #   whether row 26 appears)
    ("", "합계", 1),                             # row 28 (checkpoint #3, FIXED)
]
assert len(ROW32) == 28
N_A, N_B, N_C, N_D = 6, 6, 4, 3  # leaves per general-account category before 소계1
N_SPECIAL_MIN, N_SPECIAL_MAX = 5, 6  # leaves in 특별계정 before 소계2 (5 standard + optional 기타)

LEAF_KEYWORDS = {"주식", "출자금", "채권", "수익증권", "외화표시유가증권", "외화유가증권", "기타유가증권", "기타"}

# label variants seen across companies for the same conceptual leaf (this repo's
# established "label variants" pattern -- e.g. reference_kics_label_variants -- KICS
# labels are not byte-identical across insurers' own PDF templates).
# "익증권": corrupted docling MD table OCR (KB손해보험 2026.2Q's 특별계정 block drops
#   the leading "수" from "수익증권").
# "해외유가증권": 삼성화재해상보험 2026.2Q's own PDF template uses this instead of
#   "외화유가증권" for the SAME 특별계정 row (both mean FX-denominated securities;
#   confirmed by row position + reconciliation into 소계).
_LEAF_ALIASES = {"익증권": "수익증권", "해외유가증권": "외화유가증권"}


def _dedupe_doubled(c: str) -> str:
    """Collapse an immediately-repeated prefix, keeping any non-repeated suffix.

    한화생명(KR0068) 2026.2Q's PDF renders this table's LABEL text as a doubled /
    overlapping run (probably a faux-bold effect: the same text drawn twice with ~0
    offset) -- NOT its numeric values, only labels. Under fitz's sort=True (needed
    for KR0073/KR0094, see _pdf_window_text) this merges into one token with no
    separating space at all, e.g. "가중부실자산가중부실자산(A)" (base word "가중부실자산"
    literally repeated, then the "(A)" suffix that only the second copy carries) or
    even single syllables: "주주"/"식식" instead of "주"/"식". Finds the LARGEST k
    such that c[:k] == c[k:2k] and reconstructs as c[:k] + c[2k:], so a same-length
    full double ("계계" -> "계") and a suffixed double ("...(A)" case above) both
    resolve correctly. Safe on genuinely non-doubled tokens (numbers, and every
    other label observed) -- no k satisfies the equality, so they pass through
    unchanged; run BEFORE _merge_fragments so a doubled single-syllable fragment
    ("주주") collapses to "주" first and can then still be reassembled with its
    neighbor "식" the normal fragment-merge way."""
    n = len(c)
    for k in range(n // 2, 0, -1):
        if c[:k] == c[k : 2 * k]:
            return c[:k] + c[2 * k :]
    return c


def _normalize_aliases(lines):
    out = []
    for l in lines:
        c = _compact(l)
        out.append(_LEAF_ALIASES[c] if c in _LEAF_ALIASES else l)
    return out


def _dedupe_doubled_lines(lines):
    out = []
    for l in lines:
        c = _compact(l)
        out.append(l if _looks_like_value_token(c) else _dedupe_doubled(c))
    return out

# companies with a confirmed-scanned PDF text layer for a given (code, period) --
# do not attempt extraction, report as documented exception instead.
SCAN_ONLY_EXCEPTIONS = {
    ("KR0087", "FY2026_Q2"),  # 동양생명: 59p/258 chars total, 0 keyword hits (text layer absent)
    ("KR0079", "FY2026_Q2"),  # 미래에셋생명: 65p/4917 chars, 39/65 pages low-density, 0 keyword hits
}


def quarter_to_period(q: str) -> str:
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def period_to_quarter(p: str) -> str:
    m = _PERIOD_RE.match(p)
    return f"{m.group(1)}.{m.group(2)}Q"


# ---------------------------------------------------------------------------
# number parsing
# ---------------------------------------------------------------------------

_NEG_CHARS = ("△", "▲", "▽", "▼", "−")


def _parse_amount(tok: str):
    """Parse one value token from this table's context. Returns float or None.

    A bare '-' / dash-family char (with this table's leaf label CONFIRMED present)
    means "disclosed as nil" -> 0.0, per the SCHEMA docstring above. Returns None
    only when the token genuinely doesn't look like a value at all (caller should
    not have offered it as a value candidate in that case).
    """
def _normalize_numeric(c: str) -> str:
    r"""Common cleanup shared by the parser and the look-ahead prober. Handles THREE
    negative notations seen in these tables: '△ 44'/'▲ 44' (전용 부호문자),
    '(44)' (whole number wrapped in parens), and -- the one that silently broke
    item 102/103/104/106 등의 평가손익 column before this fix -- '(-)44' (ONLY the
    minus sign wrapped in its own parens, digits follow OUTSIDE: "출자금" row's
    "2,548 / (-)44" for KR0011). The old regex only matched the "(44)"/"(-44)"
    shapes (closing paren AFTER the digits) and silently treated "(-)44" as
    unparseable noise -- which _parse_32_lines's state machine then skipped over as
    if the cell didn't exist, so the leaf's 2nd (평가손익) value was dropped and the
    NEXT leaf's label got consumed as if it were this leaf's missing value's
    neighbor. Confirmed against KR0011: items 102/103/104/106 (출자금/채권/수익증권/
    기타유가증권 공정가치측정유가증권(A)) were emitted with a 공정가액 but no 평가손익
    row at all before this fix, even though the source clearly prints both."""
    c = c.replace(",", "").replace(" ", "")
    c = c.replace("(-)", "-")  # MUST run before the generic paren-negative regex below
    for ch in _NEG_CHARS:
        c = c.replace(ch, "-")
    m = re.fullmatch(r"\((-?\d[\d.]*)\)", c)  # "(44)" / "(-44)"
    if m:
        c = "-" + m.group(1).lstrip("-")
    return c.rstrip("%p").rstrip("%")


def _parse_amount(tok: str):
    if tok is None:
        return None
    c = tok.strip()
    if c in ("", "-", "־", "‑", "─", "–", "—", "phi", "(-)"):
        return 0.0
    c = _normalize_numeric(c)
    if not re.fullmatch(r"-?\d+(\.\d+)?", c):
        return None
    return float(c)


def _looks_like_value_token(tok: str) -> bool:
    """True if a (compacted) token could plausibly be a value cell (number or dash)."""
    if tok in ("-", "־", "‑", "─", "–", "—", "(-)"):
        return True
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", _normalize_numeric(tok)))


def _compact(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def _strip_footnote(c: str) -> str:
    """Drop a trailing footnote marker glued directly onto a label with no space,
    e.g. KR0072 케이디비생명보험 2026.2Q's C-category leaf renders as
    "외화표시유가증권2)" (footnoted: "손실충당금 0.5억원 포함") -- an exact LEAF_KEYWORDS
    match would silently miss this ONE row (19 group1 leaves -> 18) with no other
    symptom. The optional "주" handles the Korean footnote-marker SPELLING variant
    (KR0003 롯데손해보험 FY2023_Q2: "외화표시유가증권주2)", "주" = "note") -- without
    it, stripping just "2)" leaves a stray "주" ("외화표시유가증권주" != the keyword)
    and the row is STILL missed. Safe to apply only at label-comparison call sites,
    never on value tokens (a value like "(44)" must NOT have "4)" stripped from it)."""
    return re.sub(r"주?\d+\)$", "", c)


def _leaf_of(c: str):
    """Canonical leaf keyword for a compacted label cell, or None. Applies the
    footnote strip and the alias table (see _LEAF_ALIASES)."""
    for cand in (c, _strip_footnote(c)):
        if cand in LEAF_KEYWORDS:
            return cand
        if cand in _LEAF_ALIASES:
            return _LEAF_ALIASES[cand]
    return None


# some companies' PDF tables render with such narrow columns that fitz emits one
# Korean SYLLABLE per line (e.g. "주"/"식" as two separate lines instead of one
# "주 식" line -- seen in KR0080/KR1000; even single-character-per-line for
# "채"/"권" and "소"/"계" in KR1000's 특별계정 block). Reassemble these before the
# state machine runs, so both backends see whole-keyword lines uniformly.
_MERGE_TARGETS = set(LEAF_KEYWORDS) | {"소계", "합계"} | set(_LEAF_ALIASES.keys())


def _merge_fragments(lines):
    out = []
    i = 0
    n = len(lines)
    while i < n:
        merged = ""
        j = i
        last_complete, last_complete_j = None, None
        while j < n and len(merged) < 10:
            c = _compact(lines[j])
            if not c or re.search(r"\d", c) or len(c) > 3:
                break
            candidate = merged + c
            if not any(t.startswith(candidate) for t in _MERGE_TARGETS):
                break
            merged = candidate
            j += 1
            if merged in _MERGE_TARGETS:
                last_complete, last_complete_j = merged, j
        if last_complete and last_complete_j > i + 1:
            out.append(last_complete)
            i = last_complete_j
        else:
            out.append(lines[i])
            i += 1
    return out


# ---------------------------------------------------------------------------
# shared line-based state machine (fed by either PDF-fitz lines or MD-table lines)
# ---------------------------------------------------------------------------

_MAX_LABEL_LEN = 20  # excludes the "3-1. 자산건전성(부실자산비율)" chapter/section
                      # HEADER (which itself contains the substring "부실자산비율" and
                      # would otherwise false-match the item-3 anchor) and narrative
                      # "주요변동요인: ..." sentences (which can contain "분류대상자산"
                      # as a substring too) -- both run well past this length; the
                      # real data-row labels are all under 16 chars.


def _parse_31_lines(lines):
    """lines: flat list of stripped strings in reading order. Returns ({1: val,
    2: val, 3: val} -- 당기/current-period column only, i.e. the first value of
    each row's run), evidence).

    RUN-based, not label-anchored: collects maximal consecutive runs of
    value-looking tokens between the "가중부실자산" anchor and the "3-2" boundary,
    and takes the first 3 runs as item1/item2/item3 in that fixed row order (a
    regulatory-template invariant confirmed across every company sampled -- see
    module docstring). This deliberately does NOT try to pair each run with its
    OWN label by position, because fitz's sort=True word-tokenization (needed to
    fix badly-scrambled companies like KR0073/KR0094 -- see _pdf_window_text) can
    still reorder a WRAPPED label's own two halves to opposite sides of its value
    run (KR0011 DB손해보험: "자산건전성"(idx23) 565,371(24) 526,547(25) 38,824(26)
    "분류대상자산(B)"(27, only AFTER its own values)) -- a forward-scan-from-label
    approach chases that reordering forever, while a run only needs SOME
    non-value token to separate it from its neighbors, regardless of which side
    of the run the label ends up on. Robust to a short row too (KB손해보험 KB0010's
    MD 자산건전성분류대상자산(B) row has no 증감/3rd column at all -- a 2-token run
    -- unlike a fixed vals[0]/vals[3]/vals[6] index scheme, which that shifts out
    of alignment)."""
    n = len(lines)
    start = None
    for i in range(n):
        if "가중부실자산" in _compact(lines[i]):
            start = i
            break
    if start is None:
        return {}, {"note": "가중부실자산 anchor not found"}

    end = n
    for i in range(start + 1, n):
        c = _compact(lines[i])
        if c.startswith("3-2") or c in ("유가증권",) or "유가증권투자" in c:
            end = i
            break

    runs = []
    cur = []
    for i in range(start, end):
        tokc = _compact(lines[i])
        if _looks_like_value_token(tokc):
            cur.append(_parse_amount(tokc))
        elif cur:
            runs.append(cur)
            cur = []
        if len(runs) >= 3:
            break
    if cur and len(runs) < 3:
        runs.append(cur)

    out = {}
    for item_no in (1, 2, 3):
        idx = item_no - 1
        if idx < len(runs) and runs[idx]:
            out[item_no] = runs[idx][0]
    evidence = {"span": f"[{start}:{end}]", "runs": runs}
    return out, evidence


def _parse_32_lines(lines):
    """Sequential leaf-keyword alignment against the fixed 27-row canonical schema.
    Returns (values: {item_no(101-128,201-228, +141-.../241-... for extras): float},
    status: str, detail: str, extra_labels: {item_no: str}).
    status in {"ok", "structure_mismatch", "not_found"}. extra_labels names any
    company-specific rows beyond the canonical template (see ROW32/canonical_leaf_seq
    below) that couldn't be dropped without losing disclosed data.
    """
    def _is_row_marker(c):
        return (_leaf_of(c) is not None) or c.startswith("소계") or c.startswith("합계") or "A+B+C+D" in c.upper()

    def _marker_kind(c):
        """Classify a marker line so a same-kind duplicate can be told apart from a
        genuinely different next row, even when the duplicate's TEXT differs (KB/한화생명
        etc. render the 일반계정 subtotal TWICE across merged hierarchy columns, but only
        the SECOND copy carries the "(A+B+C+D)" suffix -- "소계" != "소계(A+B+C+D)" as
        exact strings, so a plain tokc==compact check misses this and the empty first
        copy gets miscounted as its own subtotal candidate, throwing off the group1/
        group2 boundary split entirely -- see 한화생명 KR0068 2026.2Q)."""
        leaf = _leaf_of(c)
        if leaf is not None:
            return ("leaf", leaf)
        if c.startswith("소계") or "A+B+C+D" in c.upper():
            return ("subtotal", None)
        if c.startswith("합계"):
            return ("total", None)
        return None

    n = len(lines)
    # Bound the scan to start AFTER the "3-2" marker when present. Without this,
    # a 3-1 narrative sentence that happens to contain a bare word matching a leaf
    # keyword exactly pollutes the count -- KR0071 케이디비생명보험 2026.2Q's 3-1
    # "주요변동요인" narrative literally reads "...수익증권 일부 자산건전성 분류
    # 조정에 따라..." and "수익증권" alone IS one of LEAF_KEYWORDS, so it was being
    # counted as a phantom 20th 일반계정 leaf before this fix (found via the exact
    # same failure in KR0073/KR0083/KR0094/KR0097's own 3-1 narratives). The MD
    # backend's lines already come pre-sliced to just the 3-2 table (see
    # _md_window_lines), so it has no "3-2" token to find -- scan_start stays 0.
    scan_start = 0
    for i in range(n):
        if _compact(lines[i]).startswith("3-2"):
            scan_start = i + 1
            break

    # candidate leaf occurrences: (line_idx, keyword, val1, val2)
    candidates = []
    i = scan_start
    while i < n:
        compact = _compact(lines[i])
        is_leaf = _leaf_of(compact) is not None
        is_subtotal = compact.startswith("소계") or "A+B+C+D" in compact.upper()
        is_total = compact.startswith("합계")
        if is_leaf or is_subtotal or is_total:
            anchor_kind = _marker_kind(compact)
            vals = []
            j = i + 1
            scanned = 0
            while j < n and len(vals) < 2 and scanned < 6:
                tokc = _compact(lines[j])
                if _looks_like_value_token(tokc):
                    vals.append(_parse_amount(tokc))
                elif _marker_kind(tokc) == anchor_kind:
                    pass  # duplicate/continuation of THIS row's own marker (docling
                          # renders e.g. "계(A+B+C+D)" or "주식" twice across merged
                          # hierarchy columns, sometimes with a differing suffix on
                          # only one copy) -- skip past it, do not stop the scan
                elif _is_row_marker(tokc):
                    break  # a DIFFERENT row's marker appeared -- this row has no value
                j += 1
                scanned += 1
            kind = "subtotal" if is_subtotal else ("total" if is_total else compact)
            candidates.append((i, kind, vals))
            # j always ends >= i+1 (its initial value), whether via value-collection,
            # self-duplicate skipping, or an immediate break -- advancing to it (never
            # just i+1) is what skips PAST a same-label duplicate even when this row's
            # values were genuinely empty (e.g. a blank cell, not even "-"), so that
            # duplicate is never re-visited as a phantom second candidate.
            i = j
        else:
            i += 1

    if not candidates:
        return {}, "not_found", "no leaf/소계/합계 keyword lines found in window", {}

    leaves = [c for c in candidates if c[1] not in ("subtotal", "total")]
    subtotals = [c for c in candidates if c[1] == "subtotal"]
    totals = [c for c in candidates if c[1] == "total"]

    if len(subtotals) < 2 or len(totals) < 1:
        return {}, "structure_mismatch", f"leaves={len(leaves)} subtotal_lines={len(subtotals)} total_lines={len(totals)} (need >=2 subtotal, >=1 total)", {}

    sub1_idx = subtotals[0][0]
    sub2_idx = subtotals[1][0]
    group1_leaves = [c for c in leaves if c[0] < sub1_idx]
    group2_leaves = [c for c in leaves if sub1_idx < c[0] < sub2_idx]

    expect1 = N_A + N_B + N_C + N_D  # 19
    if len(group1_leaves) < expect1:
        return {}, "structure_mismatch", f"일반계정 leaves={len(group1_leaves)} expected>={expect1}", {}
    if not (N_SPECIAL_MIN <= len(group2_leaves) <= N_SPECIAL_MAX):
        return {}, "structure_mismatch", f"특별계정 leaves={len(group2_leaves)} expected={N_SPECIAL_MIN}-{N_SPECIAL_MAX}", {}

    # Sequence-align group1 against the canonical 19-keyword order, rather than
    # requiring an exact count: 교보생명(KR0073) 2026.2Q discloses TWO extra bare
    # "기타" rows (one after A's 기타유가증권, one after B's) that aren't in the
    # standard template at all (21 leaves total, not 19) -- but they're genuine
    # extra disclosure, not a mis-extraction, so they must not be silently dropped
    # NOR mis-assigned to a canonical slot (a naive positional zip would shift
    # every row after the first extra by one, corrupting 13 downstream values).
    # Greedy left-to-right alignment: consume the observed leaf into the next
    # canonical slot when it matches; otherwise park it as an "extra" without
    # advancing the canonical pointer. Requires the run to be a strict template
    # SUPERSET (all 19 canonical keywords found in order) -- a genuine missing
    # canonical row still fails structure_mismatch rather than silently
    # misaligning everything after the gap.
    canonical_leaf_seq = [leaf for (_cat, leaf, _lvl) in ROW32[:19]]
    aligned = {}
    extra_group1 = []
    ci = 0
    for cand in group1_leaves:
        _idx, kind, vals = cand
        kw = _leaf_of(kind) or kind
        if ci < len(canonical_leaf_seq) and kw == canonical_leaf_seq[ci]:
            aligned[ci + 1] = vals
            ci += 1
        else:
            extra_group1.append((kw, vals))
    if ci != len(canonical_leaf_seq):
        return {}, "structure_mismatch", f"일반계정 alignment matched {ci}/{len(canonical_leaf_seq)} canonical rows ({len(group1_leaves)} observed)", {}

    # rows 1-19 (group1, fixed), row 20 (subtotal1, fixed), rows 21..21+len(group2)-1
    # (group2, 5 or 6 -- AIA생명 discloses an extra 특별계정_기타 leaf, see ROW32
    # comment), row 27 (subtotal2, FIXED regardless of group2 length so downstream
    # item numbers never shift company to company), row 28 (total, FIXED). Extra
    # rows beyond the canonical 19/5-6 (from either group) get appended starting
    # at row 41 (items 141+/241+, a reserved never-otherwise-used range) rather
    # than dropped -- see extra_group1 above.
    values = {}

    def _emit(row_no, vals):
        fv = vals[0] if len(vals) >= 1 else None
        pl = vals[1] if len(vals) >= 2 else None
        if fv is not None:
            values[100 + row_no] = fv
        if pl is not None:
            values[200 + row_no] = pl

    for row_no, vals in aligned.items():
        _emit(row_no, vals)
    _emit(20, subtotals[0][2])
    for idx, (_, _kind, vals) in enumerate(group2_leaves):
        _emit(21 + idx, vals)
    _emit(27, subtotals[1][2])
    _emit(28, totals[0][2])
    extra_labels = {}
    for k, (kw, vals) in enumerate(extra_group1):
        row_no = 41 + k
        _emit(row_no, vals)
        extra_labels[row_no] = f"일반계정_기타추가항목_{kw}"
    return values, "ok", (f"leaves1={len(group1_leaves)}({expect1}canonical+{len(extra_group1)}extra) "
                           f"leaves2={len(group2_leaves)}"), extra_labels


# ---------------------------------------------------------------------------
# PDF backend
# ---------------------------------------------------------------------------

def find_pdf(period: str, code: str):
    """Prefer pdf/ (current-quarter layout), fall back to raw/ (historical)."""
    candidates = []
    for sub in ("pdf", "raw"):
        d = DISCLOSURE / period / sub
        if d.is_dir():
            candidates.extend(sorted(d.glob(f"{code}_*.pdf")))
    if not candidates:
        return None

    def rank(p: Path):
        name = p.name
        m = re.search(r"_amended(\d*)", name)
        if m:
            return (1, int(m.group(1)) if m.group(1) else 1)
        return (0, 0)

    candidates.sort(key=rank)
    return candidates[-1]


def _page_leaf_density(txt: str) -> int:
    """Count of tokens on a page that are EXACT leaf-keyword matches (or a known
    alias) -- the 27-row 3-2 template's reliable fingerprint. Used to locate that
    table independently of chapter numbering (see _pdf_window_text)."""
    return sum(1 for t in txt.split() if _compact(t) in LEAF_KEYWORDS or _compact(t) in _LEAF_ALIASES)


def _pdf_window_text(pdf_path: Path):
    """Return (tokens_31, tokens_32, page_info, total_chars): word-token windows
    for the 3-1 (자산건전성) and 3-2 (유가증권투자) sub-tables, found and windowed
    INDEPENDENTLY, or (None, None, page_info, total_chars) if neither anchor is
    found at all.

    Uses fitz's sort=True (position-sorted, not raw content-stream order) then
    splits on ANY whitespace run into flat word tokens -- NOT `.split("\\n")`. Two
    companies (KR0073 교보생명보험, KR0094 신한라이프생명보험) emit this table with
    a badly scrambled content-stream order under plain get_text() (label block, then
    a disconnected value block, then the CATEGORY headers last) -- unusable for the
    label-then-adjacent-value state machine below. sort=True reconstructs correct
    visual reading order and, as a bonus, puts a whole row ("가중부실자산(A)  3,251
    2,053  1,197") on one text line, multi-space-delimited by column.

    3-1 and 3-2 are windowed SEPARATELY, not as one "anchor1 forward to a chapter-4
    boundary" span: ANNUAL (4Q, 연간결산) 경영공시 use a completely different
    template than quarterly filings, where 자산건전성 and 유가증권투자 aren't even
    adjacent -- confirmed on 메리츠화재 KR0001 FY2023_Q4: 유가증권투자 is "4-3."
    under "Ⅳ. 재무에 관한 상황" (page 26 of 102) while 자산건전성 is "5-4." under a
    LATER, differently-numbered chapter (page 40) -- 유가증권투자 comes BEFORE
    자산건전성 in reading order, the opposite of quarterly filings, and a
    forward-only scan from the 자산건전성 anchor never reaches it at all (or, worse,
    sweeps through several UNRELATED intervening chapters -- 수익성/유동성/신용평가
    등급/부동산보유현황/보험계약부채 -- whose own tables' words and subtotal rows
    pollute the leaf/subtotal counts). 3-2's table is instead located by a
    whole-document leaf-keyword-DENSITY scan (_page_leaf_density) -- the real table
    has ~19-27 bare "주식"/"채권"/... cells; even a table that happens to mention
    the same GROUP-header phrase ("당기손익-공정가치측정유가증권" is itself one line
    item on 메리츠화재's own "4-1. 요약 재무상태표" balance-sheet summary, page 21 --
    a false-positive a phrase-co-occurrence check doesn't reject) scores at most 1-2,
    nowhere near the density threshold."""
    import fitz

    doc = fitz.open(pdf_path)
    n = len(doc)
    total_chars = 0
    anchor1 = None  # 가중부실자산 (3-1)
    page_texts = []
    for i in range(n):
        txt = doc[i].get_text()
        page_texts.append(txt)
        total_chars += len(txt)
        if anchor1 is None and "가중부실자산" in txt:
            anchor1 = i

    # 3-2 candidate scoring REQUIRES "공정가액"+"평가손익" (this table's own column
    # headers) within a 3-page rolling window, not leaf-density alone: 흥국화재
    # KR0005 2026.2Q's 재무제표 주석 "금융상품의 평가수준별 공정가치" fair-value-
    # hierarchy footnote (a DIFFERENT, IFRS13-mandated table, elsewhere in this
    # 181-page filing) ALSO breaks securities down as bare 주식/출자금/수익증권/
    # 외화유가증권/기타유가증권 rows -- scoring 9, higher than that quarter's REAL
    # 3-2 table -- but its columns are "수준1/수준2/수준3/합계" (fair-value levels),
    # never "공정가액"/"평가손익", so gating on those column headers rejects it.
    best2, score2 = None, 0
    for i in range(n):
        lo, hi = max(0, i - 1), min(n - 1, i + 1)
        window_blob = "".join(page_texts[lo : hi + 1])
        if "공정가액" not in window_blob or "평가손익" not in window_blob:
            continue
        score = _page_leaf_density(page_texts[i])
        if score > score2:
            score2, best2 = score, i
    if anchor1 is None and (best2 is None or score2 < 5):
        doc.close()
        return None, None, "", total_chars

    def _window_tokens(center, before, after):
        lo, hi = max(0, center - before), min(n - 1, center + after)
        parts = [doc[i].get_text(sort=True) for i in range(lo, hi + 1)]
        return "\n".join(parts).split(), lo + 1, hi + 1

    tokens_31, p31 = None, ""
    if anchor1 is not None:
        tokens_31, s, e = _window_tokens(anchor1, 0, 2)
        p31 = f"31:p{s}-{e}"

    tokens_32, p32 = None, ""
    if best2 is not None and score2 >= 5:
        tokens_32, s, e = _window_tokens(best2, 1, 3)
        p32 = f"32:p{s}-{e}(density={score2})"

    doc.close()
    page_info = ",".join(x for x in (p31, p32) if x)
    return tokens_31, tokens_32, page_info, total_chars


def _detect_unit_scale(lines):
    # unit cue can land split across adjacent tokens after word-tokenization (e.g.
    # "(단위" ":" "억원," as 3 separate tokens) -- check a joined window, not one
    # token at a time.
    blob = _compact("".join(lines[:60]))
    if "단위" in blob:
        if "백만원" in blob:
            return 100.0, "백만원"
        if "억원" in blob:
            return 1.0, "억원"
    return 1.0, "억원(기본값,단위행 미검출)"


# ---------------------------------------------------------------------------
# MD backend (fallback)
# ---------------------------------------------------------------------------

def find_md(period: str, code: str):
    d = MD_INBOX / period
    cands = sorted(d.glob(f"{code}_*.md")) if d.is_dir() else []
    return cands[0] if cands else None


def _md_table_blocks(md_text: str):
    """Yield lists-of-rows for each markdown pipe-table in the document, in order.
    Each row is a list of cell strings (already stripped)."""
    lines = md_text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith("|"):
            block = []
            j = i
            while j < n and lines[j].lstrip().startswith("|"):
                block.append(lines[j])
                j += 1
            rows = []
            for raw in block:
                cells = [c.strip() for c in raw.strip().strip("|").split("|")]
                if all(re.fullmatch(r":?-+:?", c or "-") for c in cells):
                    continue  # separator row
                rows.append(cells)
            if rows:
                yield rows
            i = j
        else:
            i += 1


def _md_window_lines(md_path: Path):
    """Return (lines_31, lines_32), each None if not found. Locates the
    자산건전성/유가증권투자 sections anywhere in the MD (chapter number prefix
    ignored -- KB손보 2026.2Q labels it '5-2.' not '3-2.', a source-document quirk)
    and flattens each into the same line-token stream the PDF backend produces, so
    both feed the identical state machine. Independent per-table lookup (like the
    PDF backend's _pdf_window_text) rather than one combined window, for the same
    reason: annual (4Q) filings don't keep these tables adjacent.

    Table selection for 3-2 is by LEAF-KEYWORD CELL DENSITY, not by nearby header
    text: KB손해보험 2026.2Q has an earlier, unrelated BS-composition table whose
    row labels happen to include the phrase "당기손익-공정가치측정유가증권" too (it's
    one of ITS line items) -- a naive "table mentions 당기손익+공정가치측정" match
    grabs that wrong table instead of the real 27-row 3-2 template. The real 3-2
    table has ~19-27 cells that are EXACT leaf keywords (주식/채권/...); the BS
    table has none. Picking the highest-scoring table avoids the false match."""
    text = md_path.read_text(encoding="utf-8")
    if "가중부실자산" not in text:
        return None, None
    lines_31 = None
    best_score, best_cells = 0, None
    for rows in _md_table_blocks(text):
        cells = [c for row in rows for c in row if c and not re.fullmatch(r":?-+:?", c)]
        joined = "".join(cells)
        if lines_31 is None and "가중부실자산" in joined:
            lines_31 = cells
            continue
        score = sum(1 for c in cells if (_compact(c) in LEAF_KEYWORDS or _compact(c) in _LEAF_ALIASES))
        if score > best_score:
            best_score, best_cells = score, cells
    lines_32 = best_cells if best_score >= 10 else None
    return lines_31, lines_32


# ---------------------------------------------------------------------------
# company registry (원수사명/티커/생손보여부) -- union across kics_disclosure.json
# ---------------------------------------------------------------------------

def build_registry():
    rows = json.loads(KICS_JSON_PATH.read_text(encoding="utf-8"))
    reg = {}
    for r in rows:
        reg[r["원보험사코드"]] = {
            "원수사명": r["원수사명"],
            "티커": r["티커"],
            "생손보여부": r["생손보여부"],
        }
    return reg


_NAME_FROM_FILE_RE = re.compile(r"^(KR\d+)_(.+)$")


def _registry_fallback_from_filename(path: Path):
    m = _NAME_FROM_FILE_RE.match(path.stem)
    name = m.group(2) if m else path.stem
    name = re.sub(r"_amended\d*$", "", name)
    return {"원수사명": name, "티커": "X", "생손보여부": ""}


# ---------------------------------------------------------------------------
# per-company extraction
# ---------------------------------------------------------------------------

def extract_company_quarter(code: str, period: str, registry: dict, diagnostics: list):
    quarter = period_to_quarter(period)
    rec = {"code": code, "period": period, "quarter": quarter}

    if (code, period) in SCAN_ONLY_EXCEPTIONS:
        rec.update(status="scan_exception", detail="documented scan-only exception (see SCAN_ONLY_EXCEPTIONS)")
        diagnostics.append(rec)
        return []

    # 3-1 and 3-2 are located and windowed INDEPENDENTLY (see _pdf_window_text /
    # _md_window_lines docstrings -- annual/4Q filings put them under different,
    # non-adjacent chapters), each preferring PDF then falling back to MD, so one
    # sub-table's source doesn't gate the other's.
    pdf_path = find_pdf(period, code)
    tokens_31 = tokens_32 = None
    source_31 = source_32 = None
    page_info = ""
    pdf_total_chars = 0
    if pdf_path is not None:
        try:
            t31, t32, pinfo, total_chars = _pdf_window_text(pdf_path)
        except Exception as e:
            t31, t32, pinfo, total_chars = None, None, "", 0
            rec["pdf_error"] = str(e)
        pdf_total_chars = total_chars
        page_info = pinfo
        if t31:
            tokens_31, source_31 = t31, "pdf"
        if t32:
            tokens_32, source_32 = t32, "pdf"

    if tokens_31 is None or tokens_32 is None:
        md_path = find_md(period, code)
        if md_path is not None:
            m31, m32 = _md_window_lines(md_path)
            if tokens_31 is None and m31:
                tokens_31, source_31 = m31, "md_fallback"
                page_info += (";" if page_info else "") + f"31:{md_path.name}"
            if tokens_32 is None and m32:
                tokens_32, source_32 = m32, "md_fallback"
                page_info += (";" if page_info else "") + f"32:{md_path.name}"

    if tokens_31 is None and tokens_32 is None:
        rec.update(status="not_found",
                    detail=f"no usable text for either sub-table: pdf={'present' if pdf_path else 'missing'} chars={pdf_total_chars}, md checked")
        diagnostics.append(rec)
        return []

    lines_31 = _normalize_aliases(_merge_fragments(_dedupe_doubled_lines(tokens_31))) if tokens_31 else []
    lines_32 = _normalize_aliases(_merge_fragments(_dedupe_doubled_lines(tokens_32))) if tokens_32 else []

    scale, unit_label = 1.0, "억원"
    if source_32 == "pdf" and lines_32:
        scale, unit_label = _detect_unit_scale(lines_32)
    elif source_31 == "pdf" and lines_31:
        scale, unit_label = _detect_unit_scale(lines_31)

    vals31, ev31 = _parse_31_lines(lines_31) if lines_31 else ({}, {"note": "3-1 window not located"})
    if lines_32:
        vals32, status32, detail32, extra_labels32 = _parse_32_lines(lines_32)
    else:
        vals32, status32, detail32, extra_labels32 = {}, "not_found", "3-2 window not located", {}

    meta = registry.get(code)
    if meta is None:
        meta = _registry_fallback_from_filename(pdf_path or (find_md(period, code) or Path(code)))

    out_rows = []

    def _mk(item_no, name, section, level, raw_val):
        if raw_val is None:
            return
        eok = raw_val if section == SEC_31 and item_no == 3 else raw_val / scale
        out_rows.append({
            "원보험사코드": code,
            "원수사명": meta["원수사명"],
            "티커": meta["티커"],
            "생손보여부": meta["생손보여부"],
            "항목번호": item_no,
            "항목명": name,
            "섹션": section,
            "레벨": level,
            "공시분기": quarter,
            "값": round(eok, 6) if isinstance(eok, float) else eok,
        })

    for item_no, (name, level) in ITEM_31.items():
        _mk(item_no, name, SEC_31, level, vals31.get(item_no))

    if status32 == "ok":
        for row_idx, (cat, leaf, level) in enumerate(ROW32):
            row_no = row_idx + 1
            name = f"{cat}_{leaf}" if cat else leaf
            _mk(100 + row_no, f"{name}(공정가액)", SEC_32, level, vals32.get(100 + row_no))
            _mk(200 + row_no, f"{name}(평가손익)", SEC_32, level, vals32.get(200 + row_no))
        for row_no, name in extra_labels32.items():
            _mk(100 + row_no, f"{name}(공정가액)", SEC_32, 2, vals32.get(100 + row_no))
            _mk(200 + row_no, f"{name}(평가손익)", SEC_32, 2, vals32.get(200 + row_no))

    n31 = len(vals31)
    rec.update(
        status="ok" if (n31 == 3 and status32 == "ok") else ("partial" if (n31 > 0 or status32 == "ok") else "not_found"),
        source_31=source_31, source_32=source_32, page_info=page_info, unit=unit_label,
        n31_found=n31, status32=status32, detail32=detail32,
        rows_emitted=len(out_rows),
    )
    diagnostics.append(rec)
    return out_rows


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def _codes_for_period(period: str):
    md_dir = MD_INBOX / period
    codes = set()
    if md_dir.is_dir():
        for p in md_dir.glob("KR*_*.md"):
            m = re.match(r"^(KR\d+)_", p.name)
            if m:
                codes.add(m.group(1))
    for sub in ("pdf", "raw"):
        d = DISCLOSURE / period / sub
        if d.is_dir():
            for p in d.glob("KR*_*.pdf"):
                m = re.match(r"^(KR\d+)_", p.name)
                if m:
                    codes.add(m.group(1))
    return sorted(codes)


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", action="append", help="e.g. FY2026_Q2 (repeatable)")
    ap.add_argument("--all-periods", action="store_true")
    ap.add_argument("--company", action="append", help="restrict to these KR codes")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--write", dest="dry_run", action="store_false")
    args = ap.parse_args(argv)

    if args.all_periods:
        periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q?") if p.is_dir())
    elif args.period:
        periods = args.period
    else:
        periods = ["FY2026_Q2"]

    registry = build_registry()

    existing_rows = []
    existing_keys = set()
    if JSON_PATH.exists():
        existing_rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        existing_keys = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in existing_rows}
        print(f"existing asset_quality.json: {len(existing_rows)} rows")

    all_diag = []
    new_rows = []
    for period in periods:
        codes = args.company if args.company else _codes_for_period(period)
        print(f"\n=== {period}: {len(codes)} companies ===")
        for code in codes:
            rows = extract_company_quarter(code, period, registry, all_diag)
            for r in rows:
                key = (r["원보험사코드"], r["항목번호"], r["공시분기"])
                if key in existing_keys:
                    continue
                new_rows.append(r)
                existing_keys.add(key)

    ok = sum(1 for d in all_diag if d.get("status") == "ok")
    partial = sum(1 for d in all_diag if d.get("status") == "partial")
    nf = sum(1 for d in all_diag if d.get("status") == "not_found")
    scan_exc = sum(1 for d in all_diag if d.get("status") == "scan_exception")
    print(f"\n=== summary: ok={ok} partial={partial} not_found={nf} scan_exception={scan_exc} (total={len(all_diag)}) ===")
    for d in all_diag:
        if d.get("status") != "ok":
            print(f"  [{d.get('status')}] {d['code']} {d['period']}: {d.get('detail') or d.get('detail32') or d.get('status32')}")

    DIAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIAG_PATH.write_text(json.dumps(all_diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ndiagnostics written: {DIAG_PATH} ({len(all_diag)} entries)")

    print(f"\nnew rows to add: {len(new_rows)}")
    if args.dry_run:
        print("(dry-run; no write. pass --write to persist)")
        return 0

    all_rows = existing_rows + new_rows
    JSON_PATH.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {JSON_PATH} ({len(all_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
