# -*- coding: utf-8 -*-
"""KR0069 2024.4Q 8_life — 출재전(A) vs 출재후(B) 어느 컬럼이 item17 을 재현하나.
룰엔진 R4/R7 행렬은 import 한다 (재타이핑 금지)."""
import sys
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts"))
import src.solvency.validation.kics_json_rules as K

names = [n for n in dir(K) if "R7" in n or "MATRIX" in n or "CORR" in n or "R4" in n]
print("matrix symbols:", names)

# 백만원 -> 억원
A = {29:1935943, 30:2333239, 31:4611958, 32:0, 33:7034933, 34:2109148, 35:788043}
B = {29:1858938, 30:2333241, 31:4610695, 32:0, 33:6832265, 34:2110173, 35:714245}
A = {k: v/100.0 for k,v in A.items()}
B = {k: v/100.0 for k,v in B.items()}
print("\nA(출재전) 억원:", {k:round(v,2) for k,v in A.items()})
print("B(출재후) 억원:", {k:round(v,2) for k,v in B.items()})

# 룰이 쓰는 기대식을 그대로 호출
import inspect
src = inspect.getsource(K)
i = src.find("8_life")
# 룰 본문에서 expected 계산부를 찾아 출력
j = src.find("def ", max(0, src.rfind("def ", 0, src.find('"8_life", expected'))))
seg = src[src.find('life_tol')-2600: src.find('life_tol')+200]
print("\n----- 8_life expected 계산부 -----")
for ln in seg.splitlines():
    if any(k in ln for k in ("29","30","31","32","33","34","35","expected","life","sqrt","R7","mmult","matrix","17")):
        print("   ", ln.rstrip()[:150])
