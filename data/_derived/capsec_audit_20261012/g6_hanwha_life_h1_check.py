# -*- coding: utf-8 -*-
"""g6: 한화생명 (ledger as_of 2025-12-31): does the H1 2026 반기보고서 show an issuance / redemption of 신종 or 후순위 bonds that the ledger lacks?
Reads data/dart/FY2026_Q2/raw/KR0068_한화생명/*.xml (main report): prints the 신종자본증권 balance table and every excerpt that pairs 후순위 with 2026.
Output g6_hanwha_life_h1_check.txt (lines cut to 420 characters)."""
import glob
import re

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = ROOT + "data/_derived/capsec_audit_20261012/"
out = []
for f in sorted(glob.glob(ROOT + "data/dart/FY2026_Q2/raw/KR0068_한화생명/*.xml")):
    t = open(f, encoding="utf-8", errors="replace").read()
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    out.append("== %s  chars %d" % (f.split("raw/")[1], len(t)))
    for m in re.finditer(r"신종자본증권 미상환 잔액", t):
        out.append("   [신종 잔액표] " + t[m.start(): m.start() + 700])
        break
    for m in re.finditer(r"후순위", t):
        ctx = t[max(0, m.start() - 120): m.start() + 200]
        if re.search(r"2026[년.\-]", ctx):
            out.append("   [후순위+2026] " + ctx)
    for m in re.finditer(r"사채 미상환 잔액|회사채 미상환 잔액|사채 발행 현황|미상환 사채", t):
        out.append("   [사채표] " + t[m.start(): m.start() + 900])
        break
text = "\n".join(l[:420] for l in out) + "\n"
open(HERE + "g6_hanwha_life_h1_check.txt", "w", encoding="utf-8", newline="\n").write(text)
print(text[:600])
