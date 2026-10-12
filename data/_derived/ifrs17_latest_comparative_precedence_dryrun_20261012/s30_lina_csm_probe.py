"""Read-only probe for ticket case LINA CSM 2023.1Q / 2023.2Q (and the restatement vintage chain):
scan the Lina (KR0074) management-disclosure PDFs of FY2023_Q1..FY2024_Q3 for CSM roll-forward tables ((5) 보험계약부채(자산)의 측정요소별 변동내역)
with the production reader (scripts/extract_lina_csm_rows_20261011.py: read_rollforward / check_rollforward / csm_items) and print, per page,
the period marker (<당분기>/<전분기>/<당반기>/<전반기>), the 6 CSM items in 억원 and whether the page closes.

Nothing is written except lina_csm_probe.json next to this script.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import fitz  # noqa: E402

import extract_lina_csm_rows_20261011 as L  # noqa: E402  (import only)
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

fitz.TOOLS.mupdf_display_errors(False)
MARK = re.compile(r"<\s*(당분기|전분기|당반기|전반기|당기|전기)\s*>")
EOK = 100_000
out = {}
for fy in ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"]:
    pdfs = latest_disclosure_pdfs(fy, "KR0074")
    if not pdfs:
        print(fy, "NO PDF")
        continue
    pdf = pdfs[0]
    doc = fitz.open(pdf)
    print("=" * 100)
    print(fy, pdf.name, "pages", len(doc))
    hits = []
    for pno in range(len(doc)):
        page = doc[pno]
        txt = page.get_text()
        if "측정요소별" not in txt or "기초" not in txt:
            continue
        try:
            rf = L.read_rollforward(page)
        except Exception as e:  # noqa: BLE001
            continue
        if not rf["rows"] or "close" not in rf["rows"] or "open" not in rf["rows"]:
            continue
        prob = L.check_rollforward(rf["rows"])
        m = MARK.search(txt)
        items = None
        if not prob:
            it = L.csm_items(rf["rows"])
            items = {k: round(v / EOK, 2) for k, v in it.items()}
        # first heading-ish lines
        head = [ln.strip() for ln in txt.splitlines() if ln.strip()][:3]
        hits.append({"page": pno + 1, "marker": m.group(1) if m else None, "closes": not prob, "problems": prob[:2], "items_eok": items, "head": head})
        print(f"  p{pno+1:3d} marker={m.group(1) if m else '-':4s} closes={not prob} items(억)={items} head={head[:2]}")
    out[fy] = {"pdf": str(pdf.relative_to(ROOT)).replace('\\', '/'), "tables": hits}
(HERE / "lina_csm_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
