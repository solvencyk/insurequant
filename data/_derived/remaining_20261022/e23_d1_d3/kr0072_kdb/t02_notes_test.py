# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from kdb_notes import pl4_note, csm_tables
D = "data/dart"
N = {"N1": f"{D}/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml", "N2": f"{D}/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml",
     "N3": f"{D}/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml", "N4": f"{D}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml"}
O = {"O2": f"{D}/FY2023_Q2/raw/KR0072_케이디비생명보험/xml/20230814003052.xml", "O3": f"{D}/FY2023_Q3/raw/KR0072_케이디비생명보험/xml/20231114002983.xml",
     "O4": f"{D}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710.xml"}
for k, rel in {**N, **O}.items():
    print("=====", k)
    try:
        p = pl4_note(rel)
        print("  PL4 note:", p["printed"], "L", p["line"], "unit", p["unit"], "table", p["table"], "n_numeric", p["n_numeric"], "heads", p["heads"], "prior_3m", p.get("prior_3m"))
    except Exception as e:
        print("  PL4 note ERROR", e)
    try:
        T = csm_tables(rel)
        for role in sorted(T, key=str):
            t = T[role]
            print("  CSM", role, "table", t["table"], "unit", t["unit"], "caption", t["caption"], "col", t["col"])
            print("     ", [(i, (r["printed"], r["line"]) if r else None) for i, r in t["rows"].items()])
            print("      extra", {k: (v["printed"], v["line"]) for k, v in t["extra"].items()})
    except Exception as e:
        print("  CSM ERROR", e)
