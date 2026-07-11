"""Add '경과조치 적용 후' values to kics_disclosure.json as `값_적용후`.

For every (회사, 분기, 항목번호) row that already exists in
``kics_disclosure.json``, this script looks at the source markdown in
``md_inbox/<period>/`` and, if the company's '공통적용 경과조치' table (and
where applicable the '② 장수위험·사업비위험·해지위험 및 대재해위험' breakdown
table) lists an '적용 후' value that **differs** from the existing 적용 전
value (the ``값`` field), it adds a sibling field ``값_적용후`` to that row.

If the 적용 전 and 적용 후 values are equal (or 적용 후 is blank), the row
is left untouched — UI consumers should then fall back to ``값``.

This script is **surgical**: it never modifies the existing ``값`` field,
and it never deletes a ``값_적용후`` field. Idempotent across re-runs
provided the source markdown does not change.

Tables recognised
-----------------
1.  **공통적용** — preceding heading contains '공통적용' AND '경과조치'.
    Header has a column whose normalised text contains '적용후' (full form
    '경과조치적용후' or the short KR0076-style '적용후').
2.  **② 장수위험 breakdown** — preceding heading contains both '경과조치'
    and any of {'장수위험', '해지위험', '사업비위험', '대재해위험'}.
    The table is only used when at least one of the
    {사망/장수/장해·질병/장기재물·기타/해지/사업비/대재해} rows shows a
    적용 전 ≠ 적용 후 value (rule for KR0073: skip 주식위험/금리위험 표).

Both table types use the same column picker: '적용 전' column index +
'적용 후' column index. Column matching tolerates KR0076's short
'전' / '적용 후' headers because we already know the surrounding heading
is a 경과조치 section.

Row → 항목번호 mapping
----------------------
공통적용 표:
    지급여력비율  → 27
    지급여력금액  → 1
    기본자본      → 2
    보완자본      → 3
    지급여력기준금액 → 14

② breakdown 표 (additionally):
    기본요구자본            → 15
    생명·장기손해보험위험액  → 17
    사망위험                → 29
    장수위험                → 30
    장해·질병위험           → 31
    장기재물·기타위험        → 32
    해지위험                → 33
    사업비위험              → 34
    대재해위험              → 35
    일반손해보험위험액        → 18
    시장위험액              → 19
    신용위험액              → 20
    운영위험액              → 21
    법인세조정액            → 22
    기타요구자본            → 23

Usage
-----
    python scripts/fill_post_transition_to_disclosure.py [--dry-run]
        [--period FY2025_Q4] [--all-periods]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")


def _md_period_to_quarter(period_label: str) -> str:
    m = _PERIOD_RE.match(period_label)
    if not m:
        raise ValueError(f"unrecognised period label: {period_label}")
    return f"{m.group(1)}.{m.group(2)}Q"


# 지급여력비율/금액/기준금액: see the override note in _extract_post_values
# where this is used — the ②breakdown table wins over 공통적용 for these.
_RATIO_TRIAD_ITEMS = {1, 14, 27}

# 생명·장기손해보험위험액(item17)의 세부위험 7종 — see the merged-label guard
# in the breakdown-application loop below.
_LIFE_SUB_ITEMS = {29, 30, 31, 32, 33, 34, 35}

# Row label keywords → item_no. Match against normalised label.
# Order matters: more specific keywords first.
COMMON_ROW_MAP: list[tuple[str, int]] = [
    ("지급여력비율", 27),
    ("지급여력기준금액", 14),  # before '지급여력금액'
    ("지급여력금액", 1),
    ("기본자본", 2),
    ("보완자본", 3),
]

BREAKDOWN_ROW_MAP: list[tuple[str, int]] = [
    # All common-row labels also appear in the ② table
    ("지급여력비율", 27),
    ("지급여력기준금액", 14),
    ("지급여력금액", 1),
    # Sub-items first (most specific).
    ("사망위험", 29),
    ("장수위험", 30),
    ("장해질병위험", 31),
    ("장해·질병위험", 31),
    ("장기재물기타위험", 32),
    ("장기재물·기타위험", 32),
    ("해지위험", 33),
    ("사업비위험", 34),
    ("대재해위험", 35),
    # Then parent / siblings (longer/more specific labels first).
    ("생명장기손해보험위험액", 17),
    ("생명·장기손해보험위험액", 17),
    ("일반손해보험위험액", 18),
    ("시장위험액", 19),
    ("신용위험액", 20),
    ("운영위험액", 21),
    ("법인세조정액", 22),
    ("기본요구자본", 15),
    ("기타요구자본", 23),
    # Generic '기본자본' / '보완자본' last so '기본요구자본' wins above.
    ("기본자본", 2),
    ("보완자본", 3),
]

# ③ 주식위험·금리위험 경과조치 표 — this table's *own* domain is items
# 19/36-40 only (its 지급여력비율/금액/기준금액/기본요구자본/생명장기위험액 rows
# are that provision's *isolated* view, not the true combined-with-② final —
# see the ROOT CAUSE note in _extract_post_values). Deliberately excludes
# 지급여력비율(27)/지급여력금액(1)/기본자본(2)/보완자본(3)/지급여력기준금액(14)/
# 기본요구자본(15)/생명장기손해보험위험액(17) — those come from headline or ②.
MARKET_RATE_ROW_MAP: list[tuple[str, int]] = [
    ("시장위험액", 19),
    ("금리위험", 36),
    ("주식위험", 37),
    ("부동산위험", 38),
    ("외환위험", 39),
    ("자산집중위험", 40),
]

# ③표의 실제 효과가 있는지 판정하는 앵커 sub-item(금리·주식만 — 부동산/외환/
# 집중은 ③에서도 항상 pass-through).
_MARKET_RATE_EFFECT_ITEMS = {36, 37}

# Leaf sub-items in ③ (dash-as-zero applies here, not to the 시장위험액 total).
_MARKET_SUB_LEAF_ITEMS = {36, 37, 38, 39, 40}


TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
HEADING_RE = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
# In-line unit hint, e.g. "(단위: 백만원, %)".
_UNIT_HINT_RE = re.compile(r"\(\s*단위\s*[:：]?\s*[^)]*?(억원|백만원|만원|천원|원)[^)]*\)")
# Bare unit token, used for multi-line split hints (KR1010-style: "( 단위 :
# 천원 )" split across 4 lines). Matches a line whose stripped content is
# exactly one of the known units, optionally followed by ",%)" etc.
_UNIT_BARE_RE = re.compile(r"^\s*[:：]?\s*(억원|백만원|만원|천원|원)\b")


def _split_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _normalise(s: str) -> str:
    """Strip whitespace/punctuation/Roman numerals for fuzzy label matching.

    Includes both middle-dot variants: '·' (U+00B7 MIDDLE DOT) and '∙'
    (U+2219 BULLET OPERATOR) — docling renders some companies' "장해∙질병
    위험"/"장기재물∙기타위험" labels with the latter (KR0049 악사손해보험),
    which silently failed every keyword match when only U+00B7 was stripped."""
    if s is None:
        return ""
    return re.sub(r"[\s\(\)\[\]\.\,\:·∙\-\+\*Ⅰ-Ⅹⅰ-ⅸ㈜]+", "", s)


def _parse_value(raw: str) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().replace(",", "")
    if cleaned in ("", "-", "─", "–"):
        return None
    cleaned = cleaned.replace("△", "-").replace("▲", "-")
    paren = re.fullmatch(r"\((-?\d[\d.]*)\)", cleaned)
    if paren:
        cleaned = "-" + paren.group(1)
    if not re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
        return None
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
    return cleaned


_DASH_TOKENS = ("-", "─", "–", "—")


def _parse_leaf_subrisk_value(raw: str) -> str | None:
    """Like _parse_value, but a bare dash in a sub-risk LEAF cell (29-35/36-40)
    means the company discloses zero exposure to that specific risk — not
    "absent" (same convention already applied to items 36-40 in
    fill_market_subitems_to_disclosure.py). A genuinely blank cell ("") is
    still treated as absent/skip, only an explicit dash glyph means zero.
    Confirmed via raw (KR0072 케이디비생명 2023.2Q ②표): 장수위험 46,364→'-'·
    사업비위험 142,176→'-'·대재해위험 38,906→'-' sit in the same row as
    해지위험 682,308→151,038 (a real, non-dash reduction) — the dashed rows
    are the same selective-provision effect taken to its zero extreme, not
    missing data, and plain _parse_value's None was silently dropping them
    from the JSON entirely (the owner Tier-B "적용후 추출갭" report)."""
    if raw is not None and raw.strip().replace(",", "") in _DASH_TOKENS:
        return "0"
    return _parse_value(raw)


def _normalise_unit(value: str, unit: str) -> str:
    """Rescale a value string to 억원 to match existing JSON convention."""
    try:
        f = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return value
    if unit == "억원":
        scaled = f
    elif unit == "백만원":
        scaled = f / 100.0
    elif unit == "만원":
        scaled = f / 10000.0           # 1억원 = 10,000 만원
    elif unit == "천원":
        scaled = f / 100000.0          # 1억원 = 100,000 천원
    elif unit == "원":
        scaled = f / 100000000.0       # 1억원 = 100,000,000 원
    else:
        return value
    if abs(scaled - round(scaled)) < 1e-6:
        return str(int(round(scaled)))
    return f"{scaled:.2f}".rstrip("0").rstrip(".")


def _fmt_amount(x: float) -> str:
    """Format a derived amount (item1) matching _normalise_unit's convention."""
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def _fmt_ratio(x: float) -> str:
    """Format a derived ratio (item27), matching recalc_basic_capital_ratio_post.py."""
    return f"{x:.8f}".rstrip("0").rstrip(".") or "0"


