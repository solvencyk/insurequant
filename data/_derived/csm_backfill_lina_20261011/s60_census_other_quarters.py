# -*- coding: utf-8 -*-
"""Step 60 (read-only census, nothing is loaded): can the same reader read the CSM roll-forward note of the OTHER Lina quarters?

For every quarter 2023.1Q .. 2026.2Q: pages of s01_find_pages.json that look like the roll-forward note; for the first page set of
each (the 별도 / 회사 set) try the reader; report whether the page closes (all identities) and the six CSM items.
Purpose: tell the orchestrator what a later extension would find (and which quarters are unreadable with this reader)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

found = json.loads((W / "s01_find_pages.json").read_text(encoding="utf-8"))
QMAP = {"FY2023_Q1": "2023.1Q", "FY2023_Q2": "2023.2Q", "FY2023_Q3": "2023.3Q", "FY2023_Q4": "2023.4Q",
        "FY2024_Q1": "2024.1Q", "FY2024_Q2": "2024.2Q", "FY2024_Q3": "2024.3Q", "FY2024_Q4": "2024.4Q",
        "FY2025_Q1": "2025.1Q", "FY2025_Q2": "2025.2Q", "FY2025_Q3": "2025.3Q", "FY2025_Q4": "2025.4Q",
        "FY2026_Q1": "2026.1Q", "FY2026_Q2": "2026.2Q"}
master = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0074"}

out = {}
for fy, q in QMAP.items():
    info = found[fy]
    pdf = ROOT / info["file"]
    doc = fitz.open(pdf)
    cand = sorted(set(info["rollforward"]) | set(info["csm_adj"]))
    res = []
    for p in cand:
        pg = doc[p - 1]
        t = T.norm(pg.get_text())
        per = next((m.strip("<>") for m in ("<당반기>", "<전반기>", "<당분기>", "<전분기>", "<당기>", "<전기>") if m in t), None)
        acct = "유배당외" if "유배당외보험" in t else ("유배당" if "유배당보험" in t else None)
        con = "연결실체" in t
        rf = T.read_rollforward(pg)
        if rf["bad"] or len(rf["rows"]) < 10:
            res.append({"page": p, "period": per, "account": acct, "consolidated_words": con, "readable": False, "rows": len(rf["rows"]), "bad": len(rf["bad"])})
            continue
        probs = T.check_rollforward(rf["rows"])
        it = None if probs else T.csm_items(rf["rows"])
        res.append({"page": p, "period": per, "account": acct, "consolidated_words": con, "readable": not probs, "rows": len(rf["rows"]),
                    "problems": probs[:2], "csm_천원": it})
    out[q] = {"pdf": info["file"], "pages_total": info["pages"], "text_pages": info["text_pages"], "candidates": res}
    print(f"\n== {q} {Path(info['file']).name} ({info['pages']}p, text {info['text_pages']}p)")
    for r in res:
        if r.get("readable"):
            it = r["csm_천원"]
            print(f"   p{r['page']} {r['period']} {r['account']} con={r['consolidated_words']} CLOSES  open {it['open']/1e5:.2f} new {it['new']/1e5:.2f} fin {it['fin']/1e5:.2f} adj {it['adj']/1e5:.2f} amort {it['amort']/1e5:.2f} close {it['close']/1e5:.2f}")
        else:
            print(f"   p{r['page']} {r['period']} {r['account']} con={r['consolidated_words']} not read by this reader (rows={r['rows']}, {r.get('problems') or r.get('bad')})")
(W / "s60_census_other_quarters.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
