# -*- coding: utf-8 -*-
"""
Extract two sections of the K-ICS 정기경영공시 (management disclosure) PDFs into a new
master JSON, separate from kics_disclosure.json:

  2-4  회계모형별, 포트폴리오별 보험부채 현황   (insurance liability by IFRS17 measurement
                                                model: GMM/일반모형, VFA/변동수수료접근법,
                                                PAA/보험료배분접근법)
  2-5  무·저해지상품 해지율 예외모형 사용에 관한 사항 (lapse-rate exception-model usage for
                                                no-lapse/low-lapse products)

Source of truth is the raw PDF (data/disclosure/<period>/pdf/), read via pdfplumber's
page.extract_text(). This is deliberate, not an oversight of the Docling MD pipeline:
reconnaissance on 2026.2Q (36 companies) showed
  - Docling's keyword-window page selection drops these sections entirely for several
    companies even though the PDF has a clean native text layer (KR0032/NH농협손해,
    KR0069/삼성생명, KR0073/교보생명, KR0094/신한라이프, KR0150/서울보증, plus 2-5-only
    drops for KR0068/KR0070/KR0072/KR0097/KR0099) -- same failure class already flagged
    against 6-4 시장위험 in inbox/parser/20260831T0700Z.
  - Docling embeds the 2-4 table as a picture (`<!-- image -->`) instead of markdown for
    at least KR0050/KR0051, even though the PDF text layer is intact.
  - Character-variant dot glyphs (∙ U+2219 vs · U+00B7 vs ㆍ U+318D) and at least one
    scrambled reading-order case (KR1098) make plain-text MD regex matching fragile.
  - pdfplumber's own extract_tables() grid detector silently DROPS the PAA-only "일반"/
    "자동차" rows for at least KR0002 (confirmed: extract_text() shows "일반 - - - 3,554"
    / "자동차 - - - 5,549" / "합계 47,591 9,342 44,204 9,103" where 3,554+5,549=9,103,
    but extract_tables() returns only 16 rows ending in an unlabeled, PAA-blank total).
    extract_text() preserved correct left-to-right, top-to-bottom reading order in every
    sampled case (including KR0051, once its one-token-off 합계 row was understood -- see
    the L=8 note in COL_MAP below), so it is the primary path.

SCOPE DECISION (read before extending): this extractor captures model-level GRAND TOTALS
per company/quarter -- (GMM,VFA)x(BEL,RA,CSM) + PAA + grand total -- not the individual
product-type detail rows (무배당상해/무배당질병/... x Non-Par/Indirect-Par/Direct-Par).
Rationale: product-type vocabulary differs materially between life and non-life insurers
and between companies (dozens of distinct labels), several companies lose the 구분
(portfolio-group) label to merged-cell blanking on extraction, and a stable cross-company
item catalog at that granularity would be sparse and hard to census cleanly. The 합계
(grand total) row is present, uniquely identifiable, and internally self-checking (its
values equal the sum of the detail rows in every case verified during reconnaissance) --
it is the right unit for "measurement-model composition" analysis and for the item20
cross-check this master exists to support. See TODO_parser_kics.md for the full writeup.

Schema (mirrors IFRS17_BS.json exactly):
  원보험사코드, 원수사명, 티커, 생손보여부, 항목번호, 항목명, 섹션, 레벨, 공시분기, 값

Item catalog (registered once, do not silently renumber -- see ITEM_CATALOG below):
   1 일반모형_최선추정부채        보험부채_모형별구성   L2
   2 일반모형_위험조정            보험부채_모형별구성   L2
   3 일반모형_보험계약마진        보험부채_모형별구성   L2
   4 변동수수료접근법_최선추정부채 보험부채_모형별구성  L2
   5 변동수수료접근법_위험조정     보험부채_모형별구성  L2
   6 변동수수료접근법_보험계약마진 보험부채_모형별구성  L2
   7 보험료배분접근법_보험부채     보험부채_모형별구성  L2
   8 보험부채_합계                 보험부채_모형별구성   L1  (disclosed 합계 row; if the row
                                                        itself is unlabeled/blank, computed
                                                        as sum(1..7))
   9 해지율_예외모형_사용여부      해지율_예외모형       L1  (0=해당사항 없음/원칙모형만 사용,
                                                        1=예외모형 실사용 확인)

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/extract_insurance_liability_portfolio.py --period FY2026_Q2 --dry-run
  ... --period FY2026_Q2                     (writes insurance_liability_portfolio.json)
  ... --all --dry-run                        (all periods under md_inbox/, dry-run)
  ... --all --out insurance_liability_portfolio.json

This script only READS md_inbox/ (company roster per period, via filenames only -- never
parses MD content) and data/disclosure/<period>/{pdf,raw}/ (actual extraction source), plus
kics_disclosure.json once to borrow the static company-code/name/ticker/생손보여부 registry.
It only WRITES the single output JSON named by --out (default: repo-root
insurance_liability_portfolio.json). It never touches kics_disclosure.json, IFRS17_BS.json,
PL_breakdown.json, CSM_waterfall.json, or any MD file.

A small number of (company,quarter) cells need a fallback from the "plain 2-4/2-5 header,
7-column 합계 row" happy path. All of these were found by actually reconciling a company's
extracted total against the sum of its own detail rows (or against IFRS17_BS item20), not
guessed -- see the inline comments at each site for the specific evidence:
  - L=1 trailing-number run (COL_MAP): a company whose whole GMM/VFA product-detail grid
    is blank (KR0150/서울보증보험, KR1011/IBK연금보험) -- the lone number after 합계 is
    item7 (PAA), not item1.
  - L=8 trailing-number run (COL_MAP): one spurious leading token before an otherwise
    normal 7-column row (KR0051/신한이지손해보험) -- confirmed by hand-summing the detail
    rows' GMM_BEL column, which matches run[1], not run[0].
  - full_doubling: some filers double EVERY character uniformly, digits and punctuation
    included, not just CJK labels (KR0075/비엔피파리바카디프생명보험) -- detected via a
    doubled open-paren near the unit marker, then collapsed before number parsing.
  - The "2-" chapter prefix on section headers is itself optional (KR0087/동양생명 numbers
    sections "1./2./3./4./5." with no chapter-dot notation at all).
  - try_narrative_fallback(): when the table itself can't be located/parsed at all, some
    filers restate the same breakdown in prose inside "2-2 재무정보 요약사항 기술"
    (KR0009/현대해상, whose table extracts as scrambled vertical-reading-order garbage in
    at least one quarter). Lower precision (0.1조 = 1,000억), tagged status='low_confidence'
    but still emitted as real rows -- see extract_period().
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

REPO_ROOT = Path(__file__).resolve().parents[1]
MD_INBOX = REPO_ROOT / "md_inbox"
DISCLOSURE_DIR = REPO_ROOT / "data" / "disclosure"
KICS_DISCLOSURE = REPO_ROOT / "kics_disclosure.json"

# ---------------------------------------------------------------------------
# Item catalog (stable; extend by appending, never renumber existing entries)
# ---------------------------------------------------------------------------
SECTION_24 = "보험부채_모형별구성"
SECTION_25 = "해지율_예외모형"

ITEM_CATALOG = {
    1: ("일반모형_최선추정부채", SECTION_24, 2),
    2: ("일반모형_위험조정", SECTION_24, 2),
    3: ("일반모형_보험계약마진", SECTION_24, 2),
    4: ("변동수수료접근법_최선추정부채", SECTION_24, 2),
    5: ("변동수수료접근법_위험조정", SECTION_24, 2),
    6: ("변동수수료접근법_보험계약마진", SECTION_24, 2),
    7: ("보험료배분접근법_보험부채", SECTION_24, 2),
    8: ("보험부채_합계", SECTION_24, 1),
    9: ("무저해지상품_해지율_예외모형_사용여부", SECTION_25, 1),
}

# ---------------------------------------------------------------------------
# Company registry (read-only borrow from kics_disclosure.json; company code/
# name/ticker/생손보여부 are static identity fields, not this-quarter data, so
# reading them concurrently with another session's data edits is safe).
# ---------------------------------------------------------------------------


def load_company_registry() -> dict:
    registry = {}
    if not KICS_DISCLOSURE.exists():
        return registry
    with open(KICS_DISCLOSURE, encoding="utf-8") as f:
        data = json.load(f)
    for r in data:
        code = r.get("원보험사코드")
        if code and code not in registry:
            registry[code] = {
                "원수사명": r.get("원수사명"),
                "티커": r.get("티커"),
                "생손보여부": r.get("생손보여부"),
            }
    return registry


FILENAME_RE = re.compile(r"^(KR\d+)_(.+)$")


def parse_company_from_filename(path: Path) -> tuple:
    m = FILENAME_RE.match(path.stem)
    if not m:
        return None, None
    return m.group(1), m.group(2)


# ---------------------------------------------------------------------------
# PDF location helpers
# ---------------------------------------------------------------------------


def find_pdf_for_company(period: str, code: str, name_hint: str) -> Path | None:
    # Newer periods (>=FY2026_Q1) store PDFs under pdf/; older periods (FY2023_Q1..
    # FY2025_Q4) use raw/ instead -- both are checked, pdf/ first.
    for subdir in ("pdf", "raw"):
        d = DISCLOSURE_DIR / period / subdir
        if not d.exists():
            continue
        candidates = list(d.glob(f"{code}_*.pdf"))
        if candidates:
            return candidates[0]
    return None


def flex_cjk(s: str) -> str:
    """Build a regex fragment from a literal string, tolerant of two independent PDF
    text-extraction artifacts: (1) each character may appear 1 or 2 times consecutively
    -- a document-wide rendering bug confirmed on KR0068/한화생명's PDF, most likely a
    fake-bold double-strike in the source content stream ('회계모형별' ->
    '회회계계모모형형별별', '단위' -> '단단위위'); (2) arbitrary whitespace (including a
    hard line-wrap) may appear between any two characters, confirmed on KR0009/현대해상's
    prose narrative where a line break happened to fall mid-word ('보험계약마진' ->
    '보험계\n약마진'). Numbers are NOT affected by either (checked directly: '64,609'
    renders normally), so this is only used to build header/label/narrative-prose
    regexes, never for number-token parsing."""
    return "".join(f"{re.escape(c)}{{1,2}}\\s*" for c in s)


def dedupe_cjk_run(s: str) -> str:
    """Collapse doubled-character runs for containment checks on an already-isolated
    text window (e.g. the 2-5 N/A-phrase check). Never applied to number-bearing
    text: digits/commas/periods/whitespace are excluded from the collapse."""
    return re.sub(r"([^\d,.\s])\1", r"\1", s)


# Section-24 header: "2-4" / "2- 4" / "2-4)" / "2-4 )" / "2-4." followed (within a small
# window) by "회계모형별" or "포트폴리오별". Docling MD used a similar but not identical
# set of variants; PDF native text has shown fewer surprises but we still normalize
# whitespace before matching. flex_cjk() makes each matcher tolerant of the KR0068
# character-doubling bug without needing to pre-transform (and shift the positions of)
# the source text.
#   The numeral prefix itself needs the same doubling tolerance as the Korean text --
#   confirmed on KR0075/비엔피파리바카디프생명보험 2025.1Q, where the ENTIRE document
#   (not just this section) is character-doubled, including the section number itself:
#   "2-4." renders as "22--44.." (every character, digits and punctuation alike, doubled).
#   A hand-written r"2\s*-\s*4" prefix does not tolerate that, so flex_cjk("2-4") is used
#   instead of writing the numeral matcher by hand -- flex_cjk() is character-generic, not
#   CJK-specific despite the name.
# The numeral prefix is dropped entirely, not just the "2-" chapter part -- it turns out
# to vary too much across document templates to enumerate:
#   - "2-4." / "2- 4." / "2-4)" -- the ordinary quarterly 정기경영공시 (most companies).
#   - bare "4." with no chapter prefix -- KR0087/동양생명 numbers its whole document
#     "1./2./3./4./5." with no chapter-dot notation, confirmed on its 2025.1Q filing
#     (620 chars/page avg, clean text layer; the "2-4"-requiring pattern missed it
#     entirely even though nothing was wrong with the PDF).
#   - "2) 회계모형별..." as a numbered SUB-item, several sections deep -- KR0001 and
#     (going by the 2025.4Q dry run) apparently every other company's Q4 filing uses a
#     completely different, much longer annual "결산" template (130 pages vs the
#     quarterly template's ~20-70) with its own unrelated top-level numbering ("2-4."
#     means "조직" / organization chart there, not this section at all); the real
#     target only shows up nested as an unenumerated-at-the-top-level "2)" under some
#     "4-x" heading.
# Given the numeral position/format is this template-dependent, matching is anchored
# on the compound keyword phrase alone ("회계모형별" / "포트폴리오별" for 2-4; the full
# "무(·)저해지" -- not just "무" -- for 2-5, since a bare "무" is one character away
# from accidentally matching a "무배당..." product-detail row label). The "단위"-nearby
# TOC-guard below is what keeps this from firing on a 목차 (table of contents) listing.
RE_HEADER_24 = re.compile(
    "(?:" + flex_cjk("회계모형별") + "|" + flex_cjk("포트폴리오별") + ")"
)
RE_HEADER_25 = re.compile(
    flex_cjk("무") + r"[·∙ㆍ.]{0,2}\s*" + flex_cjk("저해지")
)
RE_UNIT_MARKER = re.compile(flex_cjk("단위"))

RE_VFA = re.compile(flex_cjk("변동수수료접근법"))
RE_PAA = re.compile(flex_cjk("보험료") + r"\s*" + flex_cjk("배분") + r"\s*" + flex_cjk("접근법"))

# "합 계" with an explicit space (confirmed on KR0032/KR0050/KR0094/KR0099 -- a real
# formatting variant, not the doubling bug) needs \s* between the two chars, same as
# it did before the flex_cjk rewrite; keep both tolerances at once.
RE_TOTAL_LABEL = re.compile(
    flex_cjk("합") + r"\s*" + flex_cjk("계") + "|" + flex_cjk("합") + r"\s*" + flex_cjk("산")
)

# A standalone dash used as "blank/N.A." placeholder in these tables.
DASH_ONLY_RE = re.compile(r"^[\-\u2013\u2014]$")

NA_PHRASES = [
    "해당사항 없음", "해당사항없음", "해당 사항 없음", "해당 없음",
    "해당사항이 없습니다", "해당사항 없습니다", "해당 없습니다",
    "원칙모형", "예외모형을 사용하지 않아", "가이드라인을 준용",
]


def parse_number(tok: str) -> float | None:
    """Parse a single numeric token from these tables. '-' alone => 0 (blank cell).
    '△123' / '-123' / '(123)' => negative. Returns None if not parseable."""
    tok = tok.strip()
    if not tok:
        return None
    if DASH_ONLY_RE.match(tok):
        return 0.0
    neg = False
    t = tok
    if t.startswith("△"):
        neg = True
        t = t[1:]
    if t.startswith("(") and t.endswith(")"):
        neg = True
        t = t[1:-1]
    if t.startswith("-"):
        neg = True
        t = t[1:]
    t = t.replace(",", "")
    if not t or not re.match(r"^\d+(\.\d+)?$", t):
        return None
    val = float(t)
    return -val if neg else val


RE_UNIT_100M = re.compile(flex_cjk("억원"))
RE_UNIT_MM = re.compile(flex_cjk("백만원"))
RE_UNIT_K = re.compile(flex_cjk("천원"))


def detect_unit_divisor(window_text: str) -> tuple:
    """Return (divisor_to_억원, unit_label). Table-window detection only -- never
    infer unit from page-level text (억원/백만원/천원 all coexist across sections
    of the same PDF page in some filings). flex_cjk-built patterns so the KR0068
    character-doubling bug ("(단단위위 : 억억원원)") doesn't defeat unit detection."""
    if RE_UNIT_MM.search(window_text):
        return 100.0, "백만원"
    if RE_UNIT_K.search(window_text):
        return 100000.0, "천원"
    if RE_UNIT_100M.search(window_text):
        return 1.0, "억원"
    return 1.0, "unknown(assumed 억원)"


