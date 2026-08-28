#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What does parse_filing() actually return for old_item 17/18 (item8=보증준비금 source)
for KB손해보험(KR0010) across its raw filings? And is there a '보증준비금' string in the
raw XML at all? Read-only probe for inbox/parser/20260828T2350Z."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.build_equity_composition_tier2 import parse_filing

DART = ROOT / "data" / "dart"

for fy_dir in sorted(DART.glob("FY*_Q*")):
    m = fy_dir.name.replace("FY", "").split("_Q")
    quarter = f"{m[0]}.{m[1]}Q"
    dirs = sorted((fy_dir / "raw").glob("KR0010_*"))
    if not dirs:
        continue
    xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
    if not xmls:
        print(f"{quarter}: no xml in {dirs[0]}")
        continue
    xml_path = xmls[0]
    raw_text = xml_path.read_text(encoding="utf-8", errors="replace")
    n_hits = raw_text.count("보증준비금")
    try:
        vals, diag = parse_filing(xml_path)
    except Exception as e:
        print(f"{quarter}: parse_filing raised {e!r}")
        continue
    v17 = vals.get(17)
    v18 = vals.get(18)
    print(f"{quarter}: xml={xml_path.name} size={xml_path.stat().st_size} "
          f"'보증준비금' occurrences={n_hits}  item17(기적립액)={v17!r}  item18(예정액)={v18!r}")
    if n_hits and (v17 is None and v18 is None):
        # show context around first occurrence for manual inspection
        idx = raw_text.find("보증준비금")
        print("    context:", raw_text[max(0, idx - 80):idx + 120].replace("\n", " "))
