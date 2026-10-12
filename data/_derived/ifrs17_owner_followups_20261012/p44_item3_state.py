# -*- coding: utf-8 -*-
"""Read-only: current state of the cells of items (21)/(22) that the ticket says to leave untouched; plus proof via git HEAD that this round did not change them."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def now(p): return json.loads(open(R + p, "rb").read().decode("utf-8"))
def head(p): return json.loads(subprocess.run(["git", "-C", R, "show", f"HEAD:{p}"], capture_output=True).stdout.decode("utf-8"))
ilp, ilp_h = now("insurance_liability_portfolio.json"), head("insurance_liability_portfolio.json")
sens, sens_h = now("CSM_sensitivity.json"), head("CSM_sensitivity.json")
for code, q, label in (("KR1101", "2023.4Q", "뮌헨 ILP"), ("KR1104", "2023.4Q", "하노버 ILP")):
    v = {r["항목번호"]: r["값"] for r in ilp if r["원보험사코드"] == code and r["공시분기"] == q}
    vh = {r["항목번호"]: r["값"] for r in ilp_h if r["원보험사코드"] == code and r["공시분기"] == q}
    print(label, q, "now:", v, "| same as HEAD:", v == vh)
rows_now = [r for r in sens if r["원보험사코드"] in ("KR1103", "KR1104") ]
print("CSM_sensitivity KR1103 rows now:", sum(1 for r in sens if r["원보험사코드"] == "KR1103"), "| KR1104 rows 2023.4Q now:", sum(1 for r in sens if r["원보험사코드"] == "KR1104" and r["공시분기"] == "2023.4Q"))
print("CSM_sensitivity unchanged vs HEAD:", sens == sens_h)
k = lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])
chg = [r for r in ilp if r["원보험사코드"] in ("KR1101", "KR1103", "KR1104")]
chg_h = [r for r in ilp_h if r["원보험사코드"] in ("KR1101", "KR1103", "KR1104")]
print("ILP rows of KR1101/KR1103/KR1104 unchanged vs HEAD:", chg == chg_h, len(chg))
