"""Extract 경영공시 Section 1-1 (주요 경영지표) / 1-2 (주요 경영효율 지표) / 5-1 (수익성) into
management_indicators.json.

PRIMARY SOURCE = raw PDF text (fitz), not md_inbox. Rationale (verified 2026-08-31): docling's
keyword-window MD parse is tuned for K-ICS 지급여력 items and structurally *drops* section 1
(page 1-4) for most companies whose solvency-keyword hits start later in the filing -- MD-only
header-regex hit rates for FY2026_Q2 (37 companies) were 1-1: 14/37, 1-2: 12/37, 5-1: 5/37 (broad
"Ⅴ.수익성" match 25/37). Direct PDF text extraction recovers ~36/37 (all but one genuinely
scanned/image PDF: KR0087 동양생명). md_inbox is read-only cross-reference, never written.

Schema mirrors IFRS17_BS.json field order exactly:
  원보험사코드 · 원수사명 · 티커 · 생손보여부 · 항목번호 · 항목명 · 섹션 · 레벨 · 공시분기 · 값
Amounts are already 억원 in the source tables (no unit conversion needed); ratios are % as-is.
Only the "당기"(해당분기, i.e. this quarter) column is stored -- "전년동기"/"증감" are the source
table's own comparison/delta columns and are re-derivable by reading the (company, quarter-4) row
of THIS SAME master; they are not stored to avoid dual-sourcing the same fact from two filings.

Flow vs stock (CLAUDE.md 5-24 instruction: never blind-copy a flow into a stock schema):
  - stock (기말시점): 자산 부채 자본 지급여력비율_경과조치전/후 자산운용률 계약유지율_*
  - flow, CUMULATIVE YTD (반기공시=상반기 누계, not single-quarter): 당기순이익 신계약률
    효력상실및해약률 보험금지급률 운용자산이익률 영업이익률 총자산수익률ROA 자기자본수익률ROE
    투자이익A (ROA/ROE footnote formula in the source itself multiplies by (4/경과분기수) to
    annualize a cumulative amount -- confirms 당기순이익 etc. are YTD-cumulative, not quarterly)
  - hybrid average-balance (NOT a simple stock): 경과운용자산B =
    (당기말운용자산+전년동기말운용자산-직전1년간투자영업이익)/2 per the source footnote.

Usage:
  PY scripts/extract_management_indicators.py --period FY2026_Q2 [--companies KR0001,KR0008]
  PY scripts/extract_management_indicators.py --all-periods [--apply]
  (dry-run by default; --apply writes management_indicators.json)
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import parse_value, make_quarter_column_picker  # noqa: E402

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_PATH = REPO / "management_indicators.json"
DISCLOSURE_DIR = REPO / "data" / "disclosure"
KICS_DISCLOSURE_PATH = REPO / "kics_disclosure.json"

# ---------------------------------------------------------------------------
# Item numbering / label map -- SOURCE OF TRUTH for this master.
# (item_no, canonical_name, section, level, note, label_variants[startswith, normalized])
# ---------------------------------------------------------------------------
ITEM_DEFS = [
    (1, "자산", "1-1", 1, "저량(기말)", ["자산"]),
    (2, "부채", "1-1", 1, "저량(기말)", ["부채"]),
    (3, "자본", "1-1", 1, "저량(기말)", ["자본"]),
    (4, "당기순이익", "1-1", 1, "유량(누적YTD)", ["당기순이익", "당기순손실"]),
    (5, "지급여력비율_경과조치전", "1-1", 1, "저량(기말,비율)", ["지급여력비율"]),
    (6, "지급여력비율_경과조치후", "1-1", 1, "저량(기말,비율)", ["지급여력비율"]),
    (7, "운용자산이익률", "1-1", 1, "유량비율(누적)", ["운용자산이익률"]),
    (8, "영업이익률", "1-1", 1, "유량비율(누적)", ["영업이익률"]),
    (9, "총자산수익률ROA", "1-1", 1, "유량비율(누적,연환산)", ["총자산수익률"]),
    (10, "자기자본수익률ROE", "1-1", 1, "유량비율(누적,연환산)", ["자기자본수익률"]),
    (11, "신계약률", "1-2", 1, "유량비율(누적)", ["신계약률"]),
    (12, "효력상실및해약률", "1-2", 1, "유량비율(누적)", ["효력상실및해약률", "효력상실및해약율"]),
    (13, "보험금지급률", "1-2", 1, "유량비율(누적)", ["보험금지급률"]),
    (14, "자산운용률", "1-2", 1, "저량비율(기말)", ["자산운용률", "자산운용율"]),
    (15, "계약유지율_13회차", "1-2", 2, "저량비율(코호트)", ["13회차"]),
    (16, "계약유지율_25회차", "1-2", 2, "저량비율(코호트)", ["25회차"]),
    (17, "계약유지율_37회차", "1-2", 2, "저량비율(코호트)", ["37회차"]),
    (18, "계약유지율_49회차", "1-2", 2, "저량비율(코호트)", ["49회차"]),
    (19, "계약유지율_61회차", "1-2", 2, "저량비율(코호트)", ["61회차"]),
    (20, "계약유지율_73회차", "1-2", 2, "저량비율(코호트)", ["73회차"]),
    (21, "계약유지율_85회차", "1-2", 2, "저량비율(코호트)", ["85회차"]),
    (22, "투자이익A", "5-1", 1, "유량(누적YTD)", ["투자이익"]),
    (23, "경과운용자산B", "5-1", 1, "평잔성(=(기말+전년동기말-직전1년투자영업이익)/2)", ["경과운용자산"]),
]
ITEM_BY_NO = {d[0]: d for d in ITEM_DEFS}
SEC_1_1_ITEMS = [d for d in ITEM_DEFS if d[2] == "1-1"]
SEC_1_2_ITEMS = [d for d in ITEM_DEFS if d[2] == "1-2"]
SEC_5_1_ITEMS = [d for d in ITEM_DEFS if d[2] == "5-1"]


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


ALL_LABEL_STARTS = {norm(lv) for d in ITEM_DEFS for lv in d[5]}


# ---------------------------------------------------------------------------
# PDF discovery
# ---------------------------------------------------------------------------
def find_pdf(period: str, code: str) -> Path | None:
    matches: list[Path] = []
    for sub in ("pdf", "raw"):
        d = DISCLOSURE_DIR / period / sub
        if not d.exists():
            continue
        matches.extend(d.glob(f"{code}_*.pdf"))
    if not matches:
        return None
    amended = [p for p in matches if "amended" in p.stem.lower() or "정정" in p.stem]
    return amended[0] if amended else matches[0]


def list_companies(period: str) -> list[tuple[str, Path]]:
    seen: dict[str, Path] = {}
    for sub in ("pdf", "raw"):
        d = DISCLOSURE_DIR / period / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("*.pdf")):
            m = re.match(r"^(KR\d+)_", p.stem)
            if not m:
                continue
            code = m.group(1)
            if code in seen:
                if "amended" in p.stem.lower() and "amended" not in seen[code].stem.lower():
                    seen[code] = p
                continue
            seen[code] = p
    return sorted(seen.items())


# ---------------------------------------------------------------------------
# Quarter-label verification (guards against stale-duplicate raw, e.g. KR0011/KR0029/KR0150
# 2026.2Q PDFs that turned out to be byte-identical re-serves of the 2026.1Q filing).
# ---------------------------------------------------------------------------
_Q_MONTH = {"1": "3", "2": "6", "3": "9", "4": "12"}
# explicit (year, quarter) extractors -- order matters (most specific first).
# "fixed_q" patterns capture only a year and imply a fixed quarter (반기 labels).
_EXPLICIT_Q_PATTERNS = [
    (re.compile(r"(\d{2})\.(\d)Q"), None),                # 26.2Q
    (re.compile(r"(\d{4})\.(\d)Q"), None),                 # 2026.2Q
    (re.compile(r"(\d{4})년(\d)[/／]?4?분기"), None),        # 2026년2분기 / 2026년2/4분기
    (re.compile(r"(\d{2})년도?(\d)[/／]4분기"), None),       # 26년도2/4분기
    (re.compile(r"(\d{4})년상반기"), "2"),                  # 2026년상반기 -> Q2
    (re.compile(r"(\d{4})년하반기"), "4"),                  # 2026년하반기 -> Q4
    (re.compile(r"년분기(\d{4})(\d)"), None),               # OCR/table-reflow word-scramble:
    # "2026년 2/4분기" -> cell text comes out "년 분기 2026 2/4" (words before digits) -- seen
    # on KR1098 카카오페이손보 2026.2Q; make_quarter_column_picker has the same 년분기+YYYY+Q
    # prefix rule for the identical reason.
    (re.compile(r"(\d{4})년도(?!\d)"), "4"),                # Q4/연간(결산) filings label the
    # column bare '2023년도' / '2022년도' (year only, no quarter suffix at all) since a
    # year-end filing has no quarter to name -- confirmed across many companies' 2023.4Q-
    # 2025.4Q raw. The (?!\d) guard keeps this from firing inside a MORE specific '26년도2/4분기'
    # match (2-digit year there anyway, so this 4-digit pattern wouldn't collide in practice,
    # but the guard makes the non-collision explicit rather than accidental).
    (re.compile(r"년(\d{4})(?!\d)"), "4"),                  # same bare-year Q4 label, but with
    # '년' rendered on its OWN line BEFORE the digits instead of attached ('년\n년\n2024\n년\n
    # 2023' -- confirmed KR0068 한화생명 2024.4Q); the sliding-window join in
    # find_quarter_header_line makes '년(\d{4})' visible even though no single raw line has it.
    (re.compile(r"(\d{4})년(?!\d)"), "4"),                  # plain 'YYYY년' (attached, normal
    # order, no 분기/상반기/도 suffix) as its OWN complete line -- confirmed 신한라이프 2024.4Q:
    # '2024년' / '2023년' are each a whole line by themselves. Checked on the single-line
    # candidate before the joined-window candidate (see find_quarter_header_line), so this
    # correctly wins over the previous scrambled pattern's cross-boundary false read of
    # '2024년2023년' as '년2023' when the two YEAR+년 tokens sit on adjacent lines with no
    # space -- 년(?!\d) only fires when nothing (or a non-digit) follows within THIS candidate.
]


def _explicit_quarters_in(text: str) -> list[tuple[str, str]]:
    """Extract every (yyyy, q) pair the text explicitly names, normalizing 2-digit years to
    2000+ and 상반기/하반기 to quarter 2/4. Returns [] if no explicit year+quarter signal."""
    c = norm(text)
    found = []
    for pat, fixed_q in _EXPLICIT_Q_PATTERNS:
        for m in pat.finditer(c):
            if fixed_q is not None:
                yyyy, q = m.group(1), fixed_q
            else:
                yyyy, q = m.group(1), m.group(2)
            if len(yyyy) == 2:
                yyyy = "20" + yyyy
            found.append((yyyy, q))
    return found


def quarter_label_matches(cell_text: str, quarter: str) -> bool | None:
    """True = explicit match. False = explicit MISMATCH (hard reject -- e.g. text says '26.1Q'
    while we want 2026.2Q, the stale-duplicate-raw signature). None = no explicit quarter/year
    signal found at all (caller may fall back to a weaker heuristic)."""
    y, q = quarter.split(".")
    q = q.rstrip("Q")
    explicit = _explicit_quarters_in(cell_text)
    if explicit:
        return any(yy == y and qq == q for yy, qq in explicit)
    return None


def quarter_label_weak_match(cell_text: str, quarter: str) -> bool:
    """Only used when quarter_label_matches() returned None (no explicit signal) -- bare
    당기/당분기/해당분기 style headers via the shared column-picker."""
    picker = make_quarter_column_picker(quarter)
    return picker([cell_text]) == 0


def find_quarter_header_line(lines: list[str], quarter: str, max_scan: int = 25, window: int = 5) -> tuple[int | None, str]:
    """Return (index, reason). index is non-None IFF a quarter signal matching `quarter` was
    found -- None means do-not-extract. An explicit mismatch anywhere in the scanned window
    (e.g. text says '26.1Q' while we want 2026.2Q -- the stale-duplicate-raw signature caught
    for KR0011/KR0029/KR0150) is a HARD reject and short-circuits any weaker bare-당기/당분기
    fallback match, by design.

    Checks both single lines AND a small sliding window of consecutive lines JOINED together,
    because some PDFs render a single header cell's words across multiple text lines out of
    natural reading order (e.g. KR1098 카카오페이 2026.2Q: '년' / '분기' / '2026' / '2/4' each on
    their own line instead of one '2026년2/4분기' line) -- a per-line-only regex can never see
    that pattern; the joined window can."""
    weak_idx = None
    mismatch_line = None
    n = len(lines[:max_scan])
    for i in range(n):
        candidates = [lines[i], "".join(lines[i : min(n, i + window)])]
        seen_none = True
        for cand in candidates:
            m = quarter_label_matches(cand, quarter)
            if m is True:
                return i, "explicit match"
            if m is False:
                seen_none = False
                if mismatch_line is None:
                    mismatch_line = cand.strip()
        if seen_none and weak_idx is None:
            c = norm(lines[i])
            if c == "당기":
                # bare '당기' with NO digits at all (e.g. KR0049 악사손해: '구분/당기/전년동기/증감')
                # carries no quarter info to verify against the picker -- accepted because we
                # already got here without an explicit mismatch anywhere on the page (checked
                # above, and it short-circuits this branch), which is the actual stale-duplicate
                # signature; a table that never prints a quarter number at all has no such signal
                # to give in the first place.
                weak_idx = i
            elif re.search(r"해당분기|당분기|당기말|당기\)", c) and quarter_label_weak_match(lines[i], quarter):
                weak_idx = i
    if mismatch_line is not None:
        return None, f"EXPLICIT MISMATCH (found {mismatch_line!r}) -- stale/wrong-quarter raw suspected"
    if weak_idx is not None:
        return weak_idx, "weak match (bare 당기/당분기, no explicit year+quarter nearby)"
    return None, "no quarter header found"


# ---------------------------------------------------------------------------
# Page location
# ---------------------------------------------------------------------------
_COHORT_NUMS = {"13", "25", "37", "49", "61", "73", "85"}


def merge_split_cohort_labels(lines: list[str]) -> list[str]:
    """'계약유지율 13회차' sometimes renders as two lines, '회차' then '13' -- REVERSED order,
    word before digit (e.g. KR0083 푸본현대생명 2026.2Q). Left as-is, the bare '13' etc. get
    mistaken for a data value by extract_positional's number scan, which shifts every later
    item's position by one and silently misaligns the rest of the table (confirmed: produced
    13.0/3.87/67.42/... for items 15-21 instead of the correct 91.82/77.77/57.27/...). Merge the
    pair into one '13회차' line and drop the original two so every downstream consumer (label-
    anchored AND positional) sees the same clean form as the non-split rendering."""
    out = []
    i = 0
    while i < len(lines):
        if norm(lines[i]) == "회차" and i + 1 < len(lines) and norm(lines[i + 1]) in _COHORT_NUMS:
            out.append(f"{lines[i + 1].strip()}회차")
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out


def get_page_lines(page) -> list[str]:
    lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
    return merge_split_cohort_labels(lines)


def is_data_value_line(raw_line: str) -> bool:
    v = parse_value(raw_line)
    if v is None:
        return False
    s = raw_line.strip()
    if "," in s or "." in s or any(ch in s for ch in "△▲▽▼()"):
        return True
    digits = re.sub(r"\D", "", s)
    return len(digits) >= 3


def looks_like_toc(raw_text: str) -> bool:
    return ("•••" in raw_text) or (raw_text.count("...") >= 5) or (raw_text.count(". . .") >= 3)


def has_short_label_lines(lines: list[str], labels: list[str], max_len: int = 20) -> bool:
    """True iff EVERY label in `labels` appears as the START of some SHORT line (a genuine
    table row-label), as opposed to merely appearing as a substring somewhere in a long prose
    sentence (e.g. the '운용자산이익률 = 투자이익÷경과운용자산×100' footnote formula, which
    would otherwise false-positive-match a section locator that only checks whole-page text)."""
    for label in labels:
        nlabel = norm(label)
        if not any(norm(l).startswith(nlabel) and len(norm(l)) <= max_len for l in lines):
            return False
    return True


def find_section_page(doc, require_all: list[str], start: int, end: int, min_numeric: int = 8, require_short_labels: bool = False) -> int | None:
    best = None
    for pno in range(start, min(end, len(doc))):
        raw = doc[pno].get_text()
        nt = norm(raw)
        if not all(kv in nt for kv in require_all):
            continue
        if looks_like_toc(raw):
            continue
        lines = get_page_lines(doc[pno])
        if require_short_labels and not has_short_label_lines(lines, require_all):
            continue  # keyword only in prose/footnote (e.g. a formula explanation), not a real row
        nnum = sum(1 for l in lines if is_data_value_line(l))
        if nnum >= min_numeric:
            return pno
        if best is None or nnum > best[1]:
            best = (pno, nnum)
    if best and best[1] >= 4:
        return best[0]
    return None


# ---------------------------------------------------------------------------
# Value extraction within a located page/section
# ---------------------------------------------------------------------------
def detect_layout_direction(lines: list[str], sample_labels=("당기순이익", "자산", "부채")) -> str:
    """Most tables render LABEL then its 3 values ('forward'). 삼성생명 renders the opposite:
    the row's 3 numbers (in reverse column order: 증감,전년동기,당기) come FIRST, THEN the label
    (e.g. '...\\n4153175\\n자산\\n재무손익\\n595276\\n부채...' -- confirmed KR0069 2026.2Q). A
    forward-only scan there silently reads the WRONG row's number as if it were the anchored
    label's value (caught by the item1 != item2+item3 identity check). Probe a few unambiguous
    labels once per page and use whichever direction has more immediately-adjacent numeric
    neighbors, applied consistently for every item on that page."""
    nlines = [norm(l) for l in lines]
    forward_hits = backward_hits = 0
    for lbl in sample_labels:
        nlbl = norm(lbl)
        for i, nl in enumerate(nlines):
            if nl.startswith(nlbl):
                # skip an immediately-adjacent duplicate re-render of this SAME label (e.g.
                # 한화생명's '당기순이익'\n'당기순이익'\n'5,102' -- the real neighbor is one
                # further out); without this, the duplicate-render quirk gets misread as
                # "no number immediately adjacent" and falsely tips the forward/backward vote.
                fwd_j = i + 2 if (i + 1 < len(nlines) and nlines[i + 1].startswith(nlbl)) else i + 1
                bwd_j = i - 2 if (i - 1 >= 0 and nlines[i - 1].startswith(nlbl)) else i - 1
                if fwd_j < len(lines) and parse_value(lines[fwd_j]) is not None:
                    forward_hits += 1
                if bwd_j >= 0 and parse_value(lines[bwd_j]) is not None:
                    backward_hits += 1
                break
    return "backward" if backward_hits > forward_hits else "forward"


def extract_by_label(lines: list[str], label_variants: list[str], occurrence: int, lookahead: int = 10, direction: str = "forward"):
    nlines = [norm(l) for l in lines]
    variants_n = [norm(v) for v in label_variants]
    # a row-label is often rendered twice on CONSECUTIVE lines (e.g. KR0068 한화생명's '투자이익'
    # line immediately followed by a '투자이익(A)' line before the real numbers) -- that repeat
    # must NOT be treated as "hit a different row's label, give up", or every duplicate-rendered
    # company loses the row entirely. Only the single line immediately after the anchor gets this
    # leniency (not any later recurrence) so a genuinely-blank 지급여력비율(경과조치전) can still
    # correctly stop at the 지급여력비율(경과조치후) row a few lines down rather than reading
    # past it into 후's own value.
    other_label_starts = ALL_LABEL_STARTS - set(variants_n)
    count = 0
    for i, nl in enumerate(nlines):
        if any(nl.startswith(v) for v in variants_n):
            count += 1
            if count != occurrence:
                continue
            if direction == "backward":
                # 삼성생명-style: [증감, 전년동기, 당기, LABEL] -- the value immediately BEFORE
                # the label is 당기(this-quarter); walk backward, stopping at another label.
                for j in range(i - 1, max(-1, i - 1 - lookahead), -1):
                    njl = nlines[j]
                    if j == i - 1 and any(njl.startswith(v) for v in variants_n):
                        continue
                    if any(njl.startswith(s) for s in other_label_starts) or any(njl.startswith(v) for v in variants_n):
                        return None, None
                    val = parse_value(lines[j])
                    if val is not None:
                        return val, lines[j]
                return None, None
            for j in range(i + 1, min(len(lines), i + 1 + lookahead)):
                njl = nlines[j]
                if j == i + 1 and any(njl.startswith(v) for v in variants_n):
                    continue  # immediate duplicate re-render of the SAME label -- skip past it
                if any(njl.startswith(s) for s in other_label_starts) or any(njl.startswith(v) for v in variants_n):
                    return None, None
                val = parse_value(lines[j])
                if val is not None:
                    return val, lines[j]
            return None, None
    return None, None


# item numbers whose canonical value is a percentage -- never plausibly beyond a few hundred %
# in this domain (used only to sanity-gate the POSITIONAL fallback, which has no label anchor
# to trust; label-anchored extraction is never filtered by this).
PCT_ITEMS = {5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21}
PCT_PLAUSIBLE_ABS_MAX = 1000.0


_NARRATIVE_MARKERS = ("주요변동요인", "주요변동사항", "※", "*주")


def has_dense_na_placeholders(lines: list[str], min_count: int = 5) -> bool:
    """True if the TABLE region of the page is full of explicit '_'/'-'/'—' blank-cell
    placeholders (e.g. 코리안리's 1-2 table: reinsurers legitimately have no 신계약률/유지율
    etc, printed as bare '_' triples). That pattern means the row-group-of-3 positional
    assumption is UNSAFE (missing groups shift every later item's position) -- when seen,
    positional fallback must be skipped rather than silently misaligning, and the sparse-but-
    real label-anchored result should stand as-is.

    Only scans lines BEFORE the first '주요변동요인'-style narrative marker: a '- : 설명문'
    bullet-point prose footnote (common on this table, e.g. 한화생명 2026.2Q's FVOCI
    explanation) gets split by fitz into several bare '-' lines that would otherwise
    false-positive this check and wrongly suppress a fallback the page actually needs."""
    table_lines = lines
    for i, l in enumerate(lines):
        if any(marker in l for marker in _NARRATIVE_MARKERS):
            table_lines = lines[:i]
            break
    n = sum(1 for l in table_lines if norm(l) in ("_", "-", "—", "─", "–"))
    return n >= min_count


def extract_positional(lines: list[str], item_defs: list[tuple], group_size: int = 3):
    """Fallback for pages where row labels have no text layer (values-only render, e.g.
    KR0094 신한라이프 1-1/1-2) -- values still appear in fixed canonical row order. Anchor on
    the LAST '증감' (delta-column header) line before the data block, then take the first of
    every `group_size` numeric tokens as 당기(this-quarter). Percentage-scale items are sanity-
    bounded (|v|<=1000) because on a page shared by two tables (e.g. 코리안리's 1-1+1-2 combined
    page) the anchor can lock onto the WRONG '증감' and silently harvest the OTHER table's
    numbers -- bounding rejects that rather than emitting a plausible-looking wrong percentage."""
    nlines = [norm(l) for l in lines]
    anchor = None
    for i, nl in enumerate(nlines):
        if nl in ("증감", "증감(%p)"):
            anchor = i
    start = (anchor + 1) if anchor is not None else 0
    nums = [l for l in lines[start:] if parse_value(l) is not None]
    out = {}
    for idx, item_def in enumerate(item_defs):
        pos = idx * group_size
        if pos >= len(nums):
            continue
        item_no = item_def[0]
        val = parse_value(nums[pos])
        if val is None:
            continue
        if item_no in PCT_ITEMS and abs(float(val)) > PCT_PLAUSIBLE_ABS_MAX:
            continue  # implausible for a %-scale item -- anchor almost certainly landed wrong
        out[item_no] = val
    return out


def extract_section_1_1(doc, quarter: str, log: list[str]) -> tuple[dict, str | None]:
    """Returns (values, direction). `direction` ('forward'/'backward'/None) is surfaced so the
    caller can reuse it for 1-2/5-1 on the SAME company's PDF: those pages pack rows back-to-
    back with no intervening category header (unlike 1-1's own '재무손익'/'건전성'/'수익성비율'
    group labels), so a fresh per-page probe there sees numbers on BOTH sides of every label and
    can't break the forward/backward tie on its own (confirmed on KR0069 삼성생명 1-2/5-1: the
    per-page probe tied 3-3 and defaulted to the wrong 'forward'). 1-1's own group-header layout
    gives an unambiguous signal, and a single PDF's own template is consistent across its
    sections, so propagating 1-1's verdict is the reliable fix."""
    page_idx = find_section_page(doc, ["주요경영지표"], start=0, end=10)
    if page_idx is None:
        log.append("1-1: page not found")
        return {}, None
    lines = get_page_lines(doc[page_idx])
    hdr_idx, reason = find_quarter_header_line(lines, quarter)
    if hdr_idx is None:
        log.append(f"1-1: quarter header check FAILED on page {page_idx + 1} -- {reason} -- SKIPPED")
        return {}, None
    direction = detect_layout_direction(lines)
    if direction == "backward":
        log.append(f"1-1: page {page_idx + 1} detected as VALUE-then-LABEL layout (e.g. 삼성생명-style) -- reading backward")
    out: dict[int, str] = {}
    for item_no, name, sec, lvl, note, variants in SEC_1_1_ITEMS:
        occ = 2 if item_no == 6 else 1
        val, _src = extract_by_label(lines, variants, occurrence=occ, direction=direction)
        if val is not None:
            out[item_no] = val
    filled = len(out)
    if filled < 5 and has_dense_na_placeholders(lines):
        log.append(f"1-1: label-anchored scan only got {filled}/10 on page {page_idx + 1}, but page is dense with '_' N/A placeholders -- skipping positional fallback (sparse-but-real result kept)")
    elif filled < 5:
        log.append(f"1-1: label-anchored scan only got {filled}/10 on page {page_idx + 1} -- trying positional fallback")
        pos_out = extract_positional(lines, SEC_1_1_ITEMS)
        if pos_out:
            conflicts = [k for k in pos_out if k in out and out[k] != pos_out[k]]
            if conflicts:
                log.append(f"1-1: positional fallback OVERRIDES {len(conflicts)} label-anchored hit(s) that disagree (page confirmed unreliable for label-anchoring, e.g. a page-number footer mistaken for a value) -- {conflicts}")
            log.append(f"1-1: positional fallback covers {len(pos_out)}/10 (takes precedence on this confirmed-jumbled page)")
            out.update(pos_out)
    return out, direction


