"""Build consolidated IFRS17 dashboard panel JSON from extracted MVP files."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "ifrs17" / "extracted"
OUT = ROOT / "data" / "ifrs17" / "viz"

_FILENAME_RE = re.compile(r"^(.+?)_(\d{14})")
_YEAR_CELL_RE = re.compile(r"^(\d{1,2})\uB144$")
# Range-bucket cell parsers (header tokens with all spaces removed).
_RANGE_TILDE_RE = re.compile(r"^(\d{1,2})~(\d{1,2})\uB144$")  # 1~2\uB144, 5~10\uB144
_RANGE_CHOGWA_IHA_RE = re.compile(
    r"^(\d{1,2})\uB144\uCD08\uACFC(\d{1,2})\uB144\uC774\uD558$"
)  # 1\uB144\uCD08\uACFC2\uB144\uC774\uD558
_AT_OR_UNDER_RE = re.compile(r"^(\d{1,2})\uB144(?:\uC774\uD558|\uBBF8\uB9CC)$")  # 1\uB144\uC774\uD558 / 1\uB144\uBBF8\uB9CC
_OVER_ONLY_RE = re.compile(r"^(\d{1,2})\uB144(?:\uCD08\uACFC|\uC774\uC0C1|\uC774\uD6C4)$")  # 30\uB144\uCD08\uACFC/\uC774\uC0C1/\uC774\uD6C4


def parse_num(value: object, *, dash_means_zero: bool = True) -> float | None:
    """Parse Korean accounting-style numerics; commas and parentheses negatives."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.strip().replace(",", "").replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if s in ("-", "\u2014", "\uff0d"):
        return 0.0 if dash_means_zero else None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def pick_best_block(blocks: list[dict], prefer_kind: str | None = None) -> dict | None:
    if not blocks:
        return None
    return max(
        blocks,
        key=lambda b: (
            1 if prefer_kind and b.get("table_kind") == prefer_kind else 0,
            b.get("score", 0),
            len(b.get("rows") or []),
            b.get("line_no", 0),
        ),
    )


def header_has_year_buckets(header: list[list[str]]) -> bool:
    flat = " ".join(c for row in header for c in row if isinstance(c, str))
    # Year-bucket hints: 1년 2년 5년 합계 총계 이후 이하 미만.
    keys = (
        "1년",
        "2년",
        "5년",
        "합계",
        "총계",
        "이후",
        "이하",
        "미만",
    )
    return any(k in flat for k in keys)


def _classify_bucket_cell(cell: str) -> str | None:
    """Map a header cell to y1 / y1_y3 / y3_y5 / y5_plus / total or None."""
    if not isinstance(cell, str):
        return None
    plain = cell.strip()
    if not plain:
        return None

    no_space = plain.replace(" ", "").replace("\u00a0", "")
    if no_space in ("합계", "총계", "소계", "계"):
        return "total"

    m = _AT_OR_UNDER_RE.match(no_space)
    if m and int(m.group(1)) == 1:
        return "y1"

    m = _YEAR_CELL_RE.fullmatch(no_space)
    if m:
        y = int(m.group(1))
        if y == 1:
            return "y1"
        if y in (2, 3):
            return "y1_y3"
        if y in (4, 5):
            return "y3_y5"
        return "y5_plus"

    m = _RANGE_TILDE_RE.match(no_space)
    if m:
        return _bucket_for_range(int(m.group(1)), int(m.group(2)))

    m = _RANGE_CHOGWA_IHA_RE.match(no_space)
    if m:
        return _bucket_for_range(int(m.group(1)), int(m.group(2)))

    if _OVER_ONLY_RE.match(no_space):
        return "y5_plus"

    return None


def _bucket_for_range(lo: int, hi: int) -> str:
    """Route a numeric range [lo, hi] (years) to a target bucket.

    Buckets are y1 (<=1y), y1_y3 (1-3y), y3_y5 (3-5y), y5_plus (>5y).
    Uses the upper bound `hi` so 2~3년 → y1_y3, 4~5년 → y3_y5,
    5~10년 / 10~20년 → y5_plus. When `hi` straddles a boundary, the
    smaller-bucket side wins (e.g. 1~2년 → y1_y3, not y1).
    """
    if hi <= 1:
        return "y1"
    if hi <= 3:
        return "y1_y3"
    if hi <= 5:
        return "y3_y5"
    return "y5_plus"


