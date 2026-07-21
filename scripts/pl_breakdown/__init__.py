"""PL breakdown extractor, split out of scripts/build_pl_breakdown.py (2026-07-21).

Layers, in dependency order:
  common     — label/number/quarter helpers shared by everything
  tier1      — 포괄손익계산서 (income statement) extraction
  tier2      — generic 발행보험 계약유형별 / 재보험 note extraction
  companies  — per-company note handlers + the SONBO/LIFE dispatch tables

The entry point (scripts/build_pl_breakdown.py) keeps discover/assemble/main.
tier1 and tier2 have no edges between them; companies depends on all three.
"""
