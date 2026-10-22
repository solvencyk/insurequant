"""a21: KR0079 master PL item 4/5 and CSM item 5 across quarters (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "CSM_waterfall.json", encoding="utf-8").read())}
for code in ("KR0079", "KR0068"):
    for y in (2023, 2024, 2025, 2026):
        for n in (1, 2, 3, 4):
            q = f"{y}.{n}Q"
            if (code, 4, q) in pl or (code, 5, q) in csm:
                print(code, q, "PL4", pl.get((code, 4, q)), "PL5", pl.get((code, 5, q)), "CSM5", csm.get((code, 5, q)))