# ── Yearly granularity (F6) — single-year buckets y1..y10 + y10plus tail ──
_YEAR_KEYS = tuple(f"y{i}" for i in range(1, 11)) + ("y10plus",)


def _year_bucket_cell(cell: str) -> str | None:
    """Map a header cell to a single-year bucket y1..y10 / y10plus / total.

    Single '5년' -> y5; a range like '1년 초과 2년 이하' / '1~2년' routes to its
    upper year (y2); the 5-year tail groups ('11~15년', '30년 이상', ...) all
    collapse into y10plus. Companies whose tables only carry coarse ranges
    (e.g. 1년 이하 / 1년 초과 3년 이하) will populate a sparse subset.
    """
    if not isinstance(cell, str):
        return None
    no_space = cell.strip().replace(" ", "").replace(" ", "")
    if not no_space:
        return None
    if no_space in ("합계", "총계", "소계", "계"):
        return "total"
    m = _YEAR_CELL_RE.fullmatch(no_space)
    if m:
        y = int(m.group(1))
        return f"y{y}" if 1 <= y <= 10 else "y10plus"
    m = _AT_OR_UNDER_RE.match(no_space)  # 'N년 이하/미만'
    if m:
        y = int(m.group(1))
        return f"y{y}" if 1 <= y <= 10 else "y10plus"
    m = _RANGE_CHOGWA_IHA_RE.match(no_space)  # 'N년 초과 M년 이하' -> year M
    if m:
        hi = int(m.group(2))
        return f"y{hi}" if 1 <= hi <= 10 else "y10plus"
    m = _RANGE_TILDE_RE.match(no_space)  # 'N~M년' -> year M
    if m:
        hi = int(m.group(2))
        return f"y{hi}" if 1 <= hi <= 10 else "y10plus"
    if _OVER_ONLY_RE.match(no_space):  # 'N년 초과/이상/이후' tail
        return "y10plus"
    return None


def _year_bucket_indices(flat_hdr: list[str]) -> dict[str, list[int]]:
    buckets: dict[str, list[int]] = {k: [] for k in _YEAR_KEYS}
    buckets["total"] = []
    for i, cell in enumerate(flat_hdr):
        bk = _year_bucket_cell(cell)
        if bk is not None:
            buckets[bk].append(i)
    if len(buckets["total"]) > 1:
        buckets["total"] = buckets["total"][:1]
    return buckets


