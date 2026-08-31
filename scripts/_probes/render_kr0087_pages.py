import fitz
import sys
doc = fitz.open("data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf")
for i in range(15, 22):  # pages 16-22 (1-indexed)
    pix = doc[i].get_pixmap(dpi=240)
    out = f"scripts/_probes/kr0087_p{i+1}.png"
    pix.save(out)
    print(out)
