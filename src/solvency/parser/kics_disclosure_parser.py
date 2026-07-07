"""Parse K-ICS disclosure detail tables from markdown."""

from __future__ import annotations

import re
from typing import Callable

from solvency.parser.company_handlers import (
    AUDIT_LABEL_ALIASES,
    apply_label_fixes,
    build_section_end_patterns,
    build_section_start_patterns,
)

TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")

SECTION_START_PATTERNS = build_section_start_patterns()

SECTION_END_PATTERNS = build_section_end_patterns()


def _strip_label_punct(s: str) -> str:
    return apply_label_fixes(s)


def normalise_label(s: str) -> str:
    if s is None:
        return ""
    s = _strip_label_punct(s)
    s = s.replace("\uc774\uc678\uc758", "\uc774\uc678")
    return re.sub(
        r"[\s\(\)\[\]\.\,\:\-\+\*"
        r"\u2160-\u2169\u2170-\u2178"
        r"]+",
        "",
        s,
    ).lower()


def core_words(s: str) -> str:
    if s is None:
        return ""
    s = _strip_label_punct(s)
    return re.sub(
        r"[0-9A-Za-z\s\(\)\[\]\.\,\:\-\+\*"
        r"\u2160-\u2169\u2170-\u2178\u3231"
        r"]+",
        "",
        s,
    ).lower()


def parse_value(raw: str) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().replace(",", "")
    if cleaned in ("", "-", "\u2500", "\u2013"):
        return None
    cleaned = cleaned.rstrip("%").strip()
    trailing_minus = re.fullmatch(r"(\d[\d.]*)\s+-", cleaned)
    if trailing_minus:
        cleaned = "-" + trailing_minus.group(1)
    for ch in ("\u25b3", "\u25b2", "\u25bd", "\u25bc", "\u2212"):
        cleaned = cleaned.replace(ch, "-")
    cleaned = re.sub(r"^([+-])\s+", r"\1", cleaned)
    cleaned = cleaned.lstrip("+-") if cleaned.startswith("+-") else cleaned
    paren = re.fullmatch(r"\((-?\d[\d.]*)\)", cleaned)
    if paren:
        cleaned = "-" + paren.group(1)
    if not re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
        return None
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
    return cleaned


def split_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def make_quarter_column_picker(quarter: str) -> Callable[[list[str]], int | None]:
    y_full, q = quarter.split(".")
    q_num = q.rstrip("Q")
    y_short = y_full[-2:]
    fy_short = f"{y_short}.{q_num}Q"
    fy_full = f"{y_full}.{q_num}Q"
    period_month_short = {"1": "06", "2": "09", "3": "12", "4": "03"}[q_num]
    period_year_for_q4 = str(int(y_full) + 1) if q_num == "4" else y_full

    def _pick(header_cells: list[str]) -> int | None:
        def _exact_quarter_match(c: str) -> bool:
            if fy_short in c or fy_full in c:
                return True
            # '2023 년 1Q' (동양 2023.1Q) — compact form '2023년1Q'
            if f"{y_full}년{q_num}Q" in c:
                return True
            if "4/4\ubd84\uae30" in c and q_num == "4":
                return True
            if f"{y_full}\ub144{q_num}\ubd84\uae30" in c or f"{period_year_for_q4}.12" in c:
                return True
            if f"{y_full}\ub144{q_num}/4\ubd84\uae30" in c:
                return True
            if f"{q_num}/4\ubd84\uae30" in c and y_full in c:
                return True
            # OCR-scrambled headers ("2026\ub144 1\ubd84\uae30" -> "\ub144 \ubd84\uae30 2026 1"): generalize to the
            # target year instead of the 2025 literals these patterns were first seen on.
            if c.startswith("\ub144\ubd84\uae30" + y_full + q_num) or c == f"{y_full}{q_num}":
                return True
            if f"4\ubd84\uae30{y_full}" in c and q_num == "4":
                return True
            if c in (f"FY{y_full}\uacb0\uc0b0", f"FY{y_full}", f"{y_full}\uacb0\uc0b0", "\ub2f9\uae30\uacb0\uc0b0") and q_num == "4":
                return True
            if "\ub2f9\uae30\ub9d0" in c or f"\ub2f9\uae30({y_short}" in c:
                return True
            if period_month_short in c and y_full in c:
                return True
            # '2023년 (2023년 3월)' (예별손해보험 style: calendar quarter-end
            # month spelled out twice instead of '23.1Q'/'당분기') — item12
            # cellshift root-cause investigation (2026-07-07) found this
            # header shape falls through every check above, so
            # extract_kics_detail_rows never finds this quarter's column,
            # the whole core detail table extraction bails, and a narrower
            # fallback table (missing item12 entirely) is used instead.
            _cal_q_end_month = {"1": "3", "2": "6", "3": "9", "4": "12"}[q_num]
            if f"{y_full}년({y_full}년{_cal_q_end_month}월)" in c:
                return True
            return False

        for i, cell in enumerate(header_cells):
            c = cell.replace(" ", "")
            if _exact_quarter_match(c):
                return i
        for i, cell in enumerate(header_cells):
            c = cell.replace(" ", "")
            if "\ub2f9\ubd84\uae30" in c and not any(
                x in c
                for x in ("-1", "-2", "-3", "1\ubd84\uae30", "2\ubd84\uae30", "3\ubd84\uae30")
            ):
                return i
            if "\ud574\ub355\ubd84\uae30" in c and not any(
                x in c
                for x in ("-1", "-2", "-3", "1\ubd84\uae30", "2\ubd84\uae30", "3\ubd84\uae30")
            ):
                return i
        return None

    return _pick