def extract_section_1_2(doc, quarter: str, log: list[str], direction_hint: str | None = None) -> dict:
    page_idx = find_section_page(doc, ["주요경영효율지표"], start=0, end=10)
    if page_idx is None:
        log.append("1-2: page not found")
        return {}
    lines = get_page_lines(doc[page_idx])
    hdr_idx, reason = find_quarter_header_line(lines, quarter)
    if hdr_idx is None:
        log.append(f"1-2: quarter header check FAILED on page {page_idx + 1} -- {reason} -- SKIPPED")
        return {}
    if direction_hint is not None:
        # 1-2 packs rows back-to-back with no category header between them, so a fresh per-page
        # probe sees numbers on both sides of every label and can tie -- trust 1-1's verdict
        # from the SAME PDF instead (see extract_section_1_1's docstring).
        direction = direction_hint
        log.append(f"1-2: reusing direction '{direction}' detected on 1-1's page (own per-page probe would tie)")
    else:
        direction = detect_layout_direction(lines, sample_labels=("신계약률", "보험금지급률", "자산운용률"))
    if direction == "backward":
        log.append(f"1-2: page {page_idx + 1} detected as VALUE-then-LABEL layout -- reading backward")
    out: dict[int, str] = {}
    for item_no, name, sec, lvl, note, variants in SEC_1_2_ITEMS:
        val, _src = extract_by_label(lines, variants, occurrence=1, direction=direction)
        if val is not None:
            out[item_no] = val
    filled = len(out)
    if filled < 5 and has_dense_na_placeholders(lines):
        log.append(f"1-2: label-anchored scan only got {filled}/11 on page {page_idx + 1}, but page is dense with '_' N/A placeholders -- skipping positional fallback (sparse-but-real result kept)")
    elif filled < 5:
        log.append(f"1-2: label-anchored scan only got {filled}/11 on page {page_idx + 1} -- trying positional fallback")
        pos_out = extract_positional(lines, SEC_1_2_ITEMS)
        if pos_out:
            conflicts = [k for k in pos_out if k in out and out[k] != pos_out[k]]
            if conflicts:
                log.append(f"1-2: positional fallback OVERRIDES {len(conflicts)} label-anchored hit(s) that disagree -- {conflicts}")
            log.append(f"1-2: positional fallback covers {len(pos_out)}/11 (takes precedence on this confirmed-jumbled page)")
            out.update(pos_out)
    return out


