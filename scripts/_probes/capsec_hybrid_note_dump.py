# -*- coding: utf-8 -*-
"""Dump the raw '자본으로 인정되는 채무증권의 발행' note (flattened) for a company, to see if
subordinated (후순위) rows are interleaved with hybrid (신종자본) rows in the same note."""
import sys
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_capital_securities_fy2026h1 as B  # noqa: E402

code = sys.argv[1]
xml_path, text = B.load_h1_xml(code)
start = text.find("자본으로 인정되는 채무증권")
print(f"start={start}")
if start == -1:
    print("NOT FOUND")
    sys.exit(0)
# print flattened text for next ~6000 chars
chunk = text[start:start + 9000]
flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", chunk))
print(flat)
