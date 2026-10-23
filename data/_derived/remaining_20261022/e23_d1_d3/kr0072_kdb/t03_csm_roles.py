# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from kdb_notes import csm_tables
D = "data/dart"
N = {"N1": f"{D}/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml"}
for k, rel in N.items():
    T = csm_tables(rel)
    for role, t in T.items():
        print(k, repr(role), t["table"], t["caption"])