RE_NARRATIVE = re.compile(
    flex_cjk("잔여보장요소는") + r"([△\-]?[\d.,]+)\s*" + flex_cjk("조원") + r".{0,30}?"
    + flex_cjk("최선추정부채") + r"([△\-]?[\d.,]+)\s*" + flex_cjk("조원") + r".{0,10}?"
    + flex_cjk("위험조정") + r"([△\-]?[\d.,]+)\s*" + flex_cjk("조원") + r".{0,10}?"
    + flex_cjk("보험계약마진") + r"([△\-]?[\d.,]+)\s*" + flex_cjk("조원") + r".{0,10}?"
    + flex_cjk("보험료배분접근법") + flex_cjk("적용") + r"([△\-]?[\d.,]+)\s*" + flex_cjk("조원")
)


def _parse_jo(tok: str) -> float:
    """'25.9' (조원, trillion won) -> 259000.0 (억원). Same sign handling as
    parse_number, just without the comma-thousands / dash-as-blank cases (this
    narrative always writes plain decimals)."""
    neg = tok.startswith("△") or tok.startswith("-")
    t = tok.lstrip("△-").replace(",", "")
    return (-1 if neg else 1) * float(t) * 10000.0


def try_narrative_fallback(page_texts: dict) -> dict | None:
    """Look for the '2-2 재무정보 요약사항 기술' narrative that restates the 2-4
    breakdown in prose ('...잔여보장요소는 X조원으로 최선추정부채 Y조원, 위험조정
    Z조원, 보험계약마진 W조원, 보험료배분접근법 적용 V조원입니다.'). Only used when
    the table itself could not be located/parsed. Confirmed present verbatim on
    KR0009/현대해상 2026.2Q p.7; not confirmed elsewhere, so this is a narrow,
    single-purpose fallback, not a general parser."""
    for t in page_texts.values():
        m = RE_NARRATIVE.search(t)
        if m:
            gmm_bel = _parse_jo(m.group(2))
            gmm_ra = _parse_jo(m.group(3))
            gmm_csm = _parse_jo(m.group(4))
            paa = _parse_jo(m.group(5))
            values = {1: gmm_bel, 2: gmm_ra, 3: gmm_csm, 4: 0.0, 5: 0.0, 6: 0.0, 7: paa}
            return {"values": values, "total": sum(values.values()), "raw": m.group(0)}
    return None


