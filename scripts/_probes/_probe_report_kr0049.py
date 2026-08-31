# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

print(type(rep), list(rep.keys()) if isinstance(rep, dict) else len(rep))
