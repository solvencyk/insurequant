# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "_derived" / "kics_transition_applicability.json"
d = json.loads(p.read_text(encoding="utf-8"))
print("top keys:", list(d.keys()))
data = d.get("data") or d.get("records")
if data is None:
    for k, v in d.items():
        if isinstance(v, list):
            data = v
            print("using list key:", k)
            break
print(type(data), len(data) if data else None)
if data:
    print("sample record:", data[0])

codes = {"KR0070", "KR1010", "KR0069", "KR0082", "KR0001"}
if isinstance(data, list):
    for rec in data:
        if rec.get("code") in codes and rec.get("quarter") == "2026.2Q":
            print(rec)
elif isinstance(data, dict):
    for k, v in data.items():
        print(k, v if any(c in str(k) for c in codes) else None)
