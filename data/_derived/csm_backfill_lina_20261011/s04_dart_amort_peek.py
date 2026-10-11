# -*- coding: utf-8 -*-
"""Step 4 (read-only): what does the FY2025 DART annual report (two rcepts for KR0074) print as expected CSM amortisation
for the issued contracts? Compare with the management-disclosure PDF (2025.12.31 column)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

for rc in ["20260406004538", "20260406004539"]:
    d = ROOT / "data" / "dart" / "FY2025_Q4" / "raw" / f"KR0074_라이나생명보험_{rc}"
    xml = next(d.glob("*.xml"))
    raw = xml.read_bytes()
    print("=====", rc, xml.name, len(raw), "bytes")
    text = raw.decode("utf-8", errors="replace")
    # title
    m = re.search(r"<DOCUMENT-NAME[^>]*>([^<]+)<", text)
    print("doc-name:", m.group(1) if m else None)
    for m in re.finditer(r"기대상각기간별", text):
        s = max(0, m.start() - 200)
        seg = text[s: m.start() + 300]
        seg = re.sub(r"<[^>]+>", " ", seg)
        seg = re.sub(r"\s+", " ", seg)
        print("  ...", seg[:400])
