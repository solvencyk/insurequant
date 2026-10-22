#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 6: from the s4_stmt_*.txt dumps print only the rows that carry an item of the PL Tier-1 vector (1,16..32) -> stdout
usage: s6_view_keyrows.py CODE FY [FY ...]"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
KEY = re.compile(r"보험손익|보험서비스|투자손익|영업이익|영업손익|법인세|순이익|순손익|기타포괄|채무증권|위험회피|보험계약자산|재보험계약자산|지분증권|지분상품|유가증권|재평가|재측정|총포괄|금융자산관련손익|금융자산평가손익|"
                 r"보험금융|재보험금융|기타사업비용|영업외|단위|^\[.*기 ")
for fy in sys.argv[2:]:
    p = HERE / f"s4_stmt_{sys.argv[1]}_{fy}.txt"
    print("#####", p.name)
    for ln in p.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("#"):
            print(ln[:200])
            continue
        m = re.match(r"R(\d+) \[(.*?)\] (.*)$", ln)
        if not m:
            continue
        if KEY.search(m.group(2)) and not re.search(r"주당|이자수익|배당금|이익 \(주|손실 \(주", m.group(2)):
            body = m.group(3)
            body = re.sub(r"::---", "", body)
            body = re.sub(r":SEP", "", body)
            print(f"R{m.group(1)} [{m.group(2)[:46]}] {body[:330]}")