# ---------------------------------------------------------------------------
# Table checks added 2026-10-11 (ticket 20261011T0320Z stage 5; defects 3, 5, 6a, 8 of ilp_gap_runlog_textlayer_20261010.md).  None of them changes a value that was
# read before: they repair a run that was no known layout, report a footing, or name a candidate table without emitting it.
# ---------------------------------------------------------------------------
# a number split by a space in the text layer: '1 3,601' = 13,601, '6 ,876' = 6,876
RE_SPLIT_DIGITS = re.compile(r"(?<![\d,])(\d)\s+(\d{1,2},\d{3}|,\d{3})(?![\d,])")
RE_TAIL_NUMS = re.compile(r"((?:\s+(?:△?\(?-?\d[\d,]*(?:\.\d+)?\)?|-))+)\s*$")
RE_ONE_NUM = re.compile(r"△?\(?-?\d[\d,]*(?:\.\d+)?\)?|-")


def _tail_numbers(line: str):
    """the trailing number tokens of one text line ('-' = 0), or None when fewer than 3"""
    m = RE_TAIL_NUMS.search(" " + line.rstrip())        # the leading blank: a line that STARTS with its first number ('(45.69) 6.35 35.93') must not lose that number
    if not m:
        return None
    toks = RE_ONE_NUM.findall(m.group(1))
    if len(toks) < 3:
        return None
    nums = []
    for t in toks:
        v = parse_number(t)
        if v is None:
            return None
        nums.append(v)
    return nums


def _slots_by_len(nums):
    """the stage-1 column rule applied to ONE row: 7 = GMM BEL/RA/CSM + VFA BEL/RA/CSM + PAA, 6 = no PAA, 4 = GMM + PAA, 3 = GMM only, 8 = one stray leading token"""
    n = len(nums)
    if n == 1:                                           # 합계 run of a filer with PAA only (KR0150): the lone number is the PAA column
        return {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: nums[0]}
    if n == 8:
        nums, n = nums[1:], 7
    if n == 7:
        return {i + 1: nums[i] for i in range(7)}
    if n == 6:
        return {**{i + 1: nums[i] for i in range(6)}, 7: 0.0}
    if n == 4:
        return {1: nums[0], 2: nums[1], 3: nums[2], 4: 0.0, 5: 0.0, 6: 0.0, 7: nums[3]}
    if n == 3:
        return {1: nums[0], 2: nums[1], 3: nums[2], 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0}
    return None


