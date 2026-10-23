# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r01 (KR0070 ABL): dump the separate-basis 보험영업수익 / 보험영업비용 note tables of the FY2024_Q1 .. FY2026_Q2 filings with every numeric cell and its physical xml line,
plus the measurement roll-forward rows used as a cross-check (CSM release / RA release, insurance and reinsurance).
usage: r01_abl_dump.py FY2025_Q1 [FY..]   -> prints to stdout (redirect to a file)"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2")
import s2lib  # noqa: E402  (patches mlib.read_lines: plain-HTML 2026 filings indent <TD>/<TR>)
E = s2lib.E

sys.stdout.reconfigure(encoding="utf-8")
M, T, W = E.M, E.T, E.W


def nums(row):
    out = []
    for c in row["cells"][1:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "\u2212"):
            out.append((0.0, c["line"], c["text"]))
    return out


def show_table(t, rows, tag):
    print(f"  --- {tag} table@L{t['start']}-{t['end']} caption={E.nl(t['caption'] or '')[:60]!r}")
    for r in rows:
        if not r["cells"]:
            continue
        lab = r["cells"][0]["text"]
        n = nums(r)
        print(f"    R{r['tr_line']:>6} {lab[:34]:34s} " + " | ".join(f"{tx}@{ln}" for _v, ln, tx in n))


for fy in sys.argv[1:]:
    path = T.main_path("KR0070", fy)
    lines, s0, tabs = s2lib.tables_sep2(path)
    print(f"##### {fy} {M.rel(path)} separate notes start L{s0}")
    rev = [(t, rows) for t, rows in tabs if (lambda L: "예상보험금" in L and "소계" in L and "재보험수익" in L and "보험계약마진상각" in L and "위험조정변동" in L)([E.lab(r) for r in rows])]
    cost = [(t, rows) for t, rows in tabs if (lambda L: "발생보험금" in L and "예상재보험금" in L and "기타사업비용" in L)([E.lab(r) for r in rows])]
    print(f"  revenue tables {[t['start'] for t, _ in rev]}  cost tables {[t['start'] for t, _ in cost]}  unit {[T.find_unit(lines, t, span=2500) for t, _ in rev + cost]}")
    for t, rows in rev:
        show_table(t, rows, "보험영업수익")
    for t, rows in cost:
        show_table(t, rows, "보험영업비용")
    # roll-forward (current + prior) CSM / RA release rows
    for t, rows in tabs:
        cap = E.nl(t["caption"] or "")
        if not re.match(r"^[12]\)(당분기|당반기|당기|전분기|전반기|전기)$", cap):
            continue
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if "최선추정" not in hdr or "위험조정" not in hdr:
            continue
        labs = [E.lab(r) for r in rows]
        kind = "INS" if any(x.startswith("I.기초보험계약순부채") for x in labs) else ("REIN" if any(x.startswith("I.기초재보험계약순자산") for x in labs) else None)
        if kind is None:
            continue
        print(f"  --- roll-forward {kind} {cap} table@L{t['start']}")
        for r in rows:
            L = E.lab(r)
            if L.startswith("(1)서비스제공으로당기손익으로인식된보험계약마진") or L.startswith("(2)비금융위험에대한위험조정변동") or L.startswith("I.기초"):
                print(f"    R{r['tr_line']:>6} {r['cells'][0]['text'][:50]:50s} " + " | ".join(f"{tx}@{ln}" for _v, ln, tx in nums(r)))