def _yearly_from_aligned(aligned: list, ybuckets: dict[str, list[int]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for bk, idxs in ybuckets.items():
        if bk == "total":
            continue
        parts = []
        for i in idxs:
            if 0 <= i < len(aligned):
                v = parse_num(aligned[i])
                if v is not None:
                    parts.append(float(v))
        if parts:
            out[bk] = sum(parts)
    tidx = ybuckets.get("total") or []
    if tidx and 0 <= tidx[0] < len(aligned):
        tv = parse_num(aligned[tidx[0]])
        if tv is not None:
            out["total"] = float(tv)
    return out


def _extract_transposed_yearly(rows) -> dict[str, float] | None:
    """Yearly buckets when time buckets live in column 0 (row-keyed)."""
    out: dict[str, float] = {}
    total = 0.0
    saw = False
    for row in rows:
        if not row:
            continue
        bk = _year_bucket_cell(str(row[0]).strip())
        if bk is None:
            continue
        nums = [n for n in (parse_num(c) for c in row[1:]) if n is not None]
        if not nums:
            continue
        v = nums[-1] if len(nums) >= 2 else nums[0]
        if bk == "total":
            total = v
            continue
        out[bk] = out.get(bk, 0.0) + v
        saw = True
    if not saw:
        return None
    if total:
        out["total"] = total
    return out


def _yearly_granularity(yearly: dict) -> str:
    """'yearly' only when most single-year columns are present (true per-year table).

    Coarse-range tables (1년 이하 / 1년 초과 3년 이하 / ...) map to a sparse
    y1/y3/y5 subset, so requiring >=7 of y1..y10 keeps them classified 'coarse'
    (the panel then falls back to the 4-bucket view instead of a gappy chart).
    """
    if not yearly:
        return "none"
    present = sum(1 for i in range(1, 11) if f"y{i}" in yearly)
    if present >= 7:
        return "yearly"
    return "coarse"


def _flatten_header(header: list[list[str]]) -> list[str]:
    out: list[str] = []
    for row in header:
        for c in row:
            if isinstance(c, str):
                out.append(c.strip())
    return out


def _align_row_to_flat_header(flat_hdr: list[str], row: list[object]) -> list[str]:
    cells = [("" if v is None else str(v)).strip() for v in row]
    L = len(flat_hdr)
    while len(cells) < L:
        cells.insert(0, "")
    if len(cells) > L:
        cells = cells[len(cells) - L :]
    return cells


def _bucket_indices(flat_hdr: list[str]) -> dict[str, list[int]]:
    """Group flat header cell indices into target buckets.

    Uses _classify_bucket_cell so heterogeneous headers (1년 / 1년 이하 /
    1~2년 / 1년 초과 2년 이하 / 30년 이상 / 총계 / 합 계) all route correctly.
    """
    buckets: dict[str, list[int]] = {
        "y1": [],
        "y1_y3": [],
        "y3_y5": [],
        "y5_plus": [],
        "total": [],
    }
    for i, cell in enumerate(flat_hdr):
        bk = _classify_bucket_cell(cell)
        if bk is None:
            continue
        buckets[bk].append(i)
    # Keep at most one total column (first occurrence).
    if len(buckets["total"]) > 1:
        buckets["total"] = buckets["total"][:1]
    return buckets


def _row_has_year_buckets(row, threshold: int = 3) -> bool:
    """True if a flat row has enough classifiable year-bucket cells."""
    if not row:
        return False
    cnt = sum(
        1
        for c in row
        if isinstance(c, str) and _classify_bucket_cell(c) is not None
    )
    return cnt >= threshold


def _infer_header_from_rows(rows):
    """Promote a leading data row to header when THEAD is missing."""
    for k in range(min(3, len(rows))):
        row = rows[k]
        if _row_has_year_buckets(row):
            hdr = [[('' if v is None else str(v)) for v in row]]
            return hdr, list(rows[k + 1 :])
    return [], list(rows)


def _amort_caption_score(caption: str) -> int:
    """Rank competing CSM-amort blocks (higher = prefer).

    Only downranks captions dominantly about reinsurance (no direct side
    mentioned). Combined captions like "issued contracts AND held
    reinsurance" stay neutral so row-count / score wins instead.
    """
    cap = caption or ""
    score = 0
    has_direct = ("발행한 보험계약" in cap) or ("원수" in cap)
    has_reins = "재보험" in cap
    if has_direct:
        score += 4
    if has_reins and not has_direct:
        score -= 6
    stripped = cap.lstrip().lstrip("(").lstrip("\uff08")
    if stripped.startswith("주") or stripped.startswith("*"):
        score -= 4
    return score


def _bucket_columns_count(b: dict) -> int:
    """How many distinct year-bucket header columns the block exposes."""
    hdr = b.get('header') or []
    flat = _flatten_header(hdr)
    return sum(
        1
        for c in flat
        if _classify_bucket_cell(c) not in (None, "total")
    )


def _pick_amort_block(blocks):
    """Pick best CSM-amort block.

    Caption score is clamped to a non-positive value so reinsurance-only
    captions are still penalized but a small +4 direct bonus does not
    outweigh table-shape evidence. Tiebreakers (in order): year-bucket
    column count (Form A detailed > abbreviated summary), body row count,
    extractor score, line position.
    """
    if not blocks:
        return None

    def key(b):
        raw = _amort_caption_score(str(b.get('caption') or ''))
        cap = min(raw, 0)
        return (
            cap,
            _bucket_columns_count(b),
            len(b.get('rows') or []),
            b.get('score', 0),
            b.get('line_no', 0),
        )

    return max(blocks, key=key)


def _extract_transposed_amort(rows):
    """Sum buckets when time buckets live in column 0 (row-keyed)."""
    buckets: dict[str, float] = {}
    total = 0.0
    saw_any = False
    for row in rows:
        if not row:
            continue
        stub = str(row[0]).strip()
        bk = _classify_bucket_cell(stub)
        if bk is None:
            continue
        nums = [parse_num(c) for c in row[1:]]
        nums = [n for n in nums if n is not None]
        if not nums:
            continue
        v = nums[-1] if len(nums) >= 2 else nums[0]
        if bk == 'total':
            total = v
            continue
        buckets[bk] = buckets.get(bk, 0.0) + v
        saw_any = True
    if not saw_any:
        return None
    if total:
        buckets['total'] = total
    elif buckets:
        buckets['total'] = sum(
            v for k, v in buckets.items() if k in ('y1', 'y1_y3', 'y3_y5', 'y5_plus')
        )
    return buckets


def extract_amort_schedule(blocks: list[dict]) -> dict | None:
    kw = ("상각", "인식", "예상", "기대", "CSM")

    def _eligible(b: dict) -> bool:
        if not any(k in str(b.get('caption') or '') for k in kw):
            return False
        if header_has_year_buckets(b.get('header') or []):
            return True
        rows = b.get('rows') or []
        for k in range(min(3, len(rows))):
            if _row_has_year_buckets(rows[k]):
                return True
        stubs = [str(r[0]).strip() for r in rows[:6] if r]
        if sum(1 for s in stubs if _classify_bucket_cell(s) is not None) >= 3:
            return True
        return False

    candidates = [b for b in blocks if _eligible(b)]
    blk = _pick_amort_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    header = blk.get('header') or []
    rows = blk.get('rows') or []

    if not header:
        inferred, rows = _infer_header_from_rows(rows)
        header = inferred

    flat_hdr = _flatten_header(header)
    buckets_map = _bucket_indices(flat_hdr)

    header_has_buckets = any(
        len(idxs) > 0 for k, idxs in buckets_map.items() if k != 'total'
    )

    if not header_has_buckets:
        bucket_vals = _extract_transposed_amort(rows) or {}
        yearly = _extract_transposed_yearly(rows) or {}
        status = 'ok' if bucket_vals else 'partial'
        return {
            'status': status,
            'caption': blk.get('caption'),
            'buckets': bucket_vals,
            'yearly': yearly,
            'granularity': _yearly_granularity(yearly),
            'header': header,
            'row_label': "시간버킷(행)",
        }

    total_row = None
    hit_labels = (
        "당기손익인식",
        "합계",
        "소계",
    )
    for row in rows:
        if not row:
            continue
        stub = str(row[0]).strip()
        if any(k in stub for k in hit_labels) and len(row) >= 4:
            total_row = [str(v) for v in row]
            break

    if total_row is None:
        best = None
        best_n = 0
        for row in rows:
            if not row:
                continue
            aligned_try = _align_row_to_flat_header(flat_hdr, row)
            nums = sum(1 for c in aligned_try[2:] if parse_num(c) is not None)
            if nums > best_n:
                best_n = nums
                best = aligned_try
        total_row = best

    if not total_row:
        return {'status': 'no_rows', 'caption': blk.get('caption')}

    aligned = (
        total_row if len(total_row) == len(flat_hdr) else _align_row_to_flat_header(flat_hdr, total_row)
    )

    bucket_vals: dict[str, float] = {}
    seen_bucket = False

    for bucket, idxs in buckets_map.items():
        if bucket == 'total':
            continue
        usable = [i for i in idxs if 0 <= i < len(aligned)]
        if not usable:
            continue
        parts = []
        for i in usable:
            v = parse_num(aligned[i])
            if v is not None:
                parts.append(float(v))
        if not parts:
            continue
        bucket_vals[bucket] = sum(parts)
        seen_bucket = True

    tidx = (buckets_map.get('total') or [])
    if tidx:
        ti = tidx[0]
        if ti is not None and 0 <= ti < len(aligned):
            tv = parse_num(aligned[ti])
            if tv is not None:
                bucket_vals['total'] = float(tv)

    if not seen_bucket:
        numeric_tail = [float(v) for v in (parse_num(c) for c in aligned) if v is not None]
        if len(numeric_tail) >= 5:
            tail = numeric_tail[-5:]
            keys = ['y1', 'y1_y3', 'y3_y5', 'y5_plus', 'total']
            bucket_vals = {k: tail[i] for i, k in enumerate(keys)}

    if 'total' not in bucket_vals and bucket_vals:
        parts = [
            v for k, v in bucket_vals.items()
            if k in ('y1', 'y1_y3', 'y3_y5', 'y5_plus')
        ]
        if parts:
            bucket_vals['total'] = sum(parts)

    ybuckets = _year_bucket_indices(flat_hdr)
    yearly = _yearly_from_aligned(aligned, ybuckets)

    status = 'ok' if bucket_vals else 'partial'
    return {
        'status': status if bucket_vals else 'partial',
        'caption': blk.get('caption'),
        'buckets': bucket_vals,
        'yearly': yearly,
        'granularity': _yearly_granularity(yearly),
        'header': header,
        'row_label': aligned[0] if aligned else '',
    }


def extract_pl_breakdown(blocks: list[dict]) -> dict | None:
    kw_caption = (
        "\uBCF4\uD5D8\uC11C\uBE44\uC2A4",
        "\uBCF4\uD5D8\uC218\uC775",
        "\uBCF4\uD5D8\uC190\uC775",
    )
    candidates = [
        b
        for b in blocks
        if any(k in str(b.get("caption") or "") for k in kw_caption) or int(b.get("score", 0)) >= 6
    ]
    blk = pick_best_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    rows_out: list[list[str]] = []
    for row in blk.get("rows") or []:
        if not row or not isinstance(row[0], str):
            continue
        label = row[0].strip()
        if not label:
            continue
        if label.startswith("\uACC4\uC57D"):
            continue
        if sum(1 for c in row[1:] if parse_num(c) is not None) == 0:
            continue
        rows_out.append([str(c).strip() for c in row])
        if len(rows_out) >= 12:
            break

    if not rows_out:
        return {"status": "no_rows", "caption": blk.get("caption")}

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "header": blk.get("header") or [],
        "table": rows_out,
    }


def extract_bs_snapshot(blocks: list[dict]) -> dict | None:
    kw = ("\uC790\uC0B0\uBD80\uCC44", "\uD604\uD669", "\uC0C1\uC138\uB0B4\uC5ED")
    candidates = [b for b in blocks if any(k in str(b.get("caption") or "") for k in kw)]
    blk = pick_best_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    header = blk.get("header") or []
    hdr_flat = _flatten_header(header)
    rows_out: list[list[str]] = []

    for row in blk.get("rows") or []:
        if not row:
            continue
        aligned = _align_row_to_flat_header(hdr_flat, row) if hdr_flat else [str(v).strip() for v in row]
        rows_out.append(aligned)
        if len(rows_out) >= 80:
            break

    if not rows_out:
        return {"status": "no_rows", "caption": blk.get("caption")}

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "header": header,
        "table": rows_out,
    }


