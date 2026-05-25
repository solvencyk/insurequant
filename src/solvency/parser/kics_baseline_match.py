"""Match baseline labels; return 0 when MD cell is dash."""
from __future__ import annotations

from solvency.parser.kics_disclosure_parser import (
    core_words,
    labels_compatible,
    match_baseline_value,
    normalise_label,
    parse_value,
)


def _label_matches(item_name: str, table_label: str) -> bool:
    key = normalise_label(item_name)
    tkey = normalise_label(table_label)
    if not key or not tkey:
        return False
    if key == tkey:
        return labels_compatible(item_name, table_label)
    if (tkey.startswith(key) or key.startswith(tkey)) and len(tkey) > 4:
        return labels_compatible(item_name, table_label)
    core_key = core_words(item_name)
    core_t = core_words(table_label)
    if core_key and core_t:
        if core_t == core_key or core_key in core_t or core_t in core_key:
            if abs(len(core_t) - len(core_key)) <= 4:
                return labels_compatible(item_name, table_label)
    return False


def match_baseline_value_or_zero(
    item_name: str,
    lookup,
    core_lookup,
    table_pairs: list[tuple[str, str]],
) -> str | None:
    hit = match_baseline_value(item_name, lookup, core_lookup)
    if hit is not None:
        return hit
    for label, raw in table_pairs:
        if not _label_matches(item_name, label):
            continue
        if raw is None:
            continue
        cleaned = raw.strip()
        if cleaned in ("", "-", "\u2500", "\u2013"):
            return "0"
        if parse_value(raw) is None:
            return "0"
    return None