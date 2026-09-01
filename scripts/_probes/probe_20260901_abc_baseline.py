# -*- coding: utf-8 -*-
"""Baseline dump for the 18-RED closeout round (2026-09-01, kics lane).
A = AIG(KR0029) 2025.2Q/2025.3Q post-transition parent/child continuity.
B = ABL생명(KR0070) 2025.3Q R6_item16 after-identity.
C = 흥국생명(KR0071) 2023.4Q item23=24+25+26.
Read-only. No writes.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "kics_disclosure.json"

with DISC.open("r", encoding="utf-8") as f:
    records = json.load(f)

print(f"total records: {len(records)}")

CORE_ITEMS = [1, 2, 3, 4, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28]


def dump(code, quarters=None, items=CORE_ITEMS):
    byq = {}
    name = None
    for r in records:
        if r.get("원보험사코드") != code:
            continue
        name = r.get("원수사명")
        q = r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        byq.setdefault(q, {})[it] = (r.get("값"), r.get("값_적용후", "<NOKEY>"))
    print(f"\n=== {code} {name} ===")
    qs = sorted(byq.keys()) if quarters is None else quarters
    for q in qs:
        m = byq.get(q, {})
        print(f"-- {q} --")
        for it in items:
            if it in m:
                v, vp = m[it]
                print(f"  item{it}: 값={v}  값_적용후={vp}")
            else:
                print(f"  item{it}: <ABSENT ROW>")


print("\n########## A. AIG(KR0029) ##########")
dump("KR0029", quarters=["2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2026.1Q"])

print("\n########## B. ABL생명(KR0070) 2025.3Q, items 14-21 ##########")
dump("KR0070", quarters=["2025.2Q", "2025.3Q", "2026.1Q"], items=[14, 15, 16, 17, 18, 19, 20, 21])

print("\n########## C. 흥국생명(KR0071) 2023.4Q, items 22-26 ##########")
dump("KR0071", quarters=["2023.3Q", "2023.4Q", "2024.1Q"], items=[22, 23, 24, 25, 26])
