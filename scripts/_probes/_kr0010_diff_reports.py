# -*- coding: utf-8 -*-
import json, io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

files = sorted(glob.glob("artifacts/kics_validation/report_2026083*.json"), key=os.path.getmtime)
for fp in files:
    with open(fp, "r", encoding="utf-8") as f:
        r = json.load(f)
    src = r.get("source", "?")
    print(f"{fp}  mtime={os.path.getmtime(fp):.0f}  source={src}")
