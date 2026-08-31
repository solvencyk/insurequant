# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
rep = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
print("top-level keys:", list(rep.keys()) if isinstance(rep, dict) else type(rep))

# find the findings list (structure unknown yet -- probe)
def find_findings(obj, path=""):
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "rule" in obj[0]:
        print(f"FOUND findings list at {path}, len={len(obj)}")
        return obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            r = find_findings(v, path + "/" + k)
            if r is not None:
                return r
    return None

findings = find_findings(rep)
if findings is None:
    print("no findings list found via heuristic -- dumping top structure")
    print(json.dumps(rep, ensure_ascii=False)[:2000])
else:
    kr0029 = [f for f in findings if f.get("원보험사코드") == "KR0029"]
    print(f"\nTotal KR0029 findings: {len(kr0029)}")
    by_status = {}
    for f in kr0029:
        by_status.setdefault(f.get("status"), []).append(f)
    for status, fs in by_status.items():
        print(f"  {status}: {len(fs)}")
    print("\nKR0029 RED findings (any quarter):")
    for f in kr0029:
        if f.get("status") == "RED":
            print(" ", f.get("공시분기"), f.get("rule"), "expected=", f.get("expected"), "actual=", f.get("actual"), "diff=", f.get("diff"))
    print("\nKR0029 2023.1Q findings (all statuses):")
    for f in kr0029:
        if f.get("공시분기") == "2023.1Q":
            print(" ", f.get("rule"), f.get("status"), "expected=", f.get("expected"), "actual=", f.get("actual"), "diff=", f.get("diff"))
