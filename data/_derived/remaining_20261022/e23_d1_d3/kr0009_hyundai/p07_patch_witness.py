# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(__file__).resolve().parent / "e01_fy2025_witness.py"
s = p.read_text(encoding="utf-8")
a = 'V.F["N5"] = "data/dart/FY2025_Q4/raw/KR0009_현대해상_20260312001448/20260312001448.xml"\n'
b = a + 'V.LABELS["tax"] = V.LABELS["tax"] + ["법인세비용(수익)"]                    # label variants of the FY2025 annual report\nV.LABELS["oci_pension"] = V.LABELS["oci_pension"] + ["확정급여부채의재측정요소"]\n'
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
