# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_20260831T051505Z.json", "r", encoding="utf-8") as f:
    before = json.load(f)
with open("artifacts/kics_validation/report_20260831T053313Z.json", "r", encoding="utf-8") as f:
    after = json.load(f)

skip_keys = {"findings", "source", "generated_at", "spot_check"}
for k in before.keys():
    if k in skip_keys:
        continue
    if before[k] != after[k]:
        print(f"DIFFERS: {k}")
        bstr = json.dumps(before[k], ensure_ascii=False, sort_keys=True)
        astr = json.dumps(after[k], ensure_ascii=False, sort_keys=True)
        print("  before:", bstr[:1500])
        print("  after :", astr[:1500])
    else:
        print(f"same: {k}")
