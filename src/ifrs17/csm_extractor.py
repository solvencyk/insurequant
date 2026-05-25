"""Extract CSM (보험계약마진) amortisation schedule tables from a DART filing.

Strategy (semantic / fuzzy, NOT a hardcoded regex on caption text alone):

  1. Parse the filing XML into a sequence of (caption, table) pairs, where
     ``caption`` is the nearest preceding <P> text and ``table`` is a
     normalised dict {header, rows, footnotes, line_no}.

  2. Score each table by how strongly it looks like a CSM amortisation
     schedule:
        +3 caption contains both "보험계약마진" and ("상각" or "예상" or "인식")
        +2 caption contains "보험계약마진" only
        +2 header cells contain time-bucket words: "년", "1년", "2년",
           "11년~15년", "30년 이후", "계", etc.
        +1 any column header contains the literal "년"
        -3 caption clearly belongs to a different topic
           ("부채", "공정가치", "위험조정", "할인율") and CSM is not also mentioned

     Top-scoring tables (score >= threshold) are returned. We intentionally
     return *all* candidates above threshold so the caller can decide
     between e.g. consolidated vs. separate, original vs. amended.

  3. Cells are emitted as raw strings (preserving '-' for zero placeholders,
     digit grouping intact); upstream code can numeric-cast later once the
     mapping rule is approved by the user.

PoC scope: targets the inline HTML/XBRL flavour DART returns from
``/api/document.xml``. The schema there uses <TABLE>/<THEAD>/<TBODY>/
<TH>/<TD>/<P> capitalised tags - the same dialect used by the 2024
Samsung Fire annual report inspected on 2026-05-23.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from lxml import etree


# ---------------------------------------------------------------------------
# Scoring keywords (intentionally surface a few clear signals, not a giant
# regex - keep it transparent for the user to tune.)
# ---------------------------------------------------------------------------

_CAPTION_PRIMARY = "보험계약마진"
_CAPTION_VERBS = ("상각", "예상", "인식", "향후", "인식시기", "기대상각")
_NEGATIVE_TOPIC_WORDS = ("부채변동", "공정가치", "위험조정",
                         "할인율", "현금흐름")
_YEAR_BUCKET_PATTERNS = (
    re.compile(r"^\s*\d+\s*년\s*$"),                # "1년", "10년"
    re.compile(r"\d+\s*년\s*[~∼\-]\s*\d+\s*년"),     # "1~2년"
    re.compile(r"\d+\s*년\s*이후"),                 # "30년 이후"
    re.compile(r"\d+\s*년\s*초과"),                 # "5년 초과", "30년 초과"
    re.compile(r"\d+\s*년\s*이하"),                 # "1년 이하"
    re.compile(r"\d+\s*년\s*미만"),                 # "1년 미만"
    re.compile(r"\d+\s*년\s*초과\s*\d+\s*년\s*이하"),  # "1년 초과 3년 이하"
)
_TOTAL_WORDS = ("계", "합계", "총계", "합 계", "총 계")


@dataclass
class ExtractedTable:
    caption: str
    header: list[list[str]]      # may be multi-row
    rows: list[list[str]]
    footnotes: list[str]
    line_no: int
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    form_type: str = "unknown"   # "A" (portfolio x year buckets, buckets on cols),
                                  # "B" (rollforward-style residual maturity, single
                                  #      slice column), "A_rows" (buckets on rows;
                                  #      portfolios on cols, e.g. DB손해),
                                  # "unknown"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _text(el: etree._Element) -> str:
    """Flatten a node's text content, collapsing whitespace."""
    raw = "".join(el.itertext())
    return re.sub(r"\s+", " ", raw).strip()


_SUBCAPTION_PATTERNS = (
    re.compile(r"^\(?\d+\)?\s*(당기|전기|당기말|전기말)?(\s*\(.*\))?$"),
    re.compile(r"^\d+\)\s*\d{4}년"),                # "1) 2024년 12월 31일 현재"
    re.compile(r"^[<\[]?\s*(당기|전기|당기말|전기말|당분기|전분기|당반기|전반기)\s*[>\]]?$"),
    re.compile(r"^[가나다라마바사아자차]\.\s*$"),
    re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]"),
)