def extract_section_5_1(doc, quarter: str, log: list[str], direction_hint: str | None = None) -> dict:
    page_idx = find_section_page(
        doc, ["투자이익", "경과운용자산"], start=2, end=150, min_numeric=4, require_short_labels=True
    )
    if page_idx is None:
        log.append("5-1: page not found")
        return {}
    lines = get_page_lines(doc[page_idx])
    hdr_idx, reason = find_quarter_header_line(lines, quarter)
    if hdr_idx is None:
        log.append(f"5-1: quarter header check FAILED on page {page_idx + 1} -- {reason} -- SKIPPED")
        return {}
    if direction_hint is not None:
        direction = direction_hint
        log.append(f"5-1: reusing direction '{direction}' detected on 1-1's page (own per-page probe would tie)")
    else:
        direction = detect_layout_direction(lines, sample_labels=("투자이익", "경과운용자산"))
    if direction == "backward":
        log.append(f"5-1: page {page_idx + 1} detected as VALUE-then-LABEL layout -- reading backward")
    out: dict[int, str] = {}
    for item_no, name, sec, lvl, note, variants in SEC_5_1_ITEMS:
        val, _src = extract_by_label(lines, variants, occurrence=1, direction=direction)
        if val is not None:
            out[item_no] = val
    return out


