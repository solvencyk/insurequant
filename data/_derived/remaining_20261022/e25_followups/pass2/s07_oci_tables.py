# -*- coding: utf-8 -*-
"""READ-ONLY: list tables containing 총포괄손익 with title/caption/unit (diagnostic for oci_read.py)."""
import sys
import p2lib as P
sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
path = P.main_path(code, fy)
lines = P.M.read_lines(path)
for t in P.M.iter_tables(lines):
    blob = P.nl(P._TAGRE.sub("", " ".join(lines[t["start"] - 1:t["end"]])))
    if "총포괄손익" in blob or "총포괄이익" in blob:
        print(t["start"], t["end"], repr(t["title"]), repr((t["caption"] or "")[:40]), "기타포괄손익" in blob, "당기순이익" in blob, "반기순이익" in blob, "분기순이익" in blob)
