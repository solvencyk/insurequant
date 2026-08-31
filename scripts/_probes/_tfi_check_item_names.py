# -*- coding: utf-8 -*-
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
names = defaultdict(set)
for r in rows:
    n = r.get("항목번호")
    if isinstance(n, int) and 47 <= n <= 54:
        names[n].add(r.get("항목명"))
for n in sorted(names):
    print(n, names[n])
