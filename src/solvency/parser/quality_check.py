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

# inbox 20260831T0700Z ("docling window drops market section"): the keyword-window
# page selector can drop an entire 6-4 시장위험 or 6-8 위험민감도 section from
# source_page_ranges (or -- confirmed separately in this same round -- select the
# right page yet still lose the section's content in conversion), and nothing
# downstream of docling read source_page_ranges/keyword_hit_pages to notice. These
# terms are each section's own row/heading label (already proven robust across
# companies as the DEFAULT_RATIO_KEYWORDS page-selection vocabulary in
# docling_parser.py); requiring them in the *converted* MD body -- independent of
# why they'd be missing -- catches a dropped page, a dropped section, AND a
# selected-but-unconverted page in one check. Only enforced on even quarters
# (Q2/Q4): 1Q/3Q 간이공시 legitimately omit 36-40/41-46/금리민감도 (cadence, not a
# parser gap) -- see quirk #3 in the kics-parser skill.
_RE_REQUIRED_MARKET: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("금리위험액(6-4)", re.compile(r"금리\s*위험\s*액")),
    ("주식위험액(6-4)", re.compile(r"주식\s*위험\s*액")),
    ("부동산위험액(6-4)", re.compile(r"부동산\s*위험\s*액")),
    ("외환위험액(6-4)", re.compile(r"외환\s*위험\s*액")),
    ("자산집중위험액(6-4)", re.compile(r"자산\s*집중\s*위험\s*액")),
)
_RE_REQUIRED_SENSITIVITY: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("위험민감도(6-8)", re.compile(r"위험\s*민감도|금리\s*민감도|환율\s*민감도")),
)


def _is_even_quarter(meta: dict[str, str]) -> bool:
    q = meta.get("quarter", "").strip().upper()
    return q.endswith("Q2") or q.endswith("Q4")


def _page_range_span(spr: str) -> int:
    """Count selected pages from a 'source_page_ranges' front-matter string
    like '6-38;44-47'. Malformed/empty input counts as 0, never raises."""
    total = 0
    for part in (spr or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                total += int(b) - int(a) + 1
            except ValueError:
                pass
        else:
            try:
                int(part)
                total += 1
            except ValueError:
                pass
    return total


def _page_coverage_ratio(meta: dict[str, str]) -> float | None:
    """selected-page-count / total-PDF-page-count, or None if undeterminable.

    2026-09-01 calibration (39 companies, 2026.2Q, scripts/_probes/
    probe_20260901b_ratio_calibration.py): this ratio does NOT cleanly separate
    companies whose MD is missing a required section (median 57.6%, range
    11.7%-100%) from companies whose MD is fine (median 51.6%, range 18.8%-
    79.2%) -- the OCR/full-page-scan companies actually score *highest* (100%,
    because keyword selection failed outright and fell back to the whole
    document) while still being incomplete. A blanket mid-range threshold would
    misfire either way, so this is deliberately NOT used to force "review" by
    itself -- only as a diagnostic in the reason string, plus a very low
    catastrophic-failure floor (see REVIEW_RATIO_FLOOR below)."""
    spr = meta.get("source_page_ranges", "")
    selected = _page_range_span(spr)
    if selected <= 0:
        return None
    source_pdf = meta.get("source_pdf", "").strip()
    if not source_pdf:
        return None
    try:
        from pypdf import PdfReader

        total = len(PdfReader(source_pdf).pages)
    except Exception:
        return None
    if total <= 0:
        return None
    return selected / total


# Coarse, low-confidence net for a near-total selection failure (e.g. the
# whole document minus a couple of pages fell outside every keyword window).
# Deliberately far below the calibrated "ok" range's own minimum (18.8%) so it
# only fires on cases the content check below wouldn't already catch.
REVIEW_RATIO_FLOOR = 0.10

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
    """Estimate how many table *value* cells were parseable as numbers.

    Docling outputs cells separated by ``|`` in markdown tables. We sample
    cells, ignore blank/dash placeholders, and compute the fraction that
    matches a numeric pattern.

    The leading cell of each row is the Korean item label ("가. 지급여력금액"),
    never a number, so counting it measured table shape rather than parse
    quality and capped the rate near 0.5-0.6 even on a perfectly parsed file.
    Since ``score()`` multiplies the score by this rate and then requires
    >= 0.7, that made the gate unsatisfiable: 485 of 488 md_inbox files were
    routed to review, including files with every required row present.
    Skipping the label column moves the median rate 0.595 -> 0.699 and the
    accept count 3 -> 182 (measured 2026-07-21 over md_inbox, 488 files).
    """
    cells: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells.extend(c.strip() for c in stripped.strip("|").split("|")[1:])
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
    has_unit = _has_unit(body)
    has_date = bool(meta.get("disclosure_date", "").strip())
    rate = _numeric_normalisation_rate(body)

    # inbox 20260831T0700Z guard: even-quarter (Q2/Q4) full-form disclosures
    # must carry every 6-4 시장위험/6-8 위험민감도 section marker in the
    # *converted* body. 1Q/3Q 간이공시 legitimately omit these (cadence, not a
    # parser gap -- see kics-parser skill quirk #3), so the check is skipped
    # there entirely rather than risk flagging every odd-quarter filing.
    missing_window: list[str] = []
    if _is_even_quarter(meta):
        missing_window = _missing_rows(body, _RE_REQUIRED_MARKET) + _missing_rows(
            body, _RE_REQUIRED_SENSITIVITY
        )
    page_ratio = _page_coverage_ratio(meta)
    ratio_critical = page_ratio is not None and page_ratio < REVIEW_RATIO_FLOOR

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
    if (
        missing_core
        or critical_missing
        or missing_window
        or ratio_critical
        or score_value < threshold
    ):
        decision = "review"
        reason = (
            f"missing_core={missing_core} missing_ext={missing_extended} "
            f"missing_window={missing_window} "
            f"page_ratio={'n/a' if page_ratio is None else f'{page_ratio:.2f}'} "
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
        missing_rows=sorted(set(missing_core + missing_extended + missing_window)),
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
