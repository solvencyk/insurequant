# -*- coding: utf-8 -*-
"""Run the real extract_tier2() from fix_20260821_tier2_limit_lines.py against a given
(code, quarter) and print found/anchor/reason -- to see exactly why a cell is missing.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fix_20260821_tier2_limit_lines import extract_tier2, _pdf, q2p  # noqa: E402


def main():
    code = sys.argv[1]
    q = sys.argv[2]
    pdf = _pdf(q2p(q), code)
    print(f"pdf = {pdf}")
    if pdf is None:
        return 1
    found, anchor, reason = extract_tier2(pdf)
    print(f"found = {found}")
    print(f"anchor = {anchor}")
    print(f"reason = {reason}")


if __name__ == "__main__":
    raise SystemExit(main())
