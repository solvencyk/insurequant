"""Markdown -> ``kics_data.json`` builder.

DEPRECATED 2026-05-30: this module's output (``kics_data.json``) is no
longer the active K-ICS master. The live master is
``kics_disclosure.json`` (root, populated by ``scripts/fill_*`` mergers,
read directly by K-ICS.html). This builder is preserved for the legacy
Stage 6-3 harness path but should not be invoked by new code. Both
output files (``kics_data.json`` and ``insurance_data.json``) were
removed from the repo root on 2026-05-30; re-running ``write()`` will
recreate the file at ``settings.kics_json_path`` if you actually need
the legacy artifact.

Contract enforced by this module (referenced by Stage 6-3 of the harness):

- Output filename is fixed: ``kics_data.json``. ``insurance_data.json``
  is written as a deprecated alias only when the env var
  ``SOLVENCY_LEGACY_JSON_ALIAS`` is set to a non-empty path.
- Records are uniquely identified by
  ``(company_code, fiscal_year, quarter, metric_id)``. Inserts and
  updates are merged in a single deterministic dictionary so two runs
  on the same input produce byte-identical JSON.
- Numbers go through one canonical normaliser; "—" / "-" / "" become
  ``None``; parentheses become negatives; ``%`` is stripped into a
  separate ``unit`` field.
- Memory: each markdown file is opened, parsed and discarded inside the
  loop. No global accumulation of raw markdown bodies.
"""

from __future__ import annotations

import dataclasses
import gc
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from solvency.config import settings

logger = logging.getLogger(__name__)


METRIC_ID_BY_ROW = {
    "가. 지급여력금액": "solvency_amount",
    "가.지급여력금액": "solvency_amount",
    "기본자본": "tier1_capital",
    "보완자본": "tier2_capital",
    "나. 지급여력기준금액": "required_capital",
    "나.지급여력기준금액": "required_capital",
    "다. 지급여력비율": "solvency_ratio",
    "다.지급여력비율": "solvency_ratio",
}


_NUMBER_RE = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?")
_PCT_RE = re.compile(r"%")
_DASH = {"\u2014", "\u2013", "\u2015", "-", ""}


@dataclasses.dataclass
class MdRecord:
    company_code: str
    fiscal_year: str
    quarter: str
    disclosure_date: str
    metric_id: str
    metric_name_ko: str
    value: float | None
    unit: str
    source_file: str
    parse_confidence: float | None


def _normalise_numeric(raw: str) -> tuple[float | None, str]:
    """Return ``(value, unit)``.

    Examples:
        "12,345" -> (12345.0, "")
        "(1,234)" -> (-1234.0, "")
        "178.4 %" -> (178.4, "%")
        "—"      -> (None, "")
    """
    cell = raw.strip()
    if cell in _DASH:
        return None, ""
    unit = ""
    if "%" in cell:
        unit = "%"
        cell = _PCT_RE.sub("", cell).strip()
    is_negative = cell.startswith("(") and cell.endswith(")")
    if is_negative:
        cell = cell[1:-1]
    match = _NUMBER_RE.search(cell)
    if not match:
        return None, unit
    try:
        value = float(match.group(0).replace(",", ""))
    except ValueError:
        return None, unit
    return (-value if is_negative else value), unit


def _read_md(md_path: Path) -> tuple[dict[str, str], str]:
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


def _iter_table_rows(body: str) -> Iterable[list[str]]:
    """Yield cell lists for every markdown table row, ignoring separators."""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= {"-", ":"} for c in cells if c):
            continue
        yield cells


def _records_from_md(md_path: Path) -> list[MdRecord]:
    meta, body = _read_md(md_path)
    company_code = meta.get("company_code", "").strip()
    fiscal_year = meta.get("fiscal_year", "").strip()
    quarter = meta.get("quarter", "").strip()
    disclosure_date = meta.get("disclosure_date", "").strip()
    confidence_raw = meta.get("parse_confidence", "").strip()
    try:
        confidence = float(confidence_raw) if confidence_raw else None
    except ValueError:
        confidence = None

    records: list[MdRecord] = []
    for cells in _iter_table_rows(body):
        if len(cells) < 2:
            continue
        label = cells[0]
        label_compact = label.replace(" ", "")
        metric_id = None
        metric_name = None
        for canonical, mid in METRIC_ID_BY_ROW.items():
            key = canonical.replace(" ", "")
            if key in label_compact or canonical in label:
                metric_id = mid
                metric_name = canonical
                break
        if metric_id is None:
            continue
        value, unit = _normalise_numeric(cells[1])
        records.append(
            MdRecord(
                company_code=company_code,
                fiscal_year=fiscal_year,
                quarter=quarter,
                disclosure_date=disclosure_date,
                metric_id=metric_id,
                metric_name_ko=metric_name or label,
                value=value,
                unit=unit,
                source_file=md_path.name,
                parse_confidence=confidence,
            )
        )
    return records


def _record_key(record: MdRecord) -> tuple[str, str, str, str]:
    return (
        record.company_code,
        record.fiscal_year,
        record.quarter,
        record.metric_id,
    )


def _record_to_dict(record: MdRecord, created_at: str) -> dict[str, object]:
    return {
        "company_code": record.company_code,
        "fiscal_year": record.fiscal_year,
        "quarter": record.quarter,
        "disclosure_date": record.disclosure_date,
        "metric_id": record.metric_id,
        "metric_name_ko": record.metric_name_ko,
        "value": record.value,
        "unit": record.unit,
        "source_type": "docling_markdown",
        "source_file": record.source_file,
        "parse_confidence": record.parse_confidence,
        "created_at": created_at,
    }


def build(md_paths: Iterable[Path]) -> dict[str, object]:
    """Build the ``kics_data.json`` payload from a list of accepted markdowns.

    Returns a dict with two top-level keys: ``generated_at`` (ISO 8601
    UTC) and ``records`` (list, sorted by key for determinism).
    """
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    by_key: dict[tuple[str, str, str, str], dict[str, object]] = {}
    insert_count = 0
    update_count = 0

    for md_path in md_paths:
        try:
            for record in _records_from_md(md_path):
                key = _record_key(record)
                serialised = _record_to_dict(record, created_at)
                if key in by_key:
                    by_key[key].update(serialised)
                    update_count += 1
                else:
                    by_key[key] = serialised
                    insert_count += 1
        finally:
            gc.collect()

    sorted_records = [by_key[k] for k in sorted(by_key.keys())]
    return {
        "generated_at": created_at,
        "insert_count": insert_count,
        "update_count": update_count,
        "records": sorted_records,
    }


def write(payload: dict[str, object], path: Path | None = None) -> Path:
    """Persist the payload to ``kics_data.json`` deterministically."""
    target = path or settings.kics_json_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    alias = settings.legacy_json_alias_path
    if alias and str(alias):
        try:
            if alias.resolve() != target.resolve():
                alias.write_text(
                    json.dumps(
                        payload, ensure_ascii=False, indent=2, sort_keys=False
                    )
                    + "\n",
                    encoding="utf-8",
                )
                logger.warning(
                    "wrote deprecated alias %s; migrate consumers to %s",
                    alias,
                    target,
                )
        except OSError:
            pass
    return target


def checksum(path: Path) -> str:
    """SHA-256 of the JSON output, used by the idempotency harness gate."""
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
