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
    """Strip whitespace/punctuation/Roman numerals for fuzzy label matching."""
    if s is None:
        return ""
    return re.sub(r"[\s\(\)\[\]\.\,\:·\-\+\*Ⅰ-Ⅹⅰ-ⅸ㈜]+", "", s)


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
    return tables


_NEGATION_TOKENS = ("적용하지않아", "미적용", "동일함", "동일하므로", "동일한")


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
            followers = window[i + 1 : i + 3]
            if any(
                any(tok in _normalise(f) for tok in _NEGATION_TOKENS)
                for f in followers
            ):
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
    """Skip 주식위험/금리위험 경과조치 section even if heading also mentions 경과조치."""
    ctx = _heading_context(headings)
    return "주식위험" in ctx or "금리위험" in ctx


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
    tables: list[dict], company_code: str
) -> tuple[dict[int, tuple[str, str]], list[str]]:
    """Return ({item_no: (pre_value, post_value)}, debug_log_lines).

    Walks the company's tables. Picks at most one common-section table and at
    most one breakdown-section table. For KR0073 (multiple breakdown tables
    in the same MD) the breakdown table is selected as the one whose
    sub-item rows (사망/장수/해지/사업비/대재해) show a 전≠후 difference and
    is not a 시장위험/주식위험/금리위험 시나리오 table.
    """
    log: list[str] = []
    out: dict[int, tuple[str, str]] = {}

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
        log.append(
            f"  {company_code} 공통적용: rows={len(chosen_common['table'])-1}, unit={chosen_common['unit']}"
        )
    else:
        log.append(f"  {company_code} 공통적용: <none found>")

    # --- ② breakdown -------------------------------------------------------
    breakdown_candidates: list[tuple[dict, int]] = []  # (table, diff_count)
    for t in tables:
        if _is_common_section(t["headings"]):
            continue
        if _is_market_or_rate_section(t["headings"]):
            continue
        if not _is_breakdown_section(t["headings"]):
            continue
        header = t["table"][0]
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is None or post_idx is None:
            continue
        # Count subitem rows that differ.
        diff = 0
        for row in t["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            label = row[0]
            nl = _normalise(label)
            is_sub = any(
                _normalise(kw) in nl
                for kw in ("사망위험", "장수위험", "해지위험", "사업비위험", "대재해위험")
            )
            if not is_sub:
                continue
            pv = _parse_value(row[pre_idx])
            pov = _parse_value(row[post_idx])
            if pv is None or pov is None:
                continue
            if not _values_equal(pv, pov):
                diff += 1
        if diff > 0:
            breakdown_candidates.append((t, diff))

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
        for row in chosen_breakdown["table"][1:]:
            if max(pre_idx, post_idx) >= len(row):
                continue
            label = row[0]
            item_no = _match_row_label(label, BREAKDOWN_ROW_MAP)
            if item_no is None:
                continue
            if item_no in out:
                # The 공통적용 table already gave us this row — keep its
                # value (more authoritative for 공통적용 items).
                continue
            pre_v = _parse_value(row[pre_idx])
            post_v = _parse_value(row[post_idx])
            if pre_v is None or post_v is None:
                continue
            if not _is_percent_row(item_no):
                pre_v = _normalise_unit(pre_v, unit)
                post_v = _normalise_unit(post_v, unit)
            out[item_no] = (pre_v, post_v)
        log.append(
            f"  {company_code} breakdown: applied rows={len(chosen_breakdown['table'])-1}, unit={chosen_breakdown['unit']}"
        )
    else:
        log.append(f"  {company_code} breakdown: <none with subitem variation>")

    return out, log


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
        post_map, dbg = _extract_post_values(tables, code)
        log.extend(dbg)
        if not post_map:
            continue
        companies += 1

        # Apply to existing rows. Never overwrite 값; only set 값_적용후
        # when the **markdown** post value differs from the **markdown**
        # pre value (the two values come from the same table and have
        # identical rounding/unit). We do NOT compare to the JSON 값
        # because the JSON value can differ by rounding (e.g. 1229 vs
        # 1228.9) — that would falsely look like a 변동.
        #
        # Unit sanity check: a 공통적용 table may declare an unreliable
        # `(단위 : 백만원, %)` hint when the actual numbers are 억원 (KR0001
        # FY2023_Q1). Compare each item's MD pre-value against the JSON 값
        # (authoritative from main 4-2-1 table). If the ratio is ≈100 or
        # ≈0.01, derive a global correction factor and rescale post_v_md.
        company_updates = 0
        company_equal = 0
        # First pass: detect per-company unit-mismatch factor from items
        # where existing JSON 값 is reliable (items 1, 2, 3, 14 in 억원).
        scale_correction = 1.0
        votes: list[float] = []
        for item_no, (pre_v_md, _post_v_md) in post_map.items():
            if item_no not in (1, 2, 3, 14):
                continue
            row = index.get((code, quarter, item_no))
            if row is None or row.get("값") in (None, ""):
                continue
            try:
                existing = float(str(row["값"]).replace(",", ""))
                md_pre = float(pre_v_md)
            except (TypeError, ValueError):
                continue
            if md_pre == 0 or existing == 0:
                continue
            ratio = existing / md_pre
            if 95 < ratio < 105:
                votes.append(100.0)
            elif 0.0095 < ratio < 0.0105:
                votes.append(0.01)
        if votes and all(abs(v - votes[0]) < 1e-6 for v in votes):
            scale_correction = votes[0]
            log.append(f"  {code} {quarter} UNIT-FIX: applied ×{scale_correction} to post values (MD hint mismatch vs JSON 값, votes={len(votes)})")
        for item_no, (pre_v_md, post_v_md) in post_map.items():
            row = index.get((code, quarter, item_no))
            if row is None:
                # Don't create new rows here — sub-item rows are created by
                # fill_subitems_to_disclosure.py. This script only annotates
                # existing rows.
                continue
            if _values_equal(pre_v_md, post_v_md):
                company_equal += 1
                continue
            # Apply scale correction (e.g., ×100 when MD said 백만원 but values were 억원).
            # Skip correction for ratios (item 27 = 지급여력비율, item 28 if present
            # in post_map — though item 28 not in COMMON_ROW_MAP).
            if scale_correction != 1.0 and not _is_percent_row(item_no):
                try:
                    post_v_md = str(float(post_v_md) * scale_correction)
                    if post_v_md.endswith(".0"):
                        post_v_md = post_v_md[:-2]
                except (TypeError, ValueError):
                    pass
            # Only set if different. Don't overwrite existing 값_적용후 with
            # the same value (keeps idempotency).
            if row.get("값_적용후") != post_v_md:
                row["값_적용후"] = post_v_md
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