def _is_subcaption(txt: str) -> bool:
    """True if ``txt`` is a short sub-heading that should NOT overwrite
    the main caption above.
    """
    t = txt.strip()
    if len(t) > 40:
        return False
    # If the text already mentions CSM, it IS a main caption (e.g.
    # 삼성화재 "② 보험계약마진 상각").
    if _CAPTION_PRIMARY in t:
        return False
    for p in _SUBCAPTION_PATTERNS:
        if p.match(t):
            return True
    return False


def _iter_tables_with_context(xml_path: Path) -> Iterable[ExtractedTable]:
    """Yield ExtractedTable instances in document order.

    DART filing XML is not valid XHTML - it's a custom dialect with
    uppercase tags and no namespace. We parse it permissively with
    ``etree.HTMLParser`` which tolerates the structure.

    ``huge_tree=True`` is needed for the larger filings (현대해상 ~5.7MB)
    where the default libxml2 limits truncate the document and break
    table boundaries silently.
    """
    parser = etree.HTMLParser(encoding="utf-8", huge_tree=True, recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    # Walk in document order; remember the last <p>/<P> caption seen.
    # We keep the *most recent meaningful* caption: short sub-headings
    # like "1) 당기말", "2) 2024년 12월 31일 현재", "<당기>" do NOT clobber
    # a real caption above them — otherwise filings (현대해상) where
    # the table is preceded by both "25. 보험계약마진 상각 스케줄…" and
    # "1) 2024년 12월 31일 현재" would lose the CSM keyword.
    last_caption = ""
    last_caption_line = 0
    pending_footnotes: list[str] = []

    for el in root.iter():
        tag = (el.tag or "").lower()

        if tag == "p":
            txt = _text(el)
            if not txt:
                continue
            # Footnote heuristic: starts with "(*" or "주)" or "※"
            if (txt.startswith("(*") or txt.startswith("주)")
                    or txt.startswith("※")):
                pending_footnotes.append(txt)
                continue
            # Sub-caption heuristic: do NOT overwrite the main caption.
            # These are short enumerators / period labels that sit between
            # the real caption and the table.
            if _is_subcaption(txt):
                continue
            last_caption = txt
            last_caption_line = getattr(el, "sourceline", 0) or 0
            pending_footnotes = []

        elif tag == "table":
            header_rows: list[list[str]] = []
            body_rows: list[list[str]] = []

            for sub in el.iter():
                stag = (sub.tag or "").lower()
                if stag == "tr":
                    cells = []
                    for c in sub:
                        ctag = (c.tag or "").lower()
                        if ctag in ("th", "td"):
                            cells.append(_text(c))
                    if not cells:
                        continue
                    # If the row sits inside a <thead> ancestor, treat as header.
                    in_thead = False
                    parent = sub.getparent()
                    while parent is not None:
                        if (parent.tag or "").lower() == "thead":
                            in_thead = True
                            break
                        parent = parent.getparent()
                    (header_rows if in_thead else body_rows).append(cells)

            # Heuristic skip: pure layout tables (single cell, no header).
            if not body_rows and not header_rows:
                continue
            if (len(header_rows) + len(body_rows)) <= 1 and \
                    all(len(r) <= 1 for r in header_rows + body_rows):
                continue

            yield ExtractedTable(
                caption=last_caption,
                header=header_rows,
                rows=body_rows,
                footnotes=list(pending_footnotes),
                line_no=getattr(el, "sourceline", 0) or last_caption_line,
            )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _looks_like_year_bucket(cell: str) -> bool:
    return any(p.search(cell) for p in _YEAR_BUCKET_PATTERNS)


def score_table(t: ExtractedTable) -> ExtractedTable:
    score = 0
    reasons: list[str] = []
    caption = t.caption or ""

    if _CAPTION_PRIMARY in caption:
        if any(v in caption for v in _CAPTION_VERBS):
            score += 3
            reasons.append("caption: CSM + (상각/예상/인식/향후)")
        else:
            score += 2
            reasons.append("caption: CSM only")

    # Negative signal: caption is clearly about a different topic AND CSM
    # is NOT mentioned at all.
    if (_CAPTION_PRIMARY not in caption
            and any(w in caption for w in _NEGATIVE_TOPIC_WORDS)):
        score -= 3
        reasons.append("caption: negative topic word, no CSM")

    # Header cells: from THEAD if present.
    flat_header_cells = [c for row in t.header for c in row]

    # If no THEAD was emitted, scan the first few body rows for a header
    # candidate. We skip single-cell "(단위: 백만원)" decoration rows that
    # filings (흥국화재 etc.) often put as the first row.
    if not flat_header_cells and t.rows:
        for cand in t.rows[:3]:
            if not cand:
                continue
            if len(cand) == 1 and ("단위" in cand[0] or not cand[0].strip()):
                continue
            if all(_looks_like_text_label(c) for c in cand):
                flat_header_cells = list(cand)
                reasons.append(
                    "header: inferred from body row (no THEAD)"
                )
                break

    year_bucket_hits = sum(1 for c in flat_header_cells if _looks_like_year_bucket(c))
    if year_bucket_hits >= 3:
        score += 2
        reasons.append(f"header: {year_bucket_hits} year-bucket cells")
    elif any("년" in c for c in flat_header_cells):
        score += 1
        reasons.append("header: has '년' cell")

    if any(c.strip() in _TOTAL_WORDS for c in flat_header_cells):
        score += 1
        reasons.append("header: has 합계/계 column")

    # Body-left-column year buckets: some filings (e.g. DB손해) put the time
    # buckets on the rows (left column) and portfolios on the columns. If at
    # least 3 first-column cells look like year buckets, treat as a CSM
    # schedule signal worth +2. Skip single-cell decoration rows.
    first_col = [r[0] for r in t.rows if r and len(r) > 1]
    body_year_hits = sum(1 for c in first_col if _looks_like_year_bucket(c))
    if body_year_hits >= 3:
        score += 2
        reasons.append(f"body left-col: {body_year_hits} year-bucket cells")

    # Classify form (rough taxonomy for downstream normalisers).
    if body_year_hits >= 3:
        t.form_type = "A_rows"        # year buckets on rows
    elif year_bucket_hits >= 3:
        t.form_type = "A"             # year buckets on cols (typical schedule)
    elif flat_header_cells and any(
        kw in c for c in flat_header_cells for kw in ("당기말", "전기말")
    ):
        t.form_type = "B"             # rollforward / residual maturity snapshot
    else:
        t.form_type = "unknown"

    # Hard gate: a CSM-amortisation table MUST have a caption mentioning
    # "보험계약마진". Structural-only signals (year buckets + 합계) are too
    # generic — e.g. DB손해's IBNR/development triangles look identical
    # structurally. If the gate fails, cap the score to at most 3 so it
    # cannot cross the default threshold of 4.
    if _CAPTION_PRIMARY not in caption:
        if score > 3:
            score = 3
            reasons.append("gate: no CSM caption → score capped at 3")

    t.score = score
    t.reasons = reasons
    return t


_NUMERIC_CELL = re.compile(r"^[\s\-\(\)\d,\.]+$")


def _looks_like_text_label(cell: str) -> bool:
    """True if the cell text looks like a header label rather than a number.

    Empty cells are allowed (they often appear in spanned headers).
    """
    s = (cell or "").strip()
    if not s:
        return True
    if _NUMERIC_CELL.match(s):
        return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_csm_tables(
    xml_path: Path, min_score: int = 4
) -> list[ExtractedTable]:
    """Return CSM amortisation tables found in ``xml_path``.

    A score of 4+ requires at least: a CSM caption verb (3) AND a year-bucket
    or '년' header (>=1), so structural ambiguities don't slip through.
    """
    candidates = [score_table(t) for t in _iter_tables_with_context(xml_path)]
    return sorted(
        [c for c in candidates if c.score >= min_score],
        key=lambda c: (-c.score, c.line_no),
    )


def to_jsonable(t: ExtractedTable) -> dict:
    return {
        "caption": t.caption,
        "line_no": t.line_no,
        "score": t.score,
        "form_type": t.form_type,
        "reasons": t.reasons,
        "header": t.header,
        "rows": t.rows,
        "footnotes": t.footnotes,
    }
