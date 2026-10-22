#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 10: which companies / quarters / items does the owner-confirmed registry (data/_gold/user_pl_confirmed_cells.json) list for PL_breakdown? -> stdout"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
doc = json.loads((ROOT / "data/_gold/user_pl_confirmed_cells.json").read_text(encoding="utf-8"))
cells = [c for c in doc["cells"] if c.get("master") == "PL_breakdown"]
print(len(doc["cells"]), "cells,", len(cells), "PL_breakdown")
print(Counter(c["company"] for c in cells))
TARGET = ["DB생명보험", "푸본현대생명보험", "동양생명", "농협생명보험", "NH농협손해보험", "삼성생명보험", "신한라이프생명보험", "에이비엘생명보험", "케이디비생명보험", "한화생명", "흥국생명보험"]
for c in cells:
    if any(t in c["company"] for t in TARGET):
        print(c)
