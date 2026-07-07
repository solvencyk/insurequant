"""Registry of K-ICS disclosure parsing variants (company/quarter heterogeneity).

REFACTOR-3 slice 1 (owner parser_refactor, 2026-06-13). The parser's "intelligence"
is accumulated per-company/per-quarter heuristics. Historically a new variant meant
hand-editing tuples/dicts INSIDE kics_disclosure_parser.py (the core), so a single new
company could mean editing a 9-entry regex tuple in the parser core. This module is the
FREEZE-RULE landing spot: a new section-heading style, OCR label typo, or numbering
alias is added HERE as an append-only data entry — NOT as a new branch in the core.

Why an ORDERED spec list, not a dict[KR-code] -> handler: the docling MD does not
reliably carry the company code at section-detection time, and the SAME company's
layout changes quarter to quarter (e.g. 삼성생명 2023.1Q bullet vs 2023.2Q ※-heading).
So these variants are recognised by ORDERED pattern match, not by code lookup — an
ordered "registry of recognisers" is the correct shape for them. KR-code-keyed dispatch
is reserved for genuinely code-specific knobs (column-picker quirks, value
reconciliation) and is a later slice that first threads the company code through the
fill scripts. Each spec carries an ASCII attribution so the owner can see which
company/quarter motivated it (the prompt's "label variation matrix").

Byte-identity: kics_disclosure_parser builds its compiled SECTION_START_PATTERNS /
SECTION_END_PATTERNS and _strip_label_punct behaviour from the data here. The values
MUST stay byte-identical to the pre-refactor constants — tests/unit/
test_company_handlers.py + the full tests/unit/test_kics_disclosure_parser.py golden
suite assert this (no-regression). Sources use \\uXXXX escapes to match the parser
file's style and stay encoding-safe; the ASCII comment above each entry says what it is.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Section-start recognisers for the [경과조치 적용 전 … 지급여력비율 세부] detail
# table. Tried in order by extract_kics_detail_section; first match wins.
# Each entry: (attribution, regex_source, flags). Append a new tuple to teach the
# parser a new heading style — do NOT add a branch in the core.
# ---------------------------------------------------------------------------
SECTION_START_SPECS: tuple[tuple[str, str, int], ...] = (
    # generic: "경과조치 적용 전 … 지급여력비율 세부"
    (
        "generic_pre_ratio_detail",
        r"#{1,3}\s*\[?\s*"
        r"경과조치\s*적용\s*전.{0,40}"
        r"지급여력비율\s*세부",
        re.I,
    ),
    # generic: "경과조치 적용 전 … 세부" (no 지급여력비율 between)
    (
        "generic_pre_detail",
        r"#{1,3}\s*\[?\s*"
        r"경과조치\s*적용\s*전.{0,40}세부",
        re.I,
    ),
    # generic: "경과조치 적용 전 …" loose tail
    (
        "generic_pre_loose",
        r"#{1,3}\s*\[?\s*경과조치\s*적용\s*전.{0,30}\]?",
        re.I,
    ),
    # e.g. ## 4-2-2. 지급여력비율의 경과조치 적용에 관한 세부사항 [경과조치 적용 전 ...]
    (
        "heading_4_2_2_ratio_detail",
        r"#{1,3}\s*4-2-2\.?\s*지급여력비율[^\n]*세부",
        re.I,
    ),
    # heading + bracketed "[경과조치 적용 전 지급여력비율 세부]"
    (
        "heading_bracketed_pre_ratio_detail",
        r"#{1,3}\s*[^\n]*\[\s*경과조치\s*적용\s*전\s*"
        r"지급여력비율\s*세부\s*\]",
        re.I,
    ),
    # e.g. [경과조치  적용  전  지급여력비율 세부] (no markdown heading)
    (
        "bracketed_no_heading",
        r"\[\s*경과조치\s*적용\s*전[^\]]*"
        r"지급여력비율\s*세부\s*\]",
        re.I,
    ),
    # e.g. ## ※ 경과조치적용전지급여력비율세부 (삼성생명 2023.2Q style, no brackets)
    (
        "samsung_2023q2_heading_no_brackets",
        r"#{1,3}\s*[※\*﻿]?\s*경과조치\s*적용\s*전"
        r"[^\n]*지급여력비율\s*세부",
        re.I,
    ),
    # e.g. - ※ 경과조치적용전지급여력비율세부 (삼성생명 2023.1Q bullet, no heading/brackets)
    (
        "samsung_2023q1_bullet",
        r"^[\-\*]\s*[※\*﻿]?\s*경과조치\s*적용\s*전"
        r"[^\n]*지급여력비율\s*세부",
        re.I | re.M,
    ),
    # line-start ※/* prefixed, no heading marker
    (
        "line_start_marker_no_heading",
        r"^[※\*﻿]?\s*경과조치\s*적용\s*전"
        r"[^\n]*지급여력비율\s*세부",
        re.I | re.M,
    ),
    # e.g. ## [건전성감독기준 요약 재무상태표] (하나손해보험 style — same
    # item1-14 detail table, framed as a balance-sheet summary heading
    # instead of "경과조치 적용 전 ... 세부". Without this, none of the
    # 경과조치-worded patterns above match, extract_kics_detail_section
    # returns None, and the whole detail table (incl. item12) is skipped.
    (
        "solvency_balance_sheet_summary",
        r"#{1,3}\s*\[?\s*건전성감독기준\s*요약\s*재무상태표\s*\]?",
        re.I,
    ),
)

# Section-end recognisers: where the transition-detail section stops.
SECTION_END_SPECS: tuple[tuple[str, str, int], ...] = (
    # "지급여력비율의 경과조치" heading
    (
        "ratio_transition_heading",
        r"#{1,3}\s*\[?지급여력비율의\s*경과조치",
        re.I,
    ),
    # "(1) 공통적용 경과조치" heading
    (
        "common_application_transition_heading",
        r"#{1,3}\s*\(?1\)?\s*공통적용\s*경과조치",
        re.I,
    ),
)

# ---------------------------------------------------------------------------
# Label normalisation: bullet/middle-dot chars stripped, then OCR-typo fixes.
# PUNCT_STRIP_CHARS are removed first; LABEL_FIXES then applied IN ORDER (order
# matters — the 보헨위 fix is independent, but the two 장기손액 fixes must run as a
# pair). A new OCR misread that docling produces lands HERE as one tuple.
# ---------------------------------------------------------------------------
PUNCT_STRIP_CHARS: tuple[str, ...] = ("·", "ㆍ", "∙", "•")

LABEL_FIXES: tuple[tuple[str, str, str], ...] = (
    # OCR typo in some Shinhan MD: 보헨위 -> 보험위
    ("보헨위", "보험위", "shinhan_ocr_보헨위->보험위"),
    # OCR: 장기손액보헨 -> 장기손해보험
    ("장기손액보헨", "장기손해보험", "ocr_장기손액보헨->장기손해보험"),
    # OCR: 장기손액보험 -> 장기손해보험
    ("장기손액보험", "장기손해보험", "ocr_장기손액보험->장기손해보험"),
)

# ---------------------------------------------------------------------------
# Item-label aliases for audit/K-ICS doc tables: maps a company's wording to the
# canonical baseline label so match_baseline_value resolves it. Pure data — a new
# company numbering/wording variant is one more dict entry, not a code branch.
# (KakaoPay/MetLife reversed numbering, P&C item-10 skip, etc.)
# ---------------------------------------------------------------------------
_ITEM4_CANONICAL = (
    "Ⅰ. 건전성감독기준 재무상태표 상의 순자산"
)

AUDIT_LABEL_ALIASES: dict[str, str] = {
    "Ⅰ.순자산": "Ⅰ. 건전성감독기준 재무상태표 상의 순자산",
    "Ⅷ. 지급여력금액": "가. 지급여력금액",
    "Ⅴ.기본자본": "기본자본",
    "Ⅵ.보완자본": "보완자본",
    "(분산효과)": "- 분산효과 : (1+2+3+4+5) - Ⅰ",
    "Ⅴ. 지급여력기준금액": "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)",
    # Some P&C tables skip item 10 (non-controlling interest) and number reserve as 6.
    "6. 조정준비금": "7. 조정준비금",
    "6.조정준비금": "7. 조정준비금",
    # MetLife: roman numeral after "상의"
    "건전성감독기준 재무상태표 상의 Ⅰ. 순자산": _ITEM4_CANONICAL,
}


def build_section_start_patterns() -> tuple[re.Pattern[str], ...]:
    """Compile the ordered section-start recognisers (parser consumes this)."""
    return tuple(re.compile(src, flags) for _label, src, flags in SECTION_START_SPECS)


def build_section_end_patterns() -> tuple[re.Pattern[str], ...]:
    """Compile the ordered section-end recognisers (parser consumes this)."""
    return tuple(re.compile(src, flags) for _label, src, flags in SECTION_END_SPECS)


def apply_label_fixes(s: str) -> str:
    """Strip bullet/middle-dot punctuation, then apply OCR-typo fixes in order.

    Behaviour is byte-identical to the parser's former inline _strip_label_punct.
    """
    for ch in PUNCT_STRIP_CHARS:
        s = s.replace(ch, "")
    for wrong, right, _note in LABEL_FIXES:
        s = s.replace(wrong, right)
    return s
