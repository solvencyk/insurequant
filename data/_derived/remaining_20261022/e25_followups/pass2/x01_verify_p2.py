# -*- coding: utf-8 -*-
"""INDEPENDENT verifier for p2_plan.json (ticket 20261024T0300Z, neighbor stale cells sweep pass 2).
Standard library only: no import of p2lib / the e21 e23 readers / the planner / any scripts/ module.  For every company the table is parsed again from the raw DART file given only the table's first physical line
(taken from the reader JSON that the plan cites), the cited cells are looked up by their physical line number inside that parse, and every planned gold value is recomputed from the re-read cells:
  ABL KR0070        items 5 / 9 / 10 / 11 (+ 6 check), derived 7 = 3-(4+5+6), 12 = 8-(9+10+11); subtotals = row sums; derived 7 / 12 vs the OTHER note rows; roll-forward RA / CSM cross-check
  동양 KR0087       items 5 / 6, derived 7 (cumulative column = last numeric cell of the [3개월, 누적] pair; revenue / cost totals = row sums)
  현대해상 KR0009   items 5 / 9 / 10 (장기 column, 천원 -> 백만원), section row sums = printed 합계
  한화생명 KR0068   items 5 / 6 / 9 / 10 / 11, derived 7 / 12, section sums; the 3-month 합계 column for the planned set_dangi cells
  OCI KR0032 / KR0082  items 25..32 from the separate comprehensive income statement (원): 25 = leaf sum, 31 = 24 + 25
Usage: [P2_BASE=<backup root>] x01_verify_p2.py [--mutate KIND]   (KIND = line | value | column : an injected fault MUST make the run report problems)"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
BASE = os.environ.get("P2_BASE") or ROOT
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass2"
PLAN = json.load(open(f"{EV}/p2_plan.json", encoding="utf-8"))
C = PLAN["apply_contract"]
MUT = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None
TAG = re.compile(r"<[^>]+>")
_cache = {}
problems, ok_count = [], [0]
PLANNED = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
MASTER = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8"))}


def mv(code, item, q):
    r = MASTER.get((code, item, q))
    return None if r is None else r.get("값")


def L(rel):
    if rel not in _cache:
        _cache[rel] = open(f"{ROOT}/{rel}", encoding="utf-8", errors="replace").read().split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ").replace("\xa0", " ")).strip()


def ns(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def parse_num(t):
    t = (t or "").strip().replace(",", "").replace(" ", "")
    if t in ("-", "\u2212"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    try:
        v = float(t.strip("()"))
    except ValueError:
        return None
    return -v if neg else v


def check(cond, msg):
    if cond:
        ok_count[0] += 1
    else:
        problems.append(msg)


def tr_cells(lines, i, j):
    """cells of a TR (0-based first/last physical lines): [dict(text, line, ctx)]"""
    out, k = [], i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", lines[k], re.I)
        if m:
            ctx = re.search(r'ACONTEXT="([^"]*)"', m.group(2))
            rest = m.group(3)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append(dict(text=clean(rest), line=k + 1, ctx=ctx.group(1) if ctx else ""))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", lines[q], re.I):
                    t = clean(lines[q])
                    if t:
                        buf.append(t)
                        tl = tl or (q + 1)
                    q += 1
                out.append(dict(text=" ".join(buf).strip(), line=tl or (k + 1), ctx=ctx.group(1) if ctx else ""))
                k = q
        k += 1
    return out


def table_rows(rel, start):
    """all rows of the <TABLE> that starts at physical line `start` (1-based): [dict(tr, label, key, cells, nums)]; nums = numeric cells after the label cell(s) as (value, line, text, ctx)"""
    lines = L(rel)
    i = start - 1
    assert re.match(r"\s*<TABLE\b", lines[i], re.I), f"{rel} L{start} is not a <TABLE> line: {lines[i][:60]!r}"
    j = i
    while j < len(lines) and not re.match(r"\s*</TABLE", lines[j], re.I):
        j += 1
    rows, k = [], i
    while k < j:
        if re.match(r"\s*<TR\b", lines[k], re.I):
            e = k
            while e < j and not re.match(r"\s*</TR", lines[e], re.I):
                e += 1
            cells = tr_cells(lines, k, e)
            lab_cells = [c for c in cells if re.search(r"[가-힣A-Za-z]", c["text"]) and parse_num(c["text"]) is None]
            nums = [(parse_num(c["text"]), c["line"], c["text"], c["ctx"]) for c in cells if parse_num(c["text"]) is not None and not re.search(r"[가-힣A-Za-z]", c["text"]) and c["text"].strip() != ""]
            rows.append(dict(tr=k + 1, label=(lab_cells[0]["text"] if lab_cells else ""), key=ns(" ".join(c["text"] for c in lab_cells[:2])), key1=ns(lab_cells[0]["text"]) if lab_cells else "", nlab=len(lab_cells), cells=cells, nums=nums))
            k = e
        k += 1
    return rows, (i + 1, j + 1)


def unit_of(rel, tstart):
    lines = L(rel)
    for k in range(tstart - 1, max(tstart - 2500, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", lines[k]))
        if m:
            return m.group(1)
    return None


def mut_line(ln):
    return ln + 2 if MUT == "line" else ln


def cited(rows, line, text, what):
    """the cited physical line must hold exactly this printed text as a numeric cell of the parsed table"""
    ln = mut_line(line)
    hit = [n for r in rows for n in r["nums"] if n[1] == ln]
    check(len(hit) == 1 and hit[0][2] == text, f"{what}: cited L{line} text {text!r} not found as a numeric cell (found {[h[2] for h in hit]})")
    return hit[0] if hit else None


def pcol(n_cols):
    return n_cols - 1


# ------------------------------------------------------------------------------------------------------------------ A. ABL KR0070
def walk_abl(rows):
    sec, d, tail = None, {}, {}
    for r in rows:
        k1 = r["key1"]
        if k1 in ("보험수익", "재보험수익", "보험서비스비용", "재보험비용") and not r["nums"]:
            sec = k1
            d.setdefault(sec, {})
            continue
        if sec is None or not r["nums"]:
            continue
        if k1 in ("기타사업비용", "합계"):
            tail.setdefault(k1, r)
            continue
        d[sec].setdefault(k1, r)
    return d


def verify_abl():
    abl = json.load(open(f"{EV}/kr0070_abl/r03_abl_read.json", encoding="utf-8"))
    for q, rec in abl.items():
        rel = rec["file"]
        rev_rows, _ = table_rows(rel, rec["rev_table"])
        cost_rows, _ = table_rows(rel, rec["cost_table"])
        check(unit_of(rel, rec["rev_table"]) == "백만원" and unit_of(rel, rec["cost_table"]) == "백만원", f"ABL {q}: unit")
        rv, cv = walk_abl(rev_rows), walk_abl(cost_rows)
        n_cols = len(rv["보험수익"]["예상보험금"]["nums"])
        check(n_cols in (2, 4), f"ABL {q}: numeric columns {n_cols}")
        col = pcol(n_cols) if MUT != "column" else n_cols - 2
        # header: the prior-period column header words
        hdr = ns(" ".join(c["text"] for r in rev_rows[:6] for c in r["cells"]))
        check(("전분기" in hdr or "전반기" in hdr or "전기" in hdr) and ("당분기" in hdr or "당반기" in hdr or "당기" in hdr), f"ABL {q}: header words {hdr[:60]!r}")
        check(hdr.find("당") < hdr.find("전"), f"ABL {q}: current period column must come before the prior one")

        def cv_(d, lab):
            r = d[lab]
            n = r["nums"][col]
            return n[0], n[1], n[2]
        # cited cells (plan JSON) must be the cells at those physical lines
        for sec_key, d_, jd in (("rev", rv["보험수익"], rec["prior_cum"]["rev"]), ("re_rev", rv["재보험수익"], rec["prior_cum"]["re_rev"]), ("cost", cv["보험서비스비용"], rec["prior_cum"]["cost"]), ("re_cost", cv["재보험비용"], rec["prior_cum"]["re_cost"])):
            rr_ = rev_rows if sec_key in ("rev", "re_rev") else cost_rows
            for lab, c in jd.items():
                h = cited(rr_, c["line"], c["text"], f"ABL {q} {sec_key}/{lab}")
                if h:
                    check(abs(h[0] - c["v"]) < 1e-9, f"ABL {q} {sec_key}/{lab}: value {h[0]} != json {c['v']}")
                    check(h[1] == d_[lab]["nums"][col][1], f"ABL {q} {sec_key}/{lab}: cited line is not in the prior-period column")
        R, RR, Cc, RC = rv["보험수익"], rv["재보험수익"], cv["보험서비스비용"], cv["재보험비용"]
        g = lambda d, lab: (cv_(d, lab)[0] if lab in d else 0.0)  # noqa: E731
        i5 = abs(g(R, "위험조정변동"))
        i4 = abs(g(R, "보험계약마진상각"))
        exp4 = sum(g(R, k) for k in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비"))
        inc4 = sum(g(Cc, k) for k in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비"))
        i6 = exp4 - inc4
        i9 = -abs(g(RC, "보험계약마진상각"))
        i10 = -abs(g(RC, "위험조정변동"))
        i11 = sum(g(RR, k) for k in ("발생재보험금", "발생손해조사비")) - sum(g(RC, k) for k in ("예상재보험금", "예상손해조사비"))
        if MUT == "value":
            i5 += 1
        # subtotals
        for nm, d_ in (("보험수익", R), ("재보험수익", RR), ("보험서비스비용", Cc), ("재보험비용", RC)):
            s = sum(g(d_, k) for k in d_ if k != "소계")
            check(abs(s - g(d_, "소계")) <= 1.5, f"ABL {q}: {nm} rows {s} != 소계 {g(d_, '소계')}")
        # planned values
        for itm, v in ((5, i5), (9, i9), (10, i10), (11, i11)):
            e = PLANNED.get(("KR0070", itm, q))
            if e is not None:
                check(abs(e["value"] - v) < 5e-7, f"ABL {q} item {itm}: planned {e['value']} != re-read {v}")
            else:
                cur = mv("KR0070", itm, q)
                check(cur is not None and abs(cur - v) < 5e-7, f"ABL {q} item {itm}: no planned cell and master {cur} != re-read {v}")
        check(abs(mv("KR0070", 6, q) - i6) < 5e-7, f"ABL {q} item 6: master {mv('KR0070', 6, q)} != re-read {i6}")
        m3, m4, m8 = mv("KR0070", 3, q), mv("KR0070", 4, q), mv("KR0070", 8, q)
        check(abs(m4 - i4) < 5e-7, f"ABL {q} item 4: master {m4} != note {i4}")
        i7 = m3 - (m4 + i5 + i6)
        i12 = m8 - (i9 + i10 + i11)
        for itm, v in ((7, i7), (12, i12)):
            e = PLANNED.get(("KR0070", itm, q))
            if e is not None:
                check(abs(e["value"] - v) < 5e-7, f"ABL {q} item {itm}: planned {e['value']} != derived {v}")
        # closure against the other note rows
        o7 = sum(g(R, k) for k in R if k not in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비", "위험조정변동", "보험계약마진상각", "소계")) - sum(g(Cc, k) for k in Cc if k not in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비", "소계"))
        o12 = sum(g(RR, k) for k in RR if k not in ("발생재보험금", "발생손해조사비", "소계")) - sum(g(RC, k) for k in RC if k not in ("예상재보험금", "예상손해조사비", "위험조정변동", "보험계약마진상각", "소계"))
        check(abs(i7 - o7) <= 1.5, f"ABL {q}: derived 7 {i7} vs other rows {o7}")
        check(abs(i12 - o12) <= 1.5, f"ABL {q}: derived 12 {i12} vs other rows {o12}")
        # 3 / 8 of the master vs note subtotals
        check(abs(m3 - (g(R, "소계") - g(Cc, "소계"))) <= 1.5, f"ABL {q}: master 3 vs note")
        check(abs(m8 - (g(RR, "소계") - g(RC, "소계"))) <= 1.5, f"ABL {q}: master 8 vs note")
        # roll-forward cross-check (cells re-read by physical line)
        for key, want in (("ins_ra_release", abs(i5)), ("rein_ra_release", abs(i10)), ("rein_csm_release", abs(i9) if q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q") else None)):
            c = rec["rollforward_prior"].get(key)
            if c is None or want is None:
                continue
            lines = L(rel)
            m = re.search(r">\s*([\(\)\d,\-]+)\s*<", lines[c["line"] - 1] + "<")
            v = parse_num(clean(lines[c["line"] - 1])) if m else None
            check(v is not None and abs(abs(v) - want) <= 1.5, f"ABL {q}: roll-forward {key} L{c['line']} {c['text']} vs {want}")
        print(f"  ABL {q}: 5={i5:.0f} 9={i9:.0f} 10={i10:.0f} 11={i11:.0f} | 7={i7:.3f} (other rows {o7:.0f}) 12={i12:.3f} (other rows {o12:.0f})")
        # printed 3-month column for the single-quarter seam (Q2/Q3 filings)
        if n_cols == 4:
            def c3(d_, lab):
                return d_[lab]["nums"][2][0]
            prev = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q", "2024.2Q": "2024.1Q", "2024.3Q": "2024.2Q", "2025.2Q": "2025.1Q"}[q]
            for itm, v3 in ((5, abs(c3(R, "위험조정변동"))), (10, -abs(c3(RC, "위험조정변동"))), (9, -abs(c3(RC, "보험계약마진상각")))):
                cur = PLANNED.get(("KR0070", itm, q), {}).get("value", mv("KR0070", itm, q))
                pv = PLANNED.get(("KR0070", itm, prev), {}).get("value", mv("KR0070", itm, prev))
                if cur is not None and pv is not None:
                    check(abs((cur - pv) - v3) <= 1.0, f"ABL {q} item {itm}: single quarter {cur - pv} vs printed 3M {v3}")


# ------------------------------------------------------------------------------------------------------------------ B. 동양 KR0087
def verify_dy():
    dy = json.load(open(f"{EV}/kr0087_dongyang/r01_dy_read.json", encoding="utf-8"))
    for q, rec in dy.items():
        rel = rec["file"]
        rev_rows, _ = table_rows(rel, rec["rev_table"])
        cost_rows, _ = table_rows(rel, rec["cost_table"])
        check(unit_of(rel, rec["rev_table"]) == "백만원", f"동양 {q}: unit")

        def rowby(rows, needle, nth=1, excl=()):
            hit = [r for r in rows if needle in r["key"] and not any(e in r["key"] for e in excl) and len(r["nums"]) >= 2]
            return hit[nth - 1]
        cumi = -1 if MUT != "column" else -2
        ra, csm = rowby(rev_rows, "위험조정"), rowby(rev_rows, "보험계약마진")
        exp = rowby(rev_rows, "예상" + ("발생보험금" if q == "2024.2Q" else "보험금"), excl=("기타",))
        exp2 = rowby(rev_rows, "예상기타보험서비스비용")
        acq = rowby(rev_rows, "취득현금흐름")
        loss = rowby(rev_rows, "손실요소")
        tot_rev = [r for r in rev_rows if r["key1"] == "보험수익" and r["nlab"] == 1 and len(r["nums"]) == 2][0] if q == "2024.2Q" else [r for r in rev_rows if r["key"] == "보험수익" and len(r["nums"]) == 2][-1]
        cells = {"ra": ra, "csm": csm, "exp": exp}
        for nm, r in cells.items():
            j = rec["rev_rows"][nm]["cum"]
            h = cited(rev_rows, j["line"], j["text"], f"동양 {q} {nm}")
            check(r["nums"][cumi][1] == mut_line(j["line"]) or MUT in ("line", "column"), f"동양 {q} {nm}: cited cell is not the last (누적) numeric cell of its row")
            if q == "2024.3Q":
                check("PFY2024" in r["nums"][-1][3] and "SeparateMember" in r["nums"][-1][3] and r["nums"][-1][3].split("_")[0].endswith("TQA"), f"동양 {q} {nm}: ACONTEXT {r['nums'][-1][3][:60]!r}")
        # cost side
        if q == "2024.2Q":
            act = rowby(cost_rows, "실제발생보험금", excl=("기타",))
            others = [rowby(cost_rows, "실제기타보험서비스비용"), rowby(cost_rows, "손실부담계약인식및환입"), rowby(cost_rows, "발생사고부채변동"), rowby(cost_rows, "보험취득현금흐름상각"), rowby(cost_rows, "손실요소배분액"), [r for r in cost_rows if (r["key"].endswith("기타") or r["key"] == "기타") and len(r["nums"]) >= 2][-1]]
            tot_cost = [r for r in cost_rows if r["key1"] == "발행한보험계약에서생기는보험서비스비용" and r["nlab"] == 1 and len(r["nums"]) == 2][0]
        else:
            act = rowby(cost_rows, "보험서비스비용,발생한보험금")
            others = [rowby(cost_rows, "그밖의발생한보험서비스비용"), rowby(cost_rows, "미래서비스와관련된변동분"), rowby(cost_rows, "과거서비스와관련된금액"), rowby(cost_rows, "보험취득현금흐름의상각"), rowby(cost_rows, "손실요소배분액"), rowby(cost_rows, "기타영업비용")]
            tot_cost = [r for r in cost_rows if r["key"] == "발행한보험계약에서생기는보험서비스비용"][0]
        j = rec["cost_rows"]["act"]["cum"]
        cited(cost_rows, j["line"], j["text"], f"동양 {q} act")
        cum = lambda r: r["nums"][cumi][0]  # noqa: E731
        m3 = lambda r: r["nums"][-2][0]  # noqa: E731
        v5, v4 = abs(cum(ra)), abs(cum(csm))
        v6 = abs(cum(exp)) - abs(cum(act))
        if MUT == "value":
            v5 += 1
        for itm, v in ((5, v5), (6, v6)):
            e = PLANNED[("KR0087", itm, q)]
            check(abs(e["value"] - v) < 5e-7, f"동양 {q} item {itm}: planned {e['value']} != re-read {v}")
        check(abs(mv("KR0087", 4, q) - v4) < 5e-7, f"동양 {q} item 4: master {mv('KR0087', 4, q)} != note {v4}")
        s_rev = sum(cum(r) for r in (exp, exp2, ra, csm, acq, loss))
        s_cost = sum(cum(r) for r in [act] + others)
        check(abs(s_rev - cum(tot_rev)) <= 1.5, f"동양 {q}: revenue rows {s_rev} vs total {cum(tot_rev)}")
        check(abs(s_cost - cum(tot_cost)) <= 1.5, f"동양 {q}: cost rows {s_cost} vs total {cum(tot_cost)}")
        m3_, m4_ = mv("KR0087", 3, q), mv("KR0087", 4, q)
        check(abs(m3_ - (cum(tot_rev) - cum(tot_cost))) <= 1.5, f"동양 {q}: master 3 {m3_} vs note {cum(tot_rev) - cum(tot_cost)}")
        i7 = m3_ - (m4_ + v5 + v6)
        e7 = PLANNED[("KR0087", 7, q)]
        check(abs(e7["value"] - i7) < 5e-7, f"동양 {q} item 7: planned {e7['value']} != derived {i7}")
        o7 = sum(cum(r) for r in (exp2, acq, loss)) - sum(cum(r) for r in others)
        check(abs(i7 - o7) <= 1.5, f"동양 {q}: derived 7 {i7} vs other rows {o7}")
        # single quarter vs printed 3 months
        prev = "2024.1Q" if q == "2024.2Q" else "2024.2Q"
        pv5 = mv("KR0087", 5, prev) if prev == "2024.1Q" else PLANNED[("KR0087", 5, prev)]["value"]
        pv6 = mv("KR0087", 6, prev) if prev == "2024.1Q" else PLANNED[("KR0087", 6, prev)]["value"]
        check(abs((v5 - pv5) - abs(m3(ra))) <= 1.0, f"동양 {q} item 5: single {v5 - pv5} vs printed 3M {abs(m3(ra))}")
        check(abs((v6 - pv6) - (abs(m3(exp)) - abs(m3(act)))) <= 1.0, f"동양 {q} item 6: single {v6 - pv6} vs printed 3M {abs(m3(exp)) - abs(m3(act))}")
        print(f"  동양 {q}: 5={v5:.0f} 6={v6:.0f} 7={i7:.6f} (other rows {o7:.0f}); revenue rows {s_rev:.0f}={cum(tot_rev):.0f}; cost rows {s_cost:.0f}={cum(tot_cost):.0f}")


# ------------------------------------------------------------------------------------------------------------------ C. 현대해상 KR0009
def verify_hd():
    hd = json.load(open(f"{EV}/kr0009_hyundai/r01_hd_read.json", encoding="utf-8"))
    for q, rec in hd.items():
        rel = rec["file"]
        rows, _ = table_rows(rel, rec["table"])
        check(unit_of(rel, rec["table"]) == "천원", f"현대해상 {q}: unit")
        hdr = ns(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        check(hdr.startswith("구분장기자동차일반합계"), f"현대해상 {q}: header {hdr[:30]!r}")
        sec, d = None, {}
        for r in rows:
            if r["key1"] in ("보험수익", "재보험서비스비용") and not any(n[2] != "" for n in r["nums"]):
                sec = r["key1"]
                d.setdefault(sec, {})
                continue
            if sec and r["nums"]:
                d[sec].setdefault(r["key1"], r)
        jcol = 0 if MUT != "column" else 1
        R, RC = d["보험수익"], d["재보험서비스비용"]
        v5 = abs(R["위험조정변동"]["nums"][jcol][0]) / 1000.0
        v4 = abs(R["보험계약마진상각"]["nums"][jcol][0]) / 1000.0
        v9 = -abs(RC["보험계약마진상각"]["nums"][jcol][0]) / 1000.0
        v10 = -abs(RC["위험조정변동"]["nums"][jcol][0]) / 1000.0
        if MUT == "value":
            v5 += 1
        for nm, lab, sec_ in (("4", "보험계약마진상각", R), ("5", "위험조정변동", R), ("9", "보험계약마진상각", RC), ("10", "위험조정변동", RC)):
            j = rec["items_raw"][nm]
            cited(rows, j["line"], j["text"], f"현대해상 {q} item {nm}")
            check(sec_[lab]["nums"][0][1] == mut_line(j["line"]) or MUT in ("line", "column"), f"현대해상 {q} item {nm}: cited cell is not the 장기 column")
        for itm, v in ((5, v5), (9, v9), (10, v10)):
            e = PLANNED.get(("KR0009", itm, q))
            if e is not None:
                check(abs(e["value"] - v) < 5e-7, f"현대해상 {q} item {itm}: planned {e['value']} != re-read {v}")
            else:
                check(abs(mv("KR0009", itm, q) - v) < 5e-7, f"현대해상 {q} item {itm}: not planned and master {mv('KR0009', itm, q)} != re-read {v}")
        check(abs(mv("KR0009", 4, q) - v4) < 5e-7, f"현대해상 {q} item 4: master {mv('KR0009', 4, q)} != note {v4}")
        s_rev = sum(x["nums"][0][0] for k, x in R.items() if k != "합계")
        s_re = sum(x["nums"][0][0] for k, x in RC.items() if k != "합계")
        check(abs(s_rev - R["합계"]["nums"][0][0]) <= 2, f"현대해상 {q}: 보험수익 장기 rows {s_rev} vs 합계 {R['합계']['nums'][0][0]}")
        check(abs(s_re - RC["합계"]["nums"][0][0]) <= 2, f"현대해상 {q}: 재보험 장기 rows {s_re} vs 합계 {RC['합계']['nums'][0][0]}")
        print(f"  현대해상 {q}: 5={v5:.3f} 9={v9:.3f} 10={v10:.3f}; rows sum {s_rev:,.0f}={R['합계']['nums'][0][0]:,.0f}, {s_re:,.0f}={RC['합계']['nums'][0][0]:,.0f} (천원)")
        if "three_month" in rec and q in ("2023.2Q", "2023.3Q"):
            tm = rec["three_month"][0]
            rows3, _ = table_rows(rel, tm["table"])
            sec, d3 = None, {}
            for r in rows3:
                if r["key1"] in ("보험수익", "재보험서비스비용") and not any(n[2] != "" for n in r["nums"]):
                    sec = r["key1"]
                    d3.setdefault(sec, {})
                    continue
                if sec and r["nums"]:
                    d3[sec].setdefault(r["key1"], r)
            prev = "2023.1Q" if q == "2023.2Q" else "2023.2Q"
            pv = {5: PLANNED[("KR0009", 5, prev)]["value"] if ("KR0009", 5, prev) in PLANNED else mv("KR0009", 5, prev),
                  9: PLANNED[("KR0009", 9, prev)]["value"] if ("KR0009", 9, prev) in PLANNED else mv("KR0009", 9, prev),
                  10: PLANNED[("KR0009", 10, prev)]["value"] if ("KR0009", 10, prev) in PLANNED else mv("KR0009", 10, prev)}
            m3 = {5: abs(d3["보험수익"]["위험조정변동"]["nums"][0][0]) / 1000.0, 9: -abs(d3["재보험서비스비용"]["보험계약마진상각"]["nums"][0][0]) / 1000.0, 10: -abs(d3["재보험서비스비용"]["위험조정변동"]["nums"][0][0]) / 1000.0}
            for itm, cur in ((5, v5), (9, v9), (10, v10)):
                check(abs((cur - pv[itm]) - m3[itm]) <= 0.002, f"현대해상 {q} item {itm}: single {cur - pv[itm]} vs printed 3M {m3[itm]}")


# ------------------------------------------------------------------------------------------------------------------ D. 한화생명 KR0068
def verify_hw():
    hw = json.load(open(f"{EV}/kr0068_hanwha/r02_hw_read.json", encoding="utf-8"))
    for q, rec in hw.items():
        rel = rec["file"]
        rows, _ = table_rows(rel, rec["table"])
        check(unit_of(rel, rec["table"]) == "백만원", f"한화생명 {q}: unit")
        hdr = ns(" ".join(c["text"] for r in rows[:4] for c in r["cells"]))
        pair = "3개월누적" in hdr
        check(pair == rec["pair"], f"한화생명 {q}: pair columns {pair} vs json {rec['pair']}")
        sec, out = None, []
        for r in rows:
            k = r["key1"]
            if k.startswith("1.보험수익"):
                sec = "rev"
            elif k.startswith("2.보험서비스비용"):
                sec = "cost"
            elif k.startswith("3.재보험수익"):
                sec = "re_rev"
            elif k.startswith("4.재보험비용"):
                sec = "re_cost"
            elif k.startswith("총보험서비스결과"):
                sec = "tail"
            if not r["nums"] or sec in (None, "tail"):
                continue
            ci = -1 if MUT != "column" else -2
            out.append(dict(sec=sec, norm=re.sub(r"^[0-9\)\(\.]+", "", k), cum=r["nums"][ci], m3=(r["nums"][-2] if pair and len(r["nums"]) >= 2 else None), row=r))

        def f(sec, needle):
            h = [x for x in out if x["sec"] == sec and needle in x["norm"]]
            return h[0]
        csm = f("rev", "서비스제공에따른보험계약마진의변동"); ra = f("rev", "위험해제에따른위험조정의변동"); exp = f("rev", "예상보험금및예상보험서비스비용"); cact = f("cost", "실제보험금및실제보험서비스비용")
        has_re = any(x["sec"] == "re_rev" for x in out)
        for nm, x in dict(csm=csm, ra=ra, exp=exp, cact=cact).items():
            j = rec["rows"][nm]["cum"]
            cited(rows, j["line"], j["text"], f"한화생명 {q} {nm}")
            check(x["cum"][1] == mut_line(j["line"]) or MUT in ("line", "column"), f"한화생명 {q} {nm}: cited cell is not the 합계(누적) cell (last numeric)")
        a = lambda x: abs(x["cum"][0])  # noqa: E731
        v5 = a(ra)
        v6 = a(exp) - a(cact)
        if MUT == "value":
            v5 += 1
        vals = {5: v5, 6: v6}
        if has_re:
            ract, rexp, rera, recsm = f("re_rev", "발생재보험금및재보험서비스비용회수액"), f("re_cost", "회수예상보험금및보험서비스비용"), f("re_cost", "위험해제로인한위험조정의변동"), f("re_cost", "제공받은서비스의재보험계약마진")
            for nm, x in dict(ract=ract, rexp=rexp, rera=rera, recsm=recsm).items():
                j = rec["rows"][nm]["cum"]
                cited(rows, j["line"], j["text"], f"한화생명 {q} {nm}")
            vals.update({9: -a(recsm), 10: -a(rera), 11: a(ract) - a(rexp)})
        for itm, v in vals.items():
            e = PLANNED.get(("KR0068", itm, q))
            if e is not None:
                check(abs(e["value"] - v) < 5e-7, f"한화생명 {q} item {itm}: planned {e['value']} != re-read {v}")
            else:
                cur = mv("KR0068", itm, q)
                check(cur is not None and abs(cur - v) < 5e-7, f"한화생명 {q} item {itm}: no planned cell and master {cur} != re-read {v}")
        # section sums
        for s_ in ("rev", "cost", "re_rev", "re_cost"):
            rs = [x for x in out if x["sec"] == s_]
            if not rs:
                continue
            lead = sum(x["cum"][0] for x in rs if not x["norm"].startswith(("소계", "총", "보험료배분접근법적용계약")))
            sub = [x for x in rs if x["norm"] == "소계"][0]["cum"][0]
            paa = sum(x["cum"][0] for x in rs if x["norm"].startswith("보험료배분접근법적용계약"))
            tot = [x for x in rs if x["norm"].startswith("총")][0]["cum"][0]
            check(abs(lead - sub) <= 2 and abs(sub + paa - tot) <= 2, f"한화생명 {q} {s_}: rows {lead} sub {sub} paa {paa} total {tot}")
        m3_, m4_, m8_ = mv("KR0068", 3, q), mv("KR0068", 4, q), mv("KR0068", 8, q)
        check(abs(m4_ - a(csm)) < 5e-7, f"한화생명 {q} item 4: master {m4_} != note {a(csm)}")
        rev_tot = [x for x in out if x["sec"] == "rev" and x["norm"].startswith("총")][0]["cum"][0]
        cost_tot = [x for x in out if x["sec"] == "cost" and x["norm"].startswith("총")][0]["cum"][0]
        i3_note = rev_tot - cost_tot
        i7 = m3_ - (m4_ + v5 + v6)
        e7 = PLANNED[("KR0068", 7, q)]
        check(abs(e7["value"] - i7) < 5e-7, f"한화생명 {q} item 7: planned {e7['value']} != derived {i7}")
        o7 = sum(x["cum"][0] for x in out if x["sec"] == "rev" and x is not csm and x is not ra and x is not exp and x["norm"] != "소계" and not x["norm"].startswith("총")) - \
            sum(x["cum"][0] for x in out if x["sec"] == "cost" and x is not cact and x["norm"] != "소계" and not x["norm"].startswith("총"))
        check(abs(i7 - o7) <= abs(m3_ - i3_note) + 1.5, f"한화생명 {q}: derived 7 {i7} vs other rows {o7} (item-3 statement/note gap {m3_ - i3_note:.3f})")
        if has_re:
            i12 = m8_ - (vals[9] + vals[10] + vals[11])
            e12 = PLANNED.get(("KR0068", 12, q))
            if e12 is not None:
                check(abs(e12["value"] - i12) < 5e-7, f"한화생명 {q} item 12: planned {e12['value']} != derived {i12}")
            else:
                check(abs(mv("KR0068", 12, q) - i12) < 5e-7, f"한화생명 {q} item 12: master {mv('KR0068', 12, q)} != derived {i12} and no planned cell")
            o12 = sum(x["cum"][0] for x in out if x["sec"] == "re_rev" and x is not ract and x["norm"] != "소계" and not x["norm"].startswith("총")) - \
                sum(x["cum"][0] for x in out if x["sec"] == "re_cost" and x not in (rexp, rera, recsm) and x["norm"] != "소계" and not x["norm"].startswith("총"))
            check(abs(i12 - o12) <= 1.5, f"한화생명 {q}: derived 12 {i12} vs other rows {o12}")
        print(f"  한화생명 {q}: " + " ".join(f"{k}={v:.0f}" for k, v in vals.items()) + f" | 7={i7:.3f} (other rows {o7:.0f})")
        if pair:
            prev = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q"}[q]
            m3v = {5: a3(ra), 6: a3(exp) - a3(cact)} if False else None
            a3 = lambda x: abs(x["m3"][0])  # noqa: E731
            m3d = {5: a3(ra), 6: a3(exp) - a3(cact)}
            if has_re:
                m3d.update({9: -a3(recsm), 10: -a3(rera), 11: a3(ract) - a3(rexp)})
            for itm, v3 in m3d.items():
                cur = vals[itm]
                pvv = PLANNED[("KR0068", itm, prev)]["value"] if ("KR0068", itm, prev) in PLANNED else mv("KR0068", itm, prev)
                single = cur - pvv
                sd = [x for x in C["set_dangi_add"] if x[0] == "KR0068" and x[1] == q and x[2] == itm]
                if sd:
                    check(abs(sd[0][3] - v3) < 5e-7, f"한화생명 {q} item {itm}: set_dangi {sd[0][3]} != printed 3M {v3}")
                    check(abs(single - v3) > 1.0, f"한화생명 {q} item {itm}: set_dangi planned but single quarter {single} already equals printed 3M {v3}")
                else:
                    check(abs(single - v3) <= 1.0, f"한화생명 {q} item {itm}: single quarter {single} vs printed 3M {v3} (no set_dangi planned)")
            if q == "2023.2Q":
                sd7 = [x for x in C["set_dangi_add"] if x[0] == "KR0068" and x[1] == q and x[2] == 7][0]
                i3s = mv("KR0068", 3, q) - mv("KR0068", 3, prev)
                i4s = mv("KR0068", 4, q) - mv("KR0068", 4, prev)
                exp7 = i3s - i4s - m3d[5] - m3d[6]
                check(abs(sd7[3] - exp7) < 5e-6, f"한화생명 {q} item 7: set_dangi {sd7[3]} != 3 single - 4 single - printed 3M(5,6) = {exp7}")
                o73 = sum(x["m3"][0] for x in out if x["sec"] == "rev" and x is not csm and x is not ra and x is not exp and x["norm"] != "소계" and not x["norm"].startswith("총")) - \
                    sum(x["m3"][0] for x in out if x["sec"] == "cost" and x is not cact and x["norm"] != "소계" and not x["norm"].startswith("총"))
                check(abs(sd7[3] - o73) <= 2.5, f"한화생명 {q} item 7: set_dangi {sd7[3]} vs 3-month other rows {o73}")


# ------------------------------------------------------------------------------------------------------------------ E. OCI KR0032 / KR0082
def classify(lab, sect):
    n = ns(lab)
    if "신용손실" in n or "손상충당금" in n or "대손충당금" in n:
        return 32
    if "위험회피" in n:
        return 28
    if "재보험" in n and "금융" in n:
        return 30
    if ("보험계약" in n or "보험금융" in n) and "금융" in n:
        return 27
    if "공정가치측정" in n:
        if "채무증권" in n or "채무상품" in n:
            return 26
        if "지분증권" in n or "지분상품" in n:
            return 29
        return 26 if sect == "R" else (29 if sect == "N" else 26)
    return 32


def verify_oci():
    oci = json.load(open(f"{EV}/oci_read.json", encoding="utf-8"))
    for key, o in oci.items():
        code, q = key.split("|")
        if (code, 25, q) not in PLANNED:
            print(f"  OCI {key}: held (not planned) - skipped")
            continue
        rel = o["file"]
        rows, _ = table_rows(rel, o["table"])
        check(unit_of(rel, o["table"]) == "원", f"OCI {key}: unit")
        labs = [r["key1"] for r in rows]
        i25 = next(i for i, k in enumerate(labs) if k.endswith("기타포괄손익") or k == "기타포괄손익")
        i31 = next(i for i, k in enumerate(labs) if i > i25 and "총포괄손익" in k)
        ci = -1 if MUT != "column" else -2
        r24 = [r for r in rows if re.search(r"(당기|반기|분기)순이익", r["key1"]) and "조정" not in r["key1"] and "귀속" not in r["key1"] and "주당" not in r["key1"]][0]
        cited(rows, o["i25"]["line"], o["i25"]["text"], f"OCI {key} 25")
        cited(rows, o["i31"]["line"], o["i31"]["text"], f"OCI {key} 31")
        check(rows[i25]["nums"][ci][1] == mut_line(o["i25"]["line"]) or MUT in ("line", "column"), f"OCI {key}: item 25 cell is not the prior-period cumulative (last numeric) cell")
        v25, v31, v24 = rows[i25]["nums"][ci][0], rows[i31]["nums"][ci][0], r24["nums"][ci][0]
        check(abs(v31 - (v24 + v25)) < 1, f"OCI {key}: 31 != 24 + 25 ({v31} vs {v24 + v25})")
        sect, vals = None, {26: 0.0, 27: 0.0, 28: 0.0, 29: 0.0, 30: 0.0, 32: 0.0}
        for r in rows[i25 + 1:i31]:
            k = r["key1"]
            if "재분류되지않는" in k or "재분류되지아니하는" in k:
                sect = "N"
                continue
            if "재분류될수있는" in k or "재분류되는" in k:
                sect = "R"
                continue
            if not r["nums"]:
                continue
            vals[classify(r["label"], sect)] += r["nums"][ci][0]
        check(abs(v25 - sum(vals.values())) < 1, f"OCI {key}: 25 {v25} != leaf sum {sum(vals.values())}")
        exp_ = {25: v25 / 1e6, 31: v31 / 1e6, **{k: v / 1e6 for k, v in vals.items()}}
        if MUT == "value":
            exp_[26] += 1
        for itm, v in exp_.items():
            e = PLANNED[(code, itm, q)]
            check(abs(e["value"] - round(v, 6)) < 5e-7, f"OCI {key} item {itm}: planned {e['value']} != re-read {v}")
        check(abs(mv(code, 24, q) - v24 / 1e6) <= 0.3, f"OCI {key}: master item 24 {mv(code, 24, q)} vs printed {v24 / 1e6}")
        print(f"  OCI {key}: 25={v25 / 1e6:.6f} 31={v31 / 1e6:.6f} leaf sum {sum(vals.values()) / 1e6:.6f}; master 24 {mv(code, 24, q)} vs printed {v24 / 1e6:.6f}")


# ------------------------------------------------------------------------------------------------------------------ F. plan-level hygiene
def verify_plan():
    keys = [(e["code"], e["item"], e["quarter"]) for e in C["gold_new"] + C["gold_replace"]]
    check(len(keys) == len(set(keys)), "duplicate planned cells")
    gold = json.load(open(f"{BASE}/data/_gold/user_pl_cells.json", encoding="utf-8"))
    gb = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    for e in C["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        check(k not in gb, f"gold_new {k}: gold entry already exists")
        r = MASTER.get(k)
        check(r is not None and ((r["값"] is None and e["was"] is None) or (r["값"] is not None and e["was"] is not None and abs(r["값"] - e["was"]) < 5e-4)), f"gold_new {k}: was {e['was']} != master {None if r is None else r['값']}")
    for e in C["gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        check(k in gb and gb[k] == e["old_entry"], f"gold_replace {k}: old entry moved")
    check(len(C["null_dangi_add"]) == 2 and all(x[0] == "KR0070" and x[1] == "2025.3Q" for x in C["null_dangi_add"]), "null_dangi_add must be the two ABL 2025.3Q seam cells")
    print(f"  plan: {len(C['gold_new'])} new + {len(C['gold_replace'])} replaced gold cells, null_dangi +{len(C['null_dangi_add'])}, set_dangi +{len(C['set_dangi_add'])}")


for name, fn in (("ABL", verify_abl), ("동양", verify_dy), ("현대해상", verify_hd), ("한화생명", verify_hw), ("OCI", verify_oci), ("plan", verify_plan)):
    print(f"== {name}")
    try:
        fn()
    except Exception as ex:  # a crash is a problem, not a pass
        import traceback
        problems.append(f"{name}: crashed {ex!r}")
        traceback.print_exc()
print(f"\nchecks passed: {ok_count[0]}; problems: {len(problems)}")
for p in problems[:60]:
    print("  PROBLEM:", p)
sys.exit(1 if problems else 0)
