"""Skim-only extractor for assumption values and sensitivity analysis (B5).

DART skim PoC only — per Open Q8 (2026-05-24), primary B5 source is K-ICS
quarterly disclosure, not OpenDART notes.
"""

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

_CAPTION_ASSUMPTION = (
    "\uD604\uD589 \uCD94\uC815 \uAC00\uC815",
    "\uACC4\uB9AC\uC801 \uAC00\uC815",
    "\uAC00\uC815\uAC12",
    "(2)",
)
_CAPTION_SENSITIVITY = (
    "\uAC00\uC815\uBBFC\uAC10\uB3C4",
    "\uBBFC\uAC10\uB3C4 \uBD84\uC11D",
    "\uBBFC\uAC10\uB3C4\uBD84\uC11D",
    "\uBCF4\uD5D8\uC704\uD5C8",
)
_NEGATIVE = ("\uAE08\uC735\uC0C1\uD488", "\uC218\uC9003", "\uACF5\uC815\uAC00\uCE58")

_ROW_ASSUMPTION = (
    "\uC704\uD5C8\uB960",
    "\uD574\uC57D\uB960",
    "\uC0AC\uC5C5\uBE44",
    "\uD560\uC778\uC728",
    "\uC2E0\uB8B0\uC218\uC900",
)
_ROW_SENSITIVITY = (
    "\uC704\uD5C8\uB960",
    "\uD574\uC57D\uB960",
    "\uC0AC\uC5C5\uBE44",
    "\uC0AC\uC5C5\uBE44\uC728",
    "\uC190\uD574\uC728",
    "\uB2F9\uAE30\uC190\uC775 \uC601\uD5A5",
    "\uC794\uC5EC\uBCF4\uC791",
    "\uC704\uD5C8\uB960 \uAC00\uC815 \uBCC0\uACBD",
    "\uD574\uC57D\uB960 \uAC00\uC815 \uBCC0\uACBD",
)
_CAPTION_ROLLFORWARD = (
    "\uCE21\uC815\uC694\uC18C",
    "\uBCC0\uB3D9 \uC138\uBD80",
    "\uBCC0\uB3D9\uB0B4\uC5ED",
    "\uBBF8\uB798\uC11C\uBE44\uC2A4 \uAD00\uB828",
    "\uC0C1\uC138\uBCC0\uB3D9",
)
_ROW_ROLLFORWARD = (
    "\uB2F9\uAE30 \uCD5C\uCD08 \uC778\uC2DD",
    "\uAC00\uC815\uBCC0\uACBD\uD6A8\uACFC",
    "\uBCF4\uD5D8\uACC4\uC57D\uB9C8\uC9C4 \uCD94\uC815\uC758 \uBCC0\uACBD",
    "\uBB3C\uB7C9\uCC28\uC774",
    "\uAE30\uCD08 \uC21C\uC7A5\uBD80\uAE08\uC561",
    "\uAE30\uB9D0 \uC21C\uC7A5\uBD80\uAE08\uC561",
)
_HEADER_ROLLFORWARD = (
    "\uBBF8\uB798\uD604\uAE08\uD750\uB984\uC758 \uD604\uC7AC\uAC00\uCE58 \uCD94\uC815\uCE58",
    "\uBE44\uAE08\uC735\uC704\uD5C8\uC5D0\uB300\uD55C \uC704\uD5C8\uC870\uC815",
)


@dataclass
class ExtractedSensitivityTable:
    caption: str
    header: list[list[str]]
    rows: list[list[str]]
    footnotes: list[str]
    line_no: int
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    table_kind: str = "unknown"
    block_type: str = "unknown"
    slice_label: str = "unknown"
    slice_policy: str = "unknown"
    mvp_candidate: bool = False


def _is_rollforward_table(caption: str, row_labels: list[str], flat_header: list[str]) -> bool:
    cap = caption or ""
    if any(k in cap for k in _CAPTION_ROLLFORWARD):
        return True
    joined_rows = " ".join(row_labels[:12])
    if sum(1 for s in _ROW_ROLLFORWARD if s in joined_rows) >= 2:
        return True
    joined_hdr = " ".join(flat_header)
    if sum(1 for s in _HEADER_ROLLFORWARD if s in joined_hdr) >= 2:
        return True
    return False


