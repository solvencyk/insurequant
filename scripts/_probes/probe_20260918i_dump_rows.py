# -*- coding: utf-8 -*-
"""지정 셀의 §2-1 표 grid row 를 그대로 덤프한다 (진단 전용).
실행: ...python.exe scripts/_probes/probe_20260918i_dump_rows.py KR1098 2023.2Q [KR1098 2023.3Q ...]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # noqa: E402

from extract_pl_backfill_disclosure import _core_label_hits, _find_idx_cur, find_pdf  # noqa: E402

fitz.TOOLS.mupdf_display_errors(False)


def dump(code, q):
    pdf = find_pdf(code, q)
    print("=" * 70)
    print(code, q, pdf)
    if pdf is None:
        return
    doc = fitz.open(pdf)
    try:
        for i in range(min(40, doc.page_count)):
            page = doc[i]
            t = page.get_text()
            if "포괄손익계산서" not in t or _core_label_hits(t) < 3:
                continue
            for tab in page.find_tables().tables:
                rows = tab.extract()
                if not rows or len(rows) < 5 or _find_idx_cur(rows) is None:
                    continue
                print(f"page {i + 1} idx_cur={_find_idx_cur(rows)}")
                for ri, row in enumerate(rows):
                    print(f"  r{ri:<2}", [("" if v is None else str(v).replace("\n", "|")) for v in row])
                if i + 1 < doc.page_count:
                    for ntab in doc[i + 1].find_tables().tables:
                        nrows = ntab.extract()
                        print(f"  -- next page {i + 2} table ({len(nrows)} rows) --")
                        for ri, row in enumerate(nrows[:20]):
                            print(f"  n{ri:<2}", [("" if v is None else str(v).replace("\n", "|")) for v in row])
                return
    finally:
        doc.close()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    args = sys.argv[1:]
    for k in range(0, len(args) - 1, 2):
        dump(args[k], args[k + 1])


if __name__ == "__main__":
    main()
