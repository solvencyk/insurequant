import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context

xml_path = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명/xml/20230515002900.xml"

tables = list(_iter_tables_with_context(xml_path))
target_lines = {15088}  # first product block found

for t in tables:
    if t.line_no in target_lines:
        print(f"=== line={t.line_no} caption={t.caption!r} ===")
        print(f"header ({len(t.header)} rows):")
        for hr in t.header:
            print("  ", hr)
        print(f"rows ({len(t.rows)}):")
        for r in t.rows:
            print("  ", r)
        print("footnotes:", t.footnotes)
