# -*- coding: utf-8 -*-
"""csm_combo panel before/after leaf diff (read-only). usage: panel_diff.py <before.json> <after.json>"""
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8")); b = json.load(open(sys.argv[2], encoding="utf-8"))
def walk(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, x
fa, fb = dict(walk(a)), dict(walk(b))
diff = [(k, fa.get(k, "<absent>"), fb.get(k, "<absent>")) for k in sorted(set(fa) | set(fb)) if fa.get(k, "<absent>") != fb.get(k, "<absent>")]
print(f"leaves before={len(fa)} after={len(fb)} differing={len(diff)}")
for k, x, y in diff[:60]:
    print(f"  {k}: {x} -> {y}")
