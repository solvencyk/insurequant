"""probe_axa_tfi.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
AXA (KR0049) 2024.3Q items 47-54 (TFI table, loaded from the new site edition p15) + the five headline cells of interest, with 값/값_적용후.
"""
import io
import json
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR0049" and r["공시분기"] == "2024.3Q" and (r["항목번호"] in (1, 2, 3, 4, 27) or 47 <= r["항목번호"] <= 54):
        print(f"item {r['항목번호']:>2} 값={r.get('값')!r:>16} 후={r.get('값_적용후', '<nokey>')!r:>16}  {r['항목명']}")
