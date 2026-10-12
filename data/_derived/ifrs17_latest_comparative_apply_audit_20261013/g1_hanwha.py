import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
out = open(here + "/g1_hanwha.txt", "w", encoding="utf-8")
for fq in ("FY2023_Q1", "FY2023_Q2", "FY2024_Q1", "FY2024_Q2"):
    for pdf in sorted(glob.glob(f"{REPO}/data/disclosure/{fq}/raw/KR0002_*.pdf")):
        doc = fitz.open(pdf)
        out.write(f"#### {fq} {os.path.basename(pdf)} pages={len(doc)}\n")
        for pn in range(1, min(len(doc), 12) + 1):
            rows = page_rows(doc, pn)
            flat = " ".join(" ".join(t for _, _, t in ws) for _, ws in rows)
            if "기타사업비용" in flat.replace(" ", ""):
                out.write(f"  --- page {pn}\n")
                # header rows (periods)
                for y, ws in rows:
                    line = " ".join(t for _, _, t in ws)
                    if re.search(r"기타사업비용|보험손익|구\s*분|\(2\d\.\dQ\)|\d{4}\.\dQ|당분기|당기|전년", line.replace("  ", " ")) and y < 600:
                        out.write(f"     {y:6.1f} | {line[:200]}\n")
