# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT))
import src.solvency.validation.kics_json_rules as K

A = {29:1935943, 30:2333239, 31:4611958, 32:0, 33:7034933, 34:2109148, 35:788043}
B = {29:1858938, 30:2333241, 31:4610695, 32:0, 33:6832265, 34:2110173, 35:714245}
ITEM17 = 112233.0
for label, d in (("A 출재전(현행 마스터)", A), ("B 출재후(원문 하위항목표)", B)):
    s = [d[i]/100.0 for i in range(29,36)]
    exp = K._diversified_sqrt(s, K.R7)
    tol = max(0.0, K.DIVERSIFIED_SQRT_TOL_REL*abs(exp))
    print(f"{label:26s} expected={exp:,.4f}  item17={ITEM17:,.1f}  diff={ITEM17-exp:+,.4f}  tol(rel)={tol:,.4f}  -> {'PASS' if abs(ITEM17-exp)<=tol else 'FAIL'}")
print()
print("원문 대조: 출재전 합계행 11,431,746 백만 = 114,317.46 억")
print("           출재후 합계행 11,223,289 백만 = 112,232.89 억  (= item17 112,233)")
