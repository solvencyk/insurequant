# -*- coding: utf-8 -*-
"""read-only: set difference of data_contract findings (RED/YELLOW headline lines) between two gate-run files."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
FIND = re.compile(r"^\s{2}(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(.*)$")


def read(p):
    out = []
    lines = Path(p).read_text(encoding="utf-8", errors="replace").splitlines()
    for i, ln in enumerate(lines):
        m = FIND.match(ln)
        if m:
            out.append((m.group(1), m.group(2), m.group(3), m.group(4).strip(), lines[i + 1].strip()[:200] if i + 1 < len(lines) else ""))
    return out


a, b = read(sys.argv[1]), read(sys.argv[2])
print("counts", len(a), len(b), "RED", sum(1 for x in a if x[0] == 'RED'), sum(1 for x in b if x[0] == 'RED'))
sa, sb = set(a), set(b)
for x in sorted(sa - sb):
    print("ONLY A:", x)
for x in sorted(sb - sa):
    print("ONLY B:", x)
