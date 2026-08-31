# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\artifacts\kics_validation\report_20260831T202722Z.json", "r", encoding="utf-8") as f:
    report = json.load(f)
findings = report.get("findings") or report.get("results") or report
rows = [f for f in findings if f.get("원보험사코드")=="KR0029" and f.get("공시분기") in ("2025.2Q","2025.3Q")]
red = [f for f in rows if f.get("status")=="RED"]
print(f"KR0029 2025.2Q/3Q total findings: {len(rows)}  RED: {len(red)}")
for f in red:
    print(f"  RED {f.get('공시분기')} {f.get('rule')}: {f.get('detail')}")
