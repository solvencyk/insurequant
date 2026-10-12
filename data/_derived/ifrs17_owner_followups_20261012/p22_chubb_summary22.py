# -*- coding: utf-8 -*-
"""Read-only: 2-2 요약 재무상태표 (억원) of the Chubb PDFs: 책임준비금 / 특별계정부채 / 부채총계 rows, compared with D1+재보험계약부채 and SA of the 8-1 balance sheet."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
import fitz
from bspl_granularity.pdfrows import rows_from_page
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
D = R + "data/disclosure/"
tok = json.loads(open(R + "data/_derived/ifrs17_owner_followups_20261012/chubb_token_presence.json", "rb").read().decode("utf-8"))
bs = json.loads(open(R + "IFRS17_BS.json", "rb").read().decode("utf-8"))
re21 = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0100" and r["항목번호"] == 21}
out = {}
for q, t in tok.items():
    doc = fitz.open(D + t["pdf"])
    found = None
    for pno in range(min(len(doc), 12)):
        rows, free = rows_from_page(doc[pno], pageno=pno + 1)
        labs = {r.label: r for r in rows}
        keys = [l for l in labs if "부채총계" in l]
        if keys and any("특별계정부채" in l for l in labs) or (keys and any("책임준비금" in l for l in labs)):
            found = (pno + 1, rows)
            break
    if not found:
        print(q, "summary not found in the first 12 pages"); continue
    pno, rows = found
    line = {}
    for r in rows:
        for k in ("책임준비금", "특별계정부채", "부채총계"):
            if k in r.label and k not in line:
                line[k] = [int(v) for v in r.vals[:2]]
    d1 = t["D1_won"] / 1e8; sa = t["SA_won"] / 1e8; re_ = re21[q] * 1e6 / 1e8
    print(q, "p", pno, "summary(억원, cur,prior):", line, "| 8-1: D1+RE=%.2f SA=%.2f" % (d1 + re_, sa))
    out[q] = dict(page=pno, summary=line, d1_plus_re_eok=round(d1 + re_, 4), sa_eok=round(sa, 4))
json.dump(out, open(R + "data/_derived/ifrs17_owner_followups_20261012/chubb_summary22.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
