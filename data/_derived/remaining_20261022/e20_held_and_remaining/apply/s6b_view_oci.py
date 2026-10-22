#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 6b: from the s4_stmt_*.txt dumps print the rows from the net-income row down to 총포괄손익 (the OCI block) -> stdout, plus 3 P&L anchor rows
usage: s6b_view_oci.py CODE FY [FY ...]"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
NI = re.compile(r"순이익|순손익")
for fy in sys.argv[2:]:
    p = HERE / f"s4_stmt_{sys.argv[1]}_{fy}.txt"
    print("#####", p.name)
    on = False
    for ln in p.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("#"):
            print(ln[:160])
            continue
        m = re.match(r"R(\d+) \[(.*?)\] (.*)$", ln)
        if not m:
            continue
        lab = m.group(2)
        if re.search(r"주당", lab):
            on = False
        if NI.search(lab) and not re.search(r"지배|비지배", lab):
            on = True
        if on or re.match(r"(영업이익|영업손익|보험손익|보험서비스결과|투자손익)$", lab.replace(" ", "")):
            body = re.sub(r"::---", "", m.group(3))
            body = re.sub(r":SEP", "", body)
            body = re.sub(r"_ifrs-ful", "", body)
            print(f"R{m.group(1)} [{lab[:50]}] {body[:300]}")
