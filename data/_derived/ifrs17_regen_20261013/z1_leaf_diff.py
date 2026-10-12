# -*- coding: utf-8 -*-
"""Leaf-level diff of regenerated artifacts vs the committed HEAD version (changed cells per file).
usage: z1_leaf_diff.py <file> [<file> ...]   (paths relative to repo root). Output: z1_leaf_diff.txt in this folder."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def head(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, cwd=ROOT)
    return json.loads(r.stdout.decode("utf-8"))


def walk(a, b, p, out):
    if type(a) != type(b):
        out.append((p, a, b))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((p + "/" + str(k), "<absent>", b[k]))
            elif k not in b:
                out.append((p + "/" + str(k), a[k], "<absent>"))
            else:
                walk(a[k], b[k], p + "/" + str(k), out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((p + "[len]", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, p + f"[{i}]", out)
    elif a != b:
        out.append((p, a, b))


lines = []
for f in sys.argv[1:]:
    a = head(f)
    b = json.loads((ROOT / f).read_text(encoding="utf-8"))
    out = []
    walk(a, b, "", out)
    lines.append(f"== {f}: {len(out)} changed leaf values")
    for p, x, y in out[:60]:
        lines.append(f"   {p}: {json.dumps(x, ensure_ascii=False)[:60]} -> {json.dumps(y, ensure_ascii=False)[:60]}")
    if len(out) > 60:
        lines.append(f"   ... +{len(out) - 60} more")
(HERE / "z1_leaf_diff.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
