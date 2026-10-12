import sys, os, re, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_tier2 import *
here = os.path.dirname(os.path.abspath(__file__))
code = "KR0011"
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
applied = {(r["quarter"], int(r["item"])): r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["code"] == code and r["master"] == "PL_breakdown"}
out = open(here + "/c6_kr0011_t2.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/c6_kr0011_t2.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "applied_new", "mine(prior col recipe)", "cur-calibration", "post-apply master", "in_plan", "verdict"])
def secs_of(fyq):
    nts = note_tables(find_xml(code, fyq)[0])
    ty = pairs(nts)
    secs = []; cur = []
    for t in ty:
        if cur and t[0]["idx"] - cur[-1][0]["idx"] > 60: secs.append(cur); cur = []
        cur.append(t)
    if cur: secs.append(cur)
    return [s for s in secs if len(s) == 4 and any(("보험계약마진상각", 1) in t[0]["rows"] for t in s)]

def calc(sec, which):
    def R(ti, lab, occ=1, col="장기"): return sec[ti][which]["rows"].get((lab, occ), {}).get(col)
    v = {}
    v[3] = R(0, "합계") - R(1, "합계")
    v[4] = R(0, "보험계약마진상각")
    v[5] = R(0, "비금융위험에대한위험조정상각")
    v[6] = sum(R(0, l) for l in ("예상보험금", "예상유지비", "예상손해조사비", "예상투자관리비")) - sum(R(1, l) for l in ("발생보험금", "발생직접유지비", "손해조사비", "투자관리비"))
    v[7] = v[3] - v[4] - v[5] - v[6]
    v[8] = R(2, "합계") - R(3, "합계")
    v[9] = -R(3, "보험계약마진상각")
    v[10] = -R(3, "비금융위험에대한위험조정상각")
    v[11] = R(2, "발생출재보험금") - R(3, "예상출재보험금")
    v[12] = v[8] - v[9] - v[10] - v[11]
    v[2] = v[3] + v[8]
    for col, it in (("자동차", 13), ("일반", 14)):
        v[it] = R(0, "합계", 1, col) - R(1, "합계", 1, col) + R(2, "합계", 1, col) - R(3, "합계", 1, col)
    return v
for fyq, q, cq in (("FY2024_Q1", "2023.1Q", "2024.1Q"), ("FY2024_Q2", "2023.2Q", "2024.2Q"), ("FY2024_Q3", "2023.3Q", "2024.3Q")):
    best = None
    for sec in secs_of(fyq):
        vc = calc(sec, 0)
        sc = sum(1 for it in range(2, 15) if master.get((code, cq, it), {}).get("값") not in (None, "") and abs(float(master[(code, cq, it)]["값"]) - vc[it]) <= 2.5)
        out.write(f"{fyq} candidate section {[t[0]['idx'] for t in sec]} calibration score {sc}/13" + chr(10))
        if best is None or sc > best[0]: best = (sc, sec)
    sec = best[1]
    vp, vc = calc(sec, 1), calc(sec, 0)
    for it in range(2, 15):
        m = master.get((code, q, it), {}).get("값"); mm = float(m) if m not in (None, "") else None
        mc = master.get((code, cq, it), {}).get("값"); mcv = float(mc) if mc not in (None, "") else None
        ap = applied.get((q, it))
        ok = mm is not None and abs(mm - vp[it]) <= 2.5
        calib = mcv is not None and abs(mcv - vc[it]) <= 2.5
        out.write(f"{q} item{it}: mine(prior)={vp[it]:.1f} master={mm} | cur-calibration mine={vc[it]:.1f} master({cq})={mcv} {'OK' if calib else 'CALIB-DIFF'} {'APPLIED new='+ap['new'] if ap else ''} -> {'OK' if ok else 'DIFF'}\n")
        res.writerow([code, q, it, ap["new"] if ap else "", vp[it], "OK" if calib else "DIFF", mm, "Y" if ap else "N", "MATCH" if ok else "DIFF"])
