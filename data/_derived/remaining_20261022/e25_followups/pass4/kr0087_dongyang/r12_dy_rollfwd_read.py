# -*- coding: utf-8 -*-
"""READ-ONLY pass4 r12 (KR0087 동양생명, ticket 20261024T1000Z item 2).  Separate-basis (별도, notes after the separate statements) reinsurance-held measurement-component rollforward:
  2024.1Q <- FY2025_Q1 quarterly report, PRIOR-period table ('전분기'; style (i): 제공받은 서비스를 반영하기 위해 당기손익으로 인식한 보험계약마진 금액 / 비금융위험에 대한 위험조정 상각액; 순자산(부채) view)
  2024.3Q <- FY2025_Q3 quarterly report, PRIOR-period table ('전분기'; style (ii): 서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진 금액에 따른 증가분(감소분) / 미래 또는 과거 서비스와 관련 없는 비금융위험에
              대한 위험조정의 변동에 따른 증가분(감소분); 재보험계약부채(자산) view = opposite print sign)
Takes the TOTAL column (last numeric cell) of the CSM-release row and of the RA-release row; production definition 9 = -|CSM total|, 10 = -|RA total| (same as the live 2025.2Q/2025.3Q series).
Also prints the CURRENT-period tables of the same filings (2025.1Q / 2025.3Q) against the live master, and the opening-balance fingerprint of every prior table (all start from the same 2024-01-01 opening).
Output: r12_dy_rollfwd_read.json / .txt"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
M, E = P.M, P.E
EVD = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/kr0087_dongyang"
CODE = "KR0087"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
out_txt, res = [], {}


def PR(s=""):
    print(s)
    out_txt.append(s)


def pre_text(lines, start, n=16):
    return " | ".join(x for x in (re.sub(r"\s+", " ", P._TAGRE.sub("", y)).strip() for y in lines[max(0, start - n):start - 1]) if x)[-160:]


def nrow(r):
    return [dict(v=v, line=ln, text=tx) for v, ln, tx in P.nums(r)]


def find_row(rows, pat):
    hits = [r for r in rows if r["cells"] and any(re.search(pat, P.nl(c["text"])) for c in r["cells"][:2])]
    assert len(hits) == 1, (pat, len(hits))
    return hits[0]


STYLES = {
    "FY2025_Q1": dict(need=["출재보험계약자산", "제공받은서비스를반영하기위해당기손익으로인식한보험계약마진금액"], csm=r"제공받은서비스를반영하기위해당기손익으로인식한보험계약마진금액", ra=r"비금융위험에대한위험조정상각액",
                      open_pat=r"^기초$", style="(i)"),
    "FY2025_Q3": dict(need=["재보험계약부채(자산)", "서비스이전을반영하기위해당기손익으로인식한보험계약마진금액"], csm=r"서비스이전을반영하기위해당기손익으로인식한보험계약마진금액", ra=r"미래또는과거서비스와관련없는비금융위험에대한위험조정의변동",
                      open_pat=r"^기초재보험계약자산$", style="(ii)"),
}
for fy, st in STYLES.items():
    path, lines, s0, tabs = P.tables_with(CODE, fy, st["need"], sep_only=True)
    tabs = sorted(tabs, key=lambda tr: tr[0]["start"])
    PR(f"##### {fy} {M.rel(path)}  separate-basis notes start at L{s0}; tables with the CSM-release row: {[(t['start'], t['end']) for t, _r in tabs]}")
    assert len(tabs) == 2, len(tabs)
    for which, (t, rows) in zip(("current", "prior"), tabs):
        cap = pre_text(lines, t["start"])
        rc, rr = find_row(rows, st["csm"]), find_row(rows, st["ra"])
        nc, nr_ = nrow(rc), nrow(rr)
        # opening-balance fingerprint = first numeric row after a label matching 기초 (style i: row with '출재보험계약자산 포트폴리오'; style ii: '기초 재보험계약자산')
        orow = next(r for r in rows if r["cells"] and any(re.search(st["open_pat"].replace("^기초$", "^기초$|기초"), P.nl(c["text"])) for c in r["cells"][:1]) and len(P.nums(r)) >= 5) if fy == "FY2025_Q3" else \
            next(r for r in rows if r["cells"] and "출재보험계약자산포트폴리오" in P.nl(r["cells"][1]["text"] if len(r["cells"]) > 1 else "") and len(P.nums(r)) >= 5)
        on = nrow(orow)
        rec = dict(file=M.rel(path), fy=fy, table=[t["start"], t["end"]], which=which, caption_tail=cap, csm_row_line=rc["tr_line"], ra_row_line=rr["tr_line"],
                   csm_cells=nc, ra_cells=nr_, csm_total=nc[-1], ra_total=nr_[-1], opening=[x["v"] for x in on[:5]], opening_line=orow["tr_line"], style=st["style"])
        res[f"{fy}|{which}"] = rec
        PR(f"   [{which}] table@L{t['start']}-{t['end']} preceding='{cap}'")
        PR(f"      CSM-release row R{rc['tr_line']}: " + " | ".join(f"{x['text']}@{x['line']}" for x in nc) + f"   -> TOTAL {nc[-1]['text']}@L{nc[-1]['line']}")
        PR(f"      RA-release  row R{rr['tr_line']}: " + " | ".join(f"{x['text']}@{x['line']}" for x in nr_) + f"   -> TOTAL {nr_[-1]['text']}@L{nr_[-1]['line']}")
        PR(f"      opening row R{orow['tr_line']} first 5 numbers: {[x['v'] for x in on[:5]]}")
        # internal sums
        if st["style"] == "(i)":
            mr_fv_ot = sum(x["v"] for x in nc[2:5])
            PR(f"      check: CSM columns (수정소급+공정가치+그 밖) {mr_fv_ot:,.0f} vs 소계 {nc[5]['v']:,.0f} vs 합계 {nc[6]['v']:,.0f}; RA row columns sum {sum(x['v'] for x in nr_[:6]):,.0f} vs total {nr_[-1]['v']:,.0f}")
        else:
            mr_fv_ot = sum(x["v"] for x in nc[2:5])
            PR(f"      check: CSM columns (수정소급+공정가치+그 밖) {mr_fv_ot:,.0f} vs 합계 {nc[5]['v']:,.0f}; RA row columns sum {sum(x['v'] for x in nr_[:5]):,.0f} vs total {nr_[-1]['v']:,.0f}")
# derived items and the live master
PR("")
q1p, q3p = res["FY2025_Q1|prior"], res["FY2025_Q3|prior"]
assert q1p["opening"] == q3p["opening"], (q1p["opening"], q3p["opening"])
PR(f"opening-balance fingerprint equal in the 1Q-prior and 3Q-prior tables: {q1p['opening']}  (same 2024-01-01 opening => the 3Q-prior table is the 9-month cumulative of 2024)")
items = {}
for q, key in (("2024.1Q", "FY2025_Q1|prior"), ("2024.3Q", "FY2025_Q3|prior")):
    r_ = res[key]
    items[q] = dict(i9=-abs(r_["csm_total"]["v"]), i10=-abs(r_["ra_total"]["v"]), csm_line=r_["csm_total"]["line"], csm_text=r_["csm_total"]["text"], ra_line=r_["ra_total"]["line"], ra_text=r_["ra_total"]["text"])
    PR(f"{q}: item 9 = -|{r_['csm_total']['text']}@L{r_['csm_total']['line']}| = {items[q]['i9']:,.0f}; item 10 = -|{r_['ra_total']['text']}@L{r_['ra_total']['line']}| = {items[q]['i10']:,.0f}   | live master 9={live[(q, 9)]['값']} 10={live[(q, 10)]['값']} 11={live[(q, 11)]['값']} 12={live[(q, 12)]['값']} 8={live[(q, 8)]['값']}")
res["items"] = items
# current-period cross-checks against the live master
for q, key in (("2025.1Q", "FY2025_Q1|current"), ("2025.3Q", "FY2025_Q3|current")):
    r_ = res[key]
    PR(f"current period {q}: CSM total {r_['csm_total']['text']}@L{r_['csm_total']['line']}, RA total {r_['ra_total']['text']}@L{r_['ra_total']['line']}  | live master 9={live[(q, 9)]['값']} 10={live[(q, 10)]['값']} (gold={'owner' if q == '2025.1Q' else 'none'})  -> -|CSM|={-abs(r_['csm_total']['v']):,.0f} -|RA|={-abs(r_['ra_total']['v']):,.0f}")
json.dump(res, open(f"{EVD}/r12_dy_rollfwd_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/r12_dy_rollfwd_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
