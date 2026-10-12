import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
here = os.path.dirname(os.path.abspath(__file__))
# (code, q, filing_offset_to_use, headline page, pdf-name-substring)
CASES = [("KR0009","2023.1Q",2,12),("KR0009","2023.2Q",2,42),("KR0049","2025.1Q",2,16),("KR0050","2025.3Q",2,17),
         ("KR0069","2024.2Q",2,51),("KR0080","2026.1Q",1,20),("KR0095","2024.4Q",2,18),("KR0099","2024.3Q",2,18)]
out = open(here + "/b1_mirror_text.txt", "w", encoding="utf-8")
for code, q, n, hp in CASES:
    fq = qadd(q, n)
    pdfs = filing_pdfs(code, fq)
    out.write(f"===== {code} {q} using filing {fq}: {[os.path.basename(p) for p in pdfs]} headline p{hp}\n")
    pdf = pdfs[0]
    doc = fitz.open(pdf)
    for p in range(max(1, hp - 2), min(len(doc), hp + 8) + 1):
        flat = re.sub(r"\s+", " ", doc[p-1].get_text())
        if "경과조치" in flat:
            out.write(f"  --- p{p}: {flat[:900]}\n")
