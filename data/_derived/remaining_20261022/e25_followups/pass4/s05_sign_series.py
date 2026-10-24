# -*- coding: utf-8 -*-
"""READ-ONLY pass4 s05: sign convention of PL item 9 / 10 (reinsurance CSM release / RA release) over the whole live master, and the 동양 / ABL / KB라이프 series (evidence for the 'keep -|value|' confirmation)."""
import json
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_keys = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"]}
out = []


def PR(s=""):
    print(s)
    out.append(s)


for item in (9, 10):
    c = Counter()
    pos = []
    for r in rows:
        if r["항목번호"] != item or r["값"] is None or r["값"] == 0:
            continue
        s = "neg" if r["값"] < 0 else "pos"
        c[s] += 1
        if s == "pos":
            pos.append((r["원수사명"], r["공시분기"], r["값"], "GOLD" if (r["원보험사코드"], item, r["공시분기"]) in gold_keys else ""))
    PR(f"item {item}: non-zero cells {sum(c.values())}  negative {c['neg']}  positive {c['pos']}")
    by = defaultdict(list)
    for p in pos:
        by[p[0]].append(p)
    for k, v in sorted(by.items()):
        PR(f"   positive cells of {k}: " + ", ".join(f"{x[1]}={x[2]:,.0f}{'(' + x[3] + ')' if x[3] else ''}" for x in v[:12]) + (f" ... (+{len(v) - 12})" if len(v) > 12 else ""))
for code, nm in (("KR0087", "동양생명"), ("KR0070", "ABL"), ("KR0099", "KB라이프")):
    for item in (9, 10):
        ser = [(r["공시분기"], r["값"]) for r in rows if r["원보험사코드"] == code and r["항목번호"] == item and r["값"] is not None]
        ser.sort()
        PR(f"{nm} {code} item {item}: " + " ".join(f"{q}:{v:,.0f}" for q, v in ser))
open(f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4/s05_sign_series.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
