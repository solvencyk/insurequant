# -*- coding: utf-8 -*-
"""READ-ONLY evidence for task 5 (롯데손해보험 KR0003 2023.4Q CSM single quarter): which single-quarter cells mix two filing vintages?
Standard library only.
 (a) raw: FY2024 Q3 report, prior-year 9-month CSM table (장기, CSM 소계 column = 6th numeric cell) = the 2023.3Q vector as originally filed
 (b) raw: FY2024 annual report, prior-year (FY2023) CSM table cells cited by the D2 load = the restated 2023.4Q vector
 (c) HEAD (before the 2026-10-23 D2 load) vs live CSM master for 2023.3Q / 2023.4Q, items 1..6, cumulative and single quarter
 (d) per item: does the 4Q cumulative differ between the two vintages (-> the single quarter 4Q - 3Q mixes them) and the single-quarter roll-forward residual."""
import json
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
TAG = re.compile(r"<[^>]+>")
out = []


def P(s=""):
    print(s)
    out.append(s)


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("\u3000", " ").replace("\xa0", " ")).strip()


def num(t):
    t = t.replace(",", "").replace(" ", "")
    if t in ("-", ""):
        return 0.0 if t == "-" else None
    neg = t.startswith("(") and t.endswith(")")
    try:
        v = float(t.strip("()"))
    except ValueError:
        return None
    return -v if neg else v


def tr_cells(lines, i, j):
    out_, k = [], i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b[^>]*>(.*)$", lines[k], re.I)
        if m:
            rest = m.group(2)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out_.append((clean(rest), k + 1))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", lines[q], re.I):
                    t = clean(lines[q])
                    if t:
                        buf.append(t)
                        tl = tl or (q + 1)
                    q += 1
                out_.append((" ".join(buf).strip(), tl or (k + 1)))
                k = q
        k += 1
    return out_


def rows_at(rel, ln):
    """rows of the table containing line ln: [(tr_line, [(text, line)])]"""
    lines = open(f"{ROOT}/{rel}", encoding="utf-8", errors="replace").read().split("\n")
    i = ln - 1
    while not re.match(r"\s*<TABLE\b", lines[i], re.I):
        i -= 1
    j = ln - 1
    while not re.match(r"\s*</TABLE", lines[j], re.I):
        j += 1
    rows, k = [], i
    while k <= j:
        if re.match(r"\s*<TR\b", lines[k], re.I):
            e = k
            while not re.match(r"\s*</TR", lines[e], re.I):
                e += 1
            rows.append((k + 1, tr_cells(lines, k, e)))
            k = e
        k += 1
    return rows, lines


def vector(rel, ln, spec):
    """spec = [(label_norm, numeric_index)] -> list of (value, cell_line, printed)"""
    rows, _lines = rows_at(rel, ln)
    res = []
    for lab, idx in spec:
        hit = [r for r in rows if re.sub(r"\s+", "", r[1][0][0]) == lab] if rows else []
        if not hit:
            res.append((None, None, "ROW NOT FOUND " + lab))
            continue
        cells = hit[0][1]
        nums = [(num(t), l, t) for t, l in cells[1:] if num(t) is not None]
        res.append((nums[idx][0], nums[idx][1], nums[idx][2]))
    return res


# (a) FY2024 Q3 prior 9M table (장기), CSM 소계 = 6th numeric cell (index 5)
rel_q3 = "data/dart/FY2024_Q3/raw/KR0003_롯데손해보험/20241114002408.xml"
SPEC = [("기초순보험계약부채", 5), ("최초인식계약", 5), ("보험금융손익", 5), ("보험계약마진을조정하는추정치의변동", 5), ("보험계약마진상각액", 5), ("기말순보험계약부채", 5)]
a = vector(rel_q3, 15912, SPEC)
P("(a) FY2024 Q3 report, prior-year 9-month CSM table (L15912, 장기, 백만원, CSM 소계 column) -> 억원")
v9 = []
for (lab, _), (v, ln, t) in zip(SPEC, a):
    v9.append(v / 100)
    P(f"    {lab:22s} {t:>12s} @L{ln} -> {v / 100:>9.2f}")
P(f"    roll-forward: {v9[0]:.2f} + {v9[1]:.2f} + {v9[2]:.2f} + {v9[3]:.2f} + ({v9[4]:.2f}) = {v9[0] + v9[1] + v9[2] + v9[3] + v9[4]:.2f} vs closing {v9[5]:.2f}")

# live / HEAD masters
live = {(r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8")) if r["원보험사코드"] == "KR0003"}
plan = json.load(open(f"{ROOT}/data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte/e23_plan_lotte.json", encoding="utf-8"))
cb = [b for b in plan["csm_buckets"] if b["quarter"] == "2023.4Q"][0]
old4 = {c["item"]: c["old"] for c in cb["cells"]}
new4 = {c["item"]: c["new"] for c in cb["cells"]}
P("\n(b)/(c) 2023.4Q cumulative CSM vector: pre-D2 (original annual print) vs restated annual comparative (D2 load, FY2024 annual report prior-period table)")
orig4 = {1: 16774.4, 2: 5478.9, 3: 780.5, 4: 2801.0, 5: -1868.5, 6: 23966.2}
names = {1: "기초", 2: "신계약", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말"}
for it in range(1, 7):
    o = orig4[it]
    n = live[(it, "2023.4Q")]["값"]
    P(f"    item {it} {names[it]:8s} original {o:>9.1f} -> live (restated) {n:>9.1f}  {'CHANGED' if abs(o - n) > 0.05 else 'same'}   plan-old {old4.get(it)}")
P("    live 2023.3Q cumulative (original vintage; equals the raw vector of (a) to 0.05): " + str([live[(i, '2023.3Q')]['값'] for i in range(1, 7)]))

P("\n(d) single quarter 2023.4Q = cumulative 4Q - cumulative 3Q (flows); opening = 3Q closing; closing = 4Q closing")
c3 = {i: live[(i, "2023.3Q")]["값"] for i in range(1, 7)}
c4 = {i: live[(i, "2023.4Q")]["값"] for i in range(1, 7)}
single_new = {2: c4[2] - c3[2], 3: c4[3] - c3[3], 4: c4[4] - c3[4], 5: c4[5] - c3[5]}
single_old = {2: orig4[2] - c3[2], 3: orig4[3] - c3[3], 4: orig4[4] - c3[4], 5: orig4[5] - c3[5]}
for it in (2, 3, 4, 5):
    P(f"    item {it} {names[it]:8s}: single quarter with the original annual {single_old[it]:>8.1f} | with the restated annual {single_new[it]:>8.1f} | shift {single_new[it] - single_old[it]:+.1f}  -> {'MIXED' if abs(single_new[it] - single_old[it]) > 0.05 else 'not mixed (annual identical in both vintages)'}")
res_old = c3[6] + sum(single_old.values()) - orig4[6]
res_new = c3[6] + sum(single_new.values()) - c4[6]
P(f"    roll-forward residual (opening {c3[6]:.1f} + flows - closing): original annual {res_old:+.1f} | restated annual {res_new:+.1f}")
P(f"    live 값_당분기 now: " + str({i: live[(i, '2023.4Q')]['값_당분기'] for i in range(1, 7)}))
P("    stock cells: item 1 single = 3Q closing as filed; item 6 single = restated annual closing (not differences of cumulatives)")
open(f"{ROOT}/data/_derived/remaining_20261022/e25_followups/kr0003_lotte_csm_blank/c03_vintage_evidence.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
