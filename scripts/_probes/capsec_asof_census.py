# -*- coding: utf-8 -*-
"""Census: per-company as_of in data/bonds/capital_securities_fy2026h1.json,
split hybrid vs subordinated bond-level as_of (company as_of = min of bonds)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json").read_text(encoding="utf-8"))

TICKET_22 = ("KR0001 KR0002 KR0005 KR0009 KR0010 KR0032 KR0049 KR0050 KR0068 KR0070 KR0071 "
             "KR0072 KR0073 KR0076 KR0079 KR0082 KR0083 KR0087 KR0094 KR0097 KR1000 KR1011").split()
LEGIT_NOFILING = "KR0049 KR0050 KR0076 KR0097 KR1011 KR0004".split()

fresh, stale, no_bonds = [], [], []
for c in data["companies"]:
    code = c["code"]
    bonds = c.get("bonds", [])
    if not bonds:
        no_bonds.append((code, c["company"]))
        continue
    hyb_asof = sorted({b["as_of"] for b in bonds if b["tier"] == "hybrid"})
    sub_asof = sorted({b["as_of"] for b in bonds if b["tier"] == "subordinated"})
    row = (code, c["company"], c["as_of"], hyb_asof, sub_asof)
    if c["as_of"] == "2026-06-30":
        fresh.append(row)
    else:
        stale.append(row)

print(f"n_companies={len(data['companies'])}  fresh(as_of=2026-06-30)={len(fresh)}  stale={len(stale)}  no_bonds={len(no_bonds)}")
print()
print("=== STALE (company as_of != 2026-06-30) ===")
for code, name, asof, h, s in stale:
    ticket_flag = "[ticket-22]" if code in TICKET_22 else "[NOT-in-ticket-22]"
    legit_flag = " LEGIT-NOFILING" if code in LEGIT_NOFILING else ""
    print(f"{code} {name:12s} as_of={asof} hybrid={h} sub={s} {ticket_flag}{legit_flag}")
print()
print("=== NO BONDS (has_capital_securities likely False) ===")
for code, name in no_bonds:
    print(f"{code} {name}")
print()
print("=== FRESH but check mixed (company as_of==2026-06-30 yet one leg still old within) ===")
for code, name, asof, h, s in fresh:
    if (h and any(x != "2026-06-30" for x in h)) or (s and any(x != "2026-06-30" for x in s)):
        print(f"{code} {name} as_of={asof} hybrid={h} sub={s}")
