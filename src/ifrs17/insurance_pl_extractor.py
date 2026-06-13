"""Skim-only extractor for section 14(5) insurance P&L detail (A3)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .csm_extractor import _iter_tables_with_context, _looks_like_text_label
from .scoring import load_scoring
from .universe import (
    expected_slice_policy,
    has_short_term_markers,
    is_non_paa_gmm_context,
    table_has_long_term_label,
)

# Scoring KEYWORDS load from data/ifrs17/table_scoring_keywords.yaml (REFACTOR-2,
# 2026-06-13). Block markers (direct/ri/short-term) ride in .extra; structural
# logic unchanged. OCR-typo spellings preserved byte-identical in the YAML.
_SC = load_scoring("insurance_pl")
_CAPTION_PRIMARY = _SC.caption_primary
_CAPTION_SECONDARY = _SC.caption_secondary
_HEADER_MEASUREMENT = _SC.header
_ROW_STUBS_STRONG = _SC.row_stubs_strong
_ROW_STUBS_WEAK = _SC.row_stubs_weak
_SHORT_TERM_MARKERS = _SC.extra["short_term_markers"]
_DIRECT_BLOCK_MARKERS = _SC.extra["direct_block_markers"]
_RI_BLOCK_MARKERS = _SC.extra["ri_block_markers"]


@dataclass
class ExtractedInsurancePlTable:
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


def _flat_header(t) -> list[str]:
    flat = [c for row in t.header for c in row]
    if flat:
        return flat
    if not t.rows:
        return []
    for cand in t.rows[:3]:
        if not cand:
            continue
        if len(cand) == 1 and ("\uB2E8\uC704" in cand[0] or not cand[0].strip()):
            continue
        if all(_looks_like_text_label(c) for c in cand):
            return list(cand)
    return []


def _first_col_labels(rows: list[list[str]]) -> list[str]:
    return [r[0] for r in rows if r and r[0].strip()]


def _all_row_cells(rows: list[list[str]]) -> list[str]:
    return [c for r in rows for c in r if c and c.strip()]


def _caption_subsection(caption: str) -> str:
    """Prefer the last sub-enumerator (1)/2)/...) but skip section headers like (5)."""
    text = caption or ""
    matches = list(re.finditer(r"(?<![(\d])([1-9]\))", text))
    if matches:
        return text[matches[-1].start() :].lstrip()
    return text


def _is_reinsurance_subsection(sub: str) -> bool:
    # 2026-05-24 (A3 gap fix): combined "보험손익 및 재보험손익" sections (Lotte §31) are direct-side too.
    if "보험손익" in sub or "보험수익" in sub or "보험서비스수익" in sub:
        return False
    if any(x in sub for x in ("출재", "순재보험", "재보험계약")):
        if any(x in sub for x in ("원수", "수재(원수", "순보험계약부채")):
            return False
        return True
    has_ri = any(m in sub for m in _RI_BLOCK_MARKERS)
    has_direct = any(m in sub for m in _DIRECT_BLOCK_MARKERS)
    return has_ri and not has_direct


def _classify_block(caption: str, row_labels: list[str]) -> str:
    sub = _caption_subsection(caption)
    has_direct = any(m in sub for m in _DIRECT_BLOCK_MARKERS)
    has_ri = any(m in sub for m in _RI_BLOCK_MARKERS)

    joined_rows = " ".join(row_labels[:30])
    if "\uCD9C\uC7AC\uBCF4\uD5D8" in joined_rows or "\uCD9C\uC7AC\uBCF4\uD5D8\uACC4\uC57D" in joined_rows:
        has_ri = True
    if "\uC7AC\uBCF4\uD5D8\uC218\uC775" in joined_rows or "\uC7AC\uBCF4\uD5D8\uBE44\uC6A9" in joined_rows:
        has_ri = True
    if "\uBCF4\uD5D8\uACC4\uC57D\uC790\uC0B0" in joined_rows or "\uBCF4\uD5D8\uACC4\uC57D\uBD80\uCC44" in joined_rows:
        if "\uCD9C\uC7AC" not in joined_rows:
            has_direct = True

    # 2026-05-24 (A3 gap fix): if rows carry direct P&L lines (\uBCF4\uD5D8\uC218\uC775/\uBCF4\uD5D8\uBE44\uC6A9/\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775/\uC77C\uBC18\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775)
    # without \uCD9C\uC7AC prefix, treat as direct presence even if \uC7AC\uBCF4\uD5D8 lines also appear.
    if (
        "\uBCF4\uD5D8\uC218\uC775" in joined_rows
        or "\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775" in joined_rows
        or "\uC77C\uBC18\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775" in joined_rows
        or "\uC77C\uBC18\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uBE44\uC6A9" in joined_rows
    ):
        has_direct = True

    if has_direct and has_ri:
        return "mixed"
    if has_direct:
        return "direct"
    if has_ri:
        return "reinsurance"
    return "unknown"


def _classify_slice(
    caption: str,
    flat_header: list[str],
    row_labels: list[str],
    all_cells: list[str],
    footnotes: list[str],
    company_name: str,
) -> str:
    policy = expected_slice_policy(company_name)
    texts = [caption] + flat_header + row_labels + all_cells + list(footnotes)
    if policy == "whole_company_life":
        return "whole_company_life"
    if table_has_long_term_label(texts):
        return "long_term"
    joined = " ".join(texts)
    if is_non_paa_gmm_context(joined):
        return "long_term"
    return "unknown"


def _measurement_header_hits(flat_header: list[str]) -> int:
    return sum(1 for c in flat_header if any(k in c for k in _HEADER_MEASUREMENT))


def _has_pl_structure(t: ExtractedInsurancePlTable) -> bool:
    joined = " ".join(_first_col_labels(t.rows))
    strong = sum(1 for s in _ROW_STUBS_STRONG if s in joined)
    weak = sum(1 for s in _ROW_STUBS_WEAK if s in joined)
    if strong >= 2:
        return True
    cap = t.caption or ""
    has_pl_caption = any(k in cap for k in ("\uBCF4\uD5D8\uC190\uC775", "\uBCF4\uD5D8\uC218\uC775", "\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775"))
    if has_pl_caption and strong >= 1:
        return True
    # 2026-05-24 (A3 gap fix): captions like Samsung Life \u00A724 \"\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775 \uBC0F \uBCF4\uD5D8\uC11C\uBE44\uC2A4\uBE44\uC6A9\"
    # may yield only weak row stubs (\uC77C\uBC18\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uC218\uC775/\uC77C\uBC18\uBCF4\uD5D8\uC11C\uBE44\uC2A4\uBE44\uC6A9) plus \uD569\uACC4 rows.
    if has_pl_caption and weak >= 2:
        return True
    return False


def is_mvp_table(t: ExtractedInsurancePlTable) -> bool:
    """MVP A3: direct insurance P&L detail for target slice."""
    if not _has_pl_structure(t):
        return False
    sub = _caption_subsection(t.caption or "")
    if _is_reinsurance_subsection(sub):
        return False
    if t.block_type == "reinsurance":
        return False
    joined = " ".join([t.caption] + _first_col_labels(t.rows))
    if has_short_term_markers(joined):
        if t.slice_policy == "long_term" and t.slice_label != "long_term":
            # 2026-05-24 (A3 gap fix): combined direct+ceded P&L table (e.g. Lotte §31) lists 장기/일반/자동차
            # as COLUMNS — the short-term markers are slice columns, not slice content. Accept if header has 장기.
            flat_hdr = _flat_header(t)
            if not any("장기" in c for c in flat_hdr):
                return False
    if t.slice_policy == "whole_company_life":
        return t.slice_label == "whole_company_life" and t.block_type in ("direct", "mixed", "unknown")
    return t.slice_label == "long_term" and t.block_type in ("direct", "mixed", "unknown")


def _score_table(t, company_name: str) -> tuple[int, str, str, str, list[str]]:
    score = 0
    reasons: list[str] = []
    caption = t.caption or ""

    primary_hits = sum(1 for k in _CAPTION_PRIMARY if k in caption)
    if primary_hits >= 2:
        score += 4
        reasons.append(f"caption: P&L keywords x{primary_hits}")
    elif primary_hits == 1:
        score += 2
        reasons.append("caption: 1 P&L keyword")

    secondary_hits = sum(1 for k in _CAPTION_SECONDARY if k in caption)
    if secondary_hits >= 1 and primary_hits >= 1:
        score += 1
        reasons.append(f"caption: context keywords x{secondary_hits}")

    flat_header = _flat_header(t)
    header_hits = _measurement_header_hits(flat_header)
    if header_hits >= 4:
        score += 4
        reasons.append(f"header: measurement columns x{header_hits}")
    elif header_hits >= 2:
        score += 2
        reasons.append(f"header: measurement columns x{header_hits}")
    elif header_hits == 1:
        score += 1
        reasons.append("header: 1 measurement column")

    row_labels = _first_col_labels(t.rows)
    all_cells = _all_row_cells(t.rows)
    joined_rows = " ".join(row_labels)
    strong_hits = sum(1 for s in _ROW_STUBS_STRONG if s in joined_rows)
    weak_hits = sum(1 for s in _ROW_STUBS_WEAK if s in joined_rows)
    if strong_hits >= 3:
        score += 4
        reasons.append(f"rows: strong P&L stubs x{strong_hits}")
    elif strong_hits >= 2:
        score += 3
        reasons.append(f"rows: strong P&L stubs x{strong_hits}")
    elif strong_hits == 1:
        score += 2
        reasons.append("rows: 1 strong P&L stub")
    elif weak_hits >= 2:
        score += 1
        reasons.append(f"rows: weak stubs x{weak_hits}")

    block_type = _classify_block(caption, row_labels)
    if block_type == "reinsurance":
        score -= 2
        reasons.append("penalty: reinsurance block (A4 territory)")

    footnotes = list(t.footnotes or [])
    slice_label = _classify_slice(caption, flat_header, row_labels, all_cells, footnotes, company_name)
    slice_policy = expected_slice_policy(company_name)
    if slice_policy == "long_term" and slice_label == "long_term":
        score += 1
        if not table_has_long_term_label([caption] + row_labels + all_cells + footnotes):
            reasons.append("slice: long_term via non-PAA/GMM proxy")
        else:
            reasons.append("slice: long_term label present")
    elif slice_policy == "whole_company_life":
        score += 1
        reasons.append("slice: whole_company_life policy")

    if primary_hits == 0 and strong_hits == 0:
        if score > 3:
            score = 3
            reasons.append("gate: weak P&L signals capped at 3")

    return score, block_type, slice_label, slice_policy, reasons


def extract_insurance_pl_tables(
    xml_path: Path,
    company_name: str = "",
    min_score: int = 5,
    mvp_only: bool = False,
) -> list[ExtractedInsurancePlTable]:
    out: list[ExtractedInsurancePlTable] = []
    for t in _iter_tables_with_context(xml_path):
        score, block_type, slice_label, slice_policy, reasons = _score_table(t, company_name)
        if score < min_score:
            continue
        row = ExtractedInsurancePlTable(
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


def to_jsonable(t: ExtractedInsurancePlTable) -> dict:
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