def _is_rollforward_sensitivity_caption(caption: str) -> bool:
    cap = caption or ""
    rollforward_cues = (
        "\uCE21\uC815\uC694\uC18C",
        "\uBCC0\uB3D9 \uC138\uBD80",
        "\uBCC0\uB3D9\uB0B4\uC5ED",
        "\uBBF8\uB798\uC11C\uBE44\uC2A4 \uAD00\uB828",
        "\uC0C1\uC138\uBCC0\uB3D9",
    )
    return any(k in cap for k in rollforward_cues)


def _sensitivity_caption_score(caption: str) -> int:
    cap = caption or ""
    score = 0
    if any(k in cap for k in ("\uBBFC\uAC10\uB3C4", "\uAC00\uC815\uBBFC\uAC10")):
        score += 10
    if "\uBBFC\uAC10\uB3C4\uBD84\uC11D" in cap:
        score += 5
    if any(k in cap for k in ("\uB2F9\uAE30", "\uAE30\uB9D0", "2024", "2023")):
        score += 1
    if _is_rollforward_sensitivity_caption(cap):
        score -= 20
    return score


def _header_has_product_lines(header: list[list[str]]) -> bool:
    flat = " ".join(c for row in header for c in row if isinstance(c, str))
    return "\uC0C1\uD488\uB77C\uC778" in flat or "\uC0C1\uD488 \uB77C\uC778" in flat


