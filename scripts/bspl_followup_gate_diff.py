#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff two saved outputs of scripts/validate_data_contract.py (finding lines only): which RED/YELLOW findings appeared / vanished.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_gate_diff.py <before.txt> <after.txt>
A finding = a 'RED|YELLOW [source] RULE  subject' line plus its (indented) detail lines up to the next finding.  Read-only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HEAD = re.compile(r"^\s+(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(.*)$")


def parse(path):
    out, cur = {}, None
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = HEAD.match(ln)
        if m:
            cur = (m.group(1), m.group(2), m.group(3), m.group(4).strip())
            out.setdefault(cur, [])
        elif cur is not None and ln.startswith("         "):
            out[cur].append(ln.strip())
        elif ln.strip().startswith(("=", "-", "#")) or not ln.strip():
            cur = None if ln.strip().startswith(("=", "#")) else cur
    return out


def main():
    a, b = parse(sys.argv[1]), parse(sys.argv[2])
    ka, kb = set(a), set(b)
    print(f"before {len(ka)} findings ({sum(1 for k in ka if k[0] == 'RED')} RED), after {len(kb)} ({sum(1 for k in kb if k[0] == 'RED')} RED)")
    for k in sorted(kb - ka):
        print("NEW     ", k[0], k[1], k[2], k[3], "|", " ".join(b[k])[:300])
    for k in sorted(ka - kb):
        print("VANISHED", k[0], k[1], k[2], k[3], "|", " ".join(a[k])[:300])
    for k in sorted(ka & kb):
        if a[k] != b[k]:
            print("CHANGED ", k[0], k[1], k[2], k[3], "|", " ".join(a[k])[:200], "=>", " ".join(b[k])[:200])


if __name__ == "__main__":
    main()
