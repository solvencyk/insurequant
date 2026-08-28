"""End-to-end (but single-filing, non-destructive) verification: call the REAL production
scripts.build_pl_breakdown.parse_filing() for KR0079's 2026.2Q raw dir, exercising the actual
dispatch path (LIFE_HANDLERS -> extract_tier2_miraeasset -> _ma_yesilcha_direct) exactly as
build_pl_breakdown.py's main() would, WITHOUT running the full (slow, all-company) builder.
Read-only: does not write PL_breakdown.json / pl_breakdown_master.json.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import parse_filing  # noqa: E402

d = str(ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명")
t1, t2 = parse_filing([d], is_life=True, code="KR0079", name="미래에셋생명", quarter="2026.2Q")
print("t1 (tier1):")
for k, v in sorted((t1 or {}).items(), key=lambda kv: str(kv[0])):
    print(" ", k, "=", v)
print("\nt2 (tier2):")
for k, v in sorted((t2 or {}).items(), key=lambda kv: str(kv[0])):
    print(" ", k, "=", v)

item6 = (t2 or {}).get(6)
print(f"\nitem6 = {item6}")
assert item6 is not None, "item6 was NOT emitted -- gate failed unexpectedly"
assert abs(item6 - (-18120.139965)) < 1e-6, f"item6 mismatch: {item6}"
print("OK: item6 matches -18,120.139965 exactly via the real production dispatch path.")

from scripts.build_pl_breakdown import assemble  # noqa: E402
v = assemble(t1, t2, is_life=True)
print("\nassembled v (24 items):")
for i in range(1, 25):
    print(f"  item{i}: {v[i]}")
