# -*- coding: utf-8 -*-
"""Read-only: print every block of an extracted *_csm.json whose header looks like a CSM amortization schedule (year buckets), with all rows."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
base = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/extracted/"
fn = sys.argv[1]
only_line = int(sys.argv[2]) if len(sys.argv) > 2 else None
d = json.loads(open(base + fn, "rb").read().decode("utf-8"))
for b in sorted(d, key=lambda x: x.get("line_no") or 0):
    cap = str(b.get("caption") or "")
    hdr = b.get("header") or []
    flat = [c for r in hdr for c in r]
    if not any("년" in str(c) for c in flat):
        continue
    if only_line and b.get("line_no") != only_line:
        continue
    print("=" * 100)
    print("line", b.get("line_no"), "score", b.get("score"), "form", b.get("form_type"), "src", b.get("_source_xml"))
    print("caption:", cap[:300])
    print("header:", json.dumps(hdr, ensure_ascii=False))
    for r in b.get("rows") or []:
        print("   ", json.dumps(r, ensure_ascii=False))
    if b.get("footnotes"):
        print("foot:", json.dumps(b.get("footnotes"), ensure_ascii=False)[:300])