# ---------------------------------------------------------------------------
# Company metadata (reuse kics_disclosure.json as the join key so names/tickers stay
# consistent with the existing K-ICS master; never writes that file).
# ---------------------------------------------------------------------------
def load_company_meta() -> dict[str, tuple[str, str, str]]:
    meta: dict[str, tuple[str, str, str]] = {}
    if not KICS_DISCLOSURE_PATH.exists():
        return meta
    data = json.loads(KICS_DISCLOSURE_PATH.read_text(encoding="utf-8"))
    for r in data:
        code = r.get("원보험사코드")
        if code and code not in meta:
            meta[code] = (
                r.get("원수사명", ""),
                r.get("티커", ""),
                r.get("생손보여부", ""),
            )
    return meta


def guess_kind(name: str) -> str:
    if "생명" in name or "라이프" in name:
        return "생명보험"
    return "손해보험"


# ---------------------------------------------------------------------------
# Main per-company driver
# ---------------------------------------------------------------------------
def extract_company_period(code: str, pdf_path: Path, quarter: str, meta: dict) -> tuple[list[dict], list[str]]:
    import fitz  # local import: keep module importable without PyMuPDF for --help etc.

    log: list[str] = [f"{code} {quarter}: pdf={pdf_path.name}"]
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:  # noqa: BLE001
        log.append(f"OPEN FAILED: {e}")
        return [], log
    if len(doc) > 0 and len(doc[0].get_text()) < 20 and len(doc) > 1 and len(doc[1].get_text()) < 20:
        log.append("page1-2 near-empty text (<20 chars) -- likely scanned/image PDF, no text layer")
        doc.close()
        return [], log

    vals: dict[int, str] = {}
    v1_1, direction = extract_section_1_1(doc, quarter, log)
    vals.update(v1_1)
    vals.update(extract_section_1_2(doc, quarter, log, direction_hint=direction))
    s51 = extract_section_5_1(doc, quarter, log, direction_hint=direction)
    for k, v in s51.items():
        vals.setdefault(k, v)
    doc.close()

    name, ticker, kind = meta.get(code, ("", "", ""))
    if not name:
        name = re.sub(r"^KR\d+_", "", pdf_path.stem).replace("_", "")
        kind = guess_kind(name)

    rows = []
    for item_no in sorted(vals):
        item_no_, item_name, section, level, _note, _variants = ITEM_BY_NO[item_no]
        rows.append(
            {
                "원보험사코드": code,
                "원수사명": name,
                "티커": ticker,
                "생손보여부": kind,
                "항목번호": item_no,
                "항목명": item_name,
                "섹션": section,
                "레벨": level,
                "공시분기": quarter,
                "값": float(vals[item_no]),
            }
        )
    log.append(f"-> {len(rows)}/23 items filled")
    return rows, log


