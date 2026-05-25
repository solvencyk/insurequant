# -*- coding: utf-8 -*-
"""Debug one company's filing — print all CSM-caption tables and their scores."""

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
    if len(sys.argv) < 2:
        raise SystemExit("usage: ifrs17_debug_one.py <raw_subdir_name>")
    target_dir = settings.raw_dir / sys.argv[1]
    if not target_dir.is_dir():
        raise SystemExit(f"not a dir: {target_dir}")
    for xml in sorted(target_dir.glob("*.xml")):
        print(f"\n=== {xml.name} ===")
        for t in _iter_tables_with_context(xml):
            cap = t.caption
            if "보험계약마진" not in cap:
                continue
            t = score_table(t)
            print(f"line={t.line_no} score={t.score} form={t.form_type}")
            print(f"  caption: {cap[:160]}")
            print(f"  header rows: {len(t.header)}")
            for i, hr in enumerate(t.header[:3]):
                print(f"    [{i}] {hr[:18]}")
            print(f"  body rows: {len(t.rows)} cols={len(t.rows[0]) if t.rows else 0}")
            if t.rows:
                print(f"  first body row: {t.rows[0][:8]}")
            print(f"  reasons: {t.reasons}")
            print()


if __name__ == "__main__":
    main()
