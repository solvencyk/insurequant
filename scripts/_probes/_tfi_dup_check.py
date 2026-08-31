# -*- coding: utf-8 -*-
import io, json, sys
from collections import Counter
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = json.loads(Path("kics_disclosure.json").read_text(encoding="utf-8"))
c = Counter((r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows)
dups = {k: v for k, v in c.items() if v > 1}
print(f"total rows: {len(rows)}  total distinct combos: {len(c)}  duplicate combos: {len(dups)}")
dups_47_54 = {k: v for k, v in dups.items() if 47 <= k[2] <= 54}
print(f"duplicate combos within item47-54: {len(dups_47_54)}")
for k, v in list(dups_47_54.items())[:20]:
    print(" ", k, "count=", v)
