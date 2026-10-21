"""Read-only: list every table with a '보험계약마진' header column and 기초/기말 rows, per KR0073 filing.

Prints: file, table start/end lines, section (연결주석 / 별도FS / 별도주석), caption, unit, header, and the
CSM-column values of the 기초/기말 rows (with the cell line numbers).
Usage: python list_csm_tables.py <xml_path> [<xml_path> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xmltab import parse_tables, num  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def section_of(line, titles):
    """Which major section a line belongs to, by ATOC titles '연결재무제표 주석' / '재무제표' / '재무제표 주석'."""
    sec = "?"
    for ln, t in titles:
        if ln > line:
            break
        if t.endswith("연결재무제표 주석"):
            sec = "CONS-NOTES"
        elif t.endswith("연결재무제표"):
            sec = "CONS-FS"
        elif t.endswith("재무제표 주석") and "연결" not in t:
            sec = "SEP-NOTES"
        elif t.endswith("재무제표") and "연결" not in t and "주석" not in t:
            sec = "SEP-FS"
    return sec


def main():
    for p in sys.argv[1:]:
        tabs, titles = parse_tables(p)
        print("=" * 100)
        print(p, f"({len(tabs)} tables)")
        print("titles:", [(l, t[:30]) for l, t in titles if "재무제표" in t or "감사" in t][:12])
        for t in tabs:
            hdr_cells = []
            for _, cells, _ in t["header_rows"]:
                hdr_cells.extend(cells)
            if not any("보험계약마진" in c for c in hdr_cells):
                continue
            labels = [r[1][0] for r in t["rows"] if r[1]]
            if not any(("기초" in lb and "보험" in lb) or lb.startswith("1. 기초") for lb in labels):
                continue
            sec = section_of(t["start"], titles)
            print("-" * 100)
            print(f"TABLE L{t['start']}-{t['end']} sec={sec} nrows={len(t['rows'])}")
            print("  caption(L%d): %s" % (t["caption_line"], t["caption"][:260]))
            print("  unit:", t["unit"][:80])
            print("  header:", [c for c in hdr_cells][:8])
            # CSM column index
            hdr_last = t["header_rows"][-1][1] if t["header_rows"] else []
            idx = None
            for k, c in enumerate(hdr_last):
                if "보험계약마진" in c:
                    idx = k
            print("  csm col idx in last header row:", idx, "| ncols(first data row):", len(t["rows"][0][1]) if t["rows"] else None)
            for ln, cells, cl in t["rows"]:
                lb = cells[0] if cells else ""
                if idx is not None and len(cells) > idx:
                    v = cells[idx]
                else:
                    v = None
                if any(k in lb for k in ("기초", "기말", "보험금융", "추정치", "최초 인식", "상각", "서비스 이전", "미래서비스", "현재서비스", "과거서비스", "환율", "기타", "투자요소", "손실부담")):
                    print(f"    L{ln}: {lb[:60]} | CSM[{idx}]={v} (cell L{cl[idx] if idx is not None and len(cl) > idx else None}) | row={cells[1:]}")


if __name__ == "__main__":
    main()
