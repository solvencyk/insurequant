# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
d = json.loads((REPO / "data" / "_derived" / "kics_transition_applicability.json").read_text(encoding="utf-8"))
print("top keys:", list(d.keys()))
for k, v in d.items():
    if isinstance(v, list):
        print(f"  {k}: list len={len(v)}")
        if v:
            print("    sample:", v[0])
    elif isinstance(v, dict):
        print(f"  {k}: dict len={len(v)}")
        # try to find KR0069 2026.2Q
        for kk, vv in v.items():
            if "KR0069" in str(kk):
                print("   ", kk, "->", vv)

# also scan the whole json text for "2026.2Q" entries tied to KR0069
txt = json.dumps(d, ensure_ascii=False)
idx = 0
import re
for m in re.finditer(r'"code":\s*"KR0069"[^}]*?"quarter":\s*"([^"]+)"[^}]*?"applicable":\s*"?([^",}]+)"?', txt):
    print("match:", m.group(0)[:200])
