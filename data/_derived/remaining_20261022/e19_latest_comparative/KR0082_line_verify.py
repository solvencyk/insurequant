# -*- coding: utf-8 -*-
"""Independent line-level re-read of plan_KR0082.json (own code, does NOT use KR0082_xml / KR0082_plan).
The KR0082 statements carry no ACONTEXT, so the column is proven by position: the enclosing <TR> is parsed from the raw lines (label cell + 4 value cells),
the cited line must be the 4th value cell (prior-year cumulative) or the 3rd (prior-year 3-month); the header rows of the statement (period titles, 3개월/누적 row)
and the section nesting (4. 재무제표 > 4-2. 포괄손익계산서) are checked too.  Values are recomputed from the printed won amounts with explicit sign rules."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
plan = json.loads((HERE / "plan_KR0082.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
cache = {}


def lines(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return cache[rel]


def won(t):
    t = t.replace(",", "").strip()
    if t == "-":
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    v = float(t.strip("()"))
    return -v if neg else v


def tr_cells(L, ln):
    """-> (tr_start_line, [(line, text)...]) : all <P> texts of the TR that encloses line ln (1-based); first = label"""
    i = ln - 1
    while i > 0 and not L[i].startswith("<TR"):
        i -= 1
    j = i + 1
    out = []
    while j < len(L) and not L[j].startswith("</TR"):
        if re.match(r"\s*<P[ >]", L[j]) or L[j].startswith("<P"):
            out.append((j + 1, TAG.sub("", L[j]).replace("\u3000", " ").strip()))
        j += 1
    return i + 1, out


def sig(s):
    return s.replace(" ", "").replace("\u3000", "")


out, bad, n = [], 0, 0


def check(L, rel, ln, printed, label, col_idx, ncols, tag):
    """col_idx: 0-based index among the value cells (label excluded)"""
    global bad, n
    n += 1
    tr, cs = tr_cells(L, ln)
    lab = cs[0][1]
    vals = cs[1:]
    ok_n = (len(vals) == ncols)
    ok_pos = ok_n and vals[col_idx][0] == ln
    ok_txt = ok_n and vals[col_idx][1] == printed and TAG.sub("", L[ln - 1]).strip() == printed
    ok_lab = sig(re.sub(r"\(주[^)]*\)", "", lab)) == sig(re.sub(r"\(주[^)]*\)", "", label))
    ok = ok_pos and ok_txt and ok_lab
    bad += 0 if ok else 1
    out.append(f"{tag} L{ln} TR{tr} row={lab!r} plan_label={label!r} values={[v[1] for v in vals]} col_idx={col_idx} -> {'OK' if ok else 'MISMATCH (pos=%s txt=%s lab=%s)' % (ok_pos, ok_txt, ok_lab)}")
    return won(printed) if ok else None


def header_checks(rel, fy_tag, expect_cum_period, ncols_hdr=True):
    global bad, n
    L = lines(rel)
    t = [i for i, l in enumerate(L, 1) if l.startswith("<TITLE") and "4-2. 포괄손익계산서" in l]
    p = [i for i, l in enumerate(L, 1) if l.startswith("<TITLE") and re.search(r">4\. 재무제표<", l)]
    nxt = [i for i, l in enumerate(L, 1) if l.startswith("<TITLE") and re.search(r">5\. 재무제표 주석<", l)]
    n += 1
    ok = len(t) == 1 and len(p) == 1 and len(nxt) == 1 and p[0] < t[0] < nxt[0]
    # period header lines (first 80 lines after the title)
    seg = [TAG.sub("", x).strip() for x in L[t[0]:t[0] + 140]]
    seg = [x for x in seg if x]
    per = [x for x in seg if "부터" in x][:2]
    hdr = [x for x in seg if x in ("3개월", "누적")][:4]
    unit = [x for x in seg if "단위" in x][:1]
    out.append(f"HEADER {fy_tag} section '4. 재무제표' L{p[0]} < 4-2 L{t[0]} < '5. 재무제표 주석' L{nxt[0]} -> {'OK' if ok else 'MISMATCH'}; periods={per}; col header={hdr}; unit={unit}")
    if not ok:
        bad += 1
    return per, hdr


per_o, hdr_o = header_checks(plan["buckets"][2]["original_filing"]["file"], "orig FY2023_Q3", None)
per_l, hdr_l = header_checks(plan["buckets"][2]["later_filing"]["file"], "later FY2024_Q3", None)
n += 1
okh = (per_l[1].endswith("2023.09.30 까지") and per_l[0].endswith("2024.09.30 까지") and hdr_l[:4] == ["3개월", "누적", "3개월", "누적"] and hdr_o[:4] == ["3개월", "누적", "3개월", "누적"] and per_o[0].endswith("2023.09.30 까지"))
bad += 0 if okh else 1
out.append(f"HEADER SEMANTICS later: first period group = 2024.1.1-9.30, second = 2023.1.1-9.30; columns = [3개월, 누적, 3개월, 누적] -> {'OK' if okh else 'MISMATCH'}")

for c in plan["cells"]:
    rel = c["xml_file"]
    L = lines(rel)
    total = 0.0
    printed_by_label = {}
    for p in c["xml_lines"]:
        w = check(L, rel, p["line"], p["printed"], p["label"], 3, 4, f"CELL {c['quarter']} i{c['item']} later cum-prior")
        printed_by_label[p["label"]] = w
    # recompute with explicit rules: later filing prints expense lines positive
    P = printed_by_label
    it = c["item"]
    if it == 18:
        v = P["투자손익"] - (P["보험금융수익"] + P["재보험금융수익"] - P["보험금융비용"] - P["재보험금융비용"])
    elif it == 16:
        v = P["기타사업비용"]
    else:
        v = P[c["xml_lines"][0]["label"]]
    v /= 1e6
    okv = abs(v - c["new"]) <= 2e-5
    bad += 0 if okv else 1
    out.append(f"   recomputed i{it} = {v} vs plan new {c['new']} -> {'OK' if okv else 'MISMATCH'}")
    op = c["original_print"]
    LO = lines(op["xml_file"])
    lab = c["xml_lines"][0]["label"] if it != 18 else "투자손익"
    base = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자손익"}[it]
    # original print (direct line; item 18 derived from 투자손익 and the finance lines of the original: printed negative expenses)
    w = check(LO, op["xml_file"], op["xml_line"], TAG.sub("", LO[op["xml_line"] - 1]).strip(), base, 1, 4, f"ORIG {c['quarter']} i{it} original cum-current")
    if it == 16:
        okv = abs(-w / 1e6 - c["old"]) <= 2e-5          # original prints the expense negative
    elif it == 18:
        # original: 17 = 64,492.102378; 19 = 61,175.443868 + 1,061.308369 - 260,666.025466 - 2,427.118063
        okv = abs(w / 1e6 - c["old"]) >= 0 and True
        L_ = LO
        fm = {}
        for lbl, ln in (("보험금융수익", 24359), ("재보험금융수익", 24382), ("보험금융비용", 24612), ("재보험금융비용", 24635)):
            fm[lbl] = check(LO, op["xml_file"], ln, TAG.sub("", LO[ln - 1]).strip(), lbl, 1, 4, f"ORIG {c['quarter']} i18 part {lbl}")
        v18 = (w - (fm["보험금융수익"] + fm["재보험금융수익"] + fm["보험금융비용"] + fm["재보험금융비용"])) / 1e6        # original prints expenses negative
        okv = abs(v18 - c["old"]) <= 2e-5
    else:
        okv = abs(w / 1e6 - c["old"]) <= 2e-5
    bad += 0 if okv else 1
    out.append(f"   original recomputed vs master old {c['old']} -> {'OK' if okv else 'MISMATCH'}")

for s in plan["seam_cells"]:
    tp = s["three_month_print"]
    L = lines(tp["xml_file"])
    P = {}
    for p in tp["xml_lines"]:
        P[p["label"]] = check(L, tp["xml_file"], p["line"], p["printed"], p["label"], 2, 4, f"SEAM {s['quarter']} i{s['item']} later 3M-prior")
    it = s["item"]
    if it == 18:
        v = P["투자손익"] - (P["보험금융수익"] + P["재보험금융수익"] - P["보험금융비용"] - P["재보험금융비용"])
    else:
        v = P[tp["xml_lines"][0]["label"]]
    v /= 1e6
    okv = abs(v - s["proposed_value"]) <= 2e-5
    bad += 0 if okv else 1
    out.append(f"   recomputed 3M i{it} = {v} vs proposed {s['proposed_value']} -> {'OK' if okv else 'MISMATCH'}")
    # 9M - 6M cross-check lines: FY2024_Q2 prior cum (4th cell) of the same label
    cc = s["cross_check_9M_minus_6M_both_new_vintage"]
    L2 = lines(cc["fy2024_q2_file"])
    w6 = check(L2, cc["fy2024_q2_file"], cc["fy2024_q2_line"], TAG.sub("", L2[cc["fy2024_q2_line"] - 1]).strip(), tp["xml_lines"][0]["label"] if it != 18 else "투자손익", 3, 4, f"SEAM {s['quarter']} i{it} FY2024_Q2 6M prior cum")
    if it != 18:
        cum9 = [c for c in plan["cells"] if c["item"] == it][0]["new"]
        okx = abs(cum9 - w6 / 1e6 - s["proposed_value"]) <= 2e-5 if it != 16 else abs(cum9 - w6 / 1e6 - s["proposed_value"]) <= 2e-5
        bad += 0 if okx else 1
        out.append(f"   9M(plan) - 6M(Q2 report, L{cc['fy2024_q2_line']}) = {cum9 - w6 / 1e6} vs 3M print -> {'OK' if okx else 'MISMATCH'}")

# set_dangi source strings: every cited 'L<digits> [label] printed원' exists
for cell in plan["apply_contract"]["set_dangi_cells"]:
    for m in re.finditer(r"(?:(data/dart/[^: ]+\.xml):)?L(\d+) \[([^\]]+)\] ([^ ]+)원", cell[4]):
        n += 1
        rel = m.group(1) or "data/dart/FY2024_Q3/raw/KR0082_DB생명보험/20241114001831.xml"
        L = lines(rel)
        txt = TAG.sub("", L[int(m.group(2)) - 1]).strip()
        okx = (txt == m.group(4))
        bad += 0 if okx else 1
        out.append(f"SRC i{cell[2]} L{m.group(2)} {txt!r} vs source string {m.group(4)!r} -> {'OK' if okx else 'MISMATCH'}")

# auto-follow annual prints (2023.4Q): original annual and FY2024 annual prior, 3 value cells: [cur, prior, prior2]
for a in plan["auto_follow_cells"]:
    ac = a["annual_checks"]
    lab = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자손익"}[a["item"]]
    wo = check(lines(plan["buckets"][2]["original_filing"]["file"].replace("FY2023_Q3/raw/KR0082_DB생명보험/20231114002805", "FY2023_Q4/raw/KR0082_DB생명보험_20240329001728/20240329001728")),
               "FY2023_Q4", ac["xml_line_orig"], TAG.sub("", lines("data/dart/FY2023_Q4/raw/KR0082_DB생명보험_20240329001728/20240329001728.xml")[ac["xml_line_orig"] - 1]).strip(), lab, 0, 3, f"ANNUAL i{a['item']} FY2023 report cur")
    LL = lines("data/dart/FY2024_Q4/raw/KR0082_DB생명보험_20250328002241/20250328002241.xml")
    wl = check(LL, "FY2024_Q4", ac["xml_line_later"], TAG.sub("", LL[ac["xml_line_later"] - 1]).strip(), lab, 1, 3, f"ANNUAL i{a['item']} FY2024 report prior")
    te = LL[ac["xml_line_later"] - 2]
    out.append(f"   ctx of the cited FY2024 annual cell: {re.search(r'ACONTEXT=\"([^\"]*)\"', te).group(1) if re.search(r'ACONTEXT=', te) else None}")
    if a["item"] in (1, 17):
        okx = wo is not None and wl is not None and abs(wo - wl) < 1 and abs(wo / 1e6 - ac["master_annual"]) <= 2e-5
        bad += 0 if okx else 1
        out.append(f"   annual i{a['item']} orig={wo} later={wl} master={ac['master_annual']} -> {'OK' if okx else 'MISMATCH'}")

out.append(f"TOTAL line checks {n}, problems {bad}")
(HERE / "KR0082_line_verify.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
plan["verification"]["xml_line_reread"] = dict(script="KR0082_line_verify.py (own parser, position-based column proof; no ACONTEXT in these filings)", n_line_checks=n, n_problems=bad, report="KR0082_line_verify.txt")
(HERE / "plan_KR0082.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(n, bad)
