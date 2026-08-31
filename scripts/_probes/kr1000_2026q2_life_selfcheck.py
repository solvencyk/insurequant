# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from solvency.validation.kics_json_rules import R7, _diversified_sqrt

# order = 29..35 = 사망,장수,장해질병,장기재물기타,해지,사업비,대재해 (1-1..1-7)
S = np.array([4343.11, 208.09, 6917.23, 287.23, 4566.36, 1200.93, 3682.58], dtype=float)
item17 = 12903.0
expected = _diversified_sqrt(S, R7)
print(f"item17 disclosed={item17} vs derived(R7)={expected:.4f} diff={item17-expected:+.4f} "
      f"rel={abs(item17-expected)/expected*100:.4f}%")
print(f"sum(29-35)={S.sum():.2f} ratio to item17={S.sum()/item17:.4f}")