def extract_kics_detail_section(md: str) -> str | None:
    for pat in SECTION_START_PATTERNS:
        m = pat.search(md)
        if m:
            start = m.end()
            end = len(md)
            for end_pat in SECTION_END_PATTERNS:
                em = end_pat.search(md, start)
                if em:
                    end = min(end, em.start())
            return md[start:end]
    return None


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


_ITEM4_CANONICAL = (
    "\u2160. \uac74\uc804\uc131\uac10\ub3c5\uae30\uc900 \uc7ac\ubb34\uc0c1\ud0dc\ud45c \uc0c1\uc758 \uc21c\uc790\uc0b0"
)
_TRAILING_NUM_LABEL = re.compile(r"^(.+?)\s+(\d+)\.\s*$")
_MID_NUM_LABEL = re.compile(r"^(.+?)\s+(\d+)\.\s*(.+)$")
_CAPITAL_LABEL_HINTS = (
    "\ubcf4\ud1b5\uc8fc",
    "\uc774\uc775\uc789\uc5ec\uae08",
    "\uc790\ubcf8\uc870\uc815",
    "\uae30\ud0c0\ud3ec\uad04\uc190\uc775",
    "\ube44\uc9c0\ubc30\uc9c0\ubd84",
    "\uc870\uc815\uc900\ube44\uae08",
    "\uc790\ubcf8\uc99d\uad8c",
)


def _canonicalize_table_label(label: str) -> list[str]:
    """Return label variants (KakaoPay/MetLife reversed numbering, item4 wording)."""
    stripped = label.strip()
    if not stripped:
        return []
    variants: list[str] = [stripped]
    if (
        "\u2160.\uc21c\uc790\uc0b0" in stripped
        and "\uac74\uc804\uc131" in stripped
        and not stripped.startswith("\u2160")
    ):
        variants.append(_ITEM4_CANONICAL)
    trailing = _TRAILING_NUM_LABEL.match(stripped)
    if trailing:
        variants.append(f"{trailing.group(2)}. {trailing.group(1).strip()}")
    mid = _MID_NUM_LABEL.match(stripped)
    if mid:
        prefix, num, suffix = mid.group(1).strip(), mid.group(2), mid.group(3).strip()
        canonical = f"{num}. {prefix} {suffix}".strip() if suffix else f"{num}. {prefix}"
        variants.append(canonical)
    out: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        out.append(variant)
        mapped = _AUDIT_LABEL_ALIASES.get(variant)
        if mapped and mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
    return out


def _register_label_pairs(
    label: str,
    value: str,
    seen: set[str],
    pairs: list[tuple[str, str]],
) -> None:
    for variant in _canonicalize_table_label(label):
        if variant in seen:
            continue
        pairs.append((variant, value))
        seen.add(variant)