def _is_shock_label(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    # %, \uC99D\uAC00, \uAC10\uC18C, \uC0C1\uC2B9, \uD558\uB77D, or a (-) prefix all denote a shock magnitude.
    return (
        "%" in t
        or "\uC99D\uAC00" in t  # \uC99D\uAC00
        or "\uAC10\uC18C" in t  # \uAC10\uC18C
        or "\uC0C1\uC2B9" in t  # \uC0C1\uC2B9
        or "\uD558\uB77D" in t  # \uD558\uB77D
        or t.startswith("(-)")
    )


def _band_sensitivity_columns(header: list[list[str]]) -> tuple[int, int | None] | None:
    """Locate \u0394CSM and \uB2F9\uAE30\uC190\uC775 value-column indices for the \uC6D0\uC218/\uCD9C\uC7AC band layout.

    These tables (\uD55C\uD654/\uCF00\uC774\uB514\uBE44/\uD765\uAD6D \uC0DD\uBCF4) use a 3-row header:
        \uAD6C\uBD84 | \uBBFC\uAC10\uB3C4 | \uBCC0\uB3D9\uAE08\uC561 | \uC774\uC775 \uBC0F \uC790\uBCF8 \uC601\uD5A5
                     \uC774\uD589\uD604\uAE08\uD750\uB984 \uBCF4\uD5D8\uACC4\uC57D\uB9C8\uC9C4 | \uB2F9\uAE30\uC190\uC775 \uAE30\uD0C0\uD3EC\uAD04\uC190\uC775
                     \uC6D0\uC218 \uCD9C\uC7AC    \uC6D0\uC218 \uCD9C\uC7AC      \uC6D0\uC218 \uCD9C\uC7AC  \uC6D0\uC218 \uCD9C\uC7AC
    Returns (csm_value_idx, pl_value_idx) indexing into the per-row value
    cells (after the label cells), preferring the \uC6D0\uC218 (direct) sub-column.
    ``None`` when this layout is not present (caller falls back).
    """
    csm_tokens = ("\uBCF4\uD5D8\uACC4\uC57D\uB9C8\uC9C4", "\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uB9C8\uC9C4")  # DART note / K-ICS term
    # Label cells that may sit in the same header row as the value-group names
    # (e.g. \uCF00\uC774\uB514\uBE44: ['\uC704\uD5D8\uBCC0\uC218','\uBCC0\uB3D9','\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uB9C8\uC9C4','\uB2F9\uAE30\uC190\uC775',...]); drop them
    # so group indices align with the value columns.
    label_exact = {"\uAD6C\uBD84", "\uBBFC\uAC10\uB3C4", "\uC704\uD5D8\uBCC0\uC218", "\uC704\uD5D8\uC694\uC778", "\uC704\uD5D8\uC885\uB958", "\uBCC0\uB3D9", "\uBCC0\uB3D9\uB960", "\uC0C1\uD488\uB77C\uC778"}

    def _is_csm(c: str) -> bool:
        return any(t in c for t in csm_tokens)

    def _is_label(c: str) -> bool:
        s = c.strip()
        return s in label_exact or s.startswith("\uCDA9\uACA9")

    group_row = None
    for hr in header:
        cells = [c for c in hr if isinstance(c, str) and not _is_label(c)]
        if any(_is_csm(c) for c in cells) and any(
            ("\uB2F9\uAE30\uC190\uC775" in c or "\uC190\uC775" in c) for c in cells  # \uB2F9\uAE30\uC190\uC775 / \uC190\uC775
        ):
            group_row = cells
            break
    if not group_row:
        return None
    # LAST CSM column: when a table shows \uAE30\uC900\uAE08\uC561 then \uBCC0\uB3D9\uAE08\uC561 each with a
    # \uBCF4\uD5D8\uACC4\uC57D\uB9C8\uC9C4 sub-column (e.g. \uAD50\uBCF4), the \u0394CSM we want is the \uBCC0\uB3D9\uAE08\uC561 one.
    csm_g = max((i for i, c in enumerate(group_row) if _is_csm(c)), default=None)
    if csm_g is None:
        return None
    pl_g = next((i for i, c in enumerate(group_row) if "\uB2F9\uAE30\uC190\uC775" in c), None)
    n_groups = len(group_row)
    n_bottom = max(
        (len([c for c in hr if isinstance(c, str)]) for hr in header), default=n_groups
    )
    cpg = max(1, round(n_bottom / n_groups)) if n_groups else 1
    pl_idx = pl_g * cpg if pl_g is not None else None
    return (csm_g * cpg, pl_idx)


def _extract_sensitivity_band(
    blk: dict, csm_idx: int, pl_idx: int | None, skip_stub: tuple[str, ...]
) -> list[dict[str, object]]:
    """Parse a \uC6D0\uC218/\uCD9C\uC7AC band-layout sensitivity table, rowspan-aware.

    Risk name spans the \uC99D\uAC00/\uAC10\uC18C row pair via rowspan, so the 2nd (\uAC10\uC18C) row
    has one fewer leading cell. We detect such continuation rows (leading cell
    is a shock) and inherit the current risk, aligning the value cells.
    """
    scenarios: list[dict[str, object]] = []
    current_risk = ""
    for row in blk.get("rows") or []:
        if not row or not isinstance(row[0], str):
            continue
        label = row[0].strip()
        if not label or label in skip_stub or label.startswith("\uAE30\uC900\uAE08\uC561"):
            continue
        if _is_shock_label(label) and not _is_risk_label(label, skip_stub):
            # rowspan-elided continuation row: risk inherited, no \uAD6C\uBD84 cell.
            risk, shock, vals = current_risk, label, row[1:]
        else:
            current_risk = label
            risk = label
            shock = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ""
            vals = row[2:]
        cells = [("" if v is None else str(v)).strip() for v in vals]
        if len(cells) <= csm_idx:
            continue
        csm = parse_num(cells[csm_idx], dash_means_zero=False)
        pl = (
            parse_num(cells[pl_idx], dash_means_zero=False)
            if pl_idx is not None and pl_idx < len(cells)
            else None
        )
        if csm is None and pl is None:
            continue
        scenarios.append({"risk": risk, "shock": shock, "csm_delta": csm, "pl_impact": pl})
        if len(scenarios) >= 12:
            break
    return scenarios


def _is_risk_label(text: str, skip_stub: tuple[str, ...]) -> bool:
    t = text.strip()
    if not t or t in skip_stub:
        return False
    risk_cues = (
        "\uC704\uD5C8",
        "\uD574\uC57D",
        "\uD574\uC9C0",
        "\uC0AC\uB9DD",
        "\uC7A5\uD574",
        "\uC0AC\uC5C5\uBE44",
        "\uC190\uD574",
    )
    return any(k in t for k in risk_cues)


def _parse_sensitivity_deltas(row: list[object], *, product_line_layout: bool) -> tuple[float | None, float | None]:
    cells = [("" if v is None else str(v)).strip() for v in row]
    if product_line_layout and cells and cells[0] == "\uC21C\uC561":
        if len(cells) >= 6:
            return parse_num(cells[4], dash_means_zero=False), parse_num(cells[5], dash_means_zero=False)
        return None, None
    if len(cells) >= 6:
        return parse_num(cells[4], dash_means_zero=False), parse_num(cells[5], dash_means_zero=False)
    return None, None


def _pick_sensitivity_block(sens_blocks: list[dict]) -> dict | None:
    eligible = [b for b in sens_blocks if not _is_rollforward_sensitivity_caption(str(b.get("caption") or ""))]
    pool = eligible or sens_blocks
    return max(
        pool,
        key=lambda b: (
            _sensitivity_caption_score(str(b.get("caption") or "")),
            b.get("score", 0),
            len(b.get("rows") or []),
            -int(b.get("line_no") or 0),
        ),
    )


def extract_sensitivity(blocks: list[dict]) -> dict | None:
    sa_kind = "sensitivity_analysis"
    sens_blocks = [b for b in blocks if str(b.get("table_kind")) == sa_kind]
    if not sens_blocks:
        return {"status": "unavailable", "note": "No sensitivity_analysis block in MVP extract"}

    blk = _pick_sensitivity_block(sens_blocks)

    skip_stub = (
        "\uAE30\uC900\uAE08\uC561",
        "\uC18C\uACC4",
        "\uC21C\uC704",
        "\uC77C\uBC18 \uBCF4\uD5D8",
        "\uCD9C\uC7AC \uBCF4\uD5D8",
    )
    product_line_layout = _header_has_product_lines(blk.get("header") or [])

    # 원수/출재 band layout (한화/케이디비/흥국): header-aware + rowspan-aware.
    # Routed only when that header shape is present, so the product-line path
    # (삼성) and the generic path (other insurers) are untouched.
    if not product_line_layout:
        band = _band_sensitivity_columns(blk.get("header") or [])
        if band is not None:
            csm_idx, pl_idx = band
            band_scenarios = _extract_sensitivity_band(blk, csm_idx, pl_idx, skip_stub)
            if band_scenarios:
                return {
                    "status": "ok",
                    "caption": blk.get("caption"),
                    "table_kind": sa_kind,
                    "header": blk.get("header") or [],
                    "scenarios": band_scenarios,
                }

    scenarios: list[dict[str, object]] = []
    current_risk = ""
    current_shock = ""

    for row in blk.get("rows") or []:
        if not row:
            continue
        if not isinstance(row[0], str):
            continue

        label = row[0].strip()
        if not label or label in skip_stub:
            continue

        if product_line_layout:
            col1 = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ""
            if label == "\uC21C\uC561":
                csm_delta, pl_impact = _parse_sensitivity_deltas(row, product_line_layout=True)
                if (csm_delta is not None or pl_impact is not None) and current_risk:
                    scenarios.append(
                        {
                            "risk": current_risk,
                            "shock": current_shock,
                            "csm_delta": csm_delta,
                            "pl_impact": pl_impact,
                        },
                    )
                continue
            if _is_shock_label(label) and not _is_risk_label(label, skip_stub):
                current_shock = label
                continue
            if _is_risk_label(label, skip_stub) and _is_shock_label(col1):
                current_risk = label
                current_shock = col1
                continue
            continue

        if len(row) < 6:
            continue

        risk = label
        shock = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ""
        if shock in skip_stub:
            continue

        csm_delta, pl_impact = _parse_sensitivity_deltas(row, product_line_layout=False)
        if csm_delta is None and pl_impact is None:
            continue

        scenarios.append(
            {
                "risk": risk,
                "shock": shock,
                "csm_delta": csm_delta,
                "pl_impact": pl_impact,
            },
        )
        if len(scenarios) >= 12:
            break

    if not scenarios:
        return {
            "status": "partial",
            "caption": blk.get("caption"),
            "table_kind": sa_kind,
            "note": "sensitivity_analysis found but scenarios not parsed",
        }

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "table_kind": sa_kind,
        "header": blk.get("header") or [],
        "scenarios": scenarios,
    }


