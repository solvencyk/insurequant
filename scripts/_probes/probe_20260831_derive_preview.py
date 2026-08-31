# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
from collections import defaultdict

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
buckets = defaultdict(dict)
for r in rows:
    buckets[(r["원보험사코드"], r["공시분기"])][int(r["항목번호"]) if str(r["항목번호"]).isdigit() else r["항목번호"]] = r
for (code, q), d in buckets.items():
    if q == "2026.2Q" and 27 in d and 28 not in d and 1 in d and 14 in d and 2 in d:
        print(code, q, "would get item28")