def _classify_kind(caption: str, row_labels: list[str], flat_header: list[str]) -> str:
    if _is_rollforward_table(caption, row_labels, flat_header):
        return "unknown"
    joined = caption + " ".join(row_labels[:10]) + " ".join(flat_header)
    if any(k in joined for k in _CAPTION_SENSITIVITY) or "\uBBFC\uAC10\uB3C4" in joined:
        if sum(1 for s in _ROW_SENSITIVITY if s in joined) >= 1:
            return "sensitivity_analysis"
    if any(k in joined for k in _CAPTION_ASSUMPTION) or sum(1 for s in _ROW_ASSUMPTION if s in joined) >= 2:
        return "assumption_values"
    if sum(1 for s in _ROW_SENSITIVITY if s in joined) >= 2:
        return "sensitivity_analysis"
    return "unknown"


def is_mvp_table(t: ExtractedSensitivityTable) -> bool:
    if t.table_kind == "unknown":
        return False
    if t.block_type == "reinsurance":
        return False
    if t.slice_policy == "whole_company_life":
        return t.slice_label == "whole_company_life"
    if t.slice_label != "long_term":
        return False
    joined = " ".join([t.caption] + _first_col_labels(t.rows))
    if has_short_term_markers(joined) and not table_has_long_term_label([joined]):
        return False
    return True


def _score_table(t, company_name: str) -> tuple[int, str, str, str, str, list[str]]:
    score = 0
    reasons: list[str] = []
    caption = t.caption or ""

    if any(k in caption for k in _NEGATIVE):
        return 0, "unknown", "unknown", expected_slice_policy(company_name), "unknown", ["skip: non-insurance sensitivity"]

    assump_cap = sum(1 for k in _CAPTION_ASSUMPTION if k in caption)
    sens_cap = sum(1 for k in _CAPTION_SENSITIVITY if k in caption)
    if sens_cap >= 1:
        score += 4
        reasons.append(f"caption: sensitivity keywords x{sens_cap}")
    elif assump_cap >= 1:
        score += 3
        reasons.append(f"caption: assumption keywords x{assump_cap}")

    flat_header = _flat_header(t)
    row_labels = _first_col_labels(t.rows)
    all_cells = _all_row_cells(t.rows)
    joined = " ".join(row_labels + flat_header)

    assump_rows = sum(1 for s in _ROW_ASSUMPTION if s in joined)
    sens_rows = sum(1 for s in _ROW_SENSITIVITY if s in joined)
    if sens_rows >= 2:
        score += 3
        reasons.append(f"rows: sensitivity stubs x{sens_rows}")
    elif assump_rows >= 2:
        score += 2
        reasons.append(f"rows: assumption stubs x{assump_rows}")
    elif sens_rows == 1 or assump_rows == 1:
        score += 1
        reasons.append("rows: 1 assumption/sensitivity stub")

    if any(k in flat_header for k in ("\uB2F9\uAE30\uC190\uC775", "\uC794\uC5EC\uBCF4\uC791", "\uBBFC\uAC10\uB3C4")):
        score += 1
        reasons.append("header: sensitivity columns")

    block_type = _classify_block(caption, row_labels)
    footnotes = list(t.footnotes or [])
    slice_label = _classify_slice(caption, flat_header, row_labels, all_cells, footnotes, company_name)
    slice_policy = expected_slice_policy(company_name)
    table_kind = _classify_kind(caption, row_labels, flat_header)

    if table_kind != "unknown":
        score += 1
        reasons.append(f"kind: {table_kind}")
    if slice_label == "long_term" or slice_policy == "whole_company_life":
        score += 1
        reasons.append(f"slice: {slice_label}")

    if sens_cap == 0 and assump_cap == 0 and sens_rows == 0 and assump_rows == 0:
        if score > 3:
            score = 3
            reasons.append("gate: weak sensitivity signals capped at 3")

    return score, block_type, slice_label, slice_policy, table_kind, reasons


def extract_sensitivity_tables(
    xml_path: Path,
    company_name: str = "",
    min_score: int = 4,
    mvp_only: bool = False,
) -> list[ExtractedSensitivityTable]:
    out: list[ExtractedSensitivityTable] = []
    for t in _iter_tables_with_context(xml_path):
        score, block_type, slice_label, slice_policy, table_kind, reasons = _score_table(t, company_name)
        if score < min_score:
            continue
        row = ExtractedSensitivityTable(
            caption=t.caption,
            header=t.header,
            rows=t.rows,
            footnotes=t.footnotes,
            line_no=t.line_no,
            score=score,
            reasons=reasons,
            table_kind=table_kind,
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


def to_jsonable(t: ExtractedSensitivityTable) -> dict:
    return {
        "caption": t.caption,
        "table_kind": t.table_kind,
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
