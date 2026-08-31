import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8"))
print("top-level keys:", list(d.keys()))
for k in d.keys():
    v = d[k]
    print(f"key={k!r} type={type(v)} len={len(v) if hasattr(v,'__len__') else '?'}")
    if isinstance(v, dict):
        # print a sample item
        sample_keys = list(v.keys())[:3]
        for sk in sample_keys:
            print("   sample:", sk, "->", v[sk])

# now search for our companies
codes = ["KR0011", "KR0029", "KR0051"]

def walk(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k)
            if any(c in ks for c in codes):
                found.append((path + "/" + ks, v))
            else:
                found.extend(walk(v, path + "/" + ks))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                found.extend(walk(v, path + f"[{i}]"))
            elif isinstance(v, str) and any(c in v for c in codes):
                found.append((path + f"[{i}]", v))
    return found

hits = walk(d)
print(f"\n{len(hits)} hits for {codes}")
for p, v in hits[:60]:
    print(p, "=", v)
