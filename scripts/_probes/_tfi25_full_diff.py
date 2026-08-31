import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

before = json.load(open("artifacts/kics_validation/report_20260831T150224Z.json", encoding="utf-8"))
after = json.load(open("artifacts/kics_validation/report_20260831T151333Z.json", encoding="utf-8"))


def red_set(report):
    s = set()
    for f in report["findings"]:
        if f.get("status") == "RED":
            s.add((f.get("원보험사코드"), f.get("공시분기"), f.get("rule")))
    return s


b = red_set(before)
a = red_set(after)
print(f"before RED: {len(b)}  after RED: {len(a)}")
resolved = b - a
new = a - b
print(f"resolved: {len(resolved)}")
print(f"newly appeared: {len(new)}")
for x in sorted(new):
    print("  NEW:", x)
