# -*- coding: utf-8 -*-
"""Read-only: dump exemption ledger entries for KR0003 / KR0004."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"

data = json.loads(LEDGER.read_text(encoding="utf-8"))

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj

print("=== TOP LEVEL KEYS ===")
if isinstance(data, dict):
    for k in data:
        v = data[k]
        print(f"  {k}: {type(v).__name__} len={len(v) if hasattr(v,'__len__') else '-'}")
elif isinstance(data, list):
    print(f"  list of {len(data)}")

targets = {"KR0003", "KR0004"}

def find_entries(obj, path=""):
    out = []
    if isinstance(obj, dict):
        s = json.dumps(obj, ensure_ascii=False)
        keys = set(obj.keys())
        if ("company" in keys or "company_code" in keys or "code" in keys) and any(t in s for t in targets):
            code = obj.get("company") or obj.get("company_code") or obj.get("code")
            if code in targets:
                out.append((path, obj))
                return out
        for k, v in obj.items():
            out += find_entries(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += find_entries(v, f"{path}[{i}]")
    return out

entries = find_entries(data)
print(f"\n=== FOUND {len(entries)} entries ===")
for path, e in entries:
    print("\n" + "=" * 90)
    print("PATH:", path)
    print(json.dumps(e, ensure_ascii=False, indent=2))
