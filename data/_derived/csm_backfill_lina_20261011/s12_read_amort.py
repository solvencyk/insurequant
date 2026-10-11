# -*- coding: utf-8 -*-
"""Step 12: read the expected-CSM-amortisation schedules (period-end page and prior-year-end page) of the target quarters
and of the 2025.4Q PDF; run the schedule identities; compare with the roll-forward closing CSM; compare with the existing
master row of KR0074 2025.4Q.  Writes s12_read_amort.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

# quarter -> (FY dir, [(page, label)]) ; the first page of each is the period-end schedule (회사 = separate set)
PLAN = {
    "2026.2Q": ("FY2026_Q2", [(96, "당반기말"), (97, "전기말")], [(166, "당반기말(연결)"), (167, "전기말(연결)")]),
    "2026.1Q": ("FY2026_Q1", [(71, "당분기말"), (72, "전기말")], [(142, "당분기말(연결)"), (143, "전기말(연결)")]),
    "2025.3Q": ("FY2025_Q3", [(66, "당분기말"), (67, "전기말")], [(133, "당분기말(연결)"), (134, "전기말(연결)")]),
    "2025.4Q": ("FY2025_Q4", [(245, "당기말"), (246, "전기말")], [(374, "당기말(연결)"), (375, "전기말(연결)")]),
}

master = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
m_2025 = {r["경과차년"]: r["상각액"] for r in master if r["원보험사코드"] == "KR0074" and r["공시분기"] == "2025.4Q"}

res = {}
for q, (fy, sep, con) in PLAN.items():
    pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
    doc = fitz.open(pdf)
    res[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/")}
    print(f"\n===== {q} {pdf.name} =====")
    for label, pages in (("sep", sep), ("con", con)):
        for p, name in pages:
            pg = doc[p - 1]
            txt = T.norm(pg.get_text())
            a = T.read_amort_page(pg)
            probs = T.check_amort(a)
            grand = a["total1"][7] if a["total1"] else None
            first10 = (a["total0"] + a["total1"][:2]) if a["total0"] and a["total1"] else None
            print(f"  {label} p{p} {name}: caption_has_발행={'발행한보험계약' in txt} caption_has_출재={'출재보험계약' in txt} "
                  f"rows h0/h1={len(a['half0'])}/{len(a['half1'])} other={len(a['other'])} problems={probs}")
            if first10:
                print("      합계 1~10년 (천원):", first10, "| 계:", grand, "| 1~10년 (억원):", [round(v / 1e5, 5) for v in first10])
            res[q][f"{label}_p{p}"] = {"name": name, "total0": a["total0"], "total1": a["total1"], "problems": probs,
                                        "rows0": a["half0"], "rows1": a["half1"]}
    # existing master row comparison for 2025.4Q
if True:
    r = res["2025.4Q"]
    cur = r["sep_p245"]["total0"] + r["sep_p245"]["total1"][:2]
    prv = r["sep_p246"]["total0"] + r["sep_p246"]["total1"][:2]
    print("\nExisting master KR0074 2025.4Q amortisation rows (억원):", m_2025)
    print("  PDF 2025.12.31 schedule 1~8년 (억원):", [round(v / 1e5, 1) for v in cur[:8]])
    print("  PDF 2024.12.31 schedule 1~8년 (억원):", [round(v / 1e5, 1) for v in prv[:8]])
(OUT / "s12_read_amort.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
