import sys, os, re, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_tier2 import *
here = os.path.dirname(os.path.abspath(__file__))
code = "KR0008"
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
applied = {(r["quarter"], int(r["item"])): r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["code"] == code and r["master"] == "PL_breakdown"}
out = open(here + "/c5_kr0008_t2.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/c5_kr0008_t2.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "applied_new", "mine(prior col recipe)", "post-apply master", "in_plan", "verdict"])
def R(sec, ti, lab, occ, col, which=1):
    return sec[ti][which]["rows"].get((lab, occ), {}).get(col)
for fyq, q in (("FY2024_Q1", "2023.1Q"), ("FY2024_Q2", "2023.2Q"), ("FY2024_Q3", "2023.3Q")):
    ty = pairs(note_tables(find_xml(code, fyq)[0]))
    for si, sec in (("sep(2nd)", ty[-4:]), ("1st", ty[-8:-4])):
        v = {}
        v[3] = R(sec, 2, "합계", 1, "장기") - R(sec, 3, "합계", 1, "장기")
        v[4] = R(sec, 2, "보험계약마진상각", 1, "장기")
        v[5] = R(sec, 2, "비금융위험에대한위험조정의변동", 1, "장기")
        v[6] = R(sec, 2, "예상보험금및보험서비스비용", 1, "장기") - R(sec, 3, "발생보험금및발생보험서비스비용", 1, "장기")
        v[7] = v[3] - v[4] - v[5] - v[6]
        v[8] = -R(sec, 2, "합계", 2, "장기") + R(sec, 3, "합계", 2, "장기")
        v[9] = -R(sec, 2, "보험계약마진상각", 2, "장기")
        v[10] = -R(sec, 2, "비금융위험에대한위험조정의변동", 2, "장기")
        v[11] = -R(sec, 2, "예상출재보험금및수입손해조사비", 1, "장기") + R(sec, 3, "발생출재보험금및수입손해조사비", 1, "장기")
        v[12] = v[8] - v[9] - v[10] - v[11]
        v[2] = v[3] + v[8]
        for col, it in (("자동차", 13), ("일반", 14)):
            v[it] = R(sec, 2, "합계", 1, col) - R(sec, 3, "합계", 1, col) - R(sec, 2, "합계", 2, col) + R(sec, 3, "합계", 2, col)
        for it in range(2, 15):
            m = master.get((code, q, it), {}).get("값")
            mm = float(m) if m not in (None, "") else None
            ap = applied.get((q, it))
            ok = mm is not None and abs(mm - v[it]) <= 0.5
            out.write(f"{q} {si} item{it}: mine={v[it]:.1f} master={mm} {'APPLIED(new='+ap['new']+')' if ap else ''} {'OK' if ok else 'DIFF'}\n")
            if si == "sep(2nd)":
                res.writerow([code, q, it, ap["new"] if ap else "", v[it], mm, "Y" if ap else "N", "MATCH" if ok else "DIFF"])
