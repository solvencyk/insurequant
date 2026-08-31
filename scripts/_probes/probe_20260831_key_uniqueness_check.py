# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
from collections import Counter

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
keys3 = Counter((r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows)
dupes = {k: c for k, c in keys3.items() if c > 1}
print(f"total rows={len(rows)}  unique (code,quarter,item) keys={len(keys3)}  duplicate-key count={len(dupes)}")
for k, c in list(dupes.items())[:10]:
    print("  DUP", k, "x", c)
