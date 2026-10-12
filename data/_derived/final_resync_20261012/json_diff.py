# -*- coding: utf-8 -*-
"""Generic before/after JSON leaf diff. usage: json_diff.py <before.json> <after.json> [max_lines]"""
import json
import sys
from pathlib import Path


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append(("ADD", path + [k], None, b[k]))
            elif k not in b:
                out.append(("DEL", path + [k], a[k], None))
            else:
                walk(a[k], b[k], path + [k], out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, path + [i], out)
    elif a != b:
        out.append(("CHG", path, a, b))


before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
mx = int(sys.argv[3]) if len(sys.argv) > 3 else 40
out = []
walk(before, after, [], out)
print(f"=== {sys.argv[2]}: {len(out)} changed leaves/nodes")
groups = {}
for kind, p, x, y in out:
    groups.setdefault((kind,) + tuple(str(s) for s in p[:3]), []).append(1)
for g, items in sorted(groups.items()):
    print("  ", "/".join(g), len(items))
for kind, p, x, y in out[:mx]:
    sx, sy = json.dumps(x, ensure_ascii=False), json.dumps(y, ensure_ascii=False)
    print("   ", kind, "/".join(str(s) for s in p), sx[:140], "->", sy[:200])
