# -*- coding: utf-8 -*-
"""CSM_waterfall 기말 CSM(항목 6) 대 insurance_liability_portfolio 항목 3+6 (공유 (회사,분기)) 재현. 읽기만 한다(디스크 쓰기는 --md 지정 시 그 파일뿐).
임계 max(1억, 0.5%|ILP|). 22차 런로그 Section 6 의 273칸/6칸+롯데 군집 주장을 지금 마스터로 다시 잰다.
재현: python <이 파일> [--md 출력.md]"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
w = json.load(open("CSM_waterfall.json", encoding="utf-8"))
ilp = json.load(open("insurance_liability_portfolio.json", encoding="utf-8"))
wf = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in w if r["항목번호"] == 6 and r["값"] is not None}
names = {r["원보험사코드"]: r["원수사명"] for r in w}
i3 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ilp if r["항목번호"] == 3 and r["값"] is not None}
i6 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ilp if r["항목번호"] == 6 and r["값"] is not None}
rows = []
for k, v in sorted(wf.items()):
    if k in i3 or k in i6:
        s = (i3.get(k) or 0) + (i6.get(k) or 0)
        rows.append((k, v, s, v - s))
print("shared (company,quarter) cells:", len(rows), " waterfall cells:", len(wf), " ILP cells(3 or 6):", len(set(i3) | set(i6)))
bad = [r for r in rows if abs(r[3]) > max(1.0, 0.005 * abs(r[2]))]
within1 = [r for r in rows if abs(r[3]) <= 1.0]
print("agree within 1억:", len(within1), " within max(1억,0.5%):", len(rows) - len(bad), " beyond:", len(bad))
out = ["| 회사 | 분기 | 워터폴 기말CSM(억) | ILP 3+6(억) | 차이 | 차이/ILP |", "|---|---|---|---|---|---|"]
for (c, q), v, s, d in bad:
    out.append(f"| {c} {names.get(c, '')} | {q} | {v:,.1f} | {s:,.1f} | {d:+,.1f} | {d / s * 100 if s else float('nan'):+.2f}% |")
print("\n".join(out))
# 임계 안이지만 0 이 아닌 롯데 군집(밴드가 숨기는 것)
lo = [r for r in rows if r[0][0] == "KR0003" and abs(r[3]) > 1.0]
print("KR0003 cells with |diff|>1억:", [(r[0][1], round(r[3], 1)) for r in lo])
if "--md" in sys.argv:
    p = sys.argv[sys.argv.index("--md") + 1]
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