def _is_top_level_diversification_label(label: str) -> bool:
    """Item 16 only: exclude life/market sub-table rows labelled merely '분산효과'."""
    stripped = label.strip()
    if "\ubd84\uc0b0\ud6a8\uacfc" not in stripped:
        return False
    compact = stripped.replace(" ", "")
    if "(1+2+3+4+5)" in compact:
        return True
    if stripped.startswith(("-", "\u2010")):
        return True
    if compact in ("(\ubd84\uc0b0\ud6a8\uacfc)", "\ubd84\uc0b0\ud6a8\uacfc:"):
        return True
    return False


def _looks_like_kics_row(label: str) -> bool:
    stripped = label.strip()
    if not stripped:
        return False
    return (
        stripped.startswith(("\uac00", "\ub098", "\ub2e4"))
        or stripped.startswith(("\u2160", "\u2161", "\u2162", "\u2163", "\u2164"))
        or re.match(r"^\d+\.", stripped) is not None
        or stripped.startswith("-")
        or "\uae30\ubcf8\uc790\ubcf8" in stripped
        or "\ubcf4\uc644\uc790\ubcf8" in stripped
        or _is_top_level_diversification_label(stripped)
        or "\uc704\ud5d8\uc561" in stripped
        or "\ubc95\uc778\uc138" in stripped
        or "\uc694\uad6c\uc790\ubcf8" in stripped
        or _TRAILING_NUM_LABEL.match(stripped) is not None
        or (
            _MID_NUM_LABEL.match(stripped) is not None
            and any(h in stripped for h in _CAPITAL_LABEL_HINTS)
        )
        or ("\uc21c\uc790\uc0b0" in stripped and "\uac74\uc804\uc131" in stripped)
    )


def _iter_section_tables(section: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in section.splitlines():
        if TABLE_ROW_RE.match(line):
            cells = split_row(line)
            if _is_separator_row(cells):
                continue
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def _audit_parse_windows(md: str) -> list[str]:
    lines = md.splitlines()
    windows: list[str] = []
    seen_starts: set[int] = set()
    for i, line in enumerate(lines):
        if re.search(
            r"\uc9c0\uae09\uc5ec\ub825(?:\uae08\uc561|\uae30\uc900\uae08\uc561).*\uc81c\s*\d+\uae30",
            line,
        ) or re.search(r"^##\s*\uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561", line):
            start = max(0, i - 8)
            if start in seen_starts:
                continue
            seen_starts.add(start)
            windows.append("\n".join(lines[start : i + 140]))
    if not windows:
        for needle in ("\u2167. \uc9c0\uae09\uc5ec\ub825\uae08\uc561", "\u2164. \uc9c0\uae09\uc5ec\ub825\uae08\uc561"):
            pos = md.find(needle)
            if pos >= 0:
                windows.append(md[max(0, pos - 800) : pos + 4000])
                break
    return windows


def _unit_scale_from_context(lines: list[str], idx: int) -> float:
    for j in range(max(0, idx - 80), idx):
        line = lines[j]
        if "(단위" not in line and "단위 :" not in line and "단위:" not in line:
            continue
        if "천원" in line:
            return 100_000.0
        if "백만원" in line:
            return 100.0
        if "억원" in line:
            return 1.0
    return 1.0


def _audit_pre_transition_col(table_rows: list[list[str]]) -> int | None:
    for row in table_rows:
        for i, cell in enumerate(row):
            if "\uc801\uc6a9 \uc804" in cell.replace(" ", ""):
                return i
    return None


def _audit_pre_transition_col_from_window(lines: list[str]) -> int | None:
    for line in lines:
        if not TABLE_ROW_RE.match(line):
            continue
        cells = split_row(line)
        col = _audit_pre_transition_col([cells])
        if col is not None:
            return col
    return None


def _audit_value_from_row(cells: list[str], pre_col: int | None) -> str | None:
    dash = ("-", "\u2500", "\u2013")

    def _cell_value(idx: int) -> str | None:
        if idx >= len(cells):
            return None
        cell = cells[idx].strip()
        if not cell:
            return None
        if cell in dash:
            return "-"
        if parse_value(cell) is not None:
            return cell
        return None

    if pre_col is not None:
        hit = _cell_value(pre_col)
        if hit is not None:
            return hit
    for idx in range(1, len(cells)):
        hit = _cell_value(idx)
        if hit is not None:
            return hit
    return None


_AUDIT_LABEL_ALIASES = AUDIT_LABEL_ALIASES


def _audit_label_aliases(label: str) -> list[str]:
    stripped = label.strip()
    aliases = [stripped]
    hit = _AUDIT_LABEL_ALIASES.get(stripped)
    if hit:
        aliases.append(hit)
    if "\uc0dd\uba85" in stripped and "\uc704\ud5d8\uc561" in stripped:
        aliases.append(re.sub(r"[\u00b7\u318d]", "", stripped))
    return aliases


def _is_balance_sheet_junk_row(label: str, scaled_val: str) -> bool:
    stripped = label.strip()
    if re.match(r"^[1-6]\.", stripped) and "\uc704\ud5d8\uc561" not in stripped:
        try:
            num = abs(float(scaled_val))
        except ValueError:
            return False
        if num > 50_000:
            return True
    return False


def _looks_like_audit_kics_row(label: str) -> bool:
    stripped = label.strip()
    if not stripped:
        return False
    if _looks_like_kics_row(stripped):
        return True
    if re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦ]", stripped):
        return True
    if re.match(r"^[가나다]\.", stripped):
        return True
    if re.match(r"^\d+\.", stripped) and "\uc704\ud5d8\uc561" in stripped:
        return True
    if stripped.startswith(("-", "\u2010")) and "\ubd84\uc0b0\ud6a8\uacfc" in stripped:
        return True
    return False


