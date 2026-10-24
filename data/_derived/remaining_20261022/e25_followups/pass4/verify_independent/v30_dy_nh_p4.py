# -*- coding: utf-8 -*-
"""INDEPENDENT re-read (regex table parser of pass3/verify_independent/vlib.py; no p2lib / no pass4 reader / no applier code) of every cell changed by ticket 20261024T1000Z, against the LIVE master (or --master PATH):
  NH농협손해보험 KR0032  2023.1Q item 19; 2023.2Q items 1, 16, 17, 18, 19, 20, 21   <- FY2024_Q1 / FY2024_Q2 separate statement, PRIOR cumulative column (4th numeric cell)
                          + single quarters 2Q / 3Q (master 값_당분기) against the printed PRIOR 3-month column (3rd numeric cell) of FY2024_Q2 / FY2024_Q3
                          + unchanged cells that the ticket asked to compare: 2023.1Q items 1/16/17/18/20-24, 2023.3Q cumulative items 1/16/17/18/19/20/21
  동양생명 KR0087        2024.1Q / 2024.3Q items 9, 10 (= -|total column| of the CSM-release / RA-release rows of the separate PRIOR rollforward table), items 11 / 12 blank
                          + the current-period tables of the same filings against the master 2025.3Q series (definition check)
usage: v30_dy_nh_p4.py [--master PATH] [--out TXT]"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent")
from vlib import path, tables, num  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
args = sys.argv[1:]
MASTER = f"{ROOT}/PL_breakdown.json"
OUT = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/v30_dy_nh_p4.txt"
if "--master" in args:
    MASTER = args[args.index("--master") + 1]
if "--out" in args:
    OUT = args[args.index("--out") + 1]
rows = json.load(open(MASTER, encoding="utf-8"))
PL = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}
lines_out = []
tot = bad = 0


def W(s):
    print(s)
    lines_out.append(s)


def mv(code, q, it, fld="값"):
    r = PL.get((code, q, it))
    return None if r is None else r.get(fld)


def chk(name, raw, master, tol=2e-6):
    global tot, bad
    tot += 1
    ok = (master is None) if raw is None else (master is not None and abs(raw - master) <= tol)
    if not ok:
        bad += 1
    W("%s %-62s raw=%s master=%s" % ("OK " if ok else "BAD", name, raw, master))


def nums_of(c):
    return [num(x) for x in c if num(x) is not None]


# ------------------------------------------------------------------ NH농협손해보험: prior-period columns of the separate statement
def stmt_rows(fq):
    p = path(fq, "KR0032")
    T = tables(p)
    stmt = [(ln, rs) for ln, rs in T if any(c and c[0].replace(" ", "").startswith("VI.법인세차감전순이익") for _, c in rs)]
    assert len(stmt) == 1, (fq, len(stmt))
    return p, stmt[0]


def line_vals(rs, prefix, nth=0):
    hits = [c for _, c in rs if c and c[0].replace(" ", "").startswith(prefix)]
    assert len(hits) > nth, (prefix, len(hits))
    v = nums_of(hits[nth][1:])
    assert len(v) == 4, (prefix, v)
    return v


NH = {}
for q, fq in (("2023.1Q", "2024.1Q"), ("2023.2Q", "2024.2Q"), ("2023.3Q", "2024.3Q")):
    p, (ln, rs) = stmt_rows(fq)
    W("NH file %s statement table@L%d  (columns: cur 3M, cur cum, prior 3M, prior cum)" % (p.replace(ROOT + "/", ""), ln))
    g = {}
    for key, pref in (("i1", "I.보험손익"), ("i16", "3)기타사업비용"), ("i17", "II.투자손익"), ("ins_fi", "1)보험금융수익"), ("re_fi", "2)재보험금융수익"), ("ins_fe", "1)보험금융비용"), ("re_fe", "2)재보험금융비용"),
                      ("i20", "III.영업이익"), ("i21a", "IV.영업외수익"), ("i21b", "V.영업외비용")):
        g[key] = line_vals(rs, pref)
    NH[q] = {}
    for col, tag in ((3, "cum"), (2, "3m")):
        fin = (g["ins_fi"][col] + g["re_fi"][col]) - (g["ins_fe"][col] + g["re_fe"][col])
        v = {1: g["i1"][col], 16: g["i16"][col], 17: g["i17"][col], 19: fin, 18: g["i17"][col] - fin, 20: g["i20"][col], 21: g["i21a"][col] - g["i21b"][col]}
        NH[q][tag] = {k: x / 1e6 for k, x in v.items()}
# cumulative cells
for it in (1, 16, 17, 18, 19, 20, 21):
    chk("NH 2023.2Q item %d prior cum" % it, NH["2023.2Q"]["cum"][it], mv("KR0032", "2023.2Q", it))
for it in (1, 16, 17, 18, 19, 20, 21):
    chk("NH 2023.1Q item %d prior cum (compare: unchanged but 19)" % it, NH["2023.1Q"]["cum"][it], mv("KR0032", "2023.1Q", it))
for it in (1, 16, 17, 18, 19, 20, 21):
    chk("NH 2023.3Q item %d prior cum (compare: already latest)" % it, NH["2023.3Q"]["cum"][it], mv("KR0032", "2023.3Q", it))
# single quarters in the master vs printed prior 3-month columns
for q in ("2023.2Q", "2023.3Q"):
    for it in (1, 16, 17, 18, 19, 20, 21):
        chk("NH %s item %d single quarter (master 값_당분기) vs printed prior 3M" % (q, it), NH[q]["3m"][it], mv("KR0032", q, it, "값_당분기"))
chk("NH 2023.1Q item 19 single quarter (= cumulative)", NH["2023.1Q"]["3m"][19], mv("KR0032", "2023.1Q", 19, "값_당분기"))
# item 15 (기타영업수익) of 2023.2Q is a structural zero: the FY2024_Q2 separate statement has no such row; the 보험손익 bridge adj form (2 + 15 - 16 = 1) then closes within rounding
_p, (_ln, _rs) = stmt_rows("2024.2Q")
_labels = [c[0].replace(" ", "") for _, c in _rs if c]
chk("NH FY2024_Q2 statement rows named 기타영업수익 (expected 0)", 0.0, float(sum(1 for L in _labels if L.startswith("기타영업수익"))), tol=0)
chk("NH 2023.2Q item 15 = 0.0 (structural zero, same as every other NH quarter)", 0.0, mv("KR0032", "2023.2Q", 15))
for _q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    _b = mv("KR0032", _q, 2) + mv("KR0032", _q, 15) - mv("KR0032", _q, 16) - mv("KR0032", _q, 1)
    chk("NH %s 보험손익 bridge adj form 2 + 15 - 16 - 1 (|.| <= 2 백만원)" % _q, 0.0, _b, tol=2.0)
chk("NH 2023.3Q item 15 single quarter = 0 - 0", 0.0, mv("KR0032", "2023.3Q", 15, "값_당분기"))
# identities on the master itself (원 단위 정밀도 유지)
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    m = {i: mv("KR0032", q, i) for i in (1, 17, 18, 19, 20, 21, 22)}
    chk("NH %s master identity 1 + 17 - 20" % q, 0.0, m[1] + m[17] - m[20], tol=2e-6)
    chk("NH %s master identity 17 - (18 + 19)" % q, 0.0, m[17] - m[18] - m[19], tol=2e-6)
    chk("NH %s master identity 20 + 21 - 22" % q, 0.0, m[20] + m[21] - m[22], tol=2e-6)

# ------------------------------------------------------------------ 동양생명: separate rollforward tables of FY2025_Q1 / FY2025_Q3
ROLL = {"2025.1Q": dict(csm="제공받은 서비스를 반영하기 위해 당기손익으로 인식한 보험계약마진 금액", ra="비금융위험에 대한 위험조정 상각액", need="출재보험계약자산 포트폴리오"),
        "2025.3Q": dict(csm="서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진 금액에 따른 증가분(감소분), 재보험계약부채(자산)", ra="미래 또는 과거 서비스와 관련 없는 비금융위험에 대한 위험조정의 변동에 따른 증가분(감소분), 재보험계약부채(자산)", need="기초 재보험계약자산")}
DY = {}
for fq, cfg in ROLL.items():
    p = path(fq, "KR0087")
    T = tables(p)
    cand = []
    for ln, rs in T:
        flat = [" ".join(c) for _, c in rs]
        if any(cfg["csm"] in f for f in flat) and any(cfg["need"] in f for f in flat):
            cand.append((ln, rs))
    W("동양 %s file %s: rollforward tables with the CSM-release row at lines %s" % (fq, p.replace(ROOT + "/", ""), [c[0] for c in cand]))
    assert len(cand) == 4, len(cand)        # [consolidated current, consolidated prior, separate current, separate prior]
    DY[fq] = {}
    for tag, (ln, rs) in zip(("cons_cur", "cons_prior", "sep_cur", "sep_prior"), cand):
        csm = [c for _, c in rs if any(cfg["csm"] in x for x in c[:2])]
        ra = [c for _, c in rs if any(cfg["ra"] in x for x in c[:2])]
        assert len(csm) == 1 and len(ra) == 1, (fq, tag, len(csm), len(ra))
        # '-' cells are skipped by num(); the TOTAL column is the last numeric cell of the row
        DY[fq][tag] = dict(table=ln, csm=nums_of(csm[0][1:])[-1], ra=nums_of(ra[0][1:])[-1])
        W("   %-10s table@L%d CSM total %s  RA total %s" % (tag, ln, DY[fq][tag]["csm"], DY[fq][tag]["ra"]))
    chk("동양 %s separate = consolidated (CSM total prior)" % fq, DY[fq]["cons_prior"]["csm"], DY[fq]["sep_prior"]["csm"], tol=0)
    chk("동양 %s separate = consolidated (RA total prior)" % fq, DY[fq]["cons_prior"]["ra"], DY[fq]["sep_prior"]["ra"], tol=0)
chk("동양 2024.1Q item 9  = -|CSM total| (FY2025_Q1 separate prior)", -abs(DY["2025.1Q"]["sep_prior"]["csm"]), mv("KR0087", "2024.1Q", 9))
chk("동양 2024.1Q item 10 = -|RA total|  (FY2025_Q1 separate prior)", -abs(DY["2025.1Q"]["sep_prior"]["ra"]), mv("KR0087", "2024.1Q", 10))
chk("동양 2024.3Q item 9  = -|CSM total| (FY2025_Q3 separate prior)", -abs(DY["2025.3Q"]["sep_prior"]["csm"]), mv("KR0087", "2024.3Q", 9))
chk("동양 2024.3Q item 10 = -|RA total|  (FY2025_Q3 separate prior)", -abs(DY["2025.3Q"]["sep_prior"]["ra"]), mv("KR0087", "2024.3Q", 10))
chk("동양 2025.3Q item 9  = -|CSM total| (definition check, current table)", -abs(DY["2025.3Q"]["sep_cur"]["csm"]), mv("KR0087", "2025.3Q", 9))
chk("동양 2025.3Q item 10 = -|RA total|  (definition check, current table)", -abs(DY["2025.3Q"]["sep_cur"]["ra"]), mv("KR0087", "2025.3Q", 10))
for q in ("2024.1Q", "2024.3Q"):
    chk("동양 %s item 11 blank (no expected/actual claims rows in the filing)" % q, None, mv("KR0087", q, 11))
    chk("동양 %s item 12 blank" % q, None, mv("KR0087", q, 12))
# what the old item 11 values were: the 재보험계약의 보험서비스결과 total of the same filing (= item 8), not a 예실차
p1 = path("2025.1Q", "KR0087")
res_rows = []
for ln, rs in tables(p1):
    for lr, c in rs:
        if c and "재보험계약의보험서비스결과" in c[0].replace(" ", ""):
            res_rows.append((lr, nums_of(c[1:])))
W("동양 FY2025_Q1 '재보험계약의 보험서비스결과' rows (physical line, numbers [당분기, 전분기]): %s" % res_rows[-2:])
chk("동양 old 2024.1Q item 11 3,805 == prior-period 재보험계약의 보험서비스결과 (|diff to item 8| <= 1)", res_rows[-1][1][-1], mv("KR0087", "2024.1Q", 8), tol=1.0)
# single quarters of the master (cumulative differences) and the 4Q seams
c9 = {q: mv("KR0087", q, 9) for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q")}
c10 = {q: mv("KR0087", q, 10) for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q")}
chk("동양 2024.2Q item 9 single = cum2Q - cum1Q (printed 3M 593 -> -593, rounding 1)", -593.0, mv("KR0087", "2024.2Q", 9, "값_당분기"), tol=1.0)
chk("동양 2024.2Q item 10 single = cum2Q - cum1Q (printed 3M (399))", -399.0, mv("KR0087", "2024.2Q", 10, "값_당분기"), tol=0.0)
chk("동양 2024.3Q item 9 single = cum3Q - cum2Q", c9["2024.3Q"] - c9["2024.2Q"], mv("KR0087", "2024.3Q", 9, "값_당분기"), tol=1e-9)
chk("동양 2024.3Q item 10 single = cum3Q - cum2Q", c10["2024.3Q"] - c10["2024.2Q"], mv("KR0087", "2024.3Q", 10, "값_당분기"), tol=1e-9)
chk("동양 2024.4Q item 9 single blank (seam)", None, mv("KR0087", "2024.4Q", 9, "값_당분기"))
chk("동양 2024.4Q item 10 single blank (seam)", None, mv("KR0087", "2024.4Q", 10, "값_당분기"))
chk("동양 2024.4Q owner-gold cumulatives untouched: item 9 -1,711", -1711.0, c9["2024.4Q"], tol=0)
chk("동양 2024.4Q owner-gold cumulatives untouched: item 10 +1,559", 1559.0, c10["2024.4Q"], tol=0)
chk("동양 2024.4Q item 12 owner-gold untouched 151.725926", 151.725926, mv("KR0087", "2024.4Q", 12), tol=2e-6)
chk("동양 2025.1Q item 9 owner-gold untouched 461", 461.0, mv("KR0087", "2025.1Q", 9), tol=0)
chk("동양 2025.1Q item 10 owner-gold untouched 295", 295.0, mv("KR0087", "2025.1Q", 10), tol=0)
chk("동양 2025.1Q item 12 owner-gold untouched 6515.22178", 6515.22178, mv("KR0087", "2025.1Q", 12), tol=2e-6)
W("TOTAL %d bad %d" % (tot, bad))
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines_out) + "\n")
sys.exit(1 if bad else 0)
