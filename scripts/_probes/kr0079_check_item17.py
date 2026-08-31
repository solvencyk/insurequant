# -*- coding: utf-8 -*-
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import R7
import numpy as np

# page24/25 read (백만원 -> 억원, /100), 2026.2Q 당기
S = np.array([1842.32, 409.70, 8242.50, 0.0, 15899.62, 2479.25, 704.81])
item17_expected = float(np.sqrt(S @ R7 @ S))
print("S =", S.tolist())
print("sum(S) =", S.sum())
print("item17_expected (sqrt(S'R7S)) =", item17_expected)
print("ratio sum/expected =", S.sum() / item17_expected)
print("currently loaded (OCR) item17 = 20349")
