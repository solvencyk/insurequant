# -*- coding: utf-8 -*-
"""Check whether the table at a known XML line is being yielded at all."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def main():
    xml = Path(sys.argv[1])
    target_line = int(sys.argv[2]) if len(sys.argv) > 2 else 31100
    window = 200
    found = 0
    for t in _iter_tables_with_context(xml):
        if target_line - window < t.line_no < target_line + window:
            print(f"yielded line={t.line_no} caption={t.caption[:120]!r}")
            print(f"  rows={len(t.rows)} cols={len(t.rows[0]) if t.rows else 0}")
            if t.rows:
                print(f"  first body row: {t.rows[0][:6]}")
            found += 1
    print(f"\n[done] {found} tables in [{target_line-window}, {target_line+window}]")


if __name__ == "__main__":
    main()
