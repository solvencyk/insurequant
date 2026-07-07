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


def _fingerprint_matches(item_name: str, table_label: str) -> bool:
    """OCR-typo-tolerant fallback for item12/13, matched on "불인정"/"재분류"
    alone — each is unique to exactly one item in the whole K-ICS 1-28
    schema, so a bare substring hit is sufficient without needing a second
    confirming keyword. (Originally required "주주배당액"/"인정한도" too, but
    docling sometimes truncates the row label before reaching them — KR0099
    2023.3Q+: "Ⅱ.지분여력금액으로 불인정하는 항 목" with no suffix at all.)"""
    compact = table_label.replace(" ", "")
    if "불인정" in item_name:
        return "불인정" in compact
    if "재분류" in item_name:
        return "재분류" in compact
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
        if not _label_matches(item_name, label) and not _fingerprint_matches(item_name, label):
            continue
        if raw is None:
            continue
        cleaned = raw.strip()
        if cleaned in ("", "-", "\u2500", "\u2013"):
            return "0"
        parsed = parse_value(raw)
        if parsed is None:
            return "0"
        return parsed
    return None