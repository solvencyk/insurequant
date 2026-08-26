#!/usr/bin/env python3
"""PL 추출 테이블의 실제 line_no 와 별도 경계 대조 (HTMLParser 경로)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from lxml import etree
from scripts.pl_breakdown.common import _ofs_line_boundary

p = Path(sys.argv[1])
parser = etree.HTMLParser(encoding="utf-8", huge_tree=True, recover=True)
tree = etree.parse(str(p), parser)
sl = [e.sourceline for e in tree.iter() if e.sourceline]
nlines = sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
print(f"file lines={nlines:,}  HTMLParser max sourceline={max(sl):,}  #==65535={sum(1 for s in sl if s==65535):,}")
print("ATOC(ENG) boundary =", _ofs_line_boundary(p))
import re
pat = re.compile(r'<TITLE\s+ATOC="Y"[^>]*>([^<]{0,60})</TITLE>')
with open(p, encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        for m in pat.finditer(line):
            t = m.group(1).strip()
            if "재무제표" in t or "financial" in t.lower():
                print(f"  L{i:>7,}  {t}")
