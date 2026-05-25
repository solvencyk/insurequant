"""Quality gate for Docling markdown outputs.

The legacy parser was permissive: missing rows, mangled numbers and
broken table structure all bled silently into the final JSON. With
Docling fronting the pipeline we explicitly score each markdown file
and route low-quality ones to a manual review queue ("Send these to
Gemini and re-import").

The data harness (``--stage data``) reads the same scoring functions to
gate ``kics_data.json`` builds.
"""

from __future__ import annotations

import csv
import dataclasses
import logging
import re
from pathlib import Path
from typing import Iterable

from solvency.config import settings

logger = logging.getLogger(__name__)


# Optional space after the dot (e.g. "가.지급여력금액" vs "가. 지급여력금액").
_RE_REQUIRED_CORE: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("가. 지급여력금액", re.compile(r"가\.\s*지급여력금액")),
    ("나. 지급여력기준금액", re.compile(r"나\.\s*지급여력기준금액")),
    ("다. 지급여력비율", re.compile(r"다\.\s*지급여력비율")),
)
_RE_REQUIRED_EXTENDED: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("보완자본", re.compile(r"보완\s*자본")),
    ("생명장기손해보험위험액", re.compile(r"생명\s*장기\s*손해\s*보험\s*위험\s*액")),
)

_NUMERIC_RE = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?")
_DASH_RE = re.compile(r"^[\u2014\u2013\u2015\-]$")


@dataclasses.dataclass
class QualityReport:
    md_path: Path
    company_code: str
    score: float
    missing_rows: list[str]
    has_unit: bool
    has_disclosure_date: bool
    numeric_normalisation_rate: float
    decision: str  # "accept" | "review"
    reason: str


def _read_md(md_path: Path) -> tuple[dict[str, str], str]:
    """Return (front_matter_dict, body)."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    _, _, rest = text.partition("---\n")
    front, _, body = rest.partition("\n---\n")
    meta: dict[str, str] = {}
    for raw in front.splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, body


def _missing_rows(
    body: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]
) -> list[str]:
    return [label for label, pat in patterns if not pat.search(body)]


def _has_unit(body: str) -> bool:
    return any(token in body for token in ("억원", "백만원", "원", "%"))


def _numeric_normalisation_rate(body: str) -> float:
    """Estimate how many table cells were parseable as numbers.

    Docling outputs cells separated by ``|`` in markdown tables. We sample
    cells, ignore blank/dash placeholders, and compute the fraction that
    matches a numeric pattern.
    """
    cells: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells.extend(c.strip() for c in stripped.strip("|").split("|"))
    if not cells:
        return 0.0
    numeric = 0
    considered = 0
    for cell in cells:
        if not cell or _DASH_RE.match(cell):
            continue
        considered += 1
        if _NUMERIC_RE.search(cell):
            numeric += 1
    if considered == 0:
        return 0.0
    return numeric / considered


def score(md_path: Path) -> QualityReport:
    meta, body = _read_md(md_path)
    missing_core = _missing_rows(body, _RE_REQUIRED_CORE)
    missing_extended = _missing_rows(body, _RE_REQUIRED_EXTENDED)
    missing = list(missing_core)
    has_unit = _has_unit(body)
    has_date = bool(meta.get("disclosure_date", "").strip())
    rate = _numeric_normalisation_rate(body)

    score_value = 1.0
    score_value -= 0.2 * len(missing_core)
    score_value -= 0.1 * len(missing_extended)
    if not has_unit:
        score_value -= 0.15
    if not has_date:
        score_value -= 0.1
    score_value *= max(rate, 0.5)
    score_value = max(0.0, min(1.0, score_value))

    threshold = 0.7
    critical_missing = "생명장기손해보험위험액" in missing_extended
    if missing_core or critical_missing or score_value < threshold:
        decision = "review"
        reason = (
            f"missing_core={missing_core} missing_ext={missing_extended} "
            f"score={score_value:.2f} "
            f"unit={has_unit} date={has_date} numeric_rate={rate:.2f}"
        )
    else:
        decision = "accept"
        reason = f"score={score_value:.2f} numeric_rate={rate:.2f}"

    return QualityReport(
        md_path=md_path,
        company_code=meta.get("company_code", ""),
        score=score_value,
        missing_rows=sorted(set(missing_core + missing_extended)),
        has_unit=has_unit,
        has_disclosure_date=has_date,
        numeric_normalisation_rate=rate,
        decision=decision,
        reason=reason,
    )


def write_review_queue(reports: Iterable[QualityReport], run_id: str) -> Path:
    """Persist the list of files that need a Gemini second opinion.

    The output is a flat CSV that an operator can paste into Gemini to
    redo only the failing PDFs.
    """
    target = settings.review_queue_dir / f"review_queue_{run_id}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            [
                "md_path",
                "company_code",
                "score",
                "missing_rows",
                "has_unit",
                "has_disclosure_date",
                "numeric_normalisation_rate",
                "reason",
            ]
        )
        for report in reports:
            if report.decision != "review":
                continue
            writer.writerow(
                [
                    str(report.md_path),
                    report.company_code,
                    f"{report.score:.3f}",
                    ";".join(report.missing_rows),
                    int(report.has_unit),
                    int(report.has_disclosure_date),
                    f"{report.numeric_normalisation_rate:.3f}",
                    report.reason,
                ]
            )
    return target


def filter_accepted(reports: Iterable[QualityReport]) -> list[Path]:
    return [r.md_path for r in reports if r.decision == "accept"]
