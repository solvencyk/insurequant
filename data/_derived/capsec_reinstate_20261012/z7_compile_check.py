# -*- coding: utf-8 -*-
"""Compile every .py in this folder with warnings as errors + BOM check (one process)."""
import glob
import sys
import warnings
from pathlib import Path

warnings.simplefilter("error")
bad = []
for p in sorted(glob.glob(str(Path(__file__).resolve().parent / "*.py"))):
    b = Path(p).read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        bad.append((p, "BOM"))
    try:
        compile(b.decode("utf-8"), p, "exec")
    except Exception as e:  # noqa: BLE001
        bad.append((p, repr(e)[:100]))
print("bad:", bad)
sys.exit(1 if bad else 0)
