"""Read-only structural dump for one KR0079 filing: print header + first matching row for
every table whose rows mention '발생한 보험금' (any variant), so we can compare table SHAPE
(column count, LRC/LIC split y/n) across quarters -- not just label-string presence.

Does not touch any master JSON.

Usage:
  python mirae_yesilcha_structure_dump.py <path-to-xml> [<label>]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def main():
    xml_path = Path(sys.argv[1])
    label = sys.argv[2] if len(sys.argv) > 2 else str(xml_path)
    tables = list(_iter_tables_with_context(xml_path))
    print(f"=== {label}: {xml_path.name} -- {len(tables)} tables total ===")
    hit = 0
    for t in tables:
        flat = "".join("".join(r) for r in t.rows)
        if "발생한보험금" not in flat.replace(" ", ""):
            continue
        hit += 1
        print(f"\n--- table @ line {t.line_no}  caption={t.caption[:60]!r} ---")
        for hr in t.header:
            print("  H:", " | ".join(c[:18] for c in hr))
        for r in t.rows:
            joined = "".join(r[:2])
            if "발생한보험금" in joined.replace(" ", ""):
                print("  R:", " | ".join(c[:18] for c in r))
    print(f"\ntotal matching tables: {hit}")


if __name__ == "__main__":
    main()
