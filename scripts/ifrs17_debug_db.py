# -*- coding: utf-8 -*-
"""Debug what the extractor sees for DB손해보험."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.csm_extractor import (  # noqa: E402
    _iter_tables_with_context, score_table,
)


def main():
    target_dir = settings.raw_dir / "DB손해보험_20250313001342"
    for xml in sorted(target_dir.glob("*.xml")):
        print(f"\n=== {xml.name} ===")
        for t in _iter_tables_with_context(xml):
            cap = t.caption
            if "보험계약마진" in cap and (
                "상각" in cap or "예상" in cap or "인식" in cap
                or "향후" in cap
            ):
                t = score_table(t)
                print(f"line={t.line_no} score={t.score}")
                print(f"  caption: {cap[:120]}")
                print(f"  header rows: {len(t.header)}")
                for i, hr in enumerate(t.header):
                    print(f"    [{i}] {hr}")
                print(f"  body rows: {len(t.rows)} cols={len(t.rows[0]) if t.rows else 0}")
                if t.rows:
                    print(f"  first body row: {t.rows[0]}")
                print(f"  reasons: {t.reasons}")
                print()


if __name__ == "__main__":
    main()
