"""Read-only: list table captions + short row-1 snippet in a line-no window, for structure
scouting across KR0079 (미래에셋생명) filings. Does not touch any master JSON.

Usage: python mirae_list_captions.py <xml_path> <lo> <hi>
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def main():
    xml_path = Path(sys.argv[1])
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    tables = list(_iter_tables_with_context(xml_path))
    for t in tables:
        if lo <= t.line_no <= hi:
            flat = "".join("".join(r[:2]) for r in t.rows[:3])
            print(t.line_no, repr(t.caption[:44]), "|", flat[:64])


if __name__ == "__main__":
    main()
