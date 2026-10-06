# -*- coding: utf-8 -*-
"""20260918 특정 (code, quarter, page) 텍스트를 그대로 덤프 - 레이아웃 눈으로 확인용.
사용: python probe_20260918d_dump_pages.py <code> <quarter> <page1> [<page2> ...]
      python probe_20260918d_dump_pages.py <code> <quarter> --find <keyword>   # 전체 문서에서 키워드 있는 페이지 나열
"""
import fitz, os, io, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fitz.TOOLS.mupdf_display_errors(False)


def quarter_to_folder(q):
    fy, qq = q.split(".")
    return f"FY{fy}_Q{qq[0]}"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    code, q = sys.argv[1], sys.argv[2]
    folder = quarter_to_folder(q)
    rawdir = os.path.join(ROOT, "data", "disclosure", folder, "raw")
    cands = [f for f in os.listdir(rawdir) if f.startswith(code + "_")]
    if not cands:
        print("NO_PDF_FILE", rawdir)
        return
    pdf_path = os.path.join(rawdir, cands[0])
    print("FILE:", pdf_path)
    doc = fitz.open(pdf_path)
    print("n_pages:", doc.page_count)
    if sys.argv[3] == "--find":
        kw = sys.argv[4]
        hits = []
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if kw in t:
                hits.append(i + 1)
        print(f"pages containing '{kw}':", hits)
    else:
        for p in sys.argv[3:]:
            i = int(p) - 1
            if 0 <= i < doc.page_count:
                print(f"\n===== PAGE {p} (textlen={len(doc[i].get_text())}) =====")
                print(doc[i].get_text())
    doc.close()


if __name__ == "__main__":
    main()
