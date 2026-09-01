# -*- coding: utf-8 -*-
"""Debug: why does extract_mkt_subs find item37 for KR0005 but not KR0002?"""
from __future__ import annotations
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F  # noqa: E402

for code, fname in [("KR0005", "KR0005_흥국화재.md"), ("KR0002", "KR0002_한화손해보험.md")]:
    text = (REPO / "md_inbox" / "FY2026_Q2" / fname).read_text(encoding="utf-8")
    subs = F.extract_mkt_subs(text)
    print(f"{code}: subs.get(37) = {subs.get(37)!r}")
    print(f"{code}: full subs = {subs}")
    print()

# Direct regex tests
import re
_TOTAL_ROW_CORE_RE = re.compile(r"^[ⅠⅡⅢⅣⅤⅥ0-9]*[\.\s]*(합\s*계|계)$")
for label in ["Ⅲ. 합 계 주2)", "Ⅲ. 합 계"]:
    stripped = re.sub(r"\d*\)?\s*$", "", label).strip()
    m = _TOTAL_ROW_CORE_RE.match(stripped)
    print(f"label={label!r} -> stripped={stripped!r} -> match={bool(m)}")

print("---")
import fill_market_subitems_to_disclosure as F2
for c in ["336,516", "Ⅰ. 기본법", ""]:
    print(f"_is_total_row_label({c!r}) = {F2._is_total_row_label(c)}")
