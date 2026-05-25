"""JSON Schema validation for ``kics_data.json``.

The schema lives at ``schemas/kics_data.schema.json`` so it can be
shared with non-Python consumers (downstream dashboards, etc.).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from solvency.config import settings


@dataclasses.dataclass
class SchemaResult:
    ok: bool
    errors: list[str]


def _load_schema() -> dict[str, Any]:
    path = settings.schemas_dir / "kics_data.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(payload: dict[str, Any]) -> SchemaResult:
    """Validate a ``kics_data.json`` payload against the JSON Schema.

    Uses ``jsonschema`` if installed; falls back to a tiny structural
    check (top-level keys + record key presence) if not.
    """
    try:
        import jsonschema
    except ImportError:
        return _fallback(payload)

    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = [
        f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in validator.iter_errors(payload)
    ]
    return SchemaResult(ok=not errors, errors=errors)


def _fallback(payload: dict[str, Any]) -> SchemaResult:
    errors: list[str] = []
    for key in ("generated_at", "records"):
        if key not in payload:
            errors.append(f"missing top-level key: {key}")
    records = payload.get("records", [])
    if not isinstance(records, list):
        errors.append("records must be a list")
    seen: set[tuple[str, str, str, str]] = set()
    for idx, rec in enumerate(records or []):
        if not isinstance(rec, dict):
            errors.append(f"record[{idx}] must be an object")
            continue
        for required in (
            "company_code",
            "fiscal_year",
            "quarter",
            "metric_id",
            "metric_name_ko",
        ):
            if not rec.get(required):
                errors.append(f"record[{idx}].{required} is required")
        key = (
            str(rec.get("company_code", "")),
            str(rec.get("fiscal_year", "")),
            str(rec.get("quarter", "")),
            str(rec.get("metric_id", "")),
        )
        if key in seen:
            errors.append(f"record[{idx}] duplicate key: {key}")
        seen.add(key)
    return SchemaResult(ok=not errors, errors=errors)
