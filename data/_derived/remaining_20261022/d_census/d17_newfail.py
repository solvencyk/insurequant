# -*- coding: utf-8 -*-
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
a51 = {(r["name"], r["q"]) for r in json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8")) if r["scope"] == "A51"}
nf = []
for l in (OUT / "gates_plbreak_master_tables.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"\s*NEW-FAIL\s+(\S+)\|(\d{4}\.\dQ)\|(.+?)\s+<-", l)
    if m: nf.append((m.group(1), m.group(2), m.group(3)))
inA = [x for x in nf if (x[0], x[1]) in a51]
txt = f"NEW pl_bridge FAIL when the Tier-1 later vector is adopted alone for the item-1-moving restatement buckets: total {len(nf)}, of which in the 51: {len(inA)} ({len({(x[0], x[1]) for x in inA})} buckets)"
print(txt); (OUT / "d17_newfail.txt").write_text(txt + "\n" + "\n".join(f"{a} {b} {c}" for a, b, c in nf) + "\n", encoding="utf-8")
