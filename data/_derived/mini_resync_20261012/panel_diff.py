# -*- coding: utf-8 -*-
"""Generic before/after JSON diff for the combo and compare panels (paths of changed leaves)."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
PAIRS = {
    "panel_csm_combo": ROOT / "data/csm_combo/panel_csm_combo.json",
    "panel_compare": ROOT / "data/compare/panel_compare.json",
}


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


for name, cur in PAIRS.items():
    before = json.loads((D / "panels_before" / f"{name}.json").read_text(encoding="utf-8"))
    after = json.loads(cur.read_text(encoding="utf-8"))
    out = []
    walk(before, after, [], out)
    print(f"=== {name}: {len(out)} changed leaves/nodes")
    # group by first two path elements
    groups = {}
    for kind, p, x, y in out:
        groups.setdefault(tuple(str(s) for s in p[:3]), []).append((kind, p, x, y))
    for g, items in sorted(groups.items()):
        kinds = sorted({i[0] for i in items})
        print("  ", "/".join(g), len(items), kinds)
    for kind, p, x, y in out[:60]:
        sx, sy = json.dumps(x, ensure_ascii=False), json.dumps(y, ensure_ascii=False)
        print("   ", kind, "/".join(str(s) for s in p), sx[:120], "->", sy[:160])
