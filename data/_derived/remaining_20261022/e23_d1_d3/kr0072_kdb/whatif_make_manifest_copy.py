# -*- coding: utf-8 -*-
"""WHAT-IF only (temporary, never committed): copy tests/test_rule_coverage_manifest.py (the LOADED state, i.e. with the census already updated by the apply) to tests/test_zz_whatif_kr0072_manifest.py with
the one coverage edit that the item-23 failure calls for: item 23 moves from PL_CONSTRUCTIVE_GUARDED to PL_CONSTRUCTIVE_BLIND.  The tracked test file is not touched."""
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
src = (ROOT / "tests/test_rule_coverage_manifest.py").read_bytes().decode("utf-8")
crlf = "\r\n" in src
s = src.replace("\r\n", "\n")
start = s.index('    23: "법인세 — **좁은 커버리지**')
end = s.index('\n}\n', start)
block = s[start:end]
assert block.count('\n') <= 12 and block.rstrip().endswith('",'), block[-200:]
s = s[:start] + s[end + 1:]          # drop the GUARDED entry (keep the closing brace line)
# fix: removing the entry leaves the line before it ending with '",' -> fine; the dict closes with '}'
anchor = '    19: "보험금융손익 — item18 = 17-19 plug 가 2층(fetch_dart_fs._parse + assemble) 모두 흡수",\n}'
assert s.count(anchor) == 1
new23 = ('    23: "법인세 — assemble 이 22-24 로 무조건 덮어쓴다. 유일한 탐지였던 PL_YTD_COLLAPSE_TO_ZERO(같은 FY 인접분기, 직전값 non-zero -> 이번값 정확히 0.0)는 "\n'
         '        "KR0072 2023.2Q 의 override 22 = 24 = 57,750.0 이라는 우연에 걸려 있었고, 2023.2Q 가 최신 비교열(22 = 62,624.220676, 24 = 62,624.429999, 법인세 -0.209323)로 "\n'
         '        "바뀌면 사라진다(2026-10-23 e23 D3). 대상 회사-분기가 없으면 이 축은 BLIND",\n')
s = s.replace(anchor, anchor[:-1] + new23 + "}")
dst = ROOT / "tests/test_zz_whatif_kr0072_manifest.py"
dst.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("wrote", dst, "removed GUARDED block of", block.count("\n") + 1, "lines")
