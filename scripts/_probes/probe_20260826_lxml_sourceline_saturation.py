#!/usr/bin/env python3
"""lxml sourceline 65535 포화가 진짜인지, 옵션으로 풀리는지 실측."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from lxml import etree
p = Path(sys.argv[1])
nlines = sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
print("lxml", etree.LXML_VERSION, "libxml2", etree.LIBXML_VERSION, "file lines", f"{nlines:,}")
for label, kw in [("default", {}), ("huge_tree", {"huge_tree": True}), ("recover", {"recover": True})]:
    try:
        t = etree.parse(str(p), etree.XMLParser(**kw))
        sl = [e.sourceline for e in t.iter() if e.sourceline]
        print(f"  {label:10s} max sourceline={max(sl):,}  #==65535={sum(1 for s in sl if s == 65535):,}  elems={len(sl):,}")
    except Exception as e:
        print(f"  {label:10s} ERROR {type(e).__name__}: {e}")
