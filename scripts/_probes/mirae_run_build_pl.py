"""Call build_root_masters.build_pl() ONLY (never main()) to propagate the KR0079 2026.2Q
item6/item7 cell patch (already applied to data/dart/viz/pl_breakdown_master.json) into the
root PL_breakdown.json, matching the NH ticket's precedent (commit 72cc896).
"""
import sys
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant")

from scripts.build_root_masters import build_pl  # noqa: E402

n = build_pl()
print(f"build_pl() wrote {n} rows")
