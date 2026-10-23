# -*- coding: utf-8 -*-
"""INDEPENDENT verifier for e25_plan.json (tickets 20261023T1130Z KB라이프 / 20261023T1210Z ABL / 20261023T0600Z 농협생명 / 20261024T0100Z KB손해보험).
Standard library only: no import of the planner, the e21 / e23 readers, or any scripts/ module.  Every planned PL gold cell is re-read from the physical xml line numbers cited by the plan:
  - the number printed in the cell at that line (text -> value, parentheses = negative, '-' = 0), the unit of the table (원 / 백만원),
  - the label of the row (first cell with letters of the enclosing <TR>) and the column (numeric position / ACONTEXT / header words),
  - the production formula applied to the re-read parts (e.g. item 6 = 예상4 - 발생4, item 18 = 17 - 19, item 11 = 발생 - 예상),
  - ABL only: the note's own subtotal identities (rows add up to 소계) and item 7 = Σ of the remaining note rows (+-1 rounding) so that the block 3 = 4+5+6+7 closes against the note itself,
    and the same CSM / RA amounts in the prior-period measurement roll-forward tables.
Usage: [E25_BASE=<backup root>] x01_verify_e25.py [--mutate KIND]   (KIND = line | value | column : an injected fault MUST make the run report problems)"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
BASE = os.environ.get("E25_BASE") or ROOT      # live master / gold reads (after the apply: E25_BASE=<e25_followups/backup_before_apply>)
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups"
PLAN = json.load(open(f"{EV}/e25_plan.json", encoding="utf-8"))
C = PLAN["apply_contract"]
MUT = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None
TAG = re.compile(r"<[^>]+>")
_cache = {}
problems, ok_count = [], [0]


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


def norm_label(s):
    s = ns(s)
    s = re.sub(r"^([\u2160-\u2169]+|[IVX]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    return s


def tr_bounds(lines, ln):
    """1-based line ln -> (first, last) 0-based physical lines of the enclosing <TR>...</TR>"""
    i = ln - 1
    while i >= 0 and not re.match(r"\s*<TR\b", lines[i], re.I):
        i -= 1
    j = ln - 1
    while j < len(lines) and not re.match(r"\s*</TR", lines[j], re.I):
        j += 1
    return i, j


def tr_cells(lines, i, j):
    """cells of a TR: [dict(text, line, ctx)] (all cells, blank included)"""
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


def table_bounds(lines, ln):
    i = ln - 1
    while i >= 0 and not re.match(r"\s*<TABLE\b", lines[i], re.I):
        i -= 1
    j = ln - 1
    while j < len(lines) and not re.match(r"\s*</TABLE", lines[j], re.I):
        j += 1
    return i + 1, j + 1


def unit_of(lines, tstart):
    for k in range(tstart - 1, max(tstart - 2500, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", lines[k]))
        if m:
            return m.group(1)
    return None


def read_cell(rel, ln):
    """-> dict(value, text, label(normalised), numeric_position, unit, ctx, tr_first, table)"""
    lines = L(rel)
    i, j = tr_bounds(lines, ln)
    cells = tr_cells(lines, i, j)
    me = [c for c in cells if c["line"] == ln]
    if len(me) != 1:
        raise RuntimeError(f"{rel} L{ln}: cell not found in its TR ({[c['line'] for c in cells]})")
    me = me[0]
    label = next((c["text"] for c in cells if re.search(r"[가-힣A-Za-z]", c["text"])), "")
    num_pos = 0
    for c in cells:
        if c is me:
            break
        if parse_num(c["text"]) is not None and not re.search(r"[가-힣A-Za-z]", c["text"]):
            num_pos += 1
    ts, te = table_bounds(lines, ln)
    return dict(value=parse_num(me["text"]), text=me["text"], label=norm_label(label), label_raw=label, num_pos=num_pos, unit=unit_of(lines, ts), ctx=me["ctx"], table=(ts, te), tr_first=i + 1)


def check(cond, msg):
    if cond:
        ok_count[0] += 1
    else:
        problems.append(msg)


def mut_line(ln):
    return ln + 2 if MUT == "line" else ln


# ------------------------------------------------------------------------------------------------------------------ A. KB라이프 (3 cells)
def verify_kblife():
    k = json.load(open(f"{EV}/kr0099_kblife/k01_read_kblife.json", encoding="utf-8"))["2023.1Q"]
    rel = k["file"]
    c = k["cites"]
    exp = {"re_csm": ("제공받은서비스의재보험계약마진", -1130.0), "re_ra": ("위험해제로인한위험조정의변동", -82.0), "re_act": ("발생재보험금및재보험서비스비용회수액", 478.0), "re_exp": ("회수예상보험금및보험서비스비용", -1096.0)}
    got = {}
    for key, (lab, ev) in exp.items():
        r = read_cell(rel, mut_line(c[key]["cell_line"]))
        check(r["label"] == lab, f"KB라이프 {key}: row label {r['label']!r} != {lab!r}")
        check(r["unit"] == "백만원", f"KB라이프 {key}: unit {r['unit']!r}")
        check(r["num_pos"] == 5, f"KB라이프 {key}: numeric position {r['num_pos']} != 5 (합계 column)")
        check(abs((r["value"] if MUT != "value" else r["value"] + 1) - ev) < 1e-9, f"KB라이프 {key}: value {r['value']} != {ev}")
        # the table must be the PRIOR-period one: header words of its first rows
        lines = L(rel)
        ts, te = r["table"]
        head = ns(" ".join(clean(x) for x in lines[ts - 1: ts + 60]))
        check("전분기" in head and "당분기" not in head[: head.find("전분기")], f"KB라이프 {key}: table@L{ts} is not the prior-period (전분기) table")
        got[key] = r["value"]
    v9, v10 = -abs(got["re_csm"]), -abs(got["re_ra"])
    v11 = abs(got["re_act"]) - abs(got["re_exp"])
    pl = {(e["item"]): e for e in C["gold_new"] if e["code"] == "KR0099"}
    check(abs(pl[9]["value"] - v9) < 1e-9 and abs(pl[11]["value"] - v11) < 1e-9, "KB라이프 planned items 9/11 != formula on the re-read parts")
    # item 12 = 8 - (9+10+11) with item 8 = live master (-2146); and the BS-independent check that 8 = 9+10+11+12 closes exactly
    live8 = [r for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0099" and r["공시분기"] == "2023.1Q" and r["항목번호"] == 8][0]["값"]
    check(abs(pl[12]["value"] - (live8 - (v9 + v10 + v11))) < 1e-9, "KB라이프 planned item 12 != 8 - (9+10+11)")
    check(abs(live8 - (pl[9]["value"] - 82 + pl[11]["value"] + pl[12]["value"])) < 1e-9, "KB라이프 block 8 = 9+10+11+12 does not close")
    # note rows of the reinsurance side add up to 총 재보험수익 / 총 재보험비용 within rounding (+-1): independent column check
    print(f"  KB라이프: 9={v9:.0f} 10={v10:.0f} 11={v11:.0f} 12={pl[12]['value']:.0f}")


# ------------------------------------------------------------------------------------------------------------------ B. 농협생명 (8 cells)
def verify_nhlife():
    n = json.load(open(f"{EV}/kr0104_nhlife/n01_read_vs_master.json", encoding="utf-8"))
    FILES = {"2024.1Q": ("data/dart/FY2025_Q1/raw/KR0104_농협생명보험/20250515001350.xml", "PFY2024dFQA"), "2024.2Q": ("data/dart/FY2025_Q2/raw/KR0104_농협생명보험/20250814002779.xml", "PFY2024dHYA")}
    LAB = {17: "투자손익", 20: "영업이익", 21: "영업외손익"}
    for q, (rel, ctxp) in FILES.items():
        vals = {}
        for it in (17, 20, 21):
            ln = mut_line(n[q][str(it)]["lines"][0])
            r = read_cell(rel, ln)
            check(r["unit"] == "원", f"농협생명 {q} item {it}: unit {r['unit']!r}")
            check(r["label"].replace("(손실)", "") == LAB[it] or LAB[it] in r["label"], f"농협생명 {q} item {it}: label {r['label']!r}")
            check(ctxp in r["ctx"] and "SeparateMember" in r["ctx"], f"농협생명 {q} item {it}: context {r['ctx']!r} is not {ctxp} / SeparateMember")
            vals[it] = r["value"] / 1e6
            pe = [e for e in C["gold_new"] if e["code"] == "KR0104" and e["quarter"] == q and e["item"] == it][0]
            check(abs(vals[it] - pe["value"]) < 5e-7, f"농협생명 {q} item {it}: re-read {vals[it]} != planned {pe['value']}")
        # item 19 parts: the two finance-expense lines cited by item 18
        l18 = n[q]["18"]["lines"]
        p19 = []
        for ln in l18[1:]:
            r = read_cell(rel, ln)
            check(r["label"] in ("보험금융비용", "재보험금융비용", "보험금융수익", "재보험금융수익") and ctxp in r["ctx"] and "SeparateMember" in r["ctx"], f"농협생명 {q} item 18 part L{ln}: {r['label']!r} {r['ctx']!r}")
            sign = -1 if "비용" in r["label"] else 1
            p19.append(sign * r["value"] / 1e6)
        v19 = sum(p19)
        v18 = vals[17] - v19
        pe18 = [e for e in C["gold_new"] if e["code"] == "KR0104" and e["quarter"] == q and e["item"] == 18][0]
        check(abs(v18 - pe18["value"]) < 5e-7, f"농협생명 {q} item 18: {v18} != planned {pe18['value']}")
        # identities on the planned vector with the unchanged legs read from the master (1, 19, 22)
        live = {r["항목번호"]: r["값"] for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0104" and r["공시분기"] == q}
        check(abs(vals[20] - (live[1] + vals[17])) < 1e-6, f"농협생명 {q}: 20 != 1 + 17 ({vals[20]} vs {live[1] + vals[17]})")
        check(abs(live[22] - (vals[20] + vals[21])) < 1e-6, f"농협생명 {q}: 22 != 20 + 21")
        check(abs(vals[17] - (v18 + v19)) < 1e-6, f"농협생명 {q}: 17 != 18 + 19")
        check(abs(live[19] - v19) < 1e-6, f"농협생명 {q}: item 19 (unchanged) != re-read {v19} vs master {live[19]}")
        print(f"  농협생명 {q}: 17={vals[17]:.6f} 18={v18:.6f} 20={vals[20]:.6f} 21={vals[21]:.6f}")


# ------------------------------------------------------------------------------------------------------------------ C. ABL (18 + 1 cells)
def parse_note_table(rel, tstart):
    """{section: {label: [numeric values]}} of a note table starting at the given line (rows between <TABLE> and </TABLE>); also {(section,label): [cell lines]}"""
    lines = L(rel)
    ts, te = table_bounds(lines, tstart)
    sec, out, cl = None, {}, {}
    i = ts - 1
    while i < te:
        if re.match(r"\s*<TR\b", lines[i], re.I):
            j = i
            while not re.match(r"\s*</TR", lines[j], re.I):
                j += 1
            cells = tr_cells(lines, i, j)
            if cells:
                lab = norm_label(cells[0]["text"])
                vals = [(parse_num(c["text"]), c["line"]) for c in cells[1:] if parse_num(c["text"]) is not None]
                if not vals and lab in ("보험수익", "재보험수익", "보험서비스비용", "재보험비용"):
                    sec = lab
                elif sec is not None and vals:
                    out.setdefault(sec, {}).setdefault(lab, [v for v, _ in vals])
                    cl.setdefault((sec, lab), [ln for _, ln in vals])
                elif sec is None and vals:
                    out.setdefault("_pre", {}).setdefault(lab, [v for v, _ in vals])
            i = j
        i += 1
    return out, cl, unit_of(lines, ts)


def verify_abl():
    a = json.load(open(f"{EV}/kr0070_abl/a01_read_abl_fy2023.json", encoding="utf-8"))
    live = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
    plan = {(e["quarter"], e["item"]): e for e in C["gold_new"] + C["gold_replace"] if e["code"] == "KR0070"}
    cum_by_q = {}
    PREV_Q = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q", "2023.4Q": "2023.3Q"}
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        rec = a[q]
        rel = rec["file"]
        rv, rc, ru = parse_note_table(rel, rec["rev_table"])
        cv, cc, cu = parse_note_table(rel, rec["cost_table"])
        check(ru == "백만원" and cu == "백만원", f"ABL {q}: units {ru}/{cu}")
        n = len(rv["보험수익"]["예상보험금"])
        check(n in (2, 4), f"ABL {q}: numeric columns {n}")
        col = n - 1                       # prior-period cumulative = LAST numeric cell in all four layouts
        if MUT == "column":
            col = 0
        g = lambda d, sec, lab: d[sec][lab][col]  # noqa: E731
        csm, ra = g(rv, "보험수익", "보험계약마진상각"), g(rv, "보험수익", "위험조정변동")
        exp4 = [d for d in (g(rv, "보험수익", x) for x in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비") if x in rv["보험수익"])]
        inc4 = [d for d in (g(cv, "보험서비스비용", x) for x in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비") if x in cv["보험서비스비용"])]
        v6 = sum(exp4) - sum(inc4)
        rcsm, rra = g(cv, "재보험비용", "보험계약마진상각"), g(cv, "재보험비용", "위험조정변동")
        rinc = g(rv, "재보험수익", "발생재보험금") + (g(rv, "재보험수익", "발생손해조사비") if "발생손해조사비" in rv["재보험수익"] else 0)
        rexp = g(cv, "재보험비용", "예상재보험금") + (g(cv, "재보험비용", "예상손해조사비") if "예상손해조사비" in cv["재보험비용"] else 0)
        v9, v10, v11 = -abs(rcsm), -abs(rra), rinc - rexp
        # subtotal identities (column check)
        for name, d in (("보험수익", rv), ("재보험수익", rv), ("보험서비스비용", cv), ("재보험비용", cv)):
            rows = {k: x for k, x in d[name].items() if k not in ("소계", "합계", "기타사업비용")}
            check(abs(sum(x[col] for x in rows.values()) - d[name]["소계"][col]) <= 1.5, f"ABL {q}: {name} rows do not add up to 소계 in column {col}")
        # planned values
        for it, val in ((4, csm), (5, ra), (6, v6), (9, v9), (10, v10)):
            pe = plan.get((q, it))
            if pe is None:                    # item 4 (gold of the previous load) / item 9 2023.4Q (unchanged)
                if it == 4:
                    check(abs(live[(q, 4)] - val) < 1e-9, f"ABL {q} item 4 live {live[(q, 4)]} != re-read {val}")
                elif it == 9:
                    check(abs(live[(q, 9)] - val) < 1e-9, f"ABL {q} item 9 (unchanged cell) live {live[(q, 9)]} != re-read {val}")
                continue
            check(abs(pe["value"] - (val if MUT != "value" else val + 1)) < 1e-9, f"ABL {q} item {it}: re-read {val} != planned {pe['value']}")
        # cited cell lines of the plan (items 5, 9, 10): label + position + value
        for it, key in ((5, ("보험수익", "위험조정변동", rc)), (9, ("재보험비용", "보험계약마진상각", cc)), (10, ("재보험비용", "위험조정변동", cc))):
            ln = mut_line(key[2][(key[0], key[1])][col])
            r = read_cell(rel, ln)
            check(r["label"] == key[1] and abs(abs(r["value"]) - abs(rec["prior_cum"][str(it)][0])) < 1e-9, f"ABL {q} item {it}: cited line {ln} label {r['label']!r} value {r['value']}")
        # item 7: planned = 3 - (4+5+6) (3 and 4 = gold of the previous load) AND equals the note's remaining rows within +-1
        i3 = live[(q, 3)]
        v7 = i3 - (csm + ra + v6)
        pe7 = plan[(q, 7)]
        check(abs(pe7["value"] - v7) < 1e-6, f"ABL {q} item 7: planned {pe7['value']} != 3-(4+5+6) {v7}")
        other_rev = sum(x[col] for k, x in rv["보험수익"].items() if k not in ("소계", "합계") and k not in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비", "위험조정변동", "보험계약마진상각"))
        other_cost = sum(x[col] for k, x in cv["보험서비스비용"].items() if k not in ("소계", "합계") and k not in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비"))
        v7_note = other_rev - other_cost
        check(abs(pe7["value"] - v7_note) <= 1.0, f"ABL {q} item 7: planned {pe7['value']} vs sum of the other note rows {v7_note} (|diff| > 1)")
        sub_diff = rv["보험수익"]["소계"][col] - cv["보험서비스비용"]["소계"][col]
        check(abs(i3 - sub_diff) <= 1.0, f"ABL {q}: item 3 {i3} != 보험수익 소계 - 보험서비스비용 소계 {sub_diff}")
        # roll-forward cross-check (RA release +-1, CSM release exact)
        rf = rec["rollforward"]
        for k_, val in (("ins_csm_release", csm), ("rein_csm_release", rcsm)):
            ln = rf[k_][1]
            r = read_cell(rel, ln)
            check(abs(abs(r["value"]) - abs(val)) < 1e-9 and r["unit"] == "백만원", f"ABL {q}: roll-forward {k_} L{ln} {r['value']} != note {val}")
        for k_, val, tol in (("ins_ra_release", ra, 1.0), ("rein_ra_release", rra, 0.0)):
            ln = rf[k_][1]
            r = read_cell(rel, ln)
            check(abs(abs(r["value"]) - abs(val)) <= tol + 1e-9, f"ABL {q}: roll-forward {k_} L{ln} {r['value']} vs note {val}")
        # single-quarter seam against the printed prior 3-month column (H1 / Q3 filings)
        if n == 4:
            p3 = {it: rv["보험수익"][lab][2] for it, lab in ((4, "보험계약마진상각"), (5, "위험조정변동"))}
            p3[9] = -abs(cv["재보험비용"]["보험계약마진상각"][2])
            p3[10] = -abs(cv["재보험비용"]["위험조정변동"][2])
            p3[6] = sum(rv["보험수익"][x][2] for x in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비")) - sum(cv["보험서비스비용"][x][2] for x in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비"))
            cur = {4: csm, 5: ra, 6: v6, 9: v9, 10: v10}
            pr = cum_by_q[PREV_Q[q]]
            for it in (4, 5, 6, 9, 10):
                dq = cur[it] - pr[it]
                check(abs(dq - p3[it]) < 1e-9, f"ABL {q} item {it}: derived single quarter {dq} != printed 3-month {p3[it]}")
        cum_by_q[q] = {4: csm, 5: ra, 6: v6, 9: v9, 10: v10}
        print(f"  ABL {q}: 4={csm:.0f} 5={ra:.0f} 6={v6:.0f} 7={v7:.6f} (note rows {v7_note:.0f}) 9={v9:.0f} 10={v10:.0f} | roll-forward CSM {rf['ins_csm_release'][0]:.0f}/{rf['rein_csm_release'][0]:.0f} RA {rf['ins_ra_release'][0]:.0f}/{rf['rein_ra_release'][0]:.0f}")


# ------------------------------------------------------------------------------------------------------------------ D. KB손보 item 16 (diagnosis; the two cells fixed are the hand-loaded wrong ones)
def verify_kbson():
    series = {  # (file, cell line, expected cumulative) : raw DART separate statement, 기타사업비용 row
        "2024.3Q cur": ("data/dart/FY2024_Q3/raw/KR0010_KB손해보험/20241114002445.xml", 27294, 284474.0),
        "2024.4Q cur": ("data/dart/FY2024_Q4/raw/KR0010_KB손해보험_20250314001697/20250314001697.xml", 45345, 380949.0),
        "2024.4Q prior (FY2025 annual)": ("data/dart/FY2025_Q4/raw/KR0010_KB손해보험_20260313001064/20260313001064.xml", 44881, 380949.0),
        "2025.1Q cur": ("data/dart/FY2025_Q1/raw/KR0010_KB손해보험/20250515001437.xml", 26504, 91927.0),
        "2025.2Q cur": ("data/dart/FY2025_Q2/raw/KR0010_KB손해보험/20250814003072.xml", 29588, 190741.0),
        "2025.2Q prior (FY2026 H1)": ("data/dart/FY2026_Q2/raw/KR0010_KB손해보험/20260814002234.xml", 27709, 190741.0),
        "2025.3Q cur": ("data/dart/FY2025_Q3/raw/KR0010_KB손해보험/20251114001554.xml", 25436, 283832.0),
        "2025.4Q cur": ("data/dart/FY2025_Q4/raw/KR0010_KB손해보험_20260313001064/20260313001064.xml", 44880, 388289.0),
    }
    for name, (rel, ln, ev) in series.items():
        r = read_cell(rel, ln)
        check(r["label"].endswith("기타사업비용") and abs(r["value"] - ev) < 1e-9 and r["unit"] == "백만원", f"KB손보 {name}: L{ln} {r['label']!r} {r['value']} unit {r['unit']!r} != {ev}")
    live = {(r["공시분기"]): r["값"] for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0010" and r["항목번호"] == 16}
    for d in C["drift_fix"]:
        check(live[d["quarter"]] == d["live_value"], f"KB손보 {d['quarter']}: live {live[d['quarter']]} != plan {d['live_value']}")
        check(d["live_value"] < 192135.0 or d["quarter"] != "2024.4Q", "KB손보 2024.4Q 60,900 is below the 2024.2Q cumulative 192,135: impossible")
    print("  KB손보: raw statement series 284,474 / 380,949 / 91,927 / 190,741 / 283,832 / 388,289 re-read; live hand-loaded 60,900 / 33,300 are neither (PDF 요약 PL 기타사업비용 row, different concept)")


def verify_plan_vs_live():
    live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.load(open(f"{BASE}/PL_breakdown.json", encoding="utf-8"))}
    goldd = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in json.load(open(f"{BASE}/data/_gold/user_pl_cells.json", encoding="utf-8"))["set"]}
    for e in C["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        lvv = live.get(k)
        check((lvv is None and e["was"] is None) or (lvv is not None and e["was"] is not None and abs(lvv - e["was"]) < 5e-7), f"plan was != live master {k}: {e['was']} vs {lvv}")
        check(k not in goldd, f"plan gold_new already has gold {k}")
    for e in C["gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        check(k in goldd and goldd[k] == e["old_entry"], f"plan gold_replace old entry != live gold {k}")
        check(abs(live[k] - e["was"]) < 5e-7, f"plan replace was != live {k}")


for name, fn in (("A KB라이프", verify_kblife), ("B 농협생명", verify_nhlife), ("C ABL", verify_abl), ("D KB손보", verify_kbson), ("E plan vs live", verify_plan_vs_live)):
    print(f"== {name}")
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        problems.append(f"{name}: EXCEPTION {type(e).__name__}: {e}")
        print("   EXCEPTION", type(e).__name__, str(e)[:300])
print(f"\nchecks passed: {ok_count[0]}  problems: {len(problems)}  mutation: {MUT}")
for p in problems:
    print("  PROBLEM:", p)
sys.exit(0 if (not problems) == (MUT is None) else 3)
