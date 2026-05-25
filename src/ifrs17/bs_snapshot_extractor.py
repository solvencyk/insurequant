"""Skim-only extractor for section 14(1) BS snapshot (B1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .csm_extractor import _iter_tables_with_context
from .insurance_pl_extractor import (
    _all_row_cells,
    _classify_block,
    _classify_slice,
    _first_col_labels,
    _flat_header,
)
from .universe import expected_slice_policy, has_short_term_markers, table_has_long_term_label

_CAPTION_KEYWORDS = (
    "\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uC790\uC0B0\uBD80\uCC44",
    "\uD604\uD669",
    "(1)",
    # 2026-05-24 (B1 gap fix): DB Sonhae \u00A730-1 / Heungkuk Fire \u00A718(1) caption variants
    "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0\uBC0F\uBD80\uCC44",
    "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0\uBD80\uCC44",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0\uBC0F\uBD80\uCC44",
    "\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44(\uC790\uC0B0)",
    "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0(\uBD80\uCC44)",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0(\uBD80\uCC44)",
    "\uBC1C\uD589\uD55C \uBCF4\uD5D8\uACC4\uC57D",
    "\uC138\uBD80\uB0B4\uC5ED",
    "\uBCF4\uACE0\uAE30\uAC04\uC885\uB8CC\uC77C",
    "\uAE08\uC561\uC740 \uB2E4\uC74C",
    "\uB2F9\uAE30\uB9D0\uACFC \uC804\uAE30\uB9D0",
)
_HEADER_BS = (
    "\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uC21C\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uC21C\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
)
# 2026-05-24 (B1 gap fix): Heungkuk Fire \u00A718(1) header has \uC790\uC0B0/\uBD80\uCC44/\uD569\uACC4 (column trio);
# DB Sonhae \u00A730-1 header has \uC7A5\uAE30/\uC77C\uBC18/\uC790\uB3D9\uCC28/\uC0DD\uBA85/\uD569\uACC4 (slices on columns).
_HEADER_BS_TRIPLE = ("\uC790\uC0B0", "\uBD80\uCC44", "\uD569\uACC4", "\uD569 \uACC4")
_HEADER_BS_SLICES = ("\uC7A5\uAE30", "\uC77C\uBC18", "\uC790\uB3D9\uCC28", "\uC0DD\uBA85")
_ROW_STUBS = (
    "\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uC21C\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
    "\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44",
    "\uC21C\uC7AC\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0",
)
# 2026-05-24 (B1 gap fix): when slices are on rows (Heungkuk Fire), first column carries \uC77C\uBC18/\uC790\uB3D9\uCC28/\uC7A5\uAE30.
_ROW_SLICES = ("\uC7A5\uAE30", "\uC77C\uBC18", "\uC790\uB3D9\uCC28", "\uC0DD\uBA85")
_ROLLFORWARD_MARKERS = (
    "\uBCC0\uB3D9\uB0B4\uC5ED",
    "\uCE21\uC815\uC694\uC18C",
    "\uC794\uC5EC\uBCF4\uC7A5",
    "\uBC1C\uC0DD\uC0AC\uACE0",
)


@dataclass
class ExtractedBsSnapshotTable:
    caption: str
    header: list[list[str]]
    rows: list[list[str]]
    footnotes: list[str]
    line_no: int
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    block_type: str = "unknown"
    slice_label: str = "unknown"
    slice_policy: str = "unknown"
    mvp_candidate: bool = False


def _has_bs_structure(t: ExtractedBsSnapshotTable) -> bool:
    rows_text = _first_col_labels(t.rows)
    hdr_text = [c for row in t.header for c in row]
    joined = " ".join(rows_text + hdr_text)
    if sum(1 for s in _ROW_STUBS if s in joined) >= 2:
        return True
    # 2026-05-24 (B1 gap fix): slices-on-rows pattern (Heungkuk Fire §18(1)).
    # Rows include 일반/자동차/장기 with header trio 자산/부채/합계.
    row_slice_hits = sum(1 for s in _ROW_SLICES if any(s == r.strip() or s in r for r in rows_text))
    hdr_triple_hits = sum(1 for s in _HEADER_BS_TRIPLE if any(s in c for c in hdr_text))
    if row_slice_hits >= 2 and hdr_triple_hits >= 2:
        return True
    # Header inferred from first body row (THEAD-less) — check rows directly.
    flat = _flat_header(t)
    flat_triple = sum(1 for s in _HEADER_BS_TRIPLE if any(s in c for c in flat))
    if row_slice_hits >= 2 and flat_triple >= 2:
        return True
    # 2026-05-24 (B1 gap fix): multi-row header where triple (자산/부채/합계) sits in row[1] or row[2]
    # while flat_header() captured only row[0]. Scan first 4 rows for any-cell triple match.
    early_rows_cells = [c for r in t.rows[:4] for c in r if c]
    early_triple = sum(1 for s in _HEADER_BS_TRIPLE if any(s == c.strip() or s in c for c in early_rows_cells))
    if row_slice_hits >= 2 and early_triple >= 2:
        return True
    return False


def is_mvp_table(t: ExtractedBsSnapshotTable) -> bool:
    if not _has_bs_structure(t):
        return False
    if t.block_type == "reinsurance":
        return False
    if t.slice_policy == "whole_company_life":
        return t.slice_label == "whole_company_life"
    if t.slice_label != "long_term":
        return False
    joined = " ".join([t.caption] + _first_col_labels(t.rows))
    if has_short_term_markers(joined) and not table_has_long_term_label([joined]):
        # 2026-05-24 (B1 gap fix): slice-on-rows / slice-on-columns BS snapshots list 일반/자동차/장기 as breakdown,
        # but the table itself contains the 장기 line — accept when 장기 appears as a row or column label.
        row_labels = _first_col_labels(t.rows)
        flat_hdr = _flat_header(t)
        if any("장기" in r for r in row_labels) or any("장기" in c for c in flat_hdr):
            return True
        return False
    return True


def _score_table(t, company_name: str) -> tuple[int, str, str, str, list[str]]:
    score = 0
    reasons: list[str] = []
    caption = t.caption or ""

    cap_hits = sum(1 for k in _CAPTION_KEYWORDS if k in caption)
    if cap_hits >= 2:
        score += 3
        reasons.append(f"caption: BS keywords x{cap_hits}")
    elif cap_hits == 1:
        score += 1
        reasons.append("caption: 1 BS keyword")

    flat_header = _flat_header(t)
    header_hits = sum(1 for c in flat_header if any(k in c for k in _HEADER_BS))
    if header_hits >= 3:
        score += 4
        reasons.append(f"header: BS line items x{header_hits}")
    elif header_hits >= 2:
        score += 3
        reasons.append(f"header: BS line items x{header_hits}")
    elif header_hits == 1:
        score += 1
        reasons.append("header: 1 BS line item")

    # 2026-05-24 (B1 gap fix): slice-column header (DB Sonhae §30-1) — 장기/일반/자동차/합계
    slice_hdr_hits = sum(1 for s in _HEADER_BS_SLICES if any(s == c.strip() or s in c for c in flat_header))
    if slice_hdr_hits >= 3:
        score += 2
        reasons.append(f"header: slice columns x{slice_hdr_hits}")
    # 2026-05-24 (B1 gap fix): asset/liab/sum triple header (Heungkuk Fire §18(1))
    triple_hits = sum(1 for s in _HEADER_BS_TRIPLE if any(s == c.strip() or s in c for c in flat_header))
    if triple_hits >= 2 and header_hits == 0:
        score += 2
        reasons.append(f"header: BS triple (자산/부채/합계) x{triple_hits}")

    row_labels = _first_col_labels(t.rows)
    all_cells = _all_row_cells(t.rows)
    row_hits = sum(1 for s in _ROW_STUBS if s in " ".join(row_labels))
    if row_hits >= 3:
        score += 3
        reasons.append(f"rows: BS stubs x{row_hits}")
    elif row_hits >= 2:
        score += 2
        reasons.append(f"rows: BS stubs x{row_hits}")

    # 2026-05-24 (B1 gap fix): slice-on-rows pattern (Heungkuk Fire) — 일반/자동차/장기/합계 in col 0.
    row_slice_hits = sum(1 for s in _ROW_SLICES if any(s == r.strip() or s in r for r in row_labels))
    if row_slice_hits >= 3 and row_hits < 2:
        score += 2
        reasons.append(f"rows: slice labels x{row_slice_hits}")

    if any(k in caption for k in _ROLLFORWARD_MARKERS):
        score -= 2
        reasons.append("penalty: rollforward caption (not snapshot)")

    block_type = _classify_block(caption, row_labels)
    footnotes = list(t.footnotes or [])
    slice_label = _classify_slice(caption, flat_header, row_labels, all_cells, footnotes, company_name)
    slice_policy = expected_slice_policy(company_name)
    # 2026-05-24 (B1 gap fix): BS snapshot tables often present 장기 as a column or row label
    # alongside 일반/자동차 — promote to long_term for long_term-policy companies.
    if slice_policy == "long_term" and slice_label != "long_term":
        if any("장기" == c.strip() or "장기" in c for c in flat_header) or any(
            "장기" == r.strip() or "장기" in r for r in row_labels
        ):
            slice_label = "long_term"
            reasons.append("slice: promoted to long_term via 장기 row/col label")
    if slice_label == "long_term" or slice_policy == "whole_company_life":
        score += 1
        reasons.append(f"slice: {slice_label}")

    if (
        cap_hits == 0
        and header_hits < 2
        and row_hits < 2
        and slice_hdr_hits < 3
        and triple_hits < 2
        and row_slice_hits < 3
    ):
        if score > 3:
            score = 3
            reasons.append("gate: weak BS snapshot signals capped at 3")

    return score, block_type, slice_label, slice_policy, reasons


def extract_bs_snapshot_tables(
    xml_path: Path,
    company_name: str = "",
    min_score: int = 5,
    mvp_only: bool = False,
) -> list[ExtractedBsSnapshotTable]:
    out: list[ExtractedBsSnapshotTable] = []
    for t in _iter_tables_with_context(xml_path):
        score, block_type, slice_label, slice_policy, reasons = _score_table(t, company_name)
        if score < min_score:
            continue
        row = ExtractedBsSnapshotTable(
            caption=t.caption,
            header=t.header,
            rows=t.rows,
            footnotes=t.footnotes,
            line_no=t.line_no,
            score=score,
            reasons=reasons,
            block_type=block_type,
            slice_label=slice_label,
            slice_policy=slice_policy,
        )
        row.mvp_candidate = is_mvp_table(row)
        if mvp_only and not row.mvp_candidate:
            continue
        out.append(row)
    out.sort(key=lambda x: (-x.score, x.line_no))
    return out


def to_jsonable(t: ExtractedBsSnapshotTable) -> dict:
    return {
        "caption": t.caption,
        "block_type": t.block_type,
        "slice_label": t.slice_label,
        "slice_policy": t.slice_policy,
        "mvp_candidate": t.mvp_candidate,
        "line_no": t.line_no,
        "score": t.score,
        "reasons": t.reasons,
        "header": t.header,
        "rows": t.rows,
        "footnotes": t.footnotes,
    }
