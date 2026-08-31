import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

with open(ROOT / "data" / "_derived" / "kics_transition_applicability.json", encoding="utf-8") as f:
    data = json.load(f)

print("keys:", list(data.keys()))
meta = data.get("_meta")
print("_meta:", json.dumps(meta, ensure_ascii=False, indent=2)[:1500] if meta else None)

records = data.get("records")
print("records type:", type(records), "len:", len(records) if hasattr(records, "__len__") else "?")

if isinstance(records, list):
    sample = records[0]
    print("sample record:", json.dumps(sample, ensure_ascii=False, indent=2))
    hits = [r for r in records if isinstance(r, dict) and (r.get("원보험사코드") == "KR0008" or r.get("code") == "KR0008")]
    print("KR0008 hits in list:", len(hits))
    for h in hits:
        print(json.dumps(h, ensure_ascii=False))
elif isinstance(records, dict):
    print("records keys sample:", list(records.keys())[:5])
    for k, v in records.items():
        if "KR0008" in str(k):
            print(k, "->", json.dumps(v, ensure_ascii=False))
