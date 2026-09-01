# -*- coding: utf-8 -*-
"""Print a FLATTENED (tags -> |) window of a company's H1 XML around a given char offset."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_capital_securities_fy2026h1 as B  # noqa: E402

code, pos, before, after = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
xml_path, text = B.load_h1_xml(code)
chunk = text[max(0, pos - before):pos + after]
flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", chunk))
print(flat)
