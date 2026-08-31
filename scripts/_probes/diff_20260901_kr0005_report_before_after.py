# -*- coding: utf-8 -*-
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BEFORE = "artifacts/kics_validation/report_20260831T185616Z.json"
AFTER = "artifacts/kics_validation/report_20260831T185900Z.json"

b = json.load(open(BEFORE, encoding="utf-8"))
a = json.load(open(AFTER, encoding="utf-8"))

print("=== summary ===")
print("before:", b["summary"])
print("after :", a["summary"])

print("\n=== findings (core run_validation) for KR0005, rule in mmult15/R5.../R6... ===")
for label, d in (("BEFORE", b), ("AFTER", a)):
    print(f"--- {label} ---")
    for f in d["findings"]:
        code = f.get("원보험사코드") or f.get("code") or f.get("company_code")
        if code != "KR0005":
            continue
        rule = str(f.get("rule", ""))
        if "mmult15" in rule or "R5" in rule or "R6" in rule or rule in ("15", "16", "22"):
            print(" ", f)

print("\n=== transition_mmult_after for KR0005 ===")
for label, d in (("BEFORE", b), ("AFTER", a)):
    print(f"--- {label} ---")
    tma = d.get("transition_mmult_after")
    if isinstance(tma, dict):
        for k, v in tma.items():
            print(f"  key={k!r}")
            if isinstance(v, list):
                for item in v:
                    s = json.dumps(item, ensure_ascii=False)
                    if "KR0005" in s:
                        print("   ", s)
    elif isinstance(tma, list):
        for item in tma:
            s = json.dumps(item, ensure_ascii=False)
            if "KR0005" in s:
                print("   ", s)

print("\n=== transition_identities_after for KR0005 ===")
for label, d in (("BEFORE", b), ("AFTER", a)):
    print(f"--- {label} ---")
    tia = d.get("transition_identities_after")
    if isinstance(tia, dict):
        for k, v in tia.items():
            print(f"  key={k!r}")
            if isinstance(v, list):
                for item in v:
                    s = json.dumps(item, ensure_ascii=False)
                    if "KR0005" in s:
                        print("   ", s)
    elif isinstance(tia, list):
        for item in tia:
            s = json.dumps(item, ensure_ascii=False)
            if "KR0005" in s:
                print("   ", s)
