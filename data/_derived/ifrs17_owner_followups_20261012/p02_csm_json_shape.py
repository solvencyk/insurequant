# -*- coding: utf-8 -*-
"""Read-only: shape of an extracted *_csm.json (list of blocks)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/extracted/" + sys.argv[1]
d = json.loads(open(p, "rb").read().decode("utf-8"))
print(type(d), len(d))
for b in d:
    print("---- block keys:", list(b.keys()))
    print("   caption:", str(b.get("caption"))[:150])
    print("   line_no:", b.get("line_no"), "score:", b.get("score"), "src:", b.get("_source_xml"))
    print("   header:", json.dumps(b.get("header"), ensure_ascii=False)[:400])
    rows = b.get("rows") or []
    print("   nrows:", len(rows))
    for r in rows[:3]:
        print("     ", json.dumps(r, ensure_ascii=False)[:300])
