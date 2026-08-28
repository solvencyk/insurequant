# -*- coding: utf-8 -*-
"""Smoke test for the new build_master_xlsx.FLATTEN functions (read-only, no writes)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from build_master_xlsx import FLATTEN, MASTERS, NUMERIC_COLS, coerce  # noqa: E402
import pandas as pd  # noqa: E402

names = {fn for fn, _s, _d in MASTERS}
for fn in ("kics_tier1_utilization.json", "kics_tier2_utilization.json", "kics_forward_capital.json"):
    assert fn in names, f"{fn} missing from MASTERS"
    raw = json.loads((REPO / fn).read_text(encoding="utf-8"))
    data = FLATTEN[fn](raw)
    df = coerce(pd.DataFrame(data))
    print(f"\n=== {fn} -> {len(data)} rows, {len(df.columns)} cols ===")
    print("columns:", list(df.columns))
    print("null 원수사명:", df["원수사명"].isna().sum())
    print("null 티커:", df["티커"].isna().sum(), " (expected >0 -- some insurers have no listed ticker)")
    print("null 생손보여부:", df["생손보여부"].isna().sum())
    print("distinct 항목명 count:", df["항목명"].nunique())
    print("distinct 공시분기 values:", sorted(df["공시분기"].dropna().unique().tolist())[:12])
    n_note = (df["비고"].astype(str).str.len() > 0).sum()
    print("rows with non-empty 비고:", n_note, "/", len(df))
    print(df.head(3).to_string())

print("\nDONE — no exceptions")
