#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the structure / head of a JSON file (read-only).  usage: bspl_apply_jsonview.py <file.json> [max_chars]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = sys.argv[1]
mx = int(sys.argv[2]) if len(sys.argv) > 2 else 400
d = json.load(open(p, encoding="utf-8"))
print(type(d).__name__, (list(d.keys())[:30] if isinstance(d, dict) else len(d)))
if isinstance(d, dict):
    for k, v in list(d.items())[:40]:
        print(f"{k}: {json.dumps(v, ensure_ascii=False)[:mx]}")
else:
    for r in d[:8]:
        print(json.dumps(r, ensure_ascii=False)[:mx])
