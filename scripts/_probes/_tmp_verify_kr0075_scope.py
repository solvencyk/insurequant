# -*- coding: utf-8 -*-
"""Independently verify (using the real kics_json_rules functions, not hand
arithmetic) that KR0075 is a company-level INCL-scope filer, and that the
2026.2Q bucket (with our patched 47/48/49) lands in an uncapped-equivalent
branch under both scope readings.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "solvency" / "validation"))
sys.path.insert(0, str(REPO))

import kics_json_rules as R  # type: ignore
import scripts.validate_kics_disclosure as V  # type: ignore

SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad"
)

records = V._load_records(SCRATCH / "kics_disclosure_after_kr0075.json")
buckets = R._build_buckets(records) if hasattr(R, "_build_buckets") else None
print("has _build_buckets:", buckets is not None)
