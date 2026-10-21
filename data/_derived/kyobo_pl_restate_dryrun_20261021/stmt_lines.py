"""Read-only: locate the SEPARATE-basis income statement (포괄손익계산서) and the 4 Kyobo note tables in a raw filing with raw line numbers.

Uses the evidence-folder xmltab parser of the CSM fix (same repo-relative folder).  Prints every row of the statement with its label,
all numeric cells and the LAST cell's line number (= prior-period cumulative column).

Usage: python stmt_lines.py <FY dir name e.g. FY2024_Q1> [--notes]
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"))
from xmltab import parse_tables, num  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main_xml(fy):
    base = ROOT / "data" / "dart" / fy / "raw"
    d = sorted(base.glob("KR0073_*"))[0]
    cands = [p for p in list(d.glob("*.xml")) + list(d.glob("xml/*.xml")) if "_007" not in p.name]
    return sorted(cands, key=lambda p: p.stat().st_size, reverse=True)[0]


def sep_range(titles):
    s = e = None
    for ln, t in titles:
        if re.search(r"\d+\.\s*재무제표$", t) and "연결" not in t:
            s = ln
        if re.search(r"\d+\.\s*재무제표 주석$", t) and "연결" not in t:
            e = ln
    return s, e


def main():
    fy = sys.argv[1]
    path = main_xml(fy)
    tabs, titles = parse_tables(str(path))
    s, e = sep_range(titles)
    print(f"file={path.relative_to(ROOT)}  separate FS title line={s}  separate notes title line={e}")
    for t in tabs:
        if s and e and not (s < t["start"] < e):
            continue
        labels = [r[1][0] for r in t["rows"] if r[1]]
        if any("영업이익" in x or "영업손익" in x for x in labels) and any("당기순이익" in x or "분기순이익" in x or "반기순이익" in x for x in labels):
            hdr = [c for _, cells, _ in t["header_rows"] for c in cells]
            print(f"STATEMENT TABLE L{t['start']}-{t['end']} caption={t['caption'][:60]!r} header={hdr[:12]}")
            for ln, cells, cl in t["rows"]:
                nums = [c for c in cells[1:]]
                print(f"   L{cl[-1] if cl else ln}: {cells[0][:44]:44s} {nums}")
            break


if __name__ == "__main__":
    main()
