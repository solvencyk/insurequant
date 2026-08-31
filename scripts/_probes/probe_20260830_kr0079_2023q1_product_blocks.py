import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context

xml_path = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명/xml/20230515002900.xml"
tables = list(_iter_tables_with_context(xml_path))

# Find product-block header captions: short captions like "i) 사망", "ii) 건강" etc,
# AND tables whose first data row is the '(단위: 백만원)' + '구분' header pattern with CSM cols.
cap_pat = re.compile(r"^[ivx]+\)\s*\S")
for t in tables:
    cap = (t.caption or "").strip()
    if cap_pat.match(cap):
        print(f"line={t.line_no}  caption={cap!r}  nrows={len(t.rows)}")
