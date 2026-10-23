# -*- coding: utf-8 -*-
"""READ-ONLY pass3 d11 (KR0087 동양생명): print the reinsurance ANALYSIS tables (재보험수익 / 재보험비용 분석 공시: the small tables with the [3개월, 누적] or [당기, 전기] columns whose rows are
'재보험수익, 발생한 보험금' / 'Reinsurance expense: 예상 보험금 ...' / 보험계약마진 / 위험조정) of a filing, in document order, with physical xml line numbers.
usage: d11_dy_reins_analysis.py FYxxxx_Qn"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
path, lines, s0, tabs = P.tables_with("KR0087", fy, ["재보험"])
print(f"##### KR0087 {fy} {P.M.rel(path)} separate notes start L{s0}; {len(tabs)} tables mentioning 재보험")
for t, rows in tabs:
    labs = [P.nl(" ".join(c["text"] for c in r["cells"][:2])) for r in rows if r["cells"]]
    hdr = P.nl(" ".join(c["text"] for r in rows[:7] for c in r["cells"]))
    is_an = any(re.search(r"재보험수익,|재보험비용,|재보험자에게(서)?(회수한|지급된)", L) for L in labs) or "재보험수익분석공시" in P.nl(t["title"] + " ".join(c["text"] for r in rows[:3] for c in r["cells"])) or "재보험비용분석공시" in hdr
    if not is_an or len(rows) > 40:
        continue
    unit = P.T.find_unit(lines, t, span=2500)
    print(f"--- table@L{t['start']}-{t['end']} unit={unit} rows={len(rows)}")
    for r in rows:
        if not r["cells"]:
            continue
        txt = " | ".join(f"{c['text']}@{c['line']}" for c in r["cells"][:8] if c["text"].strip())
        if txt.strip():
            print(f"   R{r['tr_line']:>6} {txt[:230]}")