def build_panel(glob_pat: str, extractor) -> dict:
    companies: list[dict[str, object]] = []
    for path in sorted(SRC.glob(glob_pat)):
        m = _FILENAME_RE.match(path.stem)
        company = m.group(1) if m else path.stem
        rcept = m.group(2) if m else ""

        try:
            blocks_raw = json.loads(path.read_text(encoding="utf-8"))
            blocks: list = blocks_raw if isinstance(blocks_raw, list) else [blocks_raw]
            panel = extractor(blocks)
            if isinstance(panel, dict):
                companies.append({"company": company, "rcept_no": rcept, **panel})
            else:
                companies.append({"company": company, "rcept_no": rcept, "status": "empty"})
        except Exception as exc:  # noqa: BLE001
            companies.append(
                {"company": company, "rcept_no": rcept, "status": "error", "error": str(exc)},
            )

    return {"period": "annual (filings skim)", "companies": companies}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "csm_amort_schedule.json": ("*_csm.json", extract_amort_schedule),
        "insurance_pl_breakdown.json": ("*_insurance_pl_mvp.json", extract_pl_breakdown),
        "bs_snapshot.json": ("*_bs_snapshot_mvp.json", extract_bs_snapshot),
        "sensitivity_heatmap.json": ("*_sensitivity_mvp.json", extract_sensitivity),
    }

    for fname, (pat, fn) in outputs.items():
        payload = build_panel(pat, fn)
        out_path = OUT / fname
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        ok_count = sum(1 for item in payload["companies"] if str(item.get("status")) == "ok")
        total_count = len(payload["companies"])

        rel = str(out_path.relative_to(ROOT)).replace("\\", "/")
        print("Wrote " + rel + " (" + str(ok_count) + "/" + str(total_count) + " ok)")


if __name__ == "__main__":
    main()