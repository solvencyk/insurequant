"""Add 생명장기손해보험위험액 sub-item rows to kics_disclosure.json.

Adds 6 sub-item rows (and 1 optional 대재해위험) per (company × period)
under new item numbers 29..35:

  29: 사망위험액           ─ "1-1. 사망위험액"
  30: 장수위험액           ─ "1-2. 장수위험액"
  31: 장해·질병위험액      ─ "1-3. 장해·질병위험액"
  32: 장기재물·기타위험액  ─ "1-4. 장기재물·기타위험액"
  33: 해지위험액           ─ "1-5. 해지위험액"
  34: 사업비위험액         ─ "1-6. 사업비위험액"
  35: 대재해위험액         ─ "1-7. 대재해위험액"   (separately disclosed)

These are sub-items of item 17 ("1. 생명장기손해보험위험액"). The integer
item number scheme of the existing file is preserved (no sub-numbering like
17.1) so downstream consumers that key by 항목번호 still work.

UPSERT semantics: existing (회사, 분기, 항목번호) rows are never touched —
only missing rows are appended. This script is idempotent.

Usage:
    python scripts/fill_subitems_to_disclosure.py [--dry-run] [--period FY2025_Q4]
        [--period FY2024_Q4 ...]    # multiple periods
        [--all-periods]             # walk every md_inbox/<period>/
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

# Period label (md_inbox folder)  →  공시분기 string used in JSON.
_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")


def _md_period_to_quarter(period_label: str) -> str:
    """FY2025_Q4 → 2025.4Q (the convention used in 공시분기)."""
    m = _PERIOD_RE.match(period_label)
    if not m:
        raise ValueError(f"unrecognised period label: {period_label}")
    return f"{m.group(1)}.{m.group(2)}Q"


def _quarter_prior(quarter: str) -> str:
    """'2025.4Q' → '2025.3Q' ; '2025.1Q' → '2024.4Q'."""
    m = re.match(r"^(\d{4})\.([1-4])Q$", quarter)
    if not m:
        raise ValueError(f"unrecognised quarter: {quarter}")
    y, q = int(m.group(1)), int(m.group(2))
    if q == 1:
        return f"{y - 1}.4Q"
    return f"{y}.{q - 1}Q"


# Sub-item definitions: (item_no, display_name, [match keywords in order of precedence])
# Match keywords are checked against a normalised label string (no spaces/punct).
SUBITEMS: list[tuple[int, str, list[str]]] = [
    (29, "1-1. 사망위험액", ["사망위험"]),
    (30, "1-2. 장수위험액", ["장수위험"]),
    (31, "1-3. 장해·질병위험액", ["장해질병위험", "장해·질병위험", "장해질병", "장해"]),
    (32, "1-4. 장기재물·기타위험액", ["장기재물기타위험", "장기재물·기타위험", "장기재물기타", "장기재물"]),
    (33, "1-5. 해지위험액", ["해지위험"]),
    (34, "1-6. 사업비위험액", ["사업비위험"]),
    (35, "1-7. 대재해위험액", ["대재해위험"]),
]

TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")

# Patterns for picking the column whose header refers to the current period.
# Reused conventions from fill_2025_q4_to_disclosure.py.


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
    for ch in ("△", "▲", "▽", "▼", "−"):
        cleaned = cleaned.replace(ch, "-")
    cleaned = cleaned.lstrip("+-") if cleaned.startswith("+-") else cleaned
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
    """Like _parse_value, but a bare dash in a leaf sub-risk cell (29-35)
    means the company discloses zero exposure to that specific risk, not
    "no data" — same convention as _parse_leaf_subrisk_value in
    fill_post_transition_to_disclosure.py (KR0072 케이디비생명 2023.2Q ②표:
    장수위험 46,364→'-' sits beside a real, non-dash 해지위험 change, dashed
    is the same disclosure taken to its zero extreme). Without this, a row
    whose ONLY value is a dash never gets created at all here (this script's
    strict _parse_value returns None -> row skipped), which then makes the
    *post*-transition mmult check permanently unable to certify item17
    (89 of 135 residual Tier-B gaps traced to exactly this — item32
    장기재물·기타위험 row missing entirely, not just its 적용후 field)."""
    if raw is not None and raw.strip().replace(",", "") in _DASH_TOKENS:
        return "0"
    return _parse_value(raw)


def _make_quarter_column_picker(quarter: str):
    """Return a function(header_cells) -> idx for this period's value column.

    The sub-item detail tables tend to use the '경과조치 적용 전 / 적용 후'
    layout (no quarter label in the header — the table itself is dated by
    the surrounding section). For those we pick '경과조치 적용 전'. For
    the main K-ICS detail table we recognise the usual quarter labels.

    Header variants seen across companies:
      - '경과조치 적용 전' / '경과조치 적용 후'   ← sub-item table primary
      - '당분기 (25.4Q)' / '당분기 (2025.4Q)'
      - '2025년 4/4분기' / '4/4분기' / 'FY2025'
    """
    y_full, q = quarter.split(".")
    q_num = q.rstrip("Q")
    y_short = y_full[-2:]
    fy_short = f"{y_short}.{q_num}Q"
    fy_full = f"{y_full}.{q_num}Q"
    period_month_short = {"1": "06", "2": "09", "3": "12", "4": "03"}[q_num]
    period_year_for_q4 = str(int(y_full) + 1) if q_num == "4" else y_full

    def _pick(header_cells: list[str]) -> int | None:
        # PRIORITY 1: 경과조치 적용 전. (적용 후 must NOT match — it's the
        # alternate column right next to it.)
        for i, cell in enumerate(header_cells):
            c = cell.replace(" ", "")
            if "경과조치적용전" in c and "후" not in c:
                return i
        # PRIORITY 1b: short / split header variants. Only fire when at
        # least one header cell explicitly says '적용 후' (or '적용후') —
        # that's our anchor for being inside a 경과조치 pre/post layout.
        post_idx: int | None = None
        for i, cell in enumerate(header_cells):
            c = cell.replace(" ", "")
            if "적용후" in c:
                post_idx = i
                break
        if post_idx is not None:
            # KR0076 short form: a cell that is exactly '전'.
            for i, cell in enumerate(header_cells):
                if i == post_idx:
                    continue
                if cell.strip() == "전":
                    return i
            # KR0050 docling split bug: header split as
            # '경과조치 적용 | 전 경과조치 | 적용 후'. The 'pre' column is
            # the middle cell whose text starts with '전 ' — pick it.
            for i in range(post_idx):
                stripped = header_cells[i].strip()
                if stripped.startswith("전 ") or stripped.startswith("전\t"):
                    return i
            # KR0002 docling split bug: '경과조치 적용' cell followed by
            # '전 경과조치 적용 후' — find the '경과조치 적용' cell to the
            # left of post_idx.
            for i in range(post_idx):
                c = header_cells[i].replace(" ", "")
                if c.endswith("적용") and "경과조치" in c:
                    return i
            # Bare '적용 전' (no 경과조치 prefix).
            for i, cell in enumerate(header_cells):
                if i == post_idx:
                    continue
                c = cell.replace(" ", "")
                if "적용전" in c and "후" not in c:
                    return i
        # PRIORITY 2: quarter labels on the main K-ICS detail table.
        for i, cell in enumerate(header_cells):
            c = cell.replace(" ", "")
            if "당분기" in c and not any(x in c for x in ("-1", "-2", "-3", "1분기", "2분기", "3분기")):
                return i
            if fy_short in c or fy_full in c:
                return i
            if f"{y_full}년{q_num}/4분기" in c or f"{y_full}년{q_num}/4" in c:
                return i
            if f"{q_num}/4분기" in c and y_full not in c and y_short not in c:
                return i
            if c.startswith(f"년분기{y_full}{q_num}") or c == f"{y_full}{q_num}":
                return i
            if f"{q_num}분기{y_full}" in c:
                return i
            if c in (f"FY{y_full}결산", f"FY{y_full}", f"{y_full}결산", "당기결산"):
                return i
            if "당기말" in c or f"당기({y_short}" in c:
                return i
            if q_num == "4" and (f"{period_year_for_q4}.{period_month_short}" in c
                                 or f"{period_year_for_q4}.{int(period_month_short)}." in c):
                return i
            if q_num != "4" and (f"{y_full}.{period_month_short}" in c
                                 or f"{y_full}.{int(period_month_short)}." in c):
                return i
        # PRIORITY 3: 생명/장기/총계 breakdown (e.g. Meritz KR0001).
        for i, cell in enumerate(header_cells):
            c = _normalise(cell)
            if "총계" in c:
                return i
        return None
    return _pick


def _pick_subitem_column(header_rows: list[list[str]], quarter: str) -> int | None:
    """Pick value column; prefer 대재해위험액 over 익스포져 in 2-row headers."""
    pick = _make_quarter_column_picker(quarter)
    if len(header_rows) >= 2:
        sub = header_rows[1]
        for i, cell in enumerate(sub):
            c = cell.replace(" ", "")
            if "\ub300\uc7ac\ud574\uc704\ud5d8\uc561" in c and "\uc775\uc2a4\ud3ec\uc90c" not in c:
                return i
    if header_rows:
        idx = pick(header_rows[0])
        if idx is not None:
            return idx
    return None


# Existing kics_disclosure.json uses 억원 (100M KRW). Sub-item tables in
# the 경과조치 적용 전/후 section commonly use 백만원 (1M KRW). When the
# tracked unit hint preceding a table says 백만원, divide by 100.
_UNIT_HINT_RE = re.compile(r"\(\s*단위\s*[:：]?\s*[^)]*?(억원|백만원|만원|천원|원)[^)]*\)")


def _extract_unit_hint(line: str, next_lines: list[str] | None = None) -> str | None:
    """Extract (단위: …) from one line or a short multi-line blob.

    Handles docling splits such as ``(`` + ``단위 : 백만원 )``, reversed
    ``(단위 백만원 : )``, and KR1098-style ``단위 (`` + ``백 만원 : )``.

    Table rows (``| … |``) are never unit hints — some disclosures embed
    ``단위: 백만원, %`` inside a header cell (KR1098).
    """
    if TABLE_ROW_RE.match(line):
        return None
    m = _UNIT_HINT_RE.search(line)
    if m:
        return m.group(1)
    blob = line
    if next_lines:
        blob = " ".join([line, *next_lines[:2]])
    compact = re.sub(r"\s+", "", blob)
    if "단위" not in compact:
        return None
    m2 = re.search(r"단위[^)]*?(억원|백만원|만원|천원|원)", compact)
    if m2:
        return m2.group(1)
    m3 = re.search(r"(억원|백만원|만원|천원|원)\s*[:：]", blob)
    if m3 and "단위" in compact:
        return m3.group(1)
    return None


def _normalise_unit(value: str, unit: str) -> str:
    """Return a string value rescaled to 억원."""
    try:
        f = float(str(value).replace(",", ""))
    except ValueError:
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
    # Match existing JSON style: integer-like → int string, else one decimal.
    if abs(scaled - round(scaled)) < 1e-6:
        return str(int(round(scaled)))
    return f"{scaled:.2f}".rstrip("0").rstrip(".")


def _looks_like_period_cell(s: str) -> bool:
    """True if a cell holds a period tag ('당기', '(2025.4Q)', ...) rather than
    a real row label — used to see past merged-cell continuation artifacts
    where a period tag repeats down every row of its block (KR0087/KR0099
    생명·장기손해보험위험액 현황 tables)."""
    if s is None:
        return True
    t = s.strip()
    if t == "":
        return True
    if re.search(r"\(\d{4}\.\dQ\)", t):
        return True
    return t in ("당기", "직전반기", "직전 반기", "직전분기", "직전 분기", "전기", "전분기")


def _row_is_target_period(row0: str, quarter: str) -> bool:
    """Skip prior-period rows like '(2025.2Q)' when filling the current quarter.

    When row0 is empty (multi-column 현황 tables like KR0008/0011/1000 where
    the period column is elsewhere or implicit), accept — block-level pick
    already chose the right column.
    """
    if row0 is None:
        return True
    if row0.strip() == "":
        return True
    if row0.strip() in ("구분", "-"):
        return False
    y_full, q = quarter.split(".")
    q_num = q.rstrip("Q")
    target = f"{y_full}.{q_num}Q"
    norm = row0.replace(" ", "")
    m = re.search(r"\((\d{4}\.\dQ)\)", row0)
    if m:
        tagged = m.group(1)
        if tagged == target:
            return True
        if "당기" in norm and target in norm:
            return True
        return False
    if "당기" in norm:
        return target in norm or f"{y_full[-2:]}.{q_num}Q" in norm
    if any(kw in norm for kw in ("직전반기", "직전분기", "전기말", "전분기", "전기")):
        return False
    return True


def _is_merged_life_parent_death_label(norm_label: str) -> bool:
    """KR0070 경과조치 요약표: parent row label merges life total + 사망위험."""
    return (
        "사망위험" in norm_label
        and "생명" in norm_label
        and "장기손해보험" in norm_label
    )


def _is_general_insurance_catastrophe_label(label: str) -> bool:
    """일반손해 '대재해 위험' row — not life item 35.

    Some disclosures render this with a space ('대재해 위험') to distinguish it
    from life item 35's '대재해위험' (no space) — the only textual signal
    available when both rows share one merged-cell table (KR1011). When a
    company renders both identically (KR0051), this can't disambiguate by
    label text alone and needs a per-cell data override instead.
    """
    stripped = label.strip()
    return bool(re.fullmatch(r"대재해\s+위험\s*", stripped))


def _is_life_catastrophe_table(table_text: str) -> bool:
    """Life/long-term catastrophe tables only (exclude general-insurance sections)."""
    t = table_text.replace(" ", "")
    if "대재해" not in t:
        return False
    if any(
        x in t
        for x in (
            "일반손해",
            "자연재해",
            "보험가격",
            "준비금위험",
            "대형사고재물",
            "대형보증",
            "풍수해위험",
            "지진위험",
        )
    ):
        return False
    return any(x in t for x in ("전염병", "생명보험", "생명장기", "경과조치"))


def _has_life_catastrophe_markers(table_text: str) -> bool:
    """Positive-only version of _is_life_catastrophe_table's check, without the
    general-insurance exclusion — for tables that legitimately merge both
    sections under one 경과조치 breakdown (KR1011/KR1010: '생명·장기손해보험
    위험액' block immediately followed by '일반손해보험 위험액' block in the
    same table). Pair with a row-position check (has the '일반손해보험' section
    marker been seen yet?) rather than throwing out the whole table."""
    t = table_text.replace(" ", "")
    if "대재해" not in t:
        return False
    return any(x in t for x in ("전염병", "생명보험", "생명장기", "경과조치"))


def _is_general_insurance_section_marker(norm_label: str) -> bool:
    return "일반손해보험" in norm_label and "위험액" in norm_label


def _item35_row_priority(norm_label: str) -> int:
    """Lower is better. Prefer life catastrophe total (총계) rows."""
    if "총계" in norm_label:
        return 0
    if "전염병" in norm_label or "대형사고" in norm_label:
        return 1
    return 2


def _row_label_text(row: list[str]) -> str:
    """Risk label may sit in col 0, col 1, or col 2.

    Common shapes:
      KR0001 multi-cell  : ['', '위험액', '사망위험', '-', '507710', '507710'] → col 2
      KR0008 sparse rows : ['', '', '장해·질병위험', '-', '4518856', '4518856'] → col 2
      KR1000 breakdown   : ['', '사망위험', '392363', '8126', '400490']         → col 1
      Standard           : ['사망위험', ...]                                       → col 0
    """
    if len(row) >= 3 and _normalise(row[1]) == "위험액":
        return row[2]
    # Walk leading empty/period-tag cells to find the first non-empty label
    # cell (period tag may repeat down every row of its block instead of
    # being blank, e.g. '당기 (2024.2Q)' on every 당기 row — KR0087/KR0099).
    if row and _looks_like_period_cell(row[0]):
        for i in range(1, min(3, len(row))):
            if row[i].strip():
                return row[i]
    return row[0] if row else ""


def _scan_subitem_rows(md_text: str, quarter: str) -> dict[int, str]:
    """Walk every markdown table and pull values for each sub-item.

    Tracks ``(단위: 백만원)`` style hints that precede each table so values
    can be rescaled to 억원 (the unit used by the existing JSON).

    Returns {item_no: value_string}.
    """
    pick = _make_quarter_column_picker(quarter)
    lines = md_text.splitlines()
    tables: list[tuple[list[list[str]], str]] = []  # (table, unit_for_table)
    current: list[list[str]] = []
    current_unit = "억원"  # default assumption for K-ICS disclosures

    def _flush() -> None:
        if current:
            tables.append((current.copy(), current_unit))
            current.clear()

    for i, line in enumerate(lines):
        unit_hint = _extract_unit_hint(line, lines[i + 1 : i + 3])
        if unit_hint:
            current_unit = unit_hint
            # don't flush — unit hint applies to NEXT table
            continue
        if TABLE_ROW_RE.match(line):
            cells = _split_row(line)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            current.append(cells)
        else:
            _flush()
    _flush()

    out: dict[int, str] = {}
    candidates_35: list[tuple[int, str]] = []
    for tbl, unit in tables:
        if not tbl or len(tbl) < 2:
            continue
        header_rows = tbl[:2] if len(tbl) >= 2 else [tbl[0]]
        col_idx = _pick_subitem_column(header_rows, quarter)
        if col_idx is None:
            col_idx = pick(tbl[0])
        if col_idx is None:
            continue
        # KR1000 case: 현황 table with '생명보험 / 장기손해보험 / 총계'
        # signature and no nearby (단위: ...) hint — the inherited
        # current_unit can be stale (e.g. 천원 from an unrelated upstream
        # table). K-ICS 보조지표 tables are standardised to 백만원; assume
        # that for this signature when the tracked unit looks unrelated.
        norm_header = "".join(_normalise(c) for c in tbl[0])
        is_breakdown_layout = (
            "총계" in norm_header
            and ("생명보험" in norm_header or "장기손해보험" in norm_header)
        )
        full_table_text = " ".join(" ".join(r) for r in tbl)
        is_life_catastrophe = _is_life_catastrophe_table(full_table_text)
        eff_unit = unit
        if is_breakdown_layout:
            eff_unit = "백만원"
        elif is_life_catastrophe and unit == "억원":
            # Life catastrophe detail tables are virtually always 백만원 when
            # the unit hint was split across lines (KR0009/KR1098/KR0095).
            eff_unit = "백만원"
        elif unit in ("천원", "원", "만원"):
            eff_unit = "백만원" if is_breakdown_layout else unit
        if is_breakdown_layout:
            for i, cell in enumerate(tbl[0]):
                if "총계" in _normalise(cell):
                    col_idx = i
                    break
        table_text = " ".join(" ".join(r) for r in tbl[:3])
        is_daejaehae_table = "\ub300\uc7ac\ud574\uc704\ud5d8" in table_text.replace(" ", "")
        pending_death_continuation = False
        current_period_tag = None
        in_general_section = False
        for row in tbl[1:]:
            if col_idx >= len(row):
                continue
            row0 = row[0] if row else ""
            if row0 is not None and row0.strip() != "":
                current_period_tag = row0
            # A blank row0 that follows a tagged block is a merged-cell
            # continuation of that block's period, not "period unknown"
            # (KR0087/KR0099: 당기 block repeats its tag on every row, but
            # 직전반기 block only tags its first row, leaving later rows
            # blank — without inheriting, those blank rows fall through
            # _row_is_target_period's "unknown → accept" default and get
            # silently mixed into the current quarter's values).
            effective_row0 = current_period_tag if current_period_tag is not None else row0
            if not _row_is_target_period(effective_row0, quarter):
                continue
            label = _row_label_text(row)
            value_cell = row[col_idx]
            if pending_death_continuation and 29 not in out and value_cell:
                v = _parse_leaf_subrisk_value(value_cell)
                if v is not None:
                    out[29] = _normalise_unit(v, eff_unit)
                pending_death_continuation = False
                continue
            if not label or not value_cell:
                continue
            norm_label = _normalise(label)
            if _is_general_insurance_section_marker(norm_label):
                in_general_section = True
            if _is_merged_life_parent_death_label(norm_label):
                pending_death_continuation = True
                continue
            for item_no, _, keywords in SUBITEMS:
                match_keys = list(keywords)
                if item_no == 35 and is_daejaehae_table and is_life_catastrophe:
                    match_keys.append("\ucd1d\uacc4")
                if not any(_normalise(kw) in norm_label for kw in match_keys):
                    continue
                if item_no == 35 and _is_general_insurance_catastrophe_label(label):
                    continue
                v = _parse_leaf_subrisk_value(value_cell)
                if v is None:
                    continue
                if item_no == 35:
                    # A merged table can legitimately hold both the life and
                    # general-insurance \ub300\uc7ac\ud574\uc704\ud5d8 rows (KR1011/KR1010); only
                    # reject rows we've walked past the '\uc77c\ubc18\uc190\ud574\ubcf4\ud5d8' section
                    # marker for, not the whole table (regression: KR0051/
                    # KR1011 both mix sections in one table and were losing
                    # the whole table, including the correct life row).
                    if not is_life_catastrophe and not _has_life_catastrophe_markers(full_table_text):
                        continue
                    if in_general_section:
                        continue
                    if _is_general_insurance_catastrophe_label(label):
                        continue
                    try:
                        raw_f = float(str(v).replace(",", ""))
                        if eff_unit == "백만원" and raw_f > 1_000_000:
                            continue
                    except ValueError:
                        continue
                    scaled = _normalise_unit(v, eff_unit)
                    candidates_35.append((_item35_row_priority(norm_label), scaled))
                    continue
                scaled = _normalise_unit(v, eff_unit)
                if item_no in out:
                    continue
                out[item_no] = scaled
                break
    if candidates_35:
        non_zero = [(p, c) for p, c in candidates_35 if float(str(c).replace(",", "")) > 0]
        pool = non_zero if non_zero else candidates_35
        out[35] = min(pool, key=lambda x: (x[0], -float(str(x[1]).replace(",", ""))))[1]
    return out


def _baseline_meta_for_company(rows: list[dict], code: str) -> dict[str, str] | None:
    """Find 원수사명/티커/생손보여부 for a company from any existing row."""
    for r in rows:
        if r["원보험사코드"] == code:
            return {
                "원수사명": r["원수사명"],
                "티커": r["티커"],
                "생손보여부": r["생손보여부"],
            }
    return None


def _existing_keys_for_period(rows: list[dict], quarter: str) -> set[tuple[str, int]]:
    return {(r["원보험사코드"], r["항목번호"]) for r in rows if r["공시분기"] == quarter}


def _parent_value(rows: list[dict], code: str, quarter: str) -> float | None:
    """Item 17: '1. 생명장기손해보험위험액' — for the sanity-check sum."""
    for r in rows:
        if (
            r["원보험사코드"] == code
            and r["공시분기"] == quarter
            and r["항목번호"] == 17
        ):
            try:
                return float(str(r["값"]).replace(",", ""))
            except (ValueError, TypeError):
                return None
    return None


def _process_period(
    rows: list[dict], period_label: str, dry_run: bool, refresh: bool = False
) -> tuple[list[dict], int, list[tuple[str, int, int]], list[str]]:
    """Return (new_rows, updated_count, summary, warnings)."""
    quarter = _md_period_to_quarter(period_label)
    md_dir = MD_INBOX / period_label
    if not md_dir.is_dir():
        return [], 0, [], [f"md_inbox/{period_label} missing"]

    existing = _existing_keys_for_period(rows, quarter)
    row_index = {
        (r["원보험사코드"], r["항목번호"]): r
        for r in rows
        if r["공시분기"] == quarter and r["항목번호"] in range(29, 36)
    }

    new_rows: list[dict] = []
    updated = 0
    summary: list[tuple[str, int, int]] = []
    warnings: list[str] = []

    md_files = sorted(md_dir.glob("*.md"))
    for md_path in md_files:
        code = md_path.stem.split("_", 1)[0]
        meta = _baseline_meta_for_company(rows, code)
        if not meta:
            warnings.append(f"{period_label} {code}: no baseline metadata (skip)")
            continue
        text = md_path.read_text(encoding="utf-8")
        found = _scan_subitem_rows(text, quarter)
        # Parent gate: 생명장기손해보험위험액(item17)=0 ⇒ company has no
        # life/long-term business, so sub-risks 29-35 cannot exist. Drop any
        # match (e.g. a 일반손해 대재해 row leaking into the life slot).
        parent17 = _parent_value(rows, code, quarter)
        if parent17 is not None and parent17 <= 0:
            found = {}
        matched = sum(1 for n in (29, 30, 31, 32, 33, 34) if n in found)
        missed = 6 - matched

        for item_no, item_name, _ in SUBITEMS:
            if item_no not in found:
                continue
            key = (code, item_no)
            if key in row_index:
                if refresh and row_index[key].get("값") != found[item_no]:
                    row_index[key]["값"] = found[item_no]
                    updated += 1
                continue
            if key in existing:
                continue
            new_rows.append(
                {
                    "원보험사코드": code,
                    "원수사명": meta["원수사명"],
                    "티커": meta["티커"],
                    "생손보여부": meta["생손보여부"],
                    "항목번호": item_no,
                    "항목명": item_name,
                    "공시분기": quarter,
                    "값": found[item_no],
                }
            )
        summary.append((code, matched, missed))
    return new_rows, updated, summary, warnings


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="update existing sub-item rows when MD values differ",
    )
    parser.add_argument(
        "--period",
        action="append",
        help="period label like FY2025_Q4 (may be passed multiple times)",
    )
    parser.add_argument(
        "--all-periods",
        action="store_true",
        help="process every FYxxxx_Qy folder under md_inbox/",
    )
    args = parser.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")

    if args.all_periods:
        periods = sorted(
            p.name for p in MD_INBOX.glob("FY*_Q?") if p.is_dir()
        )
    elif args.period:
        periods = args.period
    else:
        periods = ["FY2025_Q4"]

    print(f"processing periods: {periods}\n")

    all_new: list[dict] = []
    total_updated = 0
    all_summaries: dict[str, list[tuple[str, int, int]]] = {}
    all_warnings: list[str] = []

    for period in periods:
        new_rows, updated, summary, warnings = _process_period(
            rows, period, args.dry_run, refresh=args.refresh
        )
        total_updated += updated
        all_summaries[period] = summary
        all_warnings.extend(warnings)
        all_new.extend(new_rows)
        print(f"=== {period} ({_md_period_to_quarter(period) if _PERIOD_RE.match(period) else '?'}) ===")
        print(f"  md files scanned: {len(summary)}")
        print(f"  new rows queued:  {len(new_rows)}")
        full = [c for c, m, miss in summary if m == 6]
        partial = [(c, m) for c, m, miss in summary if 0 < m < 6]
        zero = [c for c, m, miss in summary if m == 0]
        print(f"  full match (6/6): {len(full)}  {full[:8]}{'...' if len(full)>8 else ''}")
        if partial:
            print(f"  partial:          {len(partial)}  {partial[:8]}")
        if zero:
            print(f"  ZERO match:       {len(zero)}  {zero}")
        print()

    if all_warnings:
        print("warnings:")
        for w in all_warnings:
            print(f"  - {w}")
        print()

    # Cross-quarter check: warn when 6 sub-items disappear for a company that
    # had them in the immediately prior quarter.
    print("=== cross-quarter regression check ===")
    by_co_qtr_items: dict[tuple[str, str], set[int]] = defaultdict(set)
    combined = rows + all_new
    for r in combined:
        if r["항목번호"] in (29, 30, 31, 32, 33, 34):
            by_co_qtr_items[(r["원보험사코드"], r["공시분기"])].add(r["항목번호"])
    regressions: list[str] = []
    target_quarters = sorted({_md_period_to_quarter(p) for p in periods if _PERIOD_RE.match(p)})
    for q in target_quarters:
        prev = _quarter_prior(q)
        for (code, qtr), items in by_co_qtr_items.items():
            if qtr != q:
                continue
            prev_items = by_co_qtr_items.get((code, prev), set())
            if prev_items and len(items) < len(prev_items):
                missing = sorted(prev_items - items)
                regressions.append(
                    f"  {code} {q}: had {len(prev_items)} sub-items at {prev}, "
                    f"now {len(items)} (missing item_no {missing})"
                )
    if regressions:
        print("regression(s) detected:")
        for r in regressions:
            print(r)
    else:
        print("  no regressions vs prior quarter")
    print()

    # Sanity: 1-1..1-6 sum vs item 17. Diversification benefit means it WON'T
    # exactly equal item 17 — but if the ratio is wildly off, flag it.
    print("=== sum vs 1. 생명장기손해보험위험액 (item 17) ===")
    for period in periods:
        if not _PERIOD_RE.match(period):
            continue
        q = _md_period_to_quarter(period)
        co_to_subs: dict[str, dict[int, str]] = defaultdict(dict)
        for r in combined:
            if r["공시분기"] == q and r["항목번호"] in (29, 30, 31, 32, 33, 34):
                co_to_subs[r["원보험사코드"]][r["항목번호"]] = r["값"]
        anomalies: list[str] = []
        for code, subs in sorted(co_to_subs.items()):
            if len(subs) != 6:
                continue
            try:
                total = sum(float(str(v).replace(",", "")) for v in subs.values())
            except ValueError:
                continue
            parent = _parent_value(combined, code, q)
            if parent is None or parent <= 0:
                continue
            ratio = total / parent
            # Diversification typically gives ratio ~1.2-1.6 (sum > parent).
            if ratio < 0.95 or ratio > 2.5:
                anomalies.append(f"  {code} {q}: sum={total:,.0f}  parent={parent:,.0f}  ratio={ratio:.2f}")
        if anomalies:
            print(f"  {period} anomalies ({len(anomalies)}):")
            for a in anomalies:
                print(a)
        else:
            print(f"  {period}: all sums within sane range vs item 17")
    print()

    print(f"TOTAL new rows across all periods: {len(all_new)}")
    print(f"TOTAL updated rows: {total_updated}")

    if args.dry_run:
        print("(dry-run; no write)")
        return 0

    if not all_new and not total_updated:
        print("nothing to write")
        return 0

    rows.extend(all_new)
    JSON_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(rows)} rows to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
