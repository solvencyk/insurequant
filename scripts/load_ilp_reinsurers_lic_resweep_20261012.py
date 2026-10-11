# -*- coding: utf-8 -*-
"""Re-sweep extension of scripts/load_ilp_reinsurers_lic.py (items 10-15 of the reinsurer ILP from the 업무보고서식 BS block of the own 경영공시 PDF).

The 2026-10-11 run covered 2024.4Q-2026.2Q only.  The quarterly filings of 뮌헨(KR1101) and 하노버(KR1104) carry the same BS block from FY2023_Q1 on, so the
quarters 2023.1Q-2024.3Q (+ 2023.4Q from the prior-year-end column of the FY2024 quarterly filings) are printed too.  Same reader, same checks
(R-LIC1 item 15 == the filing's own 「(보험계약부채)」 line, R-LIC3 sums, R-LIC2 vs item 8 where item 8 exists), same additive merge + provenance.
A cell failing a check is rejected and NOTHING is written (the base script aborts) -- fix the source list, never the check.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_reinsurers_lic_resweep_20261012.py [--write] [--report out.json]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_ilp_reinsurers_lic as M  # noqa: E402

M.TICKET = "inbox/parser/20261012T0120Z__orchestrator__KR1101-KR1108_2023.1Q-2026.2Q__reinsurer_csm_ilp_sensitivity_resweep.md"
M.SOURCES = {
    "KR1101": ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"],
    "KR1104": ["FY2023_Q1", "FY2023_Q2", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"],
}
M.SCOPE_Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]

if __name__ == "__main__":
    M.main()
