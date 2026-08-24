# -*- coding: utf-8 -*-
"""Read-only: dump the exemption-registry entries for a set of (company, period) buckets."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"

TARGETS = {
    ("KR0094", "2024.2Q"), ("KR0094", "2024.4Q"),
    ("KR0094", "2025.2Q"), ("KR0094", "2025.4Q"),
    ("KR0032", "2024.3Q"), ("KR0032", "2025.4Q"),
}

data = json.loads(REG.read_text(encoding="utf-8"))
print("TOP-LEVEL KEYS:", list(data.keys()) if isinstance(data, dict) else type(data))

def walk(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += walk(v, f"{path}[{i}]")
    return out

# find records
recs = None
if isinstance(data, dict):
    for k, v in data.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            print(f"  list key '{k}' len={len(v)} sample keys={list(v[0].keys())}")
        elif isinstance(v, dict):
            print(f"  dict key '{k}' len={len(v)} sample subkey={list(v.keys())[:3]}")