def footing_of(seg: str, values: dict) -> dict:
    """detail rows of the text segment (each placed by its own token count) vs the 합계 slots (printed units).  {'ok', 'n_rows', 'diffs'}; tolerance 0.5 per row + 1.
    A row of exactly THREE numbers is ambiguous (GMM BEL/RA/CSM, or VFA BEL/RA/CSM when the filer leaves the GMM cells blank: IBK연금 변액연금 row): every assignment of
    the 3-number rows is tried (up to 12 rows, else all GMM) and the table foots when ANY assignment foots."""
    import itertools
    fixed = {i: 0.0 for i in range(1, 8)}
    amb, n = [], 0
    for ln in seg.split("\n"):
        nums = _tail_numbers(ln)
        if nums and len(nums) == 3:
            amb.append(nums)
            n += 1
            continue
        sl = _slots_by_len(nums) if nums else None
        if not sl:
            # the PAA-only rows of some filers print ONE number ('일반 8,560', '자동차 -20.90'): that number is the 보험료배분접근법 column
            m1 = re.match(r"^\s*(?:일반|자동차)\s+(△?\(?-?\d[\d,]*(?:\.\d+)?\)?)\s*$", ln)
            v1 = parse_number(m1.group(1)) if m1 else None
            if v1 is not None:
                sl = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: v1}
        if sl:
            n += 1
            for i in range(1, 8):
                fixed[i] += sl[i]
    if n == 0:
        return {"ok": None, "n_rows": 0}
    tol = 0.5 * n + 1.0
    best = None
    masks = itertools.product((0, 1), repeat=len(amb)) if len(amb) <= 12 else [(0,) * len(amb)]
    for mask in masks:
        sums = dict(fixed)
        for row, to_vfa in zip(amb, mask):
            off = 4 if to_vfa else 1
            for k in range(3):
                sums[off + k] += row[k]
        diffs = {i: round(sums[i] - values[i], 4) for i in range(1, 8)}
        ok = all(abs(d) <= tol for d in diffs.values())
        if best is None or ok or sum(abs(d) for d in diffs.values()) < sum(abs(d) for d in best[1].values()):
            best = (ok, diffs)
        if ok:
            break
    return {"ok": best[0], "n_rows": n, "diffs": best[1]}


def find_table_by_footing(page_texts: dict, max_page: int = 25, min_rows: int = 8):
    """defect 5: a filing whose 2-4 HEADER is an image (AIA) never matches RE_HEADER_24, although the numbers are text.  Look for a 합계 line with a 6/7/8-token run whose
    column sums equal the rows above it on the same page (>= min_rows rows) -- a 7 x ~40 table that foots is not an accident.  Returns the candidate when EXACTLY ONE page
    holds one, else None.  The unit is unknown (it sat in the image), so the caller never emits the values."""
    found = []
    for pi in sorted(page_texts):
        if pi >= max_page:
            break
        lines = page_texts[pi].split("\n")
        for k, ln in enumerate(lines):
            m = RE_TOTAL_LABEL.search(ln)
            if not m:
                continue
            run = _tail_numbers("x " + ln[m.end():])           # the 합계 numbers (a leading token keeps the tail regexp honest)
            if not run or len(run) not in (6, 7, 8):
                continue
            tot = _slots_by_len(run)
            rows = [_slots_by_len(nm) for nm in (_tail_numbers(x) for x in lines[max(0, k - 120):k]) if nm]
            rows = [r for r in rows if r]
            if len(rows) < min_rows:
                continue
            sums = {i: sum(r[i] for r in rows) for i in range(1, 8)}
            tol = 0.5 * len(rows) + 1.0
            if all(abs(sums[i] - tot[i]) <= tol for i in range(1, 8)):
                found.append({"page": pi + 1, "n_rows": len(rows), "run": run, "values_printed_units": tot})
    return found[0] if len(found) == 1 else None


# ---------------------------------------------------------------------------
# Text layer with a fitz fallback (ticket 20261011T0320Z stage 5, defect 1 of ilp_gap_runlog_textlayer_20261010.md):
# pdfplumber alone turned every 'Unexpected EOF' PDF into a whole-filing not_found.  The fallback only runs where pdfplumber raises, so every
# filing that read fine before reads byte-identically now.
# ---------------------------------------------------------------------------
def _fitz_page_text(doc, i: int) -> str:
    """one page rebuilt row-wise from fitz words (top-to-bottom, left-to-right: the reading order pdfplumber's extract_text() gives)"""
    rows = []                                   # [mean y, [words]]
    for w in sorted(doc[i].get_text("words"), key=lambda w: ((w[1] + w[3]) / 2.0, w[0])):
        yc = (w[1] + w[3]) / 2.0
        if rows and abs(rows[-1][0] - yc) <= 2.5:
            rows[-1][1].append(w)
            rows[-1][0] = (rows[-1][0] * (len(rows[-1][1]) - 1) + yc) / len(rows[-1][1])
        else:
            rows.append([yc, [w]])
    return "\n".join(" ".join(x[4] for x in sorted(r[1], key=lambda x: x[0])) for r in rows)


class _Page:
    def __init__(self, owner, i, page=None):
        self.owner, self.i, self.page = owner, i, page

    def extract_text(self):
        if self.page is not None:
            try:
                return self.page.extract_text() or ""
            except Exception:  # noqa: BLE001  (pdfminer 'Unexpected EOF' and friends)
                self.owner.fallback_pages.append(self.i + 1)
        return _fitz_page_text(self.owner.fitz_doc(), self.i)


class _Pdf:
    """pdfplumber document whose pages fall back to fitz word rows when pdfplumber raises; the whole file falls back when pdfplumber cannot open it"""

    def __init__(self, path):
        self.path, self._fz, self.fallback_pages, self.open_error = path, None, [], None
        try:
            self._pl = pdfplumber.open(path)
            self.pages = [_Page(self, i, p) for i, p in enumerate(self._pl.pages)]
            self.source = "pdfplumber"
        except Exception as e:  # noqa: BLE001
            self._pl, self.open_error, self.source = None, repr(e)[:120], "fitz"
            self.pages = [_Page(self, i) for i in range(self.fitz_doc().page_count)]

    def fitz_doc(self):
        if self._fz is None:
            import fitz
            self._fz = fitz.open(str(self.path))
        return self._fz

    def close(self):
        if self._pl is not None:
            self._pl.close()
        if self._fz is not None:
            self._fz.close()


