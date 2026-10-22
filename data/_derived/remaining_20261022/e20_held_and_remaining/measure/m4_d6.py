"""m4: print the d6_rows.json record(s) for code/quarters, minus bulky fields (READ-ONLY)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
code = sys.argv[1]
qs = sys.argv[2].split(",")
d6 = json.loads((D / "d6_rows.json").read_text(encoding="utf-8"))
d5 = {(r["code"], r["q"]): r for r in json.loads((D / "d5_buckets.json").read_text(encoding="utf-8"))}
for r in d6:
    if r["code"] == code and r["q"] in qs:
        print("=====", code, r["q"], r["scope"])
        for k, v in r.items():
            if k in ("disp", "its", "rel_master"):
                continue
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:400]}")
        b = d5.get((code, r["q"]))
        if b:
            print("  ITS (item: same / prior(later) / master)")
            for it, d in sorted(b["its"].items(), key=lambda kv: int(kv[0])):
                print(f"    {it:>3}: same={d.get('same')} prior={d.get('prior')} master={d.get('master')}")
