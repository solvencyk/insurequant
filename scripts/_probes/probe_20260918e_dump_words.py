# -*- coding: utf-8 -*-
"""좌표 기반 워드 덤프 - 표 재구성 설계용.
사용: python probe_20260918e_dump_words.py <code> <quarter> <page>
"""
import fitz, os, io, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fitz.TOOLS.mupdf_display_errors(False)


def quarter_to_folder(q):
    fy, qq = q.split(".")
    return f"FY{fy}_Q{qq[0]}"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    code, q, page_no = sys.argv[1], sys.argv[2], int(sys.argv[3])
    folder = quarter_to_folder(q)
    rawdir = os.path.join(ROOT, "data", "disclosure", folder, "raw")
    cands = [f for f in os.listdir(rawdir) if f.startswith(code + "_")]
    pdf_path = os.path.join(rawdir, cands[0])
    doc = fitz.open(pdf_path)
    page = doc[page_no - 1]
    words = page.get_text("words")  # (x0,y0,x1,y1,text,block,line,word)
    words.sort(key=lambda w: (round(w[1], 1), w[0]))
    for w in words:
        print(f"y={w[1]:7.1f} x={w[0]:7.1f} block={w[5]:3d} line={w[6]:2d} word='{w[4]}'")
    doc.close()


if __name__ == "__main__":
    main()
