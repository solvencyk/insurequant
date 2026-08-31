# -*- coding: utf-8 -*-
"""Plain substring/keyword scan (no tag-aware regex) across all FY2026_Q2 filed companies'
target XML, to see which phrasing each company's report actually uses for the capital
securities issuance disclosure. Diagnostic only.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
raw_dir = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"

targets_p = ROOT / "data" / "_derived" / "_probe_capsec_h1_census.json"
targets = json.loads(targets_p.read_text(encoding="utf-8"))
target_codes = [r["code"] for r in targets if r["h1_filing_status"].startswith("FILED")]

KEYWORDS = ["자본으로 인정되는 채무증권", "자본으로인정되는채무증권", "신종자본증권", "후순위채무",
            "후순위채권", "미상환사채", "미상환잔액"]

for code in target_codes:
    d = next((p for p in raw_dir.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    if xml is None:
        print(f"{code}: NO XML")
        continue
    text = xml.read_text(encoding="utf-8", errors="replace")
    counts = {kw: text.count(kw) for kw in KEYWORDS}
    print(f"{code:7} " + " ".join(f"{kw}={n}" for kw, n in counts.items() if n))
