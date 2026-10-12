import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
code = "KR0001"
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/c7_kr0001.txt", "w", encoding="utf-8")
p = find_xml(code, "FY2024_Q3", "20241114001986")[0]
tabs = load_tables(p)
def lab_vals(t):
    d = {}; occ = {}
    for r in t["rows"]:
        lab, vals = row_vals(r)
        l = lab.replace(" ", "")
        if l and len(vals) >= 8:
            occ[l] = occ.get(l, 0) + 1
            d[(l, occ[l])] = vals
    return d
cands = []
for t in tabs:
    d = lab_vals(t)
    if ("총보험수익", 1) in d and ("총보험서비스비용", 1) in d and ("총보험서비스결과", 1) in d:
        cands.append((t, d))
out.write(f"candidate tables: {[(t['idx'], t['line']) for t, d in cands]}\n")
def rec(d):
    g = lambda lab, occ=1: d[(lab.replace(' ', ''), occ)]
    # 장기 누적 = index 1 ; values: [장기3m, 장기cum, 일반3m, 일반cum, 자동차3m, 자동차cum, 합계3m, 합계cum]
    c = 1
    v = {}
    v[3] = g("총 보험수익")[c] - g("총 보험서비스비용")[c]
    v[4] = g("당기손익으로 인식한 보험계약마진 금액")[c]
    v[5] = g("위험해제에 따른 위험조정 변동")[c]
    v[6] = g("예상보험금 및 보험서비스비용")[c] - g("보험금 및 보험서비스비용")[c]
    v[7] = v[3] - v[4] - v[5] - v[6]
    v[8] = g("총 재보험수익")[c] - g("총 재보험비용")[c]
    v[9] = -g("당기손익으로 인식한 보험계약마진 금액", 2)[c]
    v[10] = -g("위험해제에 따른 위험조정 변동", 2)[c]
    v[11] = g("회수가능 보험금 및 보험서비스비용")[c] - g("회수예상 보험금 및 보험서비스비용")[c]
    v[12] = v[8] - v[9] - v[10] - v[11]
    v[2] = v[3] + v[8]
    v[13] = (g("총 보험수익")[5] - g("총 보험서비스비용")[5] + g("총 재보험수익")[5] - g("총 재보험비용")[5])
    v[14] = (g("총 보험수익")[3] - g("총 보험서비스비용")[3] + g("총 재보험수익")[3] - g("총 재보험비용")[3])
    return v
for t, d in cands:
    v = rec(d)
    for q in ("2024.3Q", "2023.3Q"):
        sc = sum(1 for it in range(2, 15) if master.get((code, q, it), {}).get("값") not in (None, "") and abs(float(master[(code, q, it)]["값"]) - v[it]) <= 0.5)
        out.write(f"table {t['idx']} line {t['line']} vs master {q}: match {sc}/13  mine={ {k: round(x) for k, x in v.items()} }\n")
    out.write("   master 2023.3Q: " + str({it: master.get((code, '2023.3Q', it), {}).get('값') for it in range(2, 15)}) + "\n")
