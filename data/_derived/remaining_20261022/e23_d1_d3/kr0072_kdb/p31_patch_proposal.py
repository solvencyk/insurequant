# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / "proposed_manifest_item23.txt"
s = p.read_text(encoding="utf-8")
a = '''  KR0004 2025.3Q is already a known RED in the baseline and the three reinsurer cells are not "new" findings, so KR0072 2023.2Q is the only candidate that produces a NEW finding.
'''
b = '''  Four of them remain after the load, and the test still reports item 23 as undetected, so none of those four produces a NEW blocking finding: KR0072 2023.2Q is the only one that did (it is the one the
  manifest text of 2026-09-12 names).  (Why each of the four stays silent was not investigated; the pytest result is the evidence.)
'''
assert s.count(a) == 1
p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")
print("patched")
