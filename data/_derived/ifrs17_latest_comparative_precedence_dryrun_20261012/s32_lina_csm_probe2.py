"""Read-only: Lina (KR0074) CSM roll-forward tables in every vintage (old 7-column layout with 보험취득현금흐름자산 and the 6-column layout).

For each PDF page that contains a roll-forward ('기초잔액' row + a closing row '기말잔액'|'분기말잔액'|'반기말잔액') print the period marker and the
CSM total (공정가치법 + 수정소급법 + 전환이후 columns, idx 2,3,4 in both layouts) for opening / 신계약 / 이자 / 가정 / 상각 / 기말 in 억원.
Closure test: open + new + fin + adj + amort == close in 천원 (no plug) on the CSM columns.
Writes lina_csm_probe2.json.
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

import extract_lina_csm_rows_20261011 as L  # noqa: E402
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

fitz.TOOLS.mupdf_display_errors(False)
MARK = re.compile(r"<\s*(당분기|전분기|당반기|전반기|당기|전기)\s*>")
EOK = 100_000
LAB = {
    "open": ("기초잔액",), "new": ("최초인식한계약의효과",), "adj": ("보험계약마진조정하는추정치의변동분",),
    "amort": ("제공한서비스반영인식한보험계약마진",), "fin": ("보험금융손익",),
    "close": ("기말잔액", "분기말잔액", "반기말잔액", "당분기말잔액", "당반기말잔액"),
}
CSM_IDX = (2, 3, 4)


def to_i(t):
    try:
        return L.to_int(t)
    except Exception:
        return None


def read_page(page):
    got = {}
    for r in L.page_rows(page):
        lab, nums = L.split_row(r)
        if len(nums) < 6:
            continue
        for k, labs in LAB.items():
            if lab in labs and k not in got:
                vals = [to_i(t) for t in nums]
                if None in vals:
                    continue
                got[k] = vals
    return got


out = {}
for fy in ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"]:
    pdfs = latest_disclosure_pdfs(fy, "KR0074")
    if not pdfs:
        print(fy, "NO PDF")
        continue
    pdf = pdfs[0]
    doc = fitz.open(pdf)
    print("=" * 110)
    print(fy, pdf.name, "pages", len(doc))
    res = []
    for pno in range(len(doc)):
        page = doc[pno]
        got = read_page(page)
        if not {"open", "close", "new", "amort"} <= set(got):
            continue
        txt = page.get_text()
        m = MARK.search(txt)
        s = {k: sum(got[k][i] for i in CSM_IDX if i < len(got[k])) for k in got}
        ncols = len(got["open"])
        resid = s["open"] + s["new"] + s.get("fin", 0) + s.get("adj", 0) + s["amort"] - s["close"]
        item = {k: round(v / EOK, 5) for k, v in s.items()}
        res.append({"page": pno + 1, "marker": m.group(1) if m else None, "ncols": ncols, "csm_eok": item, "resid_천원": resid})
        print(f"  p{pno+1:3d} {m.group(1) if m else '-':4s} ncols={ncols} open={item['open']:>12.5f} new={item['new']:>10.5f} fin={item.get('fin', float('nan')):>9.5f} adj={item.get('adj', float('nan')):>10.5f} amort={item['amort']:>10.5f} close={item['close']:>12.5f} resid(천원)={resid}")
    out[fy] = {"pdf": str(pdf.relative_to(ROOT)).replace('\\', '/'), "tables": res}
(HERE / "lina_csm_probe2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
