#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print spec cells (key, old, new) and optionally the basis text of the first/N-th cell (read-only).  usage: bspl_apply_specview.py spec.json [basis_index ...]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
cells = d["cells"]
print(len(cells), "cells")
for i, c in enumerate(cells[:400]):
    print(i, c["key"], c.get("action"), c.get("old"), "->", c["new"])
for a in sys.argv[2:]:
    print("--- basis", a, ":", cells[int(a)]["basis"])
