# -*- coding: utf-8 -*-
"""Shared IFRS17 table-scoring config loader (owner REFACTOR-1, 2026-06-13).

The IFRS17 DART-note extractors (csm / measurement / insurance_pl / reinsurance /
bs_snapshot / sensitivity) each score candidate tables by keyword signals
(caption / row-stub / header / total / negative-topic words). Those keyword sets
were hardcoded and copy-pasted across the extractors. This module externalises
them to ``data/ifrs17/table_scoring_keywords.yaml`` so a new label variant lands
in CONFIG, not Python — and gives every extractor one place to load from.

Usage:
    from .scoring import load_scoring
    _SC = load_scoring("csm")
    _CAPTION_PRIMARY = _SC.caption_primary[0]
    _CAPTION_VERBS = _SC.caption_verbs

Design notes:
- Keyword lists only. Structural regexes (year-bucket / sub-caption patterns)
  stay in each extractor — they are not user-tunable label variants.
- Unknown YAML keys for an extractor are preserved in ``.extra`` (dict of tuples)
  so an extractor can carry its own keyword sets (e.g. block markers) without a
  schema change here.
- Missing keys fall back to empty tuples (an extractor only declares what it uses).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

_YAML_PATH = Path(__file__).resolve().parents[2] / "data" / "ifrs17" / "table_scoring_keywords.yaml"

_KNOWN = (
    "caption_primary", "caption_secondary", "caption_verbs",
    "negative_topic_words", "row_stubs_strong", "row_stubs_weak",
    "header", "total_words",
)


@dataclass(frozen=True)
class ScoringConfig:
    """Per-extractor scoring keyword sets (each a tuple of str)."""
    name: str
    caption_primary: tuple = ()
    caption_secondary: tuple = ()
    caption_verbs: tuple = ()
    negative_topic_words: tuple = ()
    row_stubs_strong: tuple = ()
    row_stubs_weak: tuple = ()
    header: tuple = ()
    total_words: tuple = ()
    extra: dict = field(default_factory=dict)  # extractor-specific extra lists


def _as_tuple(value) -> tuple:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


@lru_cache(maxsize=1)
def _load_yaml() -> dict:
    return yaml.safe_load(_YAML_PATH.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=None)
def load_scoring(name: str) -> ScoringConfig:
    """Return the ScoringConfig for extractor ``name`` (cached). Unknown name
    yields an all-empty config rather than raising — lets an extractor adopt the
    loader before its YAML block exists."""
    block = _load_yaml().get(name) or {}
    return ScoringConfig(
        name=name,
        caption_primary=_as_tuple(block.get("caption_primary")),
        caption_secondary=_as_tuple(block.get("caption_secondary")),
        caption_verbs=_as_tuple(block.get("caption_verbs")),
        negative_topic_words=_as_tuple(block.get("negative_topic_words")),
        row_stubs_strong=_as_tuple(block.get("row_stubs_strong")),
        row_stubs_weak=_as_tuple(block.get("row_stubs_weak")),
        header=_as_tuple(block.get("header")),
        total_words=_as_tuple(block.get("total_words")),
        extra={k: _as_tuple(v) for k, v in block.items() if k not in _KNOWN},
    )