def _is_percent_row(item_no: int) -> bool:
    """지급여력비율 is a %, never rescaled by unit hint."""
    return item_no == 27


def _values_equal(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) < 1e-6
    except ValueError:
        return a == b


# ---------------------------------------------------------------------------
# Markdown scanning
# ---------------------------------------------------------------------------


def _scan_tables_with_context(md_text: str) -> list[dict]:
    """Return a list of {table, unit, preceding_headings} dicts.

    Each table is a list-of-list-of-cells, the first sub-list being the
    header. ``preceding_headings`` is the list of markdown headings (any
    ##-level lines) seen between the previous table boundary and the start
    of this table — newest last.
    """
    lines = md_text.splitlines()
    tables: list[dict] = []
    current: list[list[str]] = []
    current_unit = "억원"
    headings_since_last_table: list[str] = []
    # Per-table sticky unit (carried into the table once flushed).
    pending_unit = current_unit

    def _flush() -> None:
        nonlocal pending_unit
        if current:
            tables.append({
                "table": [row[:] for row in current],
                "unit": pending_unit,
                "headings": list(headings_since_last_table),
            })
            current.clear()

    saw_unit_anchor = False  # set when we've recently seen the '단위' keyword
    for line in lines:
        unit_m = _UNIT_HINT_RE.search(line)
        if unit_m:
            current_unit = unit_m.group(1)
            pending_unit = current_unit  # next-table unit
            saw_unit_anchor = False
            continue
        # Multi-line split hint: a line that's just '단위' followed within
        # a few lines by a bare unit token.
        if "단위" in line and not line.strip().startswith(("|", "#")):
            saw_unit_anchor = True
            continue
        if saw_unit_anchor:
            bm = _UNIT_BARE_RE.search(line)
            if bm:
                current_unit = bm.group(1)
                pending_unit = current_unit
                saw_unit_anchor = False
                continue
            # Don't keep the anchor live forever — drop after a table or
            # heading line.
            if HEADING_RE.match(line) or TABLE_ROW_RE.match(line):
                saw_unit_anchor = False
        heading_m = HEADING_RE.match(line)
        if heading_m and not TABLE_ROW_RE.match(line):
            # Flush any in-progress table; new context starts.
            if current:
                _flush()
                # After flushing, clear the headings memory: those
                # headings already attached to the table we just flushed
                # remain valid for it; the next table starts a fresh
                # context.
                headings_since_last_table = []
            headings_since_last_table.append(heading_m.group(1).strip())
            continue
        if TABLE_ROW_RE.match(line):
            cells = _split_row(line)
            if all(set(c) <= set("-: ") for c in cells):
                # separator row, ignore
                continue
            current.append(cells)
        else:
            # non-table line
            if current:
                _flush()
                headings_since_last_table = []
            # Plain text between tables can still carry inline headings like
            # '- (2) 선택적용 경과조치 관련' or '2. ① 자본감소분 경과조치'
            # (these come from PDFs where the heading was demoted to a list
            # item by docling). Track those too.
            stripped = line.strip()
            if stripped and (
                stripped.startswith(("-", "*"))
                or re.match(r"^\d+[\.\)]\s", stripped)        # '1. ...' / '1) ...'
                or re.match(r"^\(\d+\)\s", stripped)           # '(1) ...'
                or re.match(r"^[①②③④⑤⑥⑦⑧⑨]", stripped)        # '① ...'
            ):
                # Pull the body after the bullet/number for keyword matching.
                body = re.sub(r"^[-*\d\.\)\(①②③④⑤⑥⑦⑧⑨\s]+", "", stripped, count=1).strip()
                if body:
                    headings_since_last_table.append(body)
    _flush()
    return _merge_split_breakdown_tables(tables)


def _merge_split_breakdown_tables(tables: list[dict]) -> list[dict]:
    """Docling sometimes splits one logical ②breakdown table into two
    consecutive markdown tables at a blank line (KR0005 흥국화재/KR1010/
    KR0049 등): the first keeps the header + headline rows (지급여력비율
    ... 생명·장기손해보험위험액), the second starts straight into sub-item
    data rows (사망위험, 장수위험, ...) with no heading and no header row of
    its own — its own ``headings`` list comes back empty (the blank line
    resets ``headings_since_last_table`` same as always; only a table
    immediately preceded by another table, with nothing of its own to
    claim, is a split-continuation candidate). Merge any such table into
    the immediately preceding one so pre_idx/post_idx (derivable only from
    the first table's real header) apply across the combined row set —
    otherwise the continuation is invisible to _is_breakdown_section's
    candidate search, which requires non-empty headings to match at all.

    Deliberately requires the CONTINUATION's own headings to be empty
    (not just non-empty-but-different) — this is what distinguishes "no
    heading of its own, docling split artifact" from a genuine next
    section that happens to follow immediately (e.g. ③ 주식위험 경과조치,
    which always carries its own heading and must NOT merge into ②'s
    table)."""
    merged: list[dict] = []
    for t in tables:
        if (
            merged
            and not t["headings"]
            and merged[-1]["headings"]
            and merged[-1]["table"]
            and t["table"]
        ):
            first_cell = t["table"][0][0] if t["table"][0] else ""
            looks_like_header = any(
                kw in first_cell.replace(" ", "") for kw in ("구분", "적용")
            )
            if not looks_like_header:
                merged[-1] = {
                    **merged[-1],
                    "table": merged[-1]["table"] + t["table"],
                }
                continue
        merged.append(t)
    return merged


_NEGATION_TOKENS = ("적용하지않아", "미적용", "동일함", "동일하므로", "동일한")

# ①②③ each cover a disjoint selective-provision type. A negation line only
# invalidates the heading it's actually talking about — matched by shared
# risk-keyword group, not "any heading within 2 lines".
_RISK_KEYWORD_GROUPS = (
    ("장수위험", "해지위험", "사업비위험", "대재해위험"),  # ②
    ("주식위험", "금리위험"),  # ③
    ("자본감소분",),  # ①
)


def _filter_active_headings(headings: list[str], n: int = 12) -> list[str]:
    """Return the last ``n`` headings, *excluding* any that are followed
    (within the next 1-2 headings) by a negation marker like
    '... 적용하지 않아 ... 동일함'.

    In many K-ICS markdowns docling demotes the (1)/②/③ numbered section
    headings into list items, and the negation line ('당사는 ... 적용하지
    않아 ... 동일함') is captured as a separate heading right after.
    Treating ②/③ headings as positive section markers in that case would
    mis-classify the *single* table that actually belongs to (1) 공통적용
    as a 장수위험/주식위험 table.

    Algorithm: a heading H is dropped if (a) H itself contains a negation
    marker, or (b) one of the next 2 headings contains a negation marker
    AND H contains a section-type marker like '경과조치' / '위험'. Headings
    farther away that just describe (1) 공통적용 etc. survive.

    Caveat this guards against (한화손해보험 KR0002 2023.1Q): when a company
    discloses ②'s real heading+table immediately followed by ③'s heading+
    negation (③ genuinely not applicable), the naive "any of next 2" rule
    drops ② too — even though ③'s negation has nothing to do with ②'s own,
    applicable, real-data table. Require the negation follower to share a
    risk-keyword *group* with H (both ② or both ③) before treating it as
    that heading's own split-off negation; a negation about a *different*
    group never invalidates H.
    """
    window = headings[-n:]
    out: list[str] = []
    for i, h in enumerate(window):
        nh = _normalise(h)
        if any(tok in nh for tok in _NEGATION_TOKENS):
            continue
        # If H mentions a 위험/경과조치 section marker and is immediately
        # followed by a negation line, drop H too.
        marker = any(
            kw in nh
            for kw in ("위험", "경과조치")
        )
        if marker:
            h_groups = {
                grp for grp in _RISK_KEYWORD_GROUPS if any(kw in nh for kw in grp)
            }
            followers = window[i + 1 : i + 3]
            drop = False
            for f in followers:
                nf = _normalise(f)
                if not any(tok in nf for tok in _NEGATION_TOKENS):
                    continue
                if not h_groups:
                    # H has no specific risk-keyword group (generic '경과조치'
                    # mention) — fall back to the old any-negation-nearby rule.
                    drop = True
                    break
                f_groups = {
                    grp for grp in _RISK_KEYWORD_GROUPS if any(kw in nf for kw in grp)
                }
                if not f_groups or f_groups & h_groups:
                    drop = True
                    break
            if drop:
                continue
        out.append(h)
    return out


def _heading_context(headings: list[str]) -> str:
    """Concatenate the (filtered) recent headings into a single normalised string."""
    return _normalise(" ".join(_filter_active_headings(headings)))


def _is_common_section(headings: list[str]) -> bool:
    ctx = _heading_context(headings)
    return "공통적용" in ctx and "경과조치" in ctx


def _is_breakdown_section(headings: list[str]) -> bool:
    ctx = _heading_context(headings)
    if "경과조치" not in ctx:
        return False
    return any(
        kw in ctx
        for kw in ("장수위험", "해지위험", "사업비위험", "대재해위험")
    )


def _is_market_or_rate_section(headings: list[str]) -> bool:
    """Skip the '③ 주식위험 경과조치 또는 금리위험 경과조치' section even if the
    heading also mentions 경과조치. Match the risk keyword ADJACENT to 경과조치
    (the section title), NOT a bare '금리위험' mention — otherwise a 주요변동요인
    narrative paragraph ('…금리위험액이 소폭 증가…') captured as a heading falsely
    excludes the real 공통적용 capital table (처브 KR0100 2024.3Q)."""
    ctx = _heading_context(headings).replace(" ", "")
    return "주식위험경과조치" in ctx or "금리위험경과조치" in ctx


def _extract_tac_amount(tables: list[dict]) -> str | None:
    """'자본감소분 경과조치'(TAC) amount. Its own table's 기본자본/보완자본
    rows show unchanged 전=후 (TAC doesn't touch the tier split), but this
    row carries the amount that gets added to item1 without specifying
    which tier — validation confirmed via raw (KDB KR0072 2023.1Q) that
    this amount must be layered onto item2(기본자본) on top of whatever
    ①TFI reclassification already gave it, otherwise item1=item2+item3
    (R1) never closes for TAC-electing companies. Only the sum matters for
    R1, so any consistent convention (added to item2) works."""
    for t in tables:
        for row in t["table"]:
            if "자본감소분" not in row[0].replace(" ", ""):
                # label varies ("...적용금액" vs bare "...경과조치" — KDB
                # KR0072 2023.1Q vs 2023.2Q) but "자본감소분" alone is unique
                # to this one row across the entire K-ICS schema.
                continue
            # Don't rely on a header row to locate 적용후's column — 하나생명
            # KR0097 carries this row inside a full 별첨 지급여력금액
            # statement with no "자본감소분 경과조치" heading at all, and a
            # stray blank-line table-boundary split lands a *data* row
            # ("Ⅳ.기본자본...") as this fragment's tbl[0] instead of the
            # real 적용전/적용후 header, so no header is even recoverable.
            # In every observed shape (KDB KR0072, 하나생명 KR0097) the
            # 적용후 amount is simply the row's last non-blank, parseable
            # cell (적용전 is always blank — TAC has no "before").
            for cell in reversed(row[1:]):
                amount = _parse_value(cell)
                if amount is not None:
                    return _normalise_unit(amount, t["unit"])
    return None


_AUDIT_STATEMENT_ROW_MAP: tuple[tuple[str, int], ...] = (
    ("지급여력기준금액", 14),  # before 지급여력금액
    ("지급여력금액", 1),
    ("기본자본", 2),
    ("보완자본", 3),
)


def _extract_audit_statement_values(tables: list[dict]) -> dict[int, tuple[str, str]]:
    """Last-resort fallback for the 감사보고서 별첨 '지급여력금액'/'지급여력
    기준금액' statements (하나생명 KR0097 2024.4Q FY-end filings): a fully
    audited, Roman-numeral-itemised restatement with no '공통적용'/'경과조치
    적용 전 세부' heading at all, so none of the normal table detectors
    above ever match it. Every top-level row (Ⅳ.기본자본, Ⅶ.지급여력금액,
    etc.) has exactly one non-blank cell per column-pair (전, 후) — same
    "last non-blank cell" shape as _extract_tac_amount — with pre in the
    row's first half and post in the second. Only used when nothing else
    resolved the item, so it can't clobber a real, table-classified match.

    Two anchors, since bare "기본자본"/"보완자본"/"지급여력금액" exact-label
    rows recur all over a filing (총괄 comparison tables, 요약재무상태표,
    etc.) and can coincidentally satisfy the "exactly 2 non-blank cells"
    shape from a totally unrelated table with a different unit (KR0082
    2023.1Q matched this way and got item2_후 scaled 100x wrong before
    these anchors were added): (a) the whole document must mention
    "자본감소분" somewhere — the 지급여력기준금액 companion statement (item14)
    is a table of its own with no 자본감소분 row, so this can't be a
    per-table check — and (b) each individual table must carry at least 2
    other Roman-numeral-prefixed rows, confirming it's genuinely a full
    Ⅰ..Ⅶ-itemised statement and not some unrelated 2-column footnote.
    """
    if not any("자본감소분" in row[0].replace(" ", "") for t in tables for row in t["table"]):
        return {}
    roman = tuple("Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ".split())
    out: dict[int, tuple[str, str]] = {}
    for t in tables:
        roman_rows = sum(1 for row in t["table"] if row[0].strip().startswith(roman))
        if roman_rows < 2:
            continue
        for row in t["table"]:
            label = _normalise(row[0])
            item_no = None
            for kw, no in _AUDIT_STATEMENT_ROW_MAP:
                # Exact match only — "지급여력금액" as a bare *substring*
                # would also hit "Ⅱ.지급여력금액으로 불인정하는 항목", a
                # completely different item.
                if _normalise(kw) == label:
                    item_no = no
                    break
            if item_no is None or item_no in out:
                continue
            non_blank = [c for c in row[1:] if _parse_value(c) is not None]
            if len(non_blank) != 2:
                # Not this statement's shape (e.g. a sub-item row using the
                # other column pair, or a row with only one populated cell).
                continue
            pre_v = _normalise_unit(_parse_value(non_blank[0]), t["unit"])
            post_v = _normalise_unit(_parse_value(non_blank[1]), t["unit"])
            out[item_no] = (pre_v, post_v)
    return out


def _is_headline_summary_section(headings: list[str]) -> bool:
    """The '[지급여력비율 총괄]' table — always the true cumulative 전/후
    figure regardless of how many separate provisions (①TFI/②장수등/③주식·
    금리) are stacked, since it's the company's own headline rollup rather
    than a single provision's isolated before/after view."""
    return "지급여력비율총괄" in _heading_context(headings).replace(" ", "")


def _extract_headline_summary(
    tables: list[dict], company_code: str
) -> tuple[dict[int, tuple[str, str]], str]:
    """Parse '[지급여력비율 총괄]' if present: returns {item_no: (pre, post)}
    for items 1/14/27 plus a debug string.

    Table shape (docling mangles the '경과조치 전'/'경과조치 후' label into a
    vertical-text split across 3 rows each, e.g. col0 sequence "경","과 조",
    "치 전" then "경 과","조 치","후" — the split pattern itself varies by
    company/quarter, so col0 can't be trusted). What's stable: the row order
    is always 지급여력비율,지급여력금액,지급여력기준금액 for the 전 group,
    then the same 3 labels again for the 후 group, with the clean label
    always present *somewhere* in the row and the "당분기" (this quarter,
    right-most-recent) value in the next cell after wherever the label
    landed.
    """
    labels = (("지급여력비율", 27), ("지급여력금액", 1), ("지급여력기준금액", 14))
    for t in tables:
        if not _is_headline_summary_section(t["headings"]):
            continue
        rows = t["table"][1:] if len(t["table"]) > 1 else []
        matched: list[tuple[int, str]] = []  # (item_no, value) in row order
        for row in rows:
            label_cell_idx = None
            item_no = None
            for i, cell in enumerate(row[:-1]):  # never the last cell — need a value after it
                nl = _normalise(cell)
                for kw, no in labels:
                    if _normalise(kw) in nl:
                        label_cell_idx = i
                        item_no = no
                        break
                if item_no is not None:
                    break
            if item_no is None or label_cell_idx is None:
                continue
            value = _parse_value(row[label_cell_idx + 1])
            if value is None:
                continue
            matched.append((item_no, value))
        if len(matched) < 6:
            return {}, f"  {company_code} 총괄: found but only {len(matched)}/6 rows matched, skip"
        # First occurrence of each label = 전; second = 후.
        seen: dict[int, list[str]] = defaultdict(list)
        for item_no, value in matched:
            seen[item_no].append(value)
        if not all(len(seen.get(no, [])) >= 2 for _, no in labels):
            return {}, f"  {company_code} 총괄: incomplete pairs {dict((no, len(v)) for no, v in seen.items())}, skip"
        out = {no: (seen[no][0], seen[no][1]) for _, no in labels}
        return out, f"  {company_code} 총괄: rows={len(rows)} matched=6 -> {out}"
    return {}, f"  {company_code} 총괄: <none found>"


def _pick_pre_post_columns(header: list[str]) -> tuple[int | None, int | None]:
    """Return (idx_적용전, idx_적용후) by inspecting the header cells.

    Handles full and short variants:
      - '경과조치 적용 전' / '경과조치 적용 후'
      - '경과조치적용전' / '경과조치적용후'
      - '적용 전' / '적용 후'
      - '전' / '적용 후'   (KR0076 short form)
      - '경과조치 적용' / '전 경과조치 적용 후'  (KR0002 docling split bug)
    """
    pre_idx: int | None = None
    post_idx: int | None = None
    for i, cell in enumerate(header):
        c = cell.replace(" ", "")
        if "적용후" in c or "적용 후" in cell:
            post_idx = i
        elif "적용전" in c or "적용 전" in cell:
            pre_idx = i
    if post_idx is None and pre_idx is not None:
        # Fallback 0: docling truncated the trailing '후' off the post
        # header (KR0070 에이비엘생명 2023.4Q ②표: '경과조치 적용 전' /
        # '경과조치 적용' — the second cell should read '...적용 후' but
        # lost the last character). Any remaining cell to the right of
        # pre_idx that still mentions 적용/경과조치 but not 전 is the
        # truncated post column.
        for i in range(pre_idx + 1, len(header)):
            c = header[i].replace(" ", "")
            if c and "전" not in c and ("적용" in c or "경과조치" in c):
                post_idx = i
                break
    if post_idx is None:
        return None, None
    if pre_idx is None:
        # Fall back 1: KR0076 short form — a cell that is exactly '전'.
        for i, cell in enumerate(header):
            if i == post_idx:
                continue
            c = cell.strip()
            if c == "전":
                pre_idx = i
                break
    if pre_idx is None:
        # Fall back 2: KR0002 docling split bug — '경과조치 적용' followed
        # by a cell whose normalised text *starts* with '전' (the '전'
        # spilled into the next column header). Accept any cell to the
        # left of post_idx that contains '경과조치 적용' or '적용'.
        for i in range(post_idx):
            c = header[i].replace(" ", "")
            if c.endswith("적용") and "경과조치" in c:
                pre_idx = i
                break
    if pre_idx is None:
        # Fall back 3: pure positional — the cell immediately left of
        # post_idx, but only if it contains a numeric-friendly token. We
        # don't enable this universally; it triggers only when post_idx
        # is the rightmost column (typical of pre/post layouts).
        if post_idx >= 1 and post_idx == len(header) - 1:
            pre_idx = post_idx - 1
    return pre_idx, post_idx


def _match_row_label(label: str, mapping: list[tuple[str, int]]) -> int | None:
    """Return item_no for the first keyword in ``mapping`` whose normalised
    form is a substring of the normalised label, else None."""
    nl = _normalise(label)
    if not nl:
        return None
    for kw, item_no in mapping:
        if _normalise(kw) and _normalise(kw) in nl:
            return item_no
    return None


