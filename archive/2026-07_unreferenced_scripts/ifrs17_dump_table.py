# -*- coding: utf-8 -*-
"""Dump raw parsed table at a sourceline to see how lxml sees it."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from lxml import etree  # noqa: E402


def main():
    xml = Path(sys.argv[1])
    target_line = int(sys.argv[2])
    parser = etree.HTMLParser(encoding="utf-8", huge_tree=True, recover=True)
    tree = etree.parse(str(xml), parser)
    for el in tree.getroot().iter("table"):
        line = getattr(el, "sourceline", 0) or 0
        if not (target_line - 30 <= line <= target_line + 30):
            continue
        print(f"\n=== TABLE at line {line} ===")
        # Use the EXACT logic of _iter_tables_with_context for this element.
        header_rows = []
        body_rows = []
        for sub in el.iter():
            stag = (sub.tag or "").lower()
            if stag != "tr":
                continue
            cells = []
            for c in sub:
                ctag = (c.tag or "").lower()
                if ctag in ("th", "td"):
                    cells.append("".join(c.itertext()).strip()[:18])
            if not cells:
                continue
            in_thead = False
            parent = sub.getparent()
            while parent is not None:
                if (parent.tag or "").lower() == "thead":
                    in_thead = True
                    break
                parent = parent.getparent()
            if in_thead:
                header_rows.append(cells)
            else:
                body_rows.append(cells)
        print(f"  header_rows={len(header_rows)} body_rows={len(body_rows)}")
        for h in header_rows[:3]:
            print(f"    H{len(h)} {h}")
        for b in body_rows[:5]:
            print(f"    B{len(b)} {b}")


if __name__ == "__main__":
    main()
