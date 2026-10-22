"""m1: peek into d_census d5_buckets.json / d6_rows.json / d9_disposition.json structure (READ-ONLY)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/d_census"

d5 = json.loads((D / "d5_buckets.json").read_text(encoding="utf-8"))
print("d5 type", type(d5), len(d5))
if isinstance(d5, dict):
    ks = list(d5.keys())
    print(ks[:5])
    k0 = ks[0]
    v0 = d5[k0]
    print(k0, type(v0), (list(v0.keys()) if isinstance(v0, dict) else v0))
else:
    print(json.dumps(d5[0], ensure_ascii=False)[:3000])

d6 = json.loads((D / "d6_rows.json").read_text(encoding="utf-8"))
print("d6 type", type(d6), len(d6))
if isinstance(d6, dict):
    ks = list(d6.keys())
    print(ks[:5])
    print(json.dumps(d6[ks[0]], ensure_ascii=False)[:3000])
else:
    print(json.dumps(d6[0], ensure_ascii=False)[:3000])

d9 = json.loads((D / "d9_disposition.json").read_text(encoding="utf-8"))
print("d9 type", type(d9), len(d9))
if isinstance(d9, dict):
    ks = list(d9.keys())
    print(ks[:5])
    print(json.dumps(d9[ks[0]], ensure_ascii=False)[:3000])
else:
    print(json.dumps(d9[0], ensure_ascii=False)[:3000])