def extract_section_24_25(pdf_path: Path) -> dict:
    """Returns a dict with keys:
       status: 'ok' | 'scan_only' | 'not_found' | 'low_confidence' | 'image_header_candidate'
       values: {1..7: float}  (present only if status in ok/low_confidence)
       total_disclosed: float | None   (the literal 합계 row sum, if found)
       na_25: 0 | 1 | None
       unit: str
       evidence: str  (short human-readable trail for the '근거' the task demands)
       text_source / footing / candidate: added 2026-10-11 (informational; never change values)
    """
    result = {
        "status": "not_found",
        "values": {},
        "total_disclosed": None,
        "na_25": None,
        "unit": None,
        "evidence": "",
    }
    try:
        pdf = _Pdf(pdf_path)
    except Exception as e:  # noqa: BLE001
        result["evidence"] = f"PDF open error: {e}"
        return result

    try:
        n_pages = len(pdf.pages)
        # Every quarterly-template company sampled during reconnaissance carries 2-4
        # within pages 6-11 (1-indexed); cap the prefix scan well above that instead of
        # extract_text()-ing an entire filing. Some of these PDFs bundle the full
        # 재무제표 주석 afterwards (KR0002 runs 280+ pages) -- walking every page there
        # was why the first dry-run on all 36 companies did not finish inside several
        # minutes. Raised from 25 to 40 after KR0001's FY2025_Q4 filing turned out to be
        # a completely different, much longer annual "결산" template (130 pages) with
        # the target section nested at page 29 -- past the original cap, and the filing
        # came back "not_found" despite a perfectly clean text layer.
        PREFIX_CAP = 40
        prefix_n = min(n_pages, PREFIX_CAP)
        page_texts = {}
        start_page = None
        start_hdr_pos = 0           # offset of the section header inside the text of start_page (the 합계 search and the unit window start THERE, not at the page top)
        for i in range(prefix_n):
            t = pdf.pages[i].extract_text() or ""
            page_texts[i] = t
            m24 = RE_HEADER_24.search(t)
            if m24:
                # Guard against the 목차 (table of contents) page: it lists "2-4.
                # 회계모형별, 포트폴리오별 보험부채 현황" and "2-5. ..." as plain entries
                # right next to several other N-M section numbers, with none of the
                # unit/caption furniture the real section always carries. Confirmed
                # false-positive on KR0069/삼성생명 (TOC on PDF page 2 matched before
                # the real table on page 9). A genuine section header is always
                # followed within a couple hundred characters by the unit marker
                # "단위" (단위: 억원/백만원/천원); require it before accepting.
                # The window must be allowed to spill onto the NEXT page: confirmed on
                # KR0087/동양생명 2025.1Q, whose header ("4. 회계모형별, 포트폴리오 별
                # 보험부채 현황") sits right at the bottom of a page with only a caption
                # line after it, while "(단위:억원)" is the very first line of the next
                # page -- a same-page-only window rejected the real match as a false
                # positive and this company's whole filing came back "not_found" even
                # though the text layer was clean (620 chars/page avg, no scan issue).
                window = t[m24.start(): m24.start() + 250]
                if len(window) < 250 and i + 1 < prefix_n:
                    if (i + 1) not in page_texts:
                        page_texts[i + 1] = pdf.pages[i + 1].extract_text() or ""
                    window += page_texts[i + 1][:250 - len(window)]
                if RE_UNIT_MARKER.search(window):
                    start_page = i
                    start_hdr_pos = m24.start()
                    break
                # else: TOC-like false positive -- keep scanning subsequent pages.

        if start_page is None:
            # Table header not found -- before giving up, try the narrative fallback:
            # some filers restate the same breakdown in prose inside "2-2. 재무정보
            # 요약사항 기술" (e.g. KR0009/현대해상 2026.2Q, whose 2-4 table extracts as
            # scrambled vertical-reading-order garbage on PDF page 10 -- "2-4. 회계모형별,
            # 포트폴리오별 보험부채 현황\n- 10 -\n<\n*\n2\n상\n장\n주\n0 2\n품 유\n..." -- but
            # page 7's narrative reads cleanly: "보험계약부채 중 잔여보장요소는 25.9조원으로
            # 최선추정부채 10.6조원, 위험조정 1.7조원, 보험계약마진 9.9조원, 보험료배분접근법
            # 적용 3.7조원입니다."). Lower precision (rounded to 0.1조 = 1,000억) than the
            # table path, so it's tagged 'low_confidence' rather than 'ok' even on a hit.
            narrative = try_narrative_fallback(page_texts)
            if narrative is not None:
                result["status"] = "low_confidence"
                result["unit"] = "억원(narrative, 0.1조 precision)"
                result["values"] = narrative["values"]
                result["total_disclosed"] = narrative["total"]
                result["evidence"] = (
                    "table header not matched; recovered from '2-2 재무정보 요약사항 "
                    f"기술' narrative prose instead (lower precision): {narrative['raw']}"
                )
                # 2-5 is a separate, usually-short section that may still be intact even
                # when 2-4's table is scrambled -- reuse the already-read prefix pages.
                for t in page_texts.values():
                    m25 = RE_HEADER_25.search(t)
                    if m25:
                        w = t[m25.start(): m25.start() + 300]
                        w_dd = dedupe_cjk_run(w)
                        if any(p in w or p in w_dd for p in NA_PHRASES):
                            result["na_25"] = 0
                        result["evidence_25"] = w.replace("\n", " ")[:200]
                        break
                return result

            # defect 5: header text that is an IMAGE (AIA) while the numbers are text -- name the table that foots, but never emit it (the unit sat in the image)
            cand = find_table_by_footing(page_texts)
            if cand is not None:
                result["status"] = "image_header_candidate"
                result["candidate"] = cand
                result["text_source"] = pdf.source
                result["evidence"] = (f"no '2-4 ... 회계모형별/포트폴리오별' header in the text layer (image header?); a table that foots ({cand['n_rows']} rows x {len(cand['run'])} "
                                      f"columns, 합계 run {cand['run']}) sits on page {cand['page']}; unit unknown -> NOT emitted, verify by rendering the page")
                return result

            # Not found in the prefix -- classify scan-only vs genuinely-not-found using
            # only the pages already read (cheap: <=25 extract_text() calls, not n_pages).
            sample_chars = sum(len(t) for t in page_texts.values())
            sample_n = len(page_texts) or 1
            avg = sample_chars / sample_n
            if avg < 20:
                result["status"] = "scan_only"
                result["evidence"] = (
                    f"scan-only guard: {sample_chars} chars / {sample_n} prefix pages "
                    f"= {avg:.1f} avg/page < 20 (n_pages total={n_pages})"
                )
            else:
                result["status"] = "not_found"
                result["evidence"] = (
                    f"no '2-4 ... 회계모형별/포트폴리오별' header in first {prefix_n} "
                    f"pages (avg {avg:.1f} chars/page, so not scan-only -- section may "
                    f"use an unrecognized header variant, or genuinely sits past the cap)"
                )
            return result

        # Accumulate pages forward until we find the FIRST 합계 line (current-quarter
        # table), bounded lookahead so we never wander into the prior-year comparison
        # table or, worse, a deep 재무제표 주석 appendix that repeats a similarly-shaped
        # table under a different unit (confirmed present >100 pages later for KR0002).
        MAX_LOOKAHEAD = 5
        blob_parts = []
        total_line_idx = None
        blob = ""
        for j in range(MAX_LOOKAHEAD):
            pi = start_page + j
            if pi >= n_pages:
                break
            if pi not in page_texts:
                page_texts[pi] = pdf.pages[pi].extract_text() or ""
            blob_parts.append(page_texts[pi])
            blob = "\n".join(blob_parts)
            # defect 2 (ilp_gap_runlog_textlayer_20261010.md): search from the header, not from the page top -- a 합계 of an EARLIER table on the same page was picked (KR1000 4Q)
            m = RE_TOTAL_LABEL.search(blob, start_hdr_pos)
            if m:
                total_line_idx = m.start()
                break

        unit_window = blob[start_hdr_pos: start_hdr_pos + 400]
        divisor, unit_label = detect_unit_divisor(unit_window)
        result["unit"] = unit_label
        result["text_source"] = pdf.source + (f"+fitz(pages {pdf.fallback_pages})" if pdf.fallback_pages else "")

        # Header-text detection of has_vfa/has_paa is kept only as a soft cross-check
        # in the evidence trail -- NOT used to decide column count. Reconnaissance on
        # KR0001/KR0002 showed the wrapped, multi-line table header ("보험료" and
        # "배분접근법" landing on different reconstructed lines, with fragments of
        # *other* header cells interleaved between them) makes substring-proximity
        # detection unreliable in both directions -- it under-fires (KR0002 has real
        # PAA business, 일반 3,554 + 자동차 5,549 = 9,103, confirmed against the actual
        # 합계 row, but RE_PAA did not match the header text before 합계).
        header_window_end = len(blob) if total_line_idx is None else total_line_idx
        header_has_vfa = bool(RE_VFA.search(blob[start_hdr_pos:header_window_end]))
        header_has_paa = bool(RE_PAA.search(blob[start_hdr_pos:header_window_end]))

        if total_line_idx is None:
            result["status"] = "low_confidence"
            result["evidence"] = (
                f"no '합계' line found within {MAX_LOOKAHEAD}-page lookahead from "
                f"page {start_page + 1}; section located but total row unrecoverable"
            )
            return result

        tail = blob[total_line_idx:total_line_idx + 500]
        after_label = RE_TOTAL_LABEL.sub("", tail, count=1)

        # Some documents double EVERY character uniformly -- digits and punctuation,
        # not just CJK labels. Confirmed on KR0075/비엔피파리바카디프생명보험 2025.1Q:
        # '(단위' renders with the PARENTHESIS doubled too ('((단단위위'), and the 합계
        # row's numbers are doubled digit-by-digit ('1122,,886688' -- collapsing pairs
        # gives '12,868', which matches summing the detail rows by hand: 562+35+4,048+
        # 8,223=12,868). This is DIFFERENT from KR0068/한화생명, where CJK doubles but
        # '(' and the 합계 row's numbers stay single ('603,601' prints normally). Collapse
        # is only safe once full doubling is confirmed for THIS document -- doing it
        # blindly would corrupt a genuine repeated digit like the "00" in "1,100" on a
        # normal filing. The doubled-open-paren signature near the unit marker is the
        # detector: KR0068-style (label-only) doubling never doubles '('.
        # (the original signature looked in the first 600 characters of the PAGE; the section header may sit lower on the page, so the window behind the header is looked at too --
        #  an extension only: every document that was detected before is detected now)
        full_doubling = ("((" in blob[:600]) or ("((" in blob[start_hdr_pos: start_hdr_pos + 700])
        if full_doubling:
            after_label = re.sub(r"(.)\1", r"\1", after_label)

        # Sequential walk: consume a maximal run of number-tokens separated only by
        # whitespace, starting right after the '합계' label. This is deliberately NOT
        # re.findall() (which searches the whole 500-char window and previously swept
        # up unrelated digits from footnote markers like '주1)' or page footers like
        # '- 9 -'). Stopping at the first character that cannot start a number token
        # is what keeps those out: the moment we hit prose (a footnote, a new section
        # heading), the run ends.
        # 2026-10-11 (ticket 20261011T0320Z stage 5): the ORIGINAL token below is tried first and its result is kept whenever it is usable.  Repairs are accepted only
        #   (1) when the plain run is NO known layout (a number split by a space '1 3,601' / '6 ,876'; decimals '(673.16) 90.23 319.73' that the old token cut at the dot), or
        #   (2) when the plain run IS a known layout but the detail rows above the 합계 line clearly do not foot to it (KR1011-style L=1 read of '74,076.5 376.8 ...', a page footer
        #       '16 | Page' read as a PAA) AND a repaired reading is a known layout that DOES foot.
        # A table that foots under the plain reading is never touched, so every cell that read right before reads byte-identically now (regression: t111/t112 on 279 cells).
        NUM_PLAIN = re.compile(r"\s*(△?\(?-?[\d][\d,]*\)?|-(?!\d))")
        NUM_ALT = re.compile(r"\s*(△?\(?-?[\d][\d,]*(?:\.\d+)?\)?|-(?!\d))(?![\d,])(?!\s*\|)")     # decimals + page-footer guard ((?![\d,]) keeps '16' from backtracking to '1')
        KNOWN = (1, 3, 4, 6, 7, 8)

        def read_run(text, rx=NUM_PLAIN):
            pos, out = 0, []
            while len(out) < 10:
                m = rx.match(text, pos)
                if not m:
                    break
                v = parse_number(m.group(1))
                if v is None:
                    break
                out.append(v)
                pos = m.end()
            return out

        seg = blob[start_hdr_pos:total_line_idx]
        if full_doubling:
            seg = re.sub(r"(.)\1", r"\1", seg)

        def foot_state(r, repaired=False):
            # True / False / None (not assessable) for a candidate run (printed units)
            sl = _slots_by_len(r) if len(r) in KNOWN else None
            if sl is None:
                return None
            return footing_of(RE_SPLIT_DIGITS.sub(r"\1\2", seg) if repaired else seg, sl).get("ok")

        run = read_run(after_label)
        L = len(run)
        repair_note = ""
        fixed = RE_SPLIT_DIGITS.sub(r"\1\2", after_label)
        cands = [("decimal/footer-aware token", read_run(after_label, NUM_ALT), False)]
        if fixed != after_label:
            cands += [("split-digit repair", read_run(fixed), True), ("split-digit repair + decimal token", read_run(fixed, NUM_ALT), True)]
        cands = [(n, r, rep) for n, r, rep in cands if r and r != run]
        if L not in KNOWN:
            for n, r, rep in cands:
                if len(r) in KNOWN:
                    run, L, repair_note = r, len(r), f" [{n}: {after_label[:60].strip()!r} -> run {r}]"
                    break
        elif cands and foot_state(run) is False:
            hit = next(((n, r) for n, r, rep in cands if len(r) in KNOWN and foot_state(r, rep) is True), None)
            if hit:
                run, L, repair_note = hit[1], len(hit[1]), f" [{hit[0]}: plain run did not foot, repaired run does: {hit[1]}]"
            else:
                # a differing parse exists (decimals / footer / split digits) and the plain reading does not foot: the plain reading is a truncation artifact, not a value to emit
                result["status"] = "low_confidence"
                result["evidence"] = (f"found '합계' at page~{start_page + 1}: the plain run {run} does not foot to its detail rows and no repaired reading ({[r for _n, r, _x in cands]}) "
                                      f"does either -- withheld")
                return result
        # (has_vfa, has_paa) inferred from how many value-slots the 합계 row actually
        # carried -- this is what the disclosed template supports (GMM always first,
        # then VFA, then PAA; a genuinely-empty column contributes 0 characters to the
        # text stream, not even a dash, so its slot silently disappears from the count
        # rather than appearing as a parseable placeholder).
        #   L=1 is a distinct, confirmed shape (KR0150/서울보증보험, a surety insurer):
        #   every GMM/VFA product-detail cell is blank throughout the whole table (not
        #   even a dash -- the same "silently disappears" behaviour, just for every row,
        #   because this company genuinely writes no traditional life-style business),
        #   and only the two PAA-only rows (일반/자동차) carry numbers. The 합계 line
        #   then prints a single combined figure rather than one number per column, so
        #   that lone number IS item7 (PAA), not item1 (GMM BEL).
        #   L=8 is a confirmed shape (KR0051/신한이지손해보험 2025.1Q/2025.2Q): one
        #   spurious leading "-" token before the real 7-column run ("합계 - -1,849 260
        #   294 - - - 136,469"). Verified by hand-summing the GMM_BEL column across
        #   every detail row above 합계: -1,614-78-131-18-8 = -1,849, i.e. run[1], not
        #   run[0] -- the leading dash carries no value, likely a stray label-column
        #   placeholder bleeding into the number stream for this row only.
        COL_MAP = {
            7: (True, True), 6: (True, False), 4: (False, True), 3: (False, False),
            1: ("paa_only", "paa_only"), 8: ("skip_leading", "skip_leading"),
        }
        if L not in COL_MAP:
            result["status"] = "low_confidence"
            result["evidence"] = (
                f"found '합계' at page~{start_page + 1} but trailing numeric run "
                f"length L={L} doesn't match a known column layout {{1,3,4,6,7,8}} "
                f"(run={run}, header text suggested has_vfa={header_has_vfa} "
                f"has_paa={header_has_paa})"
            )
            return result

        has_vfa, has_paa = COL_MAP[L]
        if has_vfa == "paa_only":
            values = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: run[0]}
            has_vfa, has_paa = False, True
        else:
            if has_vfa == "skip_leading":
                run = run[1:]  # drop the spurious leading token, then it's a plain L=7
                has_vfa, has_paa = True, True
            values = {1: run[0], 2: run[1], 3: run[2]}
            if has_vfa:
                values[4], values[5], values[6] = run[3], run[4], run[5]
            else:
                values[4] = values[5] = values[6] = 0.0
            values[7] = run[-1] if has_paa else 0.0
        raw_values = dict(values)                       # printed units, for the footing check below
        for k in list(values):
            values[k] = values[k] / divisor

        # defect 6a (ilp_gap_runlog_textlayer_20261010.md): item 8 is the sum of items 1-7, so the identity item 8 = sum(1..7) can never fail.  The independent check is
        # the table itself: the detail rows above the 합계 line, each placed by its OWN token count, must add up to the 합계 run.  Informational (values never change); a failing
        # footing is printed by extract_period and returned in result['footing'].
        try:
            result["footing"] = footing_of(RE_SPLIT_DIGITS.sub(r"\1\2", seg) if "split-digit" in repair_note else seg, raw_values)
        except Exception as e:  # noqa: BLE001
            result["footing"] = {"error": repr(e)[:80]}

        result["status"] = "ok"
        result["values"] = values
        result["total_disclosed"] = sum(values.values())
        mismatch_note = ""
        if header_has_vfa != has_vfa or header_has_paa != has_paa:
            mismatch_note = (
                f" [header-text cross-check disagreed: header_has_vfa={header_has_vfa} "
                f"header_has_paa={header_has_paa} -- trusted the run-length count]"
            )
        result["evidence"] = (
            f"header page {start_page + 1} (0-idx {start_page}), lookahead "
            f"{j + 1} page(s), unit={unit_label}, run_len={L} -> has_vfa={has_vfa} "
            f"has_paa={has_paa}, 합계 run={run}{mismatch_note}"
            f"{' [full char-doubling document, digits un-collapsed]' if full_doubling else ''}{repair_note}"
        )

        # --- section 2-5 ---
        na_25 = None
        m25 = RE_HEADER_25.search(blob)
        window25 = ""
        if m25:
            window25 = blob[m25.start(): m25.start() + 300]
        else:
            # 2-5 may sit just past our lookahead window (short section, 1-2 lines);
            # search a couple more pages explicitly for the 25-header or bare N/A text.
            for j2 in range(MAX_LOOKAHEAD + 2):
                pi = start_page + j2
                if pi >= n_pages:
                    break
                if pi not in page_texts:
                    page_texts[pi] = pdf.pages[pi].extract_text() or ""
                t = page_texts[pi]
                m25b = RE_HEADER_25.search(t)
                if m25b:
                    window25 = t[m25b.start(): m25b.start() + 300]
                    break
        if window25:
            window25_dd = dedupe_cjk_run(window25)  # undo KR0068-style char doubling
            if any(p in window25 or p in window25_dd for p in NA_PHRASES):
                na_25 = 0
            else:
                na_25 = None  # present but not recognizably N/A -- needs manual review
        result["na_25"] = na_25
        if window25:
            result["evidence_25"] = window25.replace("\n", " ")[:200]
        else:
            result["evidence_25"] = "2-5 header not located in scanned window"

        return result
    finally:
        pdf.close()