def _format_scaled_value(raw: str, val: str, scale: float) -> str:
    if not val or "%" in raw:
        return val
    num = float(val)
    if scale == 1.0 and num >= 10_000:
        scale = 100_000.0
    if scale == 1.0:
        return val
    scaled = num / scale
    if abs(scaled - round(scaled)) < 1e-6:
        return str(int(round(scaled)))
    return f"{scaled:.8f}".rstrip("0").rstrip(".")


def extract_kics_audit_fallback_rows(md: str) -> list[tuple[str, str]]:
    """Parse K-ICS summary rows from audit/K-ICS doc tables when IR detail section is absent."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for window in _audit_parse_windows(md):
        lines = window.splitlines()
        pre_col = _audit_pre_transition_col_from_window(lines)
        table_rows: list[list[str]] = []
        for idx, line in enumerate(lines):
            if not TABLE_ROW_RE.match(line):
                continue
            cells = split_row(line)
            if _is_separator_row(cells) or not cells:
                continue
            table_rows.append(cells)
            label = cells[0].strip()
            if not label or "..." in label:
                continue
            if not _looks_like_audit_kics_row(label):
                continue
            raw = _audit_value_from_row(cells, pre_col)
            if raw is None:
                continue
            cleaned = raw.strip()
            if cleaned in ("", "-", "\u2500", "\u2013"):
                val = "0"
            else:
                val = parse_value(raw)
                if val is None:
                    continue
                scale = _unit_scale_from_context(lines, idx)
                val = _format_scaled_value(raw, val, scale)
                if _is_balance_sheet_junk_row(label, val):
                    continue
                if "\ubd84\uc0b0\ud6a8\uacfc" in label and val.startswith("-"):
                    val = val.lstrip("-")
            for alias in _audit_label_aliases(label):
                if alias in seen:
                    continue
                pairs.append((alias, val))
                seen.add(alias)

    return pairs


SUMMARY_OVERVIEW_RE = re.compile(
    r"(?:\[\s*\uc9c0\uae09\uc5ec\ub825\ube44\uc728\s*\ucd1d\uad04\s*\]"
    r"|[\u203b\*\uFEFF]?\s*\uc9c0\uae09\uc5ec\ub825\ube44\uc728[^\n]{0,40}\ucd1d\uad04)",
    re.I,
)
SUMMARY_METRIC_LABELS = (
    "\uc9c0\uae09\uc5ec\ub825\uae08\uc561",
    "\uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561",
    "\uc9c0\uae09\uc5ec\ub825\ube44\uc728",
)


def _normalise_summary_label(cell: str) -> str:
    return re.sub(r"\([^)]*\)", "", cell).strip()


def extract_kics_summary_overview_rows(md: str, quarter: str) -> list[tuple[str, str]]:
    """Parse [지급여력비율총괄] when solvency amount and SCR sit in a split label table."""
    m = SUMMARY_OVERVIEW_RE.search(md)
    if not m:
        return []
    chunk = md[m.end() : m.end() + 5000]
    pick_col = make_quarter_column_picker(quarter)
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for tbl in _iter_section_tables(chunk):
        if len(tbl) < 2:
            continue
        col_idx = pick_col(tbl[0])
        if col_idx is None and len(tbl[0]) > 1:
            col_idx = pick_col(tbl[0])
        if col_idx is None:
            continue
        for row in tbl[1:]:
            if col_idx >= len(row):
                continue
            raw = row[col_idx].strip()
            if raw in ("", "-", "\u2500", "\u2013"):
                continue
            label = ""
            for cell in row[: min(3, len(row))]:
                c = _normalise_summary_label(cell.strip())
                if any(met in c for met in SUMMARY_METRIC_LABELS):
                    label = c
                    break
            if not label:
                continue
            val = parse_value(raw)
            if val is None:
                continue
            if label in seen:
                continue
            pairs.append((label, val))
            seen.add(label)
        if pairs:
            break
    return pairs


def _normalise_tax_adjustment_value(item_no: int, item_name: str, value: str) -> str:
    """Item 22 (법인세조정액) is stored as positive magnitude for rule 5 (14 = 15 - 22 + 23)."""
    if item_no != 22 or "\ubc95\uc778\uc138" not in item_name:
        return value
    try:
        num = float(value)
    except ValueError:
        return value
    if num < 0:
        mag = abs(num)
        if abs(mag - round(mag)) < 1e-6:
            return str(int(round(mag)))
        return str(mag)
    return value


def extract_kics_detail_rows(md: str, quarter: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, val in extract_kics_summary_overview_rows(md, quarter):
        pairs.append((label, val))
        seen.add(label)

    section = extract_kics_detail_section(md)
    if section:
        pick_col = make_quarter_column_picker(quarter)
        active_col_idx: int | None = None

        for tbl in _iter_section_tables(section):
            if not tbl:
                continue

            header_idx = pick_col(tbl[0])
            if header_idx is not None:
                active_col_idx = header_idx
                data_rows = tbl[1:]
            elif active_col_idx is not None and _looks_like_kics_row(tbl[0][0]):
                data_rows = tbl
            else:
                continue

            for row in data_rows:
                if active_col_idx is None or active_col_idx >= len(row):
                    continue
                label = row[0]
                value = row[active_col_idx]
                if not label or not value or label in seen:
                    continue
                if not _looks_like_kics_row(label):
                    continue
                _register_label_pairs(label, value, seen, pairs)

    if pairs:
        return pairs
    anywhere = _kics_detail_table_anywhere_rows(md, quarter)
    if anywhere:
        return anywhere
    pp = _kics_pre_post_table_rows(md)
    if pp:
        return pp
    return extract_kics_audit_fallback_rows(md)


def _tables_with_positions(lines: list[str]) -> list[tuple[int, list[list[str]]]]:
    tables: list[tuple[int, list[list[str]]]] = []
    current: list[list[str]] = []
    start = 0
    for i, line in enumerate(lines):
        if TABLE_ROW_RE.match(line):
            cells = split_row(line)
            if _is_separator_row(cells):
                continue
            if not current:
                start = i
            current.append(cells)
        else:
            if current:
                tables.append((start, current))
                current = []
    if current:
        tables.append((start, current))
    return tables


def _nearest_preceding_unit_scale(lines: list[str], idx: int) -> float:
    """Nearest '(단위: …)' marker ABOVE line idx (within 80 lines). Unlike
    _unit_scale_from_context this scans backwards, so an earlier unrelated
    table's unit can't shadow the one attached to this table."""
    for j in range(idx - 1, max(0, idx - 80) - 1, -1):
        line = lines[j]
        if "(단위" not in line and "단위 :" not in line and "단위:" not in line:
            continue
        if "천원" in line:
            return 100_000.0
        if "백만원" in line:
            return 100.0
        return 1.0
    return 1.0


def _kics_detail_table_anywhere_rows(md: str, quarter: str) -> list[tuple[str, str]]:
    """Fallback for the standard multi-quarter K-ICS detail table when the
    '[…지급여력비율 세부]' section heading is lost in conversion (e.g. 한화손해
    2026.1Q — heading rendered as an image). Scans ALL tables: header must match
    the target quarter column AND row labels must contain both 지급여력금액 and
    지급여력기준금액 (excludes pre/post summary tables whose col-0 is 전/후)."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    lines = md.splitlines()
    pick_col = make_quarter_column_picker(quarter)
    for start_idx, tbl in _tables_with_positions(lines):
        if len(tbl) < 6:
            continue
        col = pick_col(tbl[0])
        if col is None:
            continue
        body = tbl[1:]
        labels = "".join(r[0] for r in body if r).replace(" ", "")
        if "지급여력기준금액" not in labels or "지급여력금액" not in labels:
            continue
        scale = _nearest_preceding_unit_scale(lines, start_idx)
        for row in body:
            if col >= len(row):
                continue
            label, raw = row[0], row[col]
            if not label or not raw or label in seen:
                continue
            if not _looks_like_kics_row(label):
                continue
            value = raw
            if "비율" not in label.replace(" ", "") and scale != 1.0:
                val = parse_value(raw)
                if val is None:
                    continue
                value = _format_scaled_value(raw, val, scale)
            _register_label_pairs(label, value, seen, pairs)
        if pairs:
            break
    return pairs


