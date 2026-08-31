# -*- coding: utf-8 -*-
"""For each FY2026_Q2 filed company, find the exact section title(s) containing
'자본으로 인정되는 채무증권' and the preceding '미상환사채' bond-name table, so we can
build a robust per-company extractor. Diagnostic only.
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

TITLE_RE = re.compile(r"<P[^>]*>\s*([^<]{0,10}자본으로\s*인정되는\s*채무증권[^<]{0,20})</P>")
BND_TABLE_RE = re.compile(r'ACODE="BND_NAME"')

for code in target_codes:
    d = next((p for p in raw_dir.iterdir() if p.name.startswith(code + "_")), None)
    if d is None:
        continue
    xml = next(d.glob("*.xml"), None)
    if xml is None:
        print(f"{code}: NO XML")
        continue
    text = xml.read_text(encoding="utf-8", errors="replace")
    titles = TITLE_RE.findall(text)
    n_bnd_tables = len(BND_TABLE_RE.findall(text))
    print(f"{code:7} titles={titles}  BND_NAME_table_hits={n_bnd_tables}  xml_len={len(text)}")
