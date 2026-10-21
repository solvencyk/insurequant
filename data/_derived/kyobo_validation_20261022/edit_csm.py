from pathlib import Path
p = Path("data/_derived/kyobo_validation_20261022/v_reread_csm.py")
s = p.read_text(encoding="utf-8")
s = s.replace('"2024.4Q": ("FY2025_Q4", [1])', '"2024.4Q": ("FY2025_Q4", [3, 4, 5])')
s = s.replace('ok = m is not None and abs(raw[it] - m[0]) <= 0.0051', 'tol = TOL.get(q, 0.0051)\n        ok = m is not None and abs(raw[it] - m[0]) <= tol')
s = s.replace('bad = 0; ncell = 0', 'bad = 0; ncell = 0\n# 2024.3Q/4Q masters were not touched by this commit and carry 1 decimal (0.1억); 2026.1Q item1/item4 carry the same 1-dec rounding of item1\nTOL = {"2024.3Q": 0.1, "2024.4Q": 0.1, "2026.1Q": 0.0151}')
p.write_text(s, encoding="utf-8", newline="")
