import sys, re, fitz
pdf, lo, hi, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
doc = fitz.open(pdf)
with open(outp, "w", encoding="utf-8") as f:
    for p in range(lo, hi + 1):
        f.write(f"--- p{p}: " + re.sub(r"\s+", " ", doc[p-1].get_text()) + "\n")
