# -*- coding: utf-8 -*-
"""fitz find_tables()가 이 표를 표준 grid로 잡아주는지 실험."""
import fitz, os, sys, io

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
    tabs = page.find_tables()
    print("n_tables:", len(tabs.tables))
    for ti, t in enumerate(tabs.tables):
        print(f"--- table {ti} bbox={t.bbox} rows={t.row_count} cols={t.col_count} ---")
        for row in t.extract():
            print(row)
    doc.close()


if __name__ == "__main__":
    main()
