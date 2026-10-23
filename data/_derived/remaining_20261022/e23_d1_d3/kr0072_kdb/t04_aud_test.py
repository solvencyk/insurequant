# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from kdb_raw import lines_of, titles, clean
from kdb_notes import csm_tables
from kdb_stmt import Stmt, items_from, identities
D = "data/dart"
AUD = {"N4AUD": f"{D}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302_00760.xml",
       "O4AUD0": f"{D}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710_00760.xml",
       "O4AUD1": f"{D}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710_00761.xml",
       "A25AUD": f"{D}/FY2025_Q4/raw/KR0072_케이디비생명보험_20260331004180/20260331004180_00760.xml"}
for k, rel in AUD.items():
    L = lines_of(rel)
    print("=====", k, len(L), "lines")
    ts = titles(L)
    print("  titles:", [(i + 1, t[:50]) for i, t in ts][:14])
    try:
        T = csm_tables(rel, 0, len(L) - 1)
        for role, t in T.items():
            print("  CSM", role, t["table"], [(i, r["printed"]) if r else None for i, r in t["rows"].items()])
    except Exception as e:
        print("  CSM ERR", e)
    for sec in (r"포괄손익계산서",):
        try:
            S = Stmt(rel, sec)
            V = S.read(2023, "cum")
            print("  stmt ok: 보험손익", V["ins_result"]["printed"], "L", V["ins_result"]["line"], "paths", S.paths)
        except Exception as e:
            print("  stmt ERR", str(e)[:200])
