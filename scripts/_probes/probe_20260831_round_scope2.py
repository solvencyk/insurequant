# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET_RULES = {"1","2","4","5","6","7","8","7_post","2_tier1_bridge","3_tier2_composition"}

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    report = json.load(f)

findings = report["findings"]
reds = [f for f in findings if f.get("status") == "RED"]
target_reds = [f for f in reds if str(f.get("rule")) in TARGET_RULES]

print("total RED:", len(reds), " target-rule RED:", len(target_reds))
print()

with open("scripts/_probes/_round_target_reds.json", "w", encoding="utf-8") as f:
    json.dump(target_reds, f, ensure_ascii=False, indent=2)

rows = sorted(target_reds, key=lambda x: (str(x.get("rule")), str(x.get("원보험사코드")), str(x.get("공시분기"))))
for r in rows:
    print(f"{r.get('rule'):22s} | {r.get('원보험사코드')} {r.get('원수사명')} | {r.get('공시분기')} | exp={r.get('expected')} act={r.get('actual')} diff={r.get('diff')} | {r.get('detail','')[:80]}")

# also print unique company/period combos in target rules
combos = sorted(set((r.get('원보험사코드'), r.get('원수사명'), r.get('공시분기')) for r in target_reds))
print()
print("unique company-period combos:", len(combos))
for c in combos:
    print(c)

# print RED counts by rule
from collections import Counter
print()
print("counts by rule:", Counter(str(r.get("rule")) for r in target_reds))

# Also check ALL red rules present (not just target) to compare with the "23" figure in the prompt
print()
print("ALL red rule types:", Counter(str(r.get("rule")) for r in reds))