_PRE_POST_CORE_LABELS = ("지급여력비율", "지급여력금액", "지급여력기준금액")


def _kics_pre_post_table_rows(md: str) -> list[tuple[str, str]]:
    """Fallback for the single-period [경과조치 적용 전 | 후] detail table when the
    '[…지급여력비율 세부]' heading is lost in conversion (e.g. 하나손해 2026.1Q — the
    heading rendered as an image, leaving the table under an unrelated ③ heading).
    Identified by the header cell '경과조치 적용 전' + K-ICS row labels; value = the
    적용 전 column (first numeric column). Core summary labels (지급여력비율/금액/
    기준금액) bypass _looks_like_kics_row; amounts are rescaled to 억원 from the
    table's '(단위: …)' context (ratio rows kept as-is)."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    lines = md.splitlines()
    for start_idx, tbl in _tables_with_positions(lines):
        if len(tbl) < 3:
            continue
        header = "".join(tbl[0]).replace(" ", "")
        if "경과조치적용전" not in header:
            continue
        body = tbl[1:]
        labels = "".join(r[0] for r in body if r).replace(" ", "")
        if "지급여력기준금액" not in labels or "지급여력금액" not in labels:
            continue
        scale = _nearest_preceding_unit_scale(lines, start_idx)
        for row in body:
            if len(row) < 2:
                continue
            label = row[0]
            raw = next((c for c in row[1:] if c and c.strip() not in ("-", "")), None)
            if not label or raw is None or label in seen:
                continue
            compact = label.replace(" ", "")
            is_core = any(compact.startswith(c) for c in _PRE_POST_CORE_LABELS)
            if not is_core and not _looks_like_kics_row(label):
                continue
            value = raw
            if "비율" not in compact and scale != 1.0:
                val = parse_value(raw)
                if val is None:
                    continue
                value = _format_scaled_value(raw, val, scale)
            _register_label_pairs(label, value, seen, pairs)
        if pairs:
            break
    return pairs


def normalise_item_value(item_no: int, item_name: str, value: str) -> str:
    return _normalise_tax_adjustment_value(item_no, item_name, value)


def labels_compatible(baseline_name: str, table_label: str) -> bool:
    if "\uc704\ud5d8\uc561" in baseline_name and "\uc704\ud5d8\uc561" not in table_label:
        return False
    if "\uc694\uad6c\uc790\ubcf8" in baseline_name and "\uc694\uad6c\uc790\ubcf8" not in table_label:
        return False
    if "\ube44\uc728" in baseline_name and "\ube44\uc728" not in table_label:
        return False
    if "\ube44\uc728" in table_label and "\ube44\uc728" not in baseline_name:
        return False
    if "\uc21c\uc790\uc0b0" in baseline_name and "\uc21c\uc790\uc0b0" not in table_label:
        return False
    if "\uc21c\uc790\uc0b0" in baseline_name and "\uc9c0\uae09\uc5ec\ub825\uae08\uc561" in table_label:
        return False
    # item12(\uc9c0\uae09\uc5ec\ub825\uae08\uc561\uc73c\ub85c "\ubd88\uc778\uc815"\ud558\ub294 \ud56d\ubaa9) starts with item1's bare label
    # "\uc9c0\uae09\uc5ec\ub825\uae08\uc561", so when item12's own row is unmatched/dropped (e.g. a
    # "-" value gets filtered out of `lookup` before this ever runs), the
    # startswith() fallback in match_baseline_value() below silently
    # substitutes item1's value for item12 (found live in ~154 rows across
    # ~15 companies, e.g. KR0004 2023.1Q, KR0005 2023.3Q). Likewise item13
    # (\ubcf4\uc644\uc790\ubcf8\uc73c\ub85c "\uc7ac\ubd84\ub958"\ud558\ub294 \ud56d\ubaa9) starts with item3's bare "\ubcf4\uc644\uc790\ubcf8" \u2014
    # same latent defect, not yet observed to fire but closed here too.
    if "\ubd88\uc778\uc815" in baseline_name and "\ubd88\uc778\uc815" not in table_label:
        return False
    if "\uc7ac\ubd84\ub958" in baseline_name and "\uc7ac\ubd84\ub958" not in table_label:
        return False
    # Reverse direction, mirroring the \uc21c\uc790\uc0b0/\ube44\uc728 guards above: some companies'
    # OWN stored baseline name for item1 is a bare "\uc9c0\uae09\uc5ec\ub825\uae08\uc561" (missing the "\uac00."
    # prefix + suffix a healthy baseline has) \u2014 e.g. KR0004(\uc608\ubcc4\uc190\ud574\ubcf4\ud5d8) 2023.2Q's own
    # item1 \ud56d\ubaa9\uba85 field is literally '\uc9c0\uae09\uc5ec\ub825\uae08\uc561'. Without this check, that bare
    # baseline_name.startswith() the item12 table row ("\uc9c0\uae09\uc5ec\ub825\uae08\uc561\uc73c\ub85c \ubd88\uc778\uc815\ud558\ub294 ...")
    # and wrongly returns item12's value (usually 0) AS item1's \u2014 the same
    # collision as above but triggered from the opposite side.
    if "\ubd88\uc778\uc815" in table_label and "\ubd88\uc778\uc815" not in baseline_name:
        return False
    if "\uc7ac\ubd84\ub958" in table_label and "\uc7ac\ubd84\ub958" not in baseline_name:
        return False
    return True


def build_label_lookups(
    table: list[tuple[str, str]],
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    lookup: dict[str, tuple[str, str]] = {}
    core_lookup: dict[str, tuple[str, str]] = {}
    for label, raw in table:
        v = parse_value(raw)
        if v is None:
            continue
        lookup.setdefault(normalise_label(label), (label, v))
        core = core_words(label)
        if core:
            core_lookup.setdefault(core, (label, v))
    return lookup, core_lookup


def match_baseline_value(
    item_name: str,
    lookup: dict[str, tuple[str, str]],
    core_lookup: dict[str, tuple[str, str]],
) -> str | None:
    key = normalise_label(item_name)
    core_key = core_words(item_name)

    hit = lookup.get(key)
    if hit and labels_compatible(item_name, hit[0]):
        return hit[1]

    for k, (label, v) in lookup.items():
        if k and (k.startswith(key) or key.startswith(k)) and len(k) > 4:
            if labels_compatible(item_name, label):
                return v

    if core_key:
        hit = core_lookup.get(core_key)
        if hit and labels_compatible(item_name, hit[0]):
            return hit[1]
        for k, (label, v) in core_lookup.items():
            if len(core_key) >= 4 and (k == core_key or core_key in k or k in core_key):
                if abs(len(k) - len(core_key)) <= 4 and labels_compatible(item_name, label):
                    return v

    return None
