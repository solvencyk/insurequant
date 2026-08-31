# -*- coding: utf-8 -*-
"""Full 2026.2Q TFI census: item47-54 presence + TFI applicability O/X/NA/UNKNOWN."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
applic = json.loads((ROOT / "data" / "_derived" / "kics_transition_applicability.json").read_text(encoding="utf-8"))
applic_by_key = {(r["code"], r["quarter"]): r for r in applic["records"]}

Q = "2026.2Q"
by_bucket = {}
for r in rows:
    if r.get("공시분기") != Q:
        continue
    key = (r["원보험사코드"], r["원수사명"])
    by_bucket.setdefault(key, {})[r["항목번호"]] = r

TFI_ITEMS = [47, 48, 49, 50, 51, 52, 53, 54]
print(f"{'code':8s} {'name':16s} {'TFI':8s} present/missing  item48==item3?")
for (code, name), items in sorted(by_bucket.items()):
    present = [i for i in TFI_ITEMS if i in items]
    missing = [i for i in TFI_ITEMS if i not in items]
    tfi = applic_by_key.get((code, Q), {}).get("TFI", "NOREC")
    i3 = items.get(3, {}).get("값")
    i48 = items.get(48, {}).get("값")
    same = (i48 is not None and i3 is not None and i48 == i3)
    print(f"{code:8s} {name:16s} TFI={tfi:8s} present={present} missing={missing} item48==item3={same}")
