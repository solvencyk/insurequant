"""k4: structure of e19 plan_KR0104.json (READ-ONLY)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/plan_KR0104.json")
d = json.loads(P.read_text(encoding="utf-8"))
print(type(d), list(d.keys())[:20] if isinstance(d, dict) else len(d))
if isinstance(d, dict):
    for k, v in d.items():
        print("KEY", k, type(v).__name__, (list(v.keys())[:25] if isinstance(v, dict) else (len(v) if hasattr(v, "__len__") else v)))
    q = d.get("buckets") or d.get("plans") or d
    if isinstance(q, dict):
        for k in list(q.keys())[:6]:
            v = q[k]
            print("  bucket", k, type(v).__name__, list(v.keys())[:30] if isinstance(v, dict) else "")
            if k in ("2023.1Q",):
                for kk, vv in v.items():
                    print("    ", kk, json.dumps(vv, ensure_ascii=False)[:700])