def _extract_post_values(
    tables: list[dict], company_code: str, existing_values: dict[int, str]
) -> tuple[dict[int, tuple[str, str]], dict[int, str], list[str], set[int]]:
    """Return ({item_no: (pre_value, post_value)}, {item_no: source_table}, debug_log_lines,
    unit_fixed_items — item_nos whose (pre,post) pair was rescaled by the
    UNIT-FIX vote below; the caller should trust their *pre_value* over a
    stale existing JSON 값 when mirroring an unchanged cell, since a
    unit-fixed pre_value has already been reconciled against other items in
    the same source table (KR0082 DB생명보험: the ②표's own '백만원' unit
    hint is simply wrong for this filing — every item in it needs ×100 to
    match reality — but item17 personally votes 1:1 so its otherwise-correct
    pre/post still get swept into the group's ×100 correction; the mirror-
    existing-값 fallback then blindly re-substituted the *stale, never-
    corrected* existing 값 for items 29-35 and silently undid the fix).

    Walks the company's tables. Picks at most one common-section table and at
    most one breakdown-section table. For KR0073 (multiple breakdown tables
    in the same MD) the breakdown table is selected as the one whose
    sub-item rows (사망/장수/해지/사업비/대재해) show a 전≠후 difference and
    is not a 시장위험/주식위험/금리위험 시나리오 table.

    ``source_table`` ("common" or "breakdown") records which table each
    item_no's value actually came from — needed because a single company's
    MD can have ONE table mistagged with the wrong 억원/백만원 unit while
    the OTHER is tagged correctly (예별손해보험 KR0004 2023.1Q: 공통적용
    table has no unit hint of its own and inherits a stale "억원" tag from
    an unrelated earlier table, while its ②breakdown table correctly
    declares "백만원"). The scale-mismatch self-correction below must be
    computed and applied per source table, not blended across both.
    """
    log: list[str] = []
    out: dict[int, tuple[str, str]] = {}
    provenance: dict[int, str] = {}
    unit_fixed_items: set[int] = set()

    # --- 공통적용 ----------------------------------------------------------
    chosen_common: dict | None = None
    for t in tables:
        if not _is_common_section(t["headings"]):
            continue
        if _is_market_or_rate_section(t["headings"]):
            continue
        header = t["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is None or post_idx is None:
            continue
        chosen_common = t
        break  # first 공통적용 table wins

    if chosen_common is not None:
        header = chosen_common["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        unit = chosen_common["unit"]
        for row in chosen_common["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            label = row[0]
            item_no = _match_row_label(label, COMMON_ROW_MAP)
            if item_no is None:
                continue
            if item_no in out:
                continue
            pre_v = _parse_value(row[pre_idx])
            post_v = _parse_value(row[post_idx])
            if pre_v is None or post_v is None:
                continue
            if not _is_percent_row(item_no):
                pre_v = _normalise_unit(pre_v, unit)
                post_v = _normalise_unit(post_v, unit)
            out[item_no] = (pre_v, post_v)
            provenance[item_no] = "common"
        log.append(
            f"  {company_code} 공통적용: rows={len(chosen_common['table'])-1}, unit={chosen_common['unit']}"
        )
    else:
        log.append(f"  {company_code} 공통적용: <none found>")

    # --- ② breakdown -------------------------------------------------------
    def _count_breakdown_subitem_diffs(t: dict, pre_idx: int, post_idx: int) -> int:
        diff = 0
        for row in t["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            nl = _normalise(row[0])
            is_sub = any(
                _normalise(kw) in nl
                for kw in ("사망위험", "장수위험", "해지위험", "사업비위험", "대재해위험")
            )
            if not is_sub:
                continue
            # STRICT parsing here (not the dash-as-zero leaf helper): this
            # count exists to prove the table is "live" (a real transition
            # effect happened), and a company that simply doesn't elect this
            # provision renders its WHOLE 적용후 column as dashes (NH농협손해
            # KR0032 2023.2Q ③표: every row incl. 지급여력비율/금액 totals is
            # dash) — treating pre=real/post=dash as a manufactured "diff"
            # would wrongly certify that placeholder table as live and then
            # zero out every leaf item under it. Only a genuine non-dash
            # pre≠post pair (e.g. KR0072 케이디비생명 해지위험 682,308→151,038)
            # should certify the table; dash-as-zero is applied afterwards,
            # in the application loop below, once liveness is already proven.
            pv = _parse_value(row[pre_idx])
            pov = _parse_value(row[post_idx])
            if pv is None or pov is None:
                continue
            if not _values_equal(pv, pov):
                diff += 1
        return diff

    def _table_has_live_headline_diff(t: dict, pre_idx: int, post_idx: int) -> bool:
        """A table's own 지급여력비율/지급여력금액/지급여력기준금액 row showing a
        genuine (strictly-parsed, non-dash) pre!=post pair proves the table is
        live, even when EVERY leaf sub-item happens to land on a dash
        (DB생명보험 KR0082, 처브라이프생명 KR0100: every quarter's real ②
        effect zeroes 장수/해지/사업비/대재해위험 all the way to '-', leaving
        zero strictly-parseable leaf diffs for _count_breakdown_subitem_diffs
        even though 지급여력비율 202.37→361.04 in the same table proves it's
        real — these two companies' entire history was silently dropped by
        the leaf-only liveness check). Deliberately still strict (not the
        dash-as-zero leaf helper): a dash in a headline %/amount row means
        "not meaningful here", not zero, so NH농협손해 KR0032's genuinely-
        inapplicable ③ table (every row incl. 지급여력비율/금액 totals dashed)
        correctly still fails this check too."""
        for row in t["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            nl = _normalise(row[0])
            if not any(
                _normalise(kw) in nl
                for kw in ("지급여력비율", "지급여력금액", "지급여력기준금액")
            ):
                continue
            pv = _parse_value(row[pre_idx])
            pov = _parse_value(row[post_idx])
            if pv is None or pov is None:
                continue
            if not _values_equal(pv, pov):
                return True
        return False

    breakdown_candidates: list[tuple[dict, int]] = []  # (table, diff_count)
    for t in tables:
        if _is_common_section(t["headings"]) and not _is_breakdown_section(t["headings"]):
            # Headings accumulate across every '(1) 공통적용'/'(2) 선택적용'/
            # '① 자본감소분'/'② 장수위험...' marker seen since the last table
            # boundary (KR1010 교보라이프플래닛 2023.2Q: all four land on the
            # SAME physical table when nothing but blank lines separates
            # them from it), so a table can legitimately satisfy both
            # _is_common_section and _is_breakdown_section at once. Only
            # exclude here when it's common-only — a table that also
            # carries the more specific ②-style markers IS the breakdown
            # table (its content confirms this: 지급여력비율 175.40->260.01
            # sub-item rows sit right there), and dropping it left every
            # 29-35 child None despite a live headline diff.
            continue
        if _is_market_or_rate_section(t["headings"]):
            continue
        if not _is_breakdown_section(t["headings"]):
            continue
        header = t["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is None or post_idx is None:
            continue
        diff = _count_breakdown_subitem_diffs(t, pre_idx, post_idx)
        if diff > 0 or _table_has_live_headline_diff(t, pre_idx, post_idx):
            breakdown_candidates.append((t, diff))

    if not breakdown_candidates:
        # Fallback: docling sometimes drops the "② 장수위험·사업비위험·해지
        # 위험 및 대재해위험 경과조치" heading line entirely (한화손해보험
        # KR0002 2025.1Q/3Q·2026.1Q, 롯데손해보험 KR0003 2023.1Q confirmed via
        # raw: the ②-table's real, differing values — e.g. KR0002 2025.1Q
        # 지급여력비율 182.5→215.8 — sit right there in the MD with a valid
        # pre/post header, just with no "②"/"장수위험" heading text above it
        # to classify it, so it silently fell through both the common and
        # breakdown detectors and got treated as "no transition effect"
        # (COPY). Recover it by row-content signature instead of heading:
        # any table with a valid pre/post header AND at least 3 of the 7
        # canonical sub-item row labels is structurally *this* table
        # regardless of what heading (if any) docling left attached to it.
        for t in tables:
            if _is_common_section(t["headings"]) or _is_market_or_rate_section(t["headings"]):
                continue
            header = t["table"][0]
            pre_idx, post_idx = _pick_pre_post_columns(header)
            if pre_idx is None or post_idx is None:
                continue
            row_labels_norm = [_normalise(row[0]) for row in t["table"][1:]]
            sub_label_hits = sum(
                1
                for kw in ("사망위험", "장수위험", "해지위험", "사업비위험", "대재해위험")
                if any(_normalise(kw) in nl for nl in row_labels_norm)
            )
            if sub_label_hits < 3:
                continue
            diff = _count_breakdown_subitem_diffs(t, pre_idx, post_idx)
            if diff > 0 or _table_has_live_headline_diff(t, pre_idx, post_idx):
                breakdown_candidates.append((t, diff))
        if breakdown_candidates:
            log.append(f"  {company_code} breakdown: recovered {len(breakdown_candidates)} candidate(s) via row-content fallback (heading missing)")

    chosen_breakdown: dict | None = None
    if len(breakdown_candidates) == 1:
        chosen_breakdown = breakdown_candidates[0][0]
        log.append(f"  {company_code} breakdown: chose sole candidate (diff_rows={breakdown_candidates[0][1]})")
    elif len(breakdown_candidates) > 1:
        # Multiple breakdown tables with subitem diffs — pick the one with
        # the most diffs (typically the dedicated 장수/해지/사업비 table).
        breakdown_candidates.sort(key=lambda x: -x[1])
        top, top_diff = breakdown_candidates[0]
        second_diff = breakdown_candidates[1][1]
        if top_diff > second_diff:
            chosen_breakdown = top
            log.append(
                f"  {company_code} breakdown: chose top of {len(breakdown_candidates)} candidates (diff_rows={top_diff} vs {second_diff})"
            )
        else:
            log.append(
                f"  {company_code} breakdown: AMBIGUOUS {len(breakdown_candidates)} candidates tied at diff_rows={top_diff} — SKIP"
            )

    if chosen_breakdown is not None:
        header = chosen_breakdown["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        unit = chosen_breakdown["unit"]
        pending_merged_item: int | None = None
        for row in chosen_breakdown["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            label = row[0]
            if pending_merged_item is not None:
                # The merged-label row below skipped its own value cells
                # (they belong to the parent, item17); docling pushed the
                # sub-item's real value down into the NEXT row instead,
                # which renders with a blank label (KR0070 2023.4Q: row
                # '생명·장기손해보험 위험액 사망위험 | 798,006 | 486,104' is
                # item17's pair, the following blank-label row
                # '| 92,888 | 92,888' is item29's true pair).
                item_no, pending_merged_item = pending_merged_item, None
                if not label.strip():
                    pre_v = _parse_leaf_subrisk_value(row[pre_idx])
                    post_v = _parse_leaf_subrisk_value(row[post_idx])
                    if pre_v is not None and post_v is not None and item_no not in out:
                        out[item_no] = (
                            _normalise_unit(pre_v, unit),
                            _normalise_unit(post_v, unit),
                        )
                        provenance[item_no] = "breakdown"
                    continue
                # Not blank after all — fall through and process this row
                # normally below (don't lose it).
            item_no = _match_row_label(label, BREAKDOWN_ROW_MAP)
            if item_no is None:
                continue
            if item_no in _LIFE_SUB_ITEMS and "위험액" in _normalise(label):
                # docling sometimes merges the parent header text into a
                # sub-item's own label cell ("생명·장기손해보험위험액사망위험"
                # — KR0070 2024.1Q), and when it does, the row's *value*
                # cells are the merged-away PARENT's (item17), not the
                # sub-item's own — silently assigning item17's number to
                # item29 breaks the mmult identity. A clean sub-item label
                # (사망위험/장수위험/etc.) never itself contains "위험액", so
                # its presence here is the merge signal; skip rather than
                # apply a value we know is wrong (unless recovered from the
                # next blank-label row above).
                pending_merged_item = item_no
                continue
            if item_no in out and item_no not in _RATIO_TRIAD_ITEMS:
                # The 공통적용 table already gave us this row — keep its
                # value (more authoritative for 기본자본/보완자본 etc., which
                # reflect the TFI reclassification that this breakdown table
                # doesn't fold in — it only varies the sub-items it's named
                # for, e.g. 사업비/해지위험).
                continue
            if item_no in _LIFE_SUB_ITEMS:
                pre_v = _parse_leaf_subrisk_value(row[pre_idx])
                post_v = _parse_leaf_subrisk_value(row[post_idx])
            else:
                pre_v = _parse_value(row[pre_idx])
                post_v = _parse_value(row[post_idx])
            if pre_v is None or post_v is None:
                continue
            if not _is_percent_row(item_no):
                pre_v = _normalise_unit(pre_v, unit)
                post_v = _normalise_unit(post_v, unit)
            # For 지급여력비율/금액/기준금액(27/1/14): when a company has BOTH
            # the common TFI provision AND a selective breakdown-type one
            # (사업비/해지/대재해 등), the 공통적용 table's 후 column only
            # reflects TFI in isolation — 기준금액 is untouched by TFI so it
            # shows 후=전 there, while the ②breakdown table shows the true
            # cumulative 후 (reflecting the selective provision too).
            # Confirmed via raw: 한화손해보험 KR0002 2023.3Q 공통적용
            # 지급여력기준금액 후=전=3,179,538(백만) vs ②breakdown
            # 후=2,138,338 — only the breakdown value satisfies
            # item1/item14×100=item27(283.1). So breakdown always wins for
            # these three when a breakdown table was chosen at all.
            out[item_no] = (pre_v, post_v)
            provenance[item_no] = "breakdown"
        log.append(
            f"  {company_code} breakdown: applied rows={len(chosen_breakdown['table'])-1}, unit={chosen_breakdown['unit']}"
        )
    else:
        log.append(f"  {company_code} breakdown: <none with subitem variation>")

    # --- ③ 주식위험·금리위험 경과조치 --------------------------------------
    # ROOT CAUSE this block fixes (validation ROUND2 반려, 20260707T0930Z):
    # the ② breakdown loop above already sets item19(시장위험액) from ②'s OWN
    # table, but ② never touches market risk — that row is a pure pass-through
    # copy of 적용전, not real information. When a company *also* applies the
    # selective ③ provision (TER 주식위험 증가분 / TIRR 금리위험액 증가분,
    # confirmed via raw IBK연금 2023.1Q md_inbox/FY2023_Q1/KR1011_...md
    # line 300-323), the true post-transition item19/36/37 only exist in
    # ③'s own table — never parsed anywhere before this block existed, so
    # item19_후 silently stayed pinned to ②'s unchanged copy (or None).
    market_rate_candidates: list[tuple[dict, int]] = []
    for t in tables:
        if not _is_market_or_rate_section(t["headings"]):
            continue
        header = t["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is None or post_idx is None:
            continue
        diff = 0
        for row in t["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            item_no = _match_row_label(row[0], MARKET_RATE_ROW_MAP)
            if item_no not in _MARKET_RATE_EFFECT_ITEMS:
                continue
            # STRICT parsing (see the identical note in
            # _count_breakdown_subitem_diffs above): a company that doesn't
            # elect ③ renders its ENTIRE 적용후 column as dashes, including
            # the totals — dash-as-zero here would manufacture a fake
            # "real->0" diff purely from that placeholder and wrongly
            # certify the whole table as live.
            pv = _parse_value(row[pre_idx])
            pov = _parse_value(row[post_idx])
            if pv is None or pov is None:
                continue
            if not _values_equal(pv, pov):
                diff += 1
        if diff > 0:
            market_rate_candidates.append((t, diff))

    chosen_market_rate: dict | None = None
    if len(market_rate_candidates) == 1:
        chosen_market_rate = market_rate_candidates[0][0]
        log.append(f"  {company_code} market_rate(③): chose sole candidate (diff_rows={market_rate_candidates[0][1]})")
    elif len(market_rate_candidates) > 1:
        market_rate_candidates.sort(key=lambda x: -x[1])
        chosen_market_rate = market_rate_candidates[0][0]
        log.append(
            f"  {company_code} market_rate(③): chose top of {len(market_rate_candidates)} candidates (diff_rows={market_rate_candidates[0][1]})"
        )
    else:
        log.append(f"  {company_code} market_rate(③): <none with 금리/주식 variation>")

    if chosen_market_rate is not None:
        header = chosen_market_rate["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        unit = chosen_market_rate["unit"]
        applied = 0
        for row in chosen_market_rate["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            item_no = _match_row_label(row[0], MARKET_RATE_ROW_MAP)
            if item_no is None:
                continue
            if item_no in _MARKET_SUB_LEAF_ITEMS:
                pre_v = _parse_leaf_subrisk_value(row[pre_idx])
                post_v = _parse_leaf_subrisk_value(row[post_idx])
            else:
                pre_v = _parse_value(row[pre_idx])
                post_v = _parse_value(row[post_idx])
            if pre_v is None or post_v is None:
                continue
            pre_v = _normalise_unit(pre_v, unit)
            post_v = _normalise_unit(post_v, unit)
            # ③ is authoritative for its own domain (19/36-40) — overrides
            # whatever pass-through copy ②/공통 may have already set for
            # item19, since only ③ carries genuine information for it.
            out[item_no] = (pre_v, post_v)
            provenance[item_no] = "market_rate"
            applied += 1
        log.append(f"  {company_code} market_rate(③): applied rows={applied}, unit={chosen_market_rate['unit']}")

    # Unit sanity check, scoped per source table: a 공통적용 or ②breakdown
    # table may declare an unreliable `(단위 : 백만원, %)` hint (or inherit a
    # stale one from an earlier, unrelated table — 예별손해보험 KR0004
    # 2023.1Q's 공통적용 table has no unit line of its own and inherits
    # "억원" when its numbers are actually 백만원). Compare each item's MD
    # pre-value against the JSON 값 (authoritative). This MUST run before
    # the item1/27 derivation below — deriving item27 from a still-
    # unit-wrong item1 bakes the error into a ratio row, which is then
    # exempt from correction (a % can't reveal an amount-unit mismatch, so
    # it would never get fixed after the fact).
    votes_by_source: dict[str, list[float]] = defaultdict(list)
    for item_no, (pre_v_md, _post_v_md) in out.items():
        if _is_percent_row(item_no):
            continue
        existing_s = existing_values.get(item_no)
        if existing_s in (None, ""):
            continue
        try:
            existing = float(str(existing_s).replace(",", ""))
            md_pre = float(pre_v_md)
        except (TypeError, ValueError):
            continue
        if md_pre == 0 or existing == 0:
            continue
        ratio = existing / md_pre
        src = provenance.get(item_no, "common")
        if 95 < ratio < 105:
            votes_by_source[src].append(100.0)
        elif 0.0095 < ratio < 0.0105:
            votes_by_source[src].append(0.01)
    for src, votes in votes_by_source.items():
        if not (votes and all(abs(v - votes[0]) < 1e-6 for v in votes)):
            continue
        factor = votes[0]
        log.append(f"  {company_code} UNIT-FIX[{src}]: applied ×{factor} to post values (MD hint mismatch vs JSON 값, votes={len(votes)})")
        for item_no in list(out.keys()):
            if provenance.get(item_no, "common") != src or _is_percent_row(item_no):
                continue
            try:
                pre_v, post_v = out[item_no]
                out[item_no] = (_fmt_amount(float(pre_v) * factor), _fmt_amount(float(post_v) * factor))
                unit_fixed_items.add(item_no)
            except (TypeError, ValueError):
                pass

    # [지급여력비율 총괄] is the company's own headline rollup — always the
    # true cumulative 전/후 regardless of how many separate provisions
    # (①TFI/②장수등/③주식·금리) are stacked. It wins over both common and
    # breakdown for items 1/14/27 when parseable, because neither single
    # provision table alone is reliable once more than one is active:
    # 아이엠라이프생명 KR0076 has BOTH ①TFI (changes the 기본/보완 split
    # *and* the total, item1 629,527→736,195) AND ②장수/사업비/해지 (changes
    # item14 only, 582,352→446,029) — ①'s own item1 row is right but its
    # item14 row is blind to ②'s effect, and vice versa for ②. Conversely
    # 예별손해보험 KR0004 2023.1Q has BOTH ② AND ③(주식·금리, not parsed by
    # this script at all) active, and there it's the ①공통 table whose
    # item14 row happens to already reflect the full cumulative reduction
    # (820,516) while ②'s own row alone only captures its own slice
    # (907,125) — the *opposite* of KR0076's pattern. No fixed table
    # priority is right for every company; only the headline rollup is.
    if not out:
        # Nothing at all matched (no 공통적용/②breakdown table) — try the
        # 감사보고서 별첨 '지급여력금액'/'지급여력기준금액' Roman-numeral
        # statement shape before giving up (하나생명 KR0097 FY-end filings).
        # Require ALL FOUR items at once — a partial hit means the exact-
        # label match landed on some unrelated 2-cell row by coincidence,
        # not this specific statement shape (KR0082 2023.1Q: bare "기본자본"
        # matched a footnote table, giving item2_후 a tiny bogus value).
        audit_vals = _extract_audit_statement_values(tables)
        if set(audit_vals) == {1, 2, 3, 14}:
            for item_no, pair in audit_vals.items():
                out[item_no] = pair
                provenance[item_no] = "audit_statement"

    headline_vals, headline_dbg = _extract_headline_summary(tables, company_code)
    log.append(headline_dbg)
    if headline_vals:
        for item_no, pair in headline_vals.items():
            out[item_no] = pair
            provenance[item_no] = "headline"
    else:
        # Fallback when the headline rollup isn't present/parseable: derive
        # item1(=기본+보완) and item27(=1/14×100) from their resolved parts
        # instead of trusting whichever raw row got matched, so R1/R7 hold
        # by construction even though item14 itself may still be an
        # incomplete (single-provision) view in this fallback path.
        if 2 in out and 3 in out and provenance.get(1) != "audit_statement":
            # Don't clobber a directly-read audit-statement item1 (already
            # includes TAC natively, e.g. 하나생명 KR0097) with a from-parts
            # sum of item2+item3 that predates the TAC addition below.
            try:
                pre1 = float(out[2][0]) + float(out[3][0])
                post1 = float(out[2][1]) + float(out[3][1])
                out[1] = (_fmt_amount(pre1), _fmt_amount(post1))
                provenance[1] = "derived"
            except (TypeError, ValueError):
                pass
        if 1 in out and 14 in out:
            try:
                pre14 = float(out[14][0])
                post14 = float(out[14][1])
                if pre14 != 0 and post14 != 0:
                    pre27 = float(out[1][0]) / pre14 * 100.0
                    post27 = float(out[1][1]) / post14 * 100.0
                    out[27] = (_fmt_ratio(pre27), _fmt_ratio(post27))
                    provenance[27] = "derived"
            except (TypeError, ValueError, ZeroDivisionError):
                pass

    # TAC(자본감소분경과조치) companies: item2/item3 above only reflect the
    # ①TFI reclassification (validation confirmed via raw, KDB KR0072
    # 2023.1Q: 기본자본 84,474→300,474·보완자본 644,136→428,136, netting to
    # zero) — TAC's own amount (342,955) is a *separate* addition to item1
    # that this company's disclosure never attributes to either tier. Add
    # it onto item2 so R1(item1=item2+item3) closes with a real, derived
    # value instead of leaving item2/3 post as if TAC didn't exist.
    tac_amount = _extract_tac_amount(tables)
    if tac_amount is not None and 2 in out:
        try:
            pre2, post2 = out[2]
            out[2] = (pre2, _fmt_amount(float(post2) + float(tac_amount)))
            if provenance.get(1) != "headline" and 3 in out:
                pre3, post3 = out[3]
                pre1 = out.get(1, (None, None))[0]
                out[1] = (pre1, _fmt_amount(float(out[2][1]) + float(post3)))
                provenance[1] = "derived"
                if 14 in out:
                    try:
                        post14 = float(out[14][1])
                        if post14 != 0:
                            pre27 = out.get(27, (None, None))[0]
                            out[27] = (pre27, _fmt_ratio(float(out[1][1]) / post14 * 100.0))
                            provenance[27] = "derived"
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
        except (TypeError, ValueError):
            pass

    # item15(기본요구자본)/item16(분산효과) — validation ROUND2 반려
    # (20260707T0930Z) root cause: neither the ②-table's nor the (new) ③-
    # table's own 기본요구자본 row is the true combined-post value — each is
    # that single provision's *isolated* view. Confirmed via raw (IBK연금
    # 2023.1Q): ②표 기본요구자본후=6,741.36 vs ③표=5,960.09 vs 총괄표
    # 지급여력기준금액후=5,141 — K-ICS 기준금액 is a correlation-matrix
    # diversification (√(V'MV)), not additive, so no combination of the two
    # isolated tables reproduces the true combined figure. What *is* reliably
    # the true combined figure is item14 itself (headline-sourced). The R5
    # identity (item14 = item15 - item22 + item23) is definitional, not
    # approximate, so back-solving item15 from it is exact. item22/23
    # (법인세조정액/기타요구자본) are untouched by every transition type in
    # this domain (TFI/TAC/TIR/TER/TIRR all target capital or insurance/
    # market risk, never tax adjustment or foreign-sub add-ons) — fall back
    # to their pre value when no table set a post value.
    if 14 in out:
        try:
            post14 = float(out[14][1])
            post22 = out.get(22, (None, existing_values.get(22)))[1]
            post23 = out.get(23, (None, existing_values.get(23)))[1]
            post22_f = float(post22) if post22 not in (None, "") else 0.0
            post23_f = float(post23) if post23 not in (None, "") else 0.0
            pre15 = existing_values.get(15)
            if pre15 not in (None, ""):
                out[15] = (pre15, _fmt_amount(post14 + post22_f - post23_f))
                provenance[15] = "derived_identity"
        except (TypeError, ValueError):
            pass

    # item16(분산효과) is never directly disclosed post-transition in any
    # table (confirmed: IBK ②/③ tables have no 분산효과 row at all — only the
    # 적용전 세부 table does) — it exists only as the derived identity
    # sum(17..21) - 15, so there is no "extraction" for it, only this.
    if 15 in out and all(i in out for i in (17, 18, 19, 20, 21)):
        try:
            post15 = float(out[15][1])
            post_subs_sum = sum(float(out[i][1]) for i in (17, 18, 19, 20, 21))
            pre16 = existing_values.get(16)
            if pre16 not in (None, ""):
                out[16] = (pre16, _fmt_amount(post_subs_sum - post15))
                provenance[16] = "derived_identity"
        except (TypeError, ValueError):
            pass

    return out, provenance, log, unit_fixed_items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _process_period(
    rows: list[dict], period_label: str
) -> tuple[int, int, int, list[str]]:
    """Return (rows_updated, rows_equal_skipped, companies_processed, log)."""
    quarter = _md_period_to_quarter(period_label)
    md_dir = MD_INBOX / period_label
    if not md_dir.is_dir():
        return 0, 0, 0, [f"md_inbox/{period_label} missing"]

    # Build an index for fast (code, quarter, item_no) lookup.
    index: dict[tuple[str, str, int], dict] = {}
    for r in rows:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    updated = 0
    equal_skipped = 0
    companies = 0
    log: list[str] = [f"=== {period_label} ({quarter}) ==="]

    for md_path in sorted(md_dir.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        text = md_path.read_text(encoding="utf-8")
        tables = _scan_tables_with_context(text)
        existing_values = {
            item_no: row.get("값")
            for (c, q, item_no), row in index.items()
            if c == code and q == quarter
        }
        post_map, provenance, dbg, unit_fixed_items = _extract_post_values(tables, code, existing_values)
        log.extend(dbg)

        # 농협생명(KR0104) 2023.2Q · 하나생명(KR0097) 2023.2Q (amended 재제출본):
        # 두 회사 다 raw PDF의 "[지급여력비율의 경과조치 적용에 관한 사항]"
        # 페이지들이 docling 변환에서 md_inbox로 아예 안 넘어옴(0 occurrence —
        # 재변환/재docling 필요, downloader/parser-docling 단계 갭이지 이
        # 스크립트 로직 문제가 아님) — `post_map`이 통째로 비어 위 continue에
        # 걸려 아무 것도 못 적재했음. item1/14/27후는 이미 JSON에 올바르게
        # 들어있음(다른 경로로 헤드라인 확보) — 깨진 건 item2/3후뿐이라
        # validation이 R1(item1=item2+item3) 위반으로 적발
        # (`inbox/parser/20260707T2223Z`). fitz로 raw PDF 직접 재확인:
        #   KR0104: ①TFI표(p11) 기본자본 3,019,101→3,269,101백만·보완자본
        #     4,167,868→3,917,868백만 = 32,691.01/39,178.68억(현재 JSON의
        #     41,871은 [경과조치 적용 전] 표의 *직전분기(1Q)* 보완자본값이
        #     잘못 흘러든 것 — 82페이지 헤드라인 item1후=71,870과 지금
        #     32,691.01+39,178.68=71,869.69로 정합).
        #   KR0097: ①TAC표(p12) 자본감소분 38,380백만(383.80억)이 item2에
        #     아예 반영 안 됨(315,582→315,582 그대로 저장돼 있었음) — 관례대로
        #     item2에 가산: 3,155.82+383.80=3,539.62억, item3은 TAC 비대상이라
        #     불변(2,428.32억, 현재 2,541은 출처 불명 — 폐기). 합 5,967.94 ≈
        #     헤드라인 item1후 5,968.
        if code == "KR0104" and quarter == "2023.2Q":
            if existing_values.get(2) not in (None, ""):
                post_map[2] = (existing_values[2], "32691.01")
            if existing_values.get(3) not in (None, ""):
                post_map[3] = (existing_values[3], "39178.68")
            log.append(f"  {code}: KR0104 2023.2Q missing-docling-pages override applied (item2/3 post)")
        if code == "KR0097" and quarter == "2023.2Q":
            if existing_values.get(2) not in (None, ""):
                post_map[2] = (existing_values[2], "3539.62")
            if existing_values.get(3) not in (None, ""):
                post_map[3] = (existing_values[3], "2428.32")
            log.append(f"  {code}: KR0097 2023.2Q missing-docling-pages override applied (item2/3 post)")

        if not post_map:
            continue
        companies += 1

        # 푸본현대(KR0083) 2023.1Q: its ①자본감소분(TAC) table has label and
        # value columns scrambled by docling in a way no other filing in
        # this corpus shows (label text lands in the *last* cell of each
        # row instead of the first) — _extract_tac_amount's "자본감소분 in
        # row[0]" scan can't find it, so item2/3 fall back to the ②-table's
        # pass-through (TAC-blind) view and break R1/item28 against the
        # reliable headline (item1_후=13,977). raw-verified split (validation
        # F1 thread, 20260706): item2_후=5,415.52 · item3_후=8,561.52 (sum
        # 13,977.04 ≈ headline 13,977). Explicit override here — instead of a
        # one-off JSON edit outside the script — so it survives re-runs.
        if code == "KR0083" and quarter == "2023.1Q" and 2 in post_map and 3 in post_map:
            post_map[2] = (post_map[2][0], "5415.52")
            post_map[3] = (post_map[3][0], "8561.52")
            log.append(f"  {code}: KR0083 2023.1Q TAC-garbled-table override applied (item2/3 post)")

        # 롯데손해보험(KR0003) 2023.1Q: its ②-equivalent table (heading
        # "： 장기손해보험 장수위험·사업비위험·해지위험 및 대재해위험 경과조치")
        # has a 5-cell header (구분/경과조치/적용전/경과조치/적용후, docling
        # split "경과조치 적용 전"/"경과조치 적용 후" into 2 cells each) whose
        # data rows are inconsistently shaped — the 해지/사업비/대재해위험 rows
        # (the very ones TIR zeroes) render their post cell one column short
        # ("- " lands in the pre_idx+1 slot, post_idx itself blank), so the
        # generic pre/post reader sees no parseable post value for any of
        # them and the whole table gets rejected as "no subitem variation".
        # raw-verified (해당 표 그대로): 지급여력비율후=178.33, 지급여력기준
        # 금액후=14,493, 기본요구자본후=18,145, 생명장기위험액후=9,384,
        # 해지·사업비·대재해위험후=0 (전부 TIR로 zeroed, 나머지 세부는 불변).
        if code == "KR0003" and quarter == "2023.1Q":
            _kr0003_override = {
                14: "14493", 15: "18145", 16: "7054", 17: "9384", 18: "523",
                19: "9160", 20: "5059", 21: "1073", 22: "3652",
                27: "178.33436832", 29: "770", 31: "9158", 32: "279",
                33: "0", 34: "0", 35: "0",
            }
            for _item_no, _post_v in _kr0003_override.items():
                _pre_v = existing_values.get(_item_no)
                if _pre_v in (None, ""):
                    continue
                post_map[_item_no] = (_pre_v, _post_v)
            log.append(f"  {code}: KR0003 2023.1Q row-shifted-breakdown-table override applied (14/15/16/17-23/27/29/31/32/33/34/35 post)")

        # 롯데손해보험(KR0003) 2026.1Q: raw엔 "(1) 공통적용 경과조치 관련"
        # 헤딩만 있고 표가 아예 없음(바로 "(2) 선택적용..."으로 넘어감) + ①TAC는
        # 명시 미적용(전부 "-") + ②표도 원문에 없음(수익성 섹션으로 바로 점프) —
        # 이 분기는 raw에 tier-split 표 자체가 없음. 유일하게 신뢰 가능한 신호는
        # 헤드라인(item1후=26,955=item1전 — TAC/TFI 둘 다 무효과 확정)이므로
        # item2/3후 = item2/3전(불변)이 유일하게 일관된 값 — 기존에 박혀있던
        # -3,421.44/29,479.93(출처 불명, 항등식 위반)을 대체.
        if code == "KR0003" and quarter == "2026.1Q":
            if existing_values.get(2) not in (None, ""):
                post_map[2] = (existing_values[2], existing_values[2])
            if existing_values.get(3) not in (None, ""):
                post_map[3] = (existing_values[3], existing_values[3])
            log.append(f"  {code}: KR0003 2026.1Q no-tier-split-table override applied (item2/3 post = pre)")

        # Apply to existing rows. Never overwrite 값; only set 값_적용후
        # when the **markdown** post value differs from the **markdown**
        # pre value (the two values come from the same table and have
        # identical rounding/unit). We do NOT compare to the JSON 값
        # because the JSON value can differ by rounding (e.g. 1229 vs
        # 1228.9) — that would falsely look like a 변동. (Unit-mismatch
        # self-correction already happened inside _extract_post_values,
        # before the item1/27 derivation there — see its docstring.)
        company_updates = 0
        company_equal = 0
        # 경과조치 적용사(공통적용 표에서 전≠후가 하나라도 있는 회사)는 **모든**
        # 항목을 전=후여도 명시 적재한다 — 지급여력금액1·기본자본2·보완자본3·
        # 지급여력기준금액14·비율27뿐 아니라 세부위험 29-35 등도 마찬가지
        # (owner 2026-07-07, `inbox/parser/20260707T0710Z`: "미공시라 비웠으면
        # 화면에서 숨기든가, mmult 닫히는 숫자를 뽑든가 — 부모후만 채우고 자식후는
        # 비워두면 화면에 안 맞는 숫자가 뜬다"). 이유는 두 갈래: (a) 지급여력
        # 기준금액 적용후(14후)가 전과 같아도(요구자본 base 불변, 가용자본만
        # 경과조치) 명시 적재돼야 검증식 (2후+3후)/14후×100≈27후 가 닫힌다
        # (validation 20260612 신규-2). (b) 세부위험(예: 사망위험) 후=전인데
        # None으로 비워두면 디자이너가 null→적용전 폴백으로 base와 섞어 mmult가
        # 깨진 숫자를 화면에 낸다 — null은 "진짜 미공시"에만 남겨야 한다.
        #
        # 예외 = item19(시장위험액): 자식(36-40후)은 이 스크립트가 아예 안 건드림
        # (스코프 밖) — item19후만 "불변"으로 명시 적재하면 부모는 확정인데
        # 자식은 여전히 미검증인 채로 남아 정확히 같은 반쪽채움 문제를 반대
        # 방향으로 재현한다(mmult 게이트가 자식결측을 못 보고 부모값만으로
        # 잘못 통과/실패 판정). item19는 실제로 값이 달라질 때만 적재.
        _NEVER_FORCE_UNCHANGED = {19}
        is_transition = any(
            not _values_equal(pre_v, post_v) for pre_v, post_v in post_map.values()
        )
        for item_no, (pre_v_md, post_v_md) in post_map.items():
            row = index.get((code, quarter, item_no))
            if row is None:
                # Don't create new rows here — sub-item rows are created by
                # fill_subitems_to_disclosure.py. This script only annotates
                # existing rows.
                continue
            force_unchanged = is_transition and item_no not in _NEVER_FORCE_UNCHANGED
            md_unchanged = _values_equal(pre_v_md, post_v_md)
            if md_unchanged and not force_unchanged:
                company_equal += 1
                continue
            if md_unchanged and item_no not in unit_fixed_items:
                # No real transition effect on this item per *this* table —
                # mirror the row's own already-established 값 rather than
                # this table's own pre-column. A company can have a 공통적용/
                # ② table whose own pre-column rounds/scopes slightly
                # differently from the JSON's already-validated 값 (AIA생명
                # KR0080·카카오페이 KR1098 2023.x: their table's pre-column
                # disagreed with 값 by a few %) — writing that table's pre
                # value straight into 값_적용후 leaks the cross-table drift
                # in as a fake "post-transition delta", tripping rule9/10's
                # monotonicity check even though nothing actually changed.
                #
                # EXCEPT when this item was already UNIT-FIXed (rescaled by
                # the vote mechanism above): a unit-fixed pre_v_md has
                # already been reconciled against sibling items in the same
                # table via a *different* signal (mutual consistency, e.g.
                # item2+item3==item1) and is more trustworthy than a stale
                # existing 값 that itself was never through that check
                # (KR0082 DB생명보험: the ②표's '백만원' label is simply
                # wrong for the whole table; items 29-35's existing 값 came
                # from a *different* script/table and was never corrected,
                # so mirroring it here silently undid the ×100 fix).
                existing_v = row.get("값")
                value_to_write = existing_v if existing_v not in (None, "") else post_v_md
            else:
                value_to_write = post_v_md
            # Only set if different. Don't overwrite existing 값_적용후 with
            # the same value (keeps idempotency).
            if row.get("값_적용후") != value_to_write:
                row["값_적용후"] = value_to_write
                company_updates += 1
        updated += company_updates
        equal_skipped += company_equal
        log.append(f"  {code}: +{company_updates} 값_적용후 added, {company_equal} equal-skipped")

    return updated, equal_skipped, companies, log


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--period", action="append")
    parser.add_argument("--all-periods", action="store_true")
    args = parser.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")

    if args.all_periods:
        periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q?") if p.is_dir())
    elif args.period:
        periods = args.period
    else:
        periods = ["FY2025_Q4"]
    print(f"processing periods: {periods}\n")

    total_updated = 0
    total_equal = 0
    total_companies = 0
    for period in periods:
        u, e, c, log = _process_period(rows, period)
        for line in log:
            print(line)
        print(
            f"  -> {period} totals: {u} 값_적용후 added across {c} companies, {e} equal-skipped"
        )
        print()
        total_updated += u
        total_equal += e
        total_companies += c

    print(f"GRAND TOTAL: {total_updated} 값_적용후 added, {total_equal} equal-skipped, {total_companies} companies touched")

    if args.dry_run:
        print("(dry-run; no write)")
        return 0
    if total_updated == 0:
        print("nothing to write")
        return 0
    JSON_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(rows)} rows to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
