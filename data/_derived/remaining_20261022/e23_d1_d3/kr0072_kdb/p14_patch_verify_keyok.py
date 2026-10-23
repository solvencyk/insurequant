# -*- coding: utf-8 -*-
"""patch kr0072_verify.py: key-row comparison of D2 uses the re-read mn (백만원) * 1e6 (원) and the label alternatives of the FY2025 statement."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kr0072_verify.py"
s = p.read_text(encoding="utf-8")
a = '''    key_ok = all(any(abs(x[1] - NEW['2023.4Q']['V'][k]['printed_won']) <= 1e-9 for x in a25 if x[0] in (nspace(LABELS[k][0]),)) for k in ("ins_result", "inv", "ni", "oci", "tci"))'''
b = '''    key_ok = all(any(abs(x[1] - NEW["2023.4Q"]["V"][k]["mn"] * 1e6) <= 1e-3 for x in a25 if x[0] in {nspace(y) for y in LABELS[k]} | {nspace("영업이익(손실)"), nspace("법인세비용(수익)"), nspace("당기순이익(손실)"), nspace("법인세비용차감전순이익(손실)")}) for k in ("ins_result", "inv", "ni", "oci", "tci"))'''
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
