"""Skim-only extractor for the 보험계약부채 detail tables.

Per user decision (Candidate C in docs/claude-agent-ifrs17.md §2):
  - Capture the raw structure (header rows + body rows) only.
  - NO per-company YAML mapping — that's a later stage.

Targets two flavours:
  - (1) BS snapshot: header has 보험계약부채 / 재보험계약자산 etc.
  - (3) Liability rollforward: header has 잔여보장 / 발생사고 multi-index.

Scoring is intentionally similar in spirit to csm_extractor: caption + header
signals, soft thresholds, no per-company regex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .csm_extractor import (
    _iter_tables_with_context,
    _looks_like_text_label,
)


_CAPTION_KEYWORDS_BS = ("보험계약부채", "재보험계약자산", "재보험계약부채",
                         "보험계약자산")
_CAPTION_KEYWORDS_ROLL = ("잔여보장", "발생사고", "보험계약부채",
                           "보험부채 변동", "측정요소", "변동내역")

_HEADER_KEYWORDS_BS = ("보험계약부채", "보험계약자산", "재보험계약자산",
                        "재보험계약부채", "순보험계약")
_HEADER_KEYWORDS_ROLL = ("잔여보장", "발생사고", "손실요소", "비손실요소",
                          "이행현금흐름")


@dataclass
class ExtractedLiabilityTable:
    caption: str
    header: list[list[str]]
    rows: list[list[str]]
    footnotes: list[str]
    line_no: int
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    kind: str = "unknown"        # "bs_snapshot", "rollforward", "unknown"


def _score(t) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    caption = t.caption or ""

    bs_caption_hits = sum(1 for k in _CAPTION_KEYWORDS_BS if k in caption)
    roll_caption_hits = sum(1 for k in _CAPTION_KEYWORDS_ROLL if k in caption)
    if bs_caption_hits >= 2:
        score += 2
        reasons.append(f"caption: BS keywords x{bs_caption_hits}")
    if roll_caption_hits >= 1:
        score += 1
        reasons.append(f"caption: rollforward keywords x{roll_caption_hits}")

    flat_header_cells = [c for row in t.header for c in row]
    if not flat_header_cells and t.rows:
        for cand in t.rows[:3]:
            if not cand:
                continue
            if len(cand) == 1 and ("단위" in cand[0] or not cand[0].strip()):
                continue
            if all(_looks_like_text_label(c) for c in cand):
                flat_header_cells = list(cand)
                break

    bs_header_hits = sum(
        1 for c in flat_header_cells
        if any(k in c for k in _HEADER_KEYWORDS_BS)
    )
    roll_header_hits = sum(
        1 for c in flat_header_cells
        if any(k in c for k in _HEADER_KEYWORDS_ROLL)
    )

    if bs_header_hits >= 2:
        score += 3
        reasons.append(f"header: BS keywords x{bs_header_hits}")
    elif bs_header_hits == 1:
        score += 1
        reasons.append("header: 1 BS keyword")
    if roll_header_hits >= 2:
        score += 3
        reasons.append(f"header: rollforward keywords x{roll_header_hits}")
    elif roll_header_hits == 1:
        score += 1
        reasons.append("header: 1 rollforward keyword")

    if roll_header_hits >= 2 and roll_header_hits >= bs_header_hits:
        kind = "rollforward"
    elif bs_header_hits >= 2:
        kind = "bs_snapshot"
    elif (roll_header_hits + bs_header_hits) >= 1:
        kind = "snapshot_or_partial"
    else:
        kind = "unknown"

    return score, kind, reasons


def extract_liability_tables(
    xml_path: Path, min_score: int = 4
) -> list[ExtractedLiabilityTable]:
    """Return liability structural-capture tables found in ``xml_path``.

    No numeric parsing — raw header + row strings only.
    """
    out: list[ExtractedLiabilityTable] = []
    for t in _iter_tables_with_context(xml_path):
        score, kind, reasons = _score(t)
        if score < min_score:
            continue
        out.append(ExtractedLiabilityTable(
            caption=t.caption,
            header=t.header,
            rows=t.rows,
            footnotes=t.footnotes,
            line_no=t.line_no,
            score=score,
            reasons=reasons,
            kind=kind,
        ))
    out.sort(key=lambda x: (-x.score, x.line_no))
    return out


def to_jsonable(t: ExtractedLiabilityTable) -> dict:
    return {
        "caption": t.caption,
        "kind": t.kind,
        "line_no": t.line_no,
        "score": t.score,
        "reasons": t.reasons,
        "header": t.header,
        "rows": t.rows,
        "footnotes": t.footnotes,
    }
