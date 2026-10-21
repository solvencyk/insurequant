"""Read-only: dump one table (by its <TABLE> start line) completely, with raw line numbers.

Usage: python dump_table.py <xml_path> <table_start_line> [more start lines ...]
Prints header rows (cells + lines) and every data row: TR line, label, all cells, plus the cell line of each value.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xmltab import parse_tables  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main():
    path = sys.argv[1]
    starts = [int(x) for x in sys.argv[2:]]
    tabs, _ = parse_tables(path)
    by_start = {t["start"]: t for t in tabs}
    for s in starts:
        t = by_start.get(s)
        if t is None:
            print(f"!! no table starting at L{s} (nearest: {sorted(by_start)[:0]})")
            continue
        print("=" * 100)
        print(f"{path}\nTABLE L{t['start']}-{t['end']}  caption(L{t['caption_line']}): {t['caption'][:200]}")
        print("unit:", t["unit"])
        for ln, cells, cl in t["header_rows"]:
            print(f"  HDR L{ln}: {cells}")
        for ln, cells, cl in t["rows"]:
            print(f"  L{ln}: {cells[0][:70]!r}")
            for k, (c, l) in enumerate(zip(cells[1:], cl[1:]), start=1):
                print(f"        c{k}=L{l}:{c}")


if __name__ == "__main__":
    main()
