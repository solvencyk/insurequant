"""Read-only: 2-4 prior-year tables (25.1Q / 25.2Q) in the 2026 Kyobo disclosure PDFs: print the 합계 row (7 numbers) and compare to master ILP items 1-7."""
import sys, re, json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from _disclosure_pdf_paths import latest_disclosure_pdfs
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
M = {(r["공시분기"], r["항목번호"]): r["값"] for r in ilp if r["원보험사코드"] == "KR0073"}
for per, q, pages in (("FY2026_Q1", "2025.1Q", [8, 9]), ("FY2026_Q2", "2025.2Q", [9, 10])):
    p = latest_disclosure_pdfs(per, "KR0073")[0]
    doc = fitz.open(str(p))
    mrun = [M.get((q, i)) for i in range(1, 8)]
    print(per, q, "master items 1-7", mrun)
    for pn in pages:
        t = doc[pn - 1].get_text()
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        head = [l for l in lines if re.search(r"\(2\d\.\dQ\)|<", l)]
        # find any run of 7 numbers equal to master or near
        nums = [l for l in lines if re.fullmatch(r"[\d,]+", l)]
        vals = [int(x.replace(",", "")) for x in nums]
        found = False
        for k in range(len(vals) - 6):
            run = vals[k:k + 7]
            if mrun[0] is not None and abs(run[0] - mrun[0]) < 1 and abs(run[2] - mrun[2]) < 1:
                found = True; print("  page", pn, "run == master at idx", k, run)
        print("  page", pn, "heads", head[:6], "contains master run:", found)
        # print candidate runs containing a number near 749,989 neighbours
        for k, v in enumerate(vals):
            if 600000 < v < 800000 and k + 6 < len(vals):
                print("  page", pn, "run@", k, vals[k:k + 7])
