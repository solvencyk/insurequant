# -*- coding: utf-8 -*-
"""READ-ONLY pass3 n01 (KR0032 NH농협손해보험): dump the separate-basis income statement + comprehensive income statement of FY2024_Q1 / FY2024_Q2 (원), all numeric columns, physical xml lines.
usage: n01_stmt_dump.py FYxxxx_Qn [needle]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
code = sys.argv[2] if len(sys.argv) > 2 else "KR0032"
path = P.main_path(code, fy)
lines = P.M.read_lines(path)
print(f"##### {code} {fy} {P.M.rel(path)}")
for t in P.M.iter_tables(lines):
    blob = P.nl(P._TAGRE.sub("", " ".join(lines[t["start"] - 1:t["end"]])))
    if "총포괄손익" not in blob and "법인세비용차감전" not in blob and "당기순이익" not in blob and "반기순이익" not in blob and "분기순이익" not in blob:
        continue
    if "연결" in t["title"] or "요약" in t["title"]:
        continue
    if "재무제표" not in t["title"]:
        continue
    rows = P.E.rows_full23(lines, t["start"], t["end"])
    unit = P.T.find_unit(lines, t, span=300)
    labs = [P.lab(r) for r in rows]
    if not any(("당기순이익" in L or "반기순이익" in L or "분기순이익" in L) for L in labs) or not any("영업이익" in L or "법인세비용차감전" in L or "총포괄손익" in L for L in labs):
        continue
    print(f"--- table@L{t['start']}-{t['end']} unit={unit} title={t['title']!r} rows={len(rows)}")
    for r in rows:
        if not r["cells"]:
            continue
        n = P.nums(r)
        if not n:
            print(f"   R{r['tr_line']:>6} {P.rowtext(r)[:50]}")
            continue
        print(f"   R{r['tr_line']:>6} {P.rowtext(r)[:46]:46s} " + " | ".join(f"{tx}@{ln}" for _v, ln, tx in n[:4]))
