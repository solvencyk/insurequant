# -*- coding: utf-8 -*-
"""REJECT_SELF_CLOSURE 5칸의 raw_value 와 원문 grid row 를 그대로 덤프한다 -- 등식이 깨진
원인이 (a) 추출기 버그인지 (b) 원문 자체의 불일치인지 가른다.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260918g_reject_raw.py
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # noqa: E402

from extract_pl_backfill_disclosure import (  # noqa: E402
    ROOT, _core_label_hits, _find_idx_cur, find_pdf,
)

fitz.TOOLS.mupdf_display_errors(False)
STAGING = os.path.join(ROOT, "data", "_derived", "pl_backfill_disclosure_20260918.json")

TARGETS = [("KR0050", "2023.1Q"), ("KR0074", "2023.2Q"),
           ("KR0080", "2024.1Q"), ("KR0080", "2024.2Q"), ("KR0080", "2024.3Q")]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    with open(STAGING, encoding="utf-8") as f:
        st = json.load(f)
    cmap = {(c["원보험사코드"], c["공시분기"]): c for c in st["cells"]}

    for code, q in TARGETS:
        cell = cmap[(code, q)]
        print("=" * 78)
        print(f"{code} {cell['원보험사명']} {q}  page={cell.get('page')}  {cell['source_file']}")
        print("-- staging raw_value --")
        for k, r in sorted(cell["items"].items(), key=lambda kv: int(kv[0])):
            print(f"   item{k:<3} {r['항목명']:<12} raw={r['raw_value']!r:<14} "
                  f"label={r['raw_label']!r}")
        for k, r in cell["components"].items():
            print(f"   comp  {k:<16} raw={r['raw_value']!r:<14} label={r['raw_label']!r}")
        print("-- pdf grid rows --")
        pdf = find_pdf(code, q)
        doc = fitz.open(pdf)
        try:
            for i in range(min(40, doc.page_count)):
                page = doc[i]
                t = page.get_text()
                if "포괄손익계산서" not in t or _core_label_hits(t) < 3:
                    continue
                for tab in page.find_tables().tables:
                    rows = tab.extract()
                    if not rows or len(rows) < 5:
                        continue
                    idx_cur = _find_idx_cur(rows)
                    if idx_cur is None:
                        continue
                    print(f"   page {i + 1}  idx_cur={idx_cur}  ncols={len(rows[0])}")
                    for ri, row in enumerate(rows):
                        cells = [("" if v is None else str(v).replace("\n", "|")) for v in row]
                        print(f"     r{ri:<2} {cells}")
                    doc.close()
                    break
                else:
                    continue
                break
        finally:
            try:
                doc.close()
            except Exception:
                pass
        print()


if __name__ == "__main__":
    main()
