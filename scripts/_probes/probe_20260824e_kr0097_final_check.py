"""Read-only: final precision check using the EXACT rounded-to-2dp strings we
plan to write to the master, to make sure the R7 residual still closes after
the same rounding the master itself uses (not the unrounded float)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402
from solvency.validation.kics_json_rules import R7  # noqa: E402

out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch_final_check.txt"

INITIAL = {30: 143.25093, 33: 664.03015, 34: 438.77926, 35: 78.47532}
ratio_2024 = 0.10
pre = {29: 230.82, 30: 95.51, 31: 391.46, 32: 0.0, 33: 1975.34, 34: 1109.63, 35: 52.08}

lines = []
raw_derived = {}
rounded_derived = {}
for i in range(29, 36):
    init = INITIAL.get(i)
    if init is None:
        raw_derived[i] = pre[i]
    else:
        raw_derived[i] = max(0.0, pre[i] - (1 - ratio_2024) * init)
    rounded_derived[i] = round(raw_derived[i], 2)

lines.append(f"raw derived (full precision): {raw_derived}")
lines.append(f"rounded to 2dp (what gets written to master): {rounded_derived}")

vec_raw = np.array([raw_derived[i] for i in range(29, 36)], dtype=float)
vec_rounded = np.array([rounded_derived[i] for i in range(29, 36)], dtype=float)

agg_raw = V._diversified_sqrt(vec_raw, R7)
agg_rounded = V._diversified_sqrt(vec_rounded, R7)

item17_post_master = 2001.90  # from JSON string "2001.90"
item17_post_pdf_thousand_won = 200_189_811  # p281, 단위 천원
item17_post_pdf_eok = item17_post_pdf_thousand_won / 100_000  # 천원 -> 억원 (1억 = 100,000천원)

lines.append(f"item17_post from master JSON string: {item17_post_master}")
lines.append(f"item17_post from raw p281 (200,189,811 천원 -> 억원): {item17_post_pdf_eok}")
lines.append(f"R7(raw derived)     = {agg_raw:.6f}  diff vs pdf = {agg_raw - item17_post_pdf_eok:+.6f}")
lines.append(f"R7(rounded derived) = {agg_rounded:.6f}  diff vs pdf = {agg_rounded - item17_post_pdf_eok:+.6f}")

# tolerance check mirroring dyn5-style: max(10.0, 5% of R7)
tol = max(10.0, 0.05 * agg_rounded)
lines.append(f"tol (max(10, 5%)) = {tol:.4f}  within_tol={abs(agg_rounded - item17_post_pdf_eok) <= tol}")

# also show what happens with the OLD stale/missing values for contrast
old = {29: 230.82, 30: 0.0, 31: 391.46, 32: 0.0, 33: 942.86, 34: 896.15, 35: 0.0}
vec_old = np.array([old[i] for i in range(29, 36)], dtype=float)
agg_old = V._diversified_sqrt(vec_old, R7)
lines.append(f"R7(old stale, missing->0) = {agg_old:.6f}  diff vs pdf = {agg_old - item17_post_pdf_eok:+.6f}")

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}")
