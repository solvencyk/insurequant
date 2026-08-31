# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

before = load(ROOT + r"\artifacts\kics_validation\report_20260831T202215Z.json")
after = load(ROOT + r"\artifacts\kics_validation\report_20260831T202310Z.json")

def findings_of(report):
    # try common shapes
    if isinstance(report, dict):
        for k in ("findings", "results", "records"):
            if k in report and isinstance(report[k], list):
                return report[k]
    if isinstance(report, list):
        return report
    return []

bf = findings_of(before)
af = findings_of(after)
print(f"before findings: {len(bf)}  after findings: {len(af)}")
if bf:
    print("sample finding keys:", list(bf[0].keys()))

def is_kr0029(f):
    return f.get("원보험사코드") == "KR0029" or f.get("code") == "KR0029"

bf29 = [f for f in bf if is_kr0029(f) and f.get("공시분기") in ("2025.2Q","2025.3Q") or (f.get("quarter") in ("2025.2Q","2025.3Q") and is_kr0029(f))]
af29 = [f for f in af if is_kr0029(f) and f.get("공시분기") in ("2025.2Q","2025.3Q") or (f.get("quarter") in ("2025.2Q","2025.3Q") and is_kr0029(f))]

print(f"\nKR0029 2025.2Q/3Q findings before: {len(bf29)}  after: {len(af29)}")

def status_of(f):
    return f.get("status") or f.get("상태")
def rule_of(f):
    return f.get("rule") or f.get("룰") or f.get("axis")
def q_of(f):
    return f.get("공시분기") or f.get("quarter")

print("\n--- BEFORE (RED/YELLOW only) ---")
for f in sorted(bf29, key=lambda x: (q_of(x), str(rule_of(x)))):
    st = status_of(f)
    if st in ("RED", "YELLOW"):
        print(f"  {q_of(f)} {rule_of(f)}: {st}  detail={str(f.get('detail') or f.get('상세'))[:100]}")

print("\n--- AFTER (all statuses) ---")
for f in sorted(af29, key=lambda x: (q_of(x), str(rule_of(x)))):
    st = status_of(f)
    print(f"  {q_of(f)} {rule_of(f)}: {st}")
