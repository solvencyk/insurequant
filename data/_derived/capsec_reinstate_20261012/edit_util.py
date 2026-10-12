# -*- coding: utf-8 -*-
"""Exact-string edit helper that preserves CRLF/LF and BOM-less UTF-8 (each old string must occur exactly once)."""
from pathlib import Path


def edit(path, pairs):
    p = Path(path)
    t = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in t
    t = t.replace("\r\n", "\n")
    for old, new in pairs:
        assert t.count(old) == 1, (path, t.count(old), old[:80])
        t = t.replace(old, new)
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))
    print("edited", path, "crlf" if crlf else "lf")