# ---------------------------------------------------------------------------
# Main extraction driver
# ---------------------------------------------------------------------------


_MASTER_ITEM8 = None


def prev_item8(code: str, label: str):
    """(quarter label, item 8) of the company's nearest EARLIER quarter in the existing master, or None.  Read only; labels 'YYYY.NQ' sort chronologically."""
    global _MASTER_ITEM8
    if _MASTER_ITEM8 is None:
        _MASTER_ITEM8 = {}
        p = REPO_ROOT / "insurance_liability_portfolio.json"
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    for r in json.load(f):
                        if r.get("항목번호") == 8:
                            _MASTER_ITEM8.setdefault(r["원보험사코드"], {})[r["공시분기"]] = r["값"]
            except Exception:  # noqa: BLE001
                _MASTER_ITEM8 = {}
    qs = sorted(q for q in _MASTER_ITEM8.get(code, {}) if q < label)
    return (qs[-1], _MASTER_ITEM8[code][qs[-1]]) if qs else None


def extract_period(period: str, registry: dict, verbose: bool = True) -> tuple:
    """Returns (rows, report_lines)."""
    md_dir = MD_INBOX / period
    if not md_dir.exists():
        return [], [f"[{period}] md_inbox dir not found, skipped"]

    rows = []
    report = []
    md_files = sorted(md_dir.glob("*.md"))
    for md_path in md_files:
        code, name_from_file = parse_company_from_filename(md_path)
        if not code:
            report.append(f"[{period}] SKIP unparseable filename {md_path.name}")
            continue
        reg = registry.get(code, {})
        name = reg.get("원수사명") or name_from_file
        ticker = reg.get("티커")
        life_nonlife = reg.get("생손보여부")

        pdf_path = find_pdf_for_company(period, code, name)
        if pdf_path is None or not pdf_path.exists():
            report.append(f"[{period}] {code} {name}: NO PDF at data/disclosure/{period}/pdf/ -- skipped")
            continue

        res = extract_section_24_25(pdf_path)
        # defect 4 (the unit is read from the header phrase only; KR0070 2025.2Q printed a wrong one -> a 100x error): a scale that jumps by >= 20x against the company's
        # previous quarter in the master is a unit/column error until proven otherwise -> the cell is withheld (documented exception), never emitted
        if res.get("values") and res.get("total_disclosed") is not None:
            prev = prev_item8(code, period_to_label(period))
            if prev is not None and abs(prev[1]) >= 10.0 and res["total_disclosed"] is not None:
                ratio = abs(res["total_disclosed"]) / abs(prev[1])
                if ratio >= 20.0 or ratio <= 0.05:
                    res["evidence"] = (f"{res.get('evidence')} [UNIT_SUSPECT: item 8 {res['total_disclosed']:,.1f} vs {prev[0]} {prev[1]:,.1f} (x{ratio:.3g}) -- withheld; "
                                       f"check the unit phrase and the table]")
                    res["status"] = "unit_suspect"
                    res["values"] = {}
        ft = res.get("footing")
        if res.get("values") and ft and ft.get("ok") is False:
            res["evidence"] = f"{res.get('evidence')} [FOOTING BAD: {ft['n_rows']} detail rows, column diffs {ft['diffs']} (printed units)]"
        status = res["status"]
        line = (
            f"[{period}] {code} {name}: status={status} unit={res.get('unit')} "
            f"na25={res.get('na_25')} :: {res.get('evidence')}"
        )
        report.append(line)
        if verbose:
            print(line, flush=True)
        if res.get("evidence_25"):
            line25 = f"    2-5 evidence: {res['evidence_25']}"
            report.append(line25)
            if verbose:
                print(line25, flush=True)

        if not res.get("values"):
            continue  # documented exception (scan_only/not_found/unrecoverable low_confidence)
        # status=='low_confidence' with non-empty values means the narrative-prose
        # fallback fired (see try_narrative_fallback) -- real, sourced numbers, just
        # lower precision than the table path. Emitted like any other row; the
        # distinction lives in this run's printed evidence line, not in the schema.

        for item_no in range(1, 8):
            label, section, level = ITEM_CATALOG[item_no]
            rows.append({
                "원보험사코드": code,
                "원수사명": name,
                "티커": ticker,
                "생손보여부": life_nonlife,
                "항목번호": item_no,
                "항목명": label,
                "섹션": section,
                "레벨": level,
                "공시분기": period_to_label(period),
                "값": round(res["values"][item_no], 4),
            })
        label8, section8, level8 = ITEM_CATALOG[8]
        rows.append({
            "원보험사코드": code,
            "원수사명": name,
            "티커": ticker,
            "생손보여부": life_nonlife,
            "항목번호": 8,
            "항목명": label8,
            "섹션": section8,
            "레벨": level8,
            "공시분기": period_to_label(period),
            "값": round(res["total_disclosed"], 4),
        })

        if res.get("na_25") is not None:
            label9, section9, level9 = ITEM_CATALOG[9]
            rows.append({
                "원보험사코드": code,
                "원수사명": name,
                "티커": ticker,
                "생손보여부": life_nonlife,
                "항목번호": 9,
                "항목명": label9,
                "섹션": section9,
                "레벨": level9,
                "공시분기": period_to_label(period),
                "값": res["na_25"],
            })

    return rows, report


