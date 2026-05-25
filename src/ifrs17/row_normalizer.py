# -*- coding: utf-8 -*-
"""Map raw IFRS17 liability-rollforward row labels to canonical_keys.

Loads ``data/ifrs17/normalization/row_aliases.yaml`` (substring matching).
Conflict resolution: longest matched alias wins; ties break by YAML document order.

See ``scripts/ifrs17_normalize_liability.py`` for batch tagging of extracted JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_ROW_ALIASES_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "ifrs17"
    / "normalization"
    / "row_aliases.yaml"
)


@dataclass(frozen=True)
class RowAliasNormalizer:
    scope: str
    version: int | None
    _pairs: tuple[tuple[str, str], ...]
    """(canonical_key, substring) pairs in deterministic document order."""

    def canonical_for_label(self, label: str) -> str | None:
        if not isinstance(label, str) or not label.strip():
            return None
        text = label
        best_key: str | None = None
        best_len = -1
        best_order = 1 << 30
        for order, (canonical_key, sub) in enumerate(self._pairs):
            if not sub:
                continue
            if sub in text:
                ln = len(sub)
                if ln > best_len or (ln == best_len and order < best_order):
                    best_len = ln
                    best_order = order
                    best_key = canonical_key
        return best_key

    def row_label_from_cells(self, cells: list[Any]) -> str:
        """First column cell is treated as the row label."""
        if not cells:
            return ""
        first = cells[0]
        return first.strip() if isinstance(first, str) else ""

    def tag_row_cells(self, cells: list[Any]) -> dict[str, Any]:
        label = self.row_label_from_cells(cells)
        ck = self.canonical_for_label(label)
        return {"cells": cells, "canonical_key": ck}


def load_row_aliases(
    yaml_path: Path | str | None = None,
    *,
    _raw: Mapping[str, Any] | None = None,
) -> RowAliasNormalizer:
    """Parse ``row_aliases.yaml`` into a matcher.

    If ``_raw`` is set (tests), ``yaml_path`` is ignored for file I/O.
    """
    raw: Mapping[str, Any]
    if _raw is not None:
        raw = _raw
    else:
        path = Path(yaml_path) if yaml_path else DEFAULT_ROW_ALIASES_PATH
        text = path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(text)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected mapping at YAML root in {path}")
        raw = parsed

    scope = raw.get("scope") or ""
    version = raw.get("version")
    if version is not None:
        version = int(version)

    aliases = raw.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise ValueError("`aliases` must be a mapping")

    pairs: list[tuple[str, str]] = []
    for canonical_key in aliases:
        entry = aliases[canonical_key]
        if not isinstance(entry, list):
            continue
        for item in entry:
            if isinstance(item, str) and item:
                pairs.append((str(canonical_key), item))

    return RowAliasNormalizer(
        scope=str(scope),
        version=version,
        _pairs=tuple(pairs),
    )
