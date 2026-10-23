# -*- coding: utf-8 -*-
"""read-only witness: the FY2025 annual report (rcept 20260312001448) prints a THIRD year column (FY2023 = 제70기) in its separate 4-2 income statement.  Compare it with the FY2024 annual report's prior-year column (the
cells the load adopted for 2023.4Q): equal = FY2023 was not restated a third time.  Uses the independent reader of kr0009_verify.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kr0009_verify as V  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
V.F["N5"] = "data/dart/FY2025_Q4/raw/KR0009_현대해상_20260312001448/20260312001448.xml"
V.LABELS["tax"] = V.LABELS["tax"] + ["법인세비용(수익)"]                    # label variants of the FY2025 annual report
V.LABELS["oci_pension"] = V.LABELS["oci_pension"] + ["확정급여부채의재측정요소"]
S5 = V.Stmt("N5")
S4 = V.Stmt("N4")
print("FY2025 annual statement:", S5.rel, "unit", S5.unit, "header paths", S5.paths)
print("period headers:", {k: v["text"] for k, v in S5.periods.items()})
v5 = V.items_from(V.stmt_vector(S5, 2023, "cum"))
v4 = V.items_from(V.stmt_vector(S4, 2023, "cum"))
bad = [(i, v4[i], v5[i]) for i in sorted(v4) if abs(v4[i] - v5[i]) > 2e-6]
print(f"items compared {len(v4)}; FY2025-annual FY2023 column vs FY2024-annual prior column: differing items {len(bad)}")
for i in sorted(v4):
    print(f"   i{i:>2}: FY2024 annual prior {v4[i]:.6f} | FY2025 annual 3rd column {v5[i]:.6f} | diff {v4[i] - v5[i]:+.6f}")
print("RESULT:", "no third restatement for the adopted FY2023 annual cells" if not bad else f"DIFFERENCES {bad}")
