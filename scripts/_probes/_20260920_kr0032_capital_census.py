"""KR0032 (NH농협손해보험) capital-component census across quarters.

Prints items 4-13 (순자산 + components) per quarter from kics_disclosure.json,
alongside IFRS17_BS.json equity values where available.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KICS = os.path.join(ROOT, "kics_disclosure.json")
BS = os.path.join(ROOT, "IFRS17_BS.json")

CODE = "KR0032"

with open(KICS, encoding="utf-8") as f:
    kics = json.load(f)

rows = [r for r in kics if r.get("원보험사코드") == CODE]
quarters = sorted({r["공시분기"] for r in rows})
items = sorted({int(r["항목번호"]) for r in rows if int(r["항목번호"]) <= 14})

print("=== KR0032 kics_disclosure.json: items 1-14 by quarter ===")
hdr = "item | label".ljust(34) + " | " + " | ".join(q.ljust(9) for q in quarters)
print(hdr)
labels = {}
for r in rows:
    labels.setdefault(int(r["항목번호"]), r["항목명"])
for it in items:
    line = (str(it).rjust(4) + " | " + str(labels.get(it, ""))[:26].ljust(26)).ljust(34) + " | "
    cells = []
    for q in quarters:
        v = [r for r in rows if int(r["항목번호"]) == it and r["공시분기"] == q]
        cells.append((str(v[0]["값"]) if v else "-").ljust(9))
    print(line + " | ".join(cells))

print()
print("=== KR0032 rows count by quarter ===")
for q in quarters:
    n = len([r for r in rows if r["공시분기"] == q])
    print(f"  {q}: {n} rows")

if os.path.exists(BS):
    with open(BS, encoding="utf-8") as f:
        bs = json.load(f)
    if isinstance(bs, dict):
        print()
        print("=== IFRS17_BS.json top-level keys ===")
        print(list(bs.keys())[:20])
    else:
        brows = [r for r in bs if r.get("원보험사코드") == CODE]
        print()
        print(f"=== IFRS17_BS.json: KR0032 rows = {len(brows)} ===")
        if brows:
            print("sample keys:", list(brows[0].keys()))
            bq = sorted({r.get("공시분기") for r in brows})
            bitems = sorted({(r.get("항목번호"), r.get("항목명")) for r in brows},
                            key=lambda t: (t[0] is None, t[0]))
            for it, lab in bitems:
                line = (str(it).rjust(4) + " | " + str(lab)[:26].ljust(26)).ljust(34) + " | "
                cells = []
                for q in bq:
                    v = [r for r in brows if r.get("항목번호") == it and r.get("공시분기") == q]
                    cells.append((str(v[0].get("값")) if v else "-").ljust(11))
                print(line + " | ".join(cells))
            print("     BS quarters:", bq)