def period_to_quarter(period: str) -> str:
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def run(periods: list[str], companies_filter: list[str] | None, apply: bool):
    meta = load_company_meta()
    all_rows: list[dict] = []
    all_logs: list[str] = []
    summary = []
    for period in periods:
        quarter = period_to_quarter(period)
        companies = list_companies(period)
        if companies_filter:
            companies = [(c, p) for c, p in companies if c in companies_filter]
        n_rows_period = 0
        n_companies_with_data = 0
        for code, pdf_path in companies:
            rows, log = extract_company_period(code, pdf_path, quarter, meta)
            all_logs.extend(log)
            if rows:
                n_companies_with_data += 1
            n_rows_period += len(rows)
            all_rows.extend(rows)
        summary.append((period, len(companies), n_companies_with_data, n_rows_period))

    print("\n".join(all_logs))
    print("\n=== SUMMARY ===")
    for period, n_co, n_ok, n_rows in summary:
        print(f"{period}: {n_ok}/{n_co} companies with >=1 item, {n_rows} rows")
    print(f"TOTAL rows: {len(all_rows)}")

    if apply:
        existing = []
        if OUT_PATH.exists():
            existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
        by_key = {key(r): r for r in existing}
        for r in all_rows:
            by_key[key(r)] = r
        merged = sorted(by_key.values(), key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
        OUT_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"WROTE {OUT_PATH} ({len(merged)} total rows)")
    else:
        print("(dry-run -- pass --apply to write management_indicators.json)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", help="e.g. FY2026_Q2")
    ap.add_argument("--all-periods", action="store_true")
    ap.add_argument("--companies", help="comma-separated KR codes filter")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.all_periods:
        periods = sorted(p.name for p in DISCLOSURE_DIR.iterdir() if p.is_dir() and p.name.startswith("FY"))
    elif args.period:
        periods = [args.period]
    else:
        ap.error("need --period or --all-periods")
        return
    companies_filter = args.companies.split(",") if args.companies else None
    run(periods, companies_filter, args.apply)


if __name__ == "__main__":
    main()
