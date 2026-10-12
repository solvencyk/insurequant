# -*- coding: utf-8 -*-
"""f2: read the DB손해보험 FY2026 반기보고서 (DART raw) text around the hybrid (신종자본증권) issuance table to see the
disclosed issue / maturity / call dates of 제1회 (공모, 2025-09-01) and 제2회 (사모, 2025-09-25). Read-only."""
import re

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
fn = ROOT + "/data/dart/FY2026_Q2/raw/KR0011_DB손해보험/20260814003682.xml"
txt = open(fn, encoding="utf-8", errors="replace").read()
clean = re.sub(r"<[^>]+>", " ", txt)
clean = re.sub(r"\s+", " ", clean)
print("chars", len(clean))
for pat in ["제1회 신종자본증권", "제2회 신종자본증권", "2025.09.01", "2025.09.25", "2030.09.01", "2030.09.25", "2025-09-01", "2030-09-25"]:
    hits = [m.start() for m in re.finditer(re.escape(pat), clean)]
    print("==", pat, "hits", len(hits))
    for h in hits[:4]:
        print("    ...", clean[max(0, h - 160): h + 260])