def period_to_label(period: str) -> str:
    """FY2026_Q2 -> '2026.2Q' (matches IFRS17_BS.json / kics_disclosure.json convention)."""
    m = re.match(r"FY(\d{4})_Q(\d)", period)
    if not m:
        return period
    return f"{m.group(1)}.{m.group(2)}Q"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", help="e.g. FY2026_Q2")
    ap.add_argument("--all", action="store_true", help="process every period under md_inbox/")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--write", action="store_true", help="disable dry-run and write the output file")
    ap.add_argument("--out", default=str(REPO_ROOT / "insurance_liability_portfolio.json"))
    args = ap.parse_args()

    if not args.period and not args.all:
        print("ERROR: pass --period FY2026_Q2 or --all", file=sys.stderr)
        sys.exit(2)

    dry_run = not args.write

    registry = load_company_registry()
    periods = []
    if args.all:
        periods = sorted(p.name for p in MD_INBOX.iterdir() if p.is_dir() and p.name.startswith("FY"))
    else:
        periods = [args.period]

    all_rows = []
    all_report = []
    for period in periods:
        rows, report = extract_period(period, registry)
        all_rows.extend(rows)
        all_report.extend(report)

    n_companies_ok = len({(r["원보험사코드"], r["공시분기"]) for r in all_rows})
    print(f"\n=== TOTAL rows: {len(all_rows)}  (company,quarter) pairs with data: {n_companies_ok} ===")

    if dry_run:
        print("[dry-run] not writing output. Pass --write to persist.")
        return

    out_path = Path(args.out)
    existing = []
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
    # Merge: replace rows for any (원보험사코드, 공시분기, 항목번호) already covered by
    # this run's periods; keep everything else untouched (idempotent UPSERT by period).
    touched_periods = {period_to_label(p) for p in periods}
    kept = [r for r in existing if r.get("공시분기") not in touched_periods]
    merged = kept + all_rows
    merged.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(merged)} rows ({len(existing)} existing + {len(all_rows)} new for "
          f"{sorted(touched_periods)}, {len(kept)} kept unchanged) to {out_path}")


if __name__ == "__main__":
    main()
