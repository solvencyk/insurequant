# -*- coding: utf-8 -*-
"""Re-sweep extension of scripts/load_ilp_reinsurers.py: ILP items 1-8 of the reinsurers for 2023.4Q.

The FY2024 year-end 경영공시 4-6-2 prints '<2023년>' next to '<2024년>' for 뮌헨(KR1101), 하노버(KR1104), 퍼시픽(KR1107) (and RGA via the audit note).
Same reader, same footing / sign / balance-sheet checks as the 2026-10-11 run; one MANUAL entry:
  KR1101 2023.4Q: the printed 합계 row of the 2023 table is sign-inverted as a whole (BEL +2,531, RA -154, CSM -502, PAA 33.61, i.e. liability-negative) while the
  2024 table of the same page is liability-positive. Independent anchors: (a) the printed numbers sum to +1,908.6 = -(net remaining-coverage liability -1,908.05 of the
  balance sheet block read by load_ilp_reinsurers_lic_resweep: R-LIC2 style check), (b) CSM 502 = audit-report CSM 502.41 (liability).  The vector is therefore loaded
  with every sign reversed; this is the only place a printed sign is changed and the evidence is stored in the provenance cell.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_reinsurers_resweep_20261012.py [--write] [--report out.json]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_ilp_reinsurers as M  # noqa: E402
import load_ilp_reinsurers_lic as LL  # noqa: E402

M.TICKET = "inbox/parser/20261012T0120Z__orchestrator__KR1101-KR1108_2023.1Q-2026.2Q__reinsurer_csm_ilp_sensitivity_resweep.md"
M.QUARTERS = ["2023.4Q"]
M.MANUAL[("KR1101", "FY2024_Q4", "2023.4Q")] = dict(
    vec=[-2531, 154, 502, 0, 0, 0, -33.61], unit="억원", page=15, label="<2023년>", src="PDF",
    evidence=("FY2024 4-6-2 p15 <2023년> 합계 printed '2,531 -154 -502 | 33.61' (generic reading: BEL +2,531, RA -154, CSM -502, PAA 33.61 = liability-negative, the 2024 table on the same page is "
              "liability-positive). Detail rows foot (건강 127-22-29, 복합 1,607-104-361, 사망 298-21-10, 장기손해 복합 499-6-103, 일반 84.57, 자동차 -50.97). "
              "Whole vector reversed: BEL -2,531, RA +154, CSM +502, PAA -33.61. Anchors: printed sum +1,908.6 = -(balance-sheet net LRC -1,908.05, FY2024_Q1 prior-year-end column) within 0.6억; "
              "CSM 502 = audit-report CSM 502.41(liability)"),
    flags=["printed_sign_reversed_whole_vector_verified_by_bs_net_lrc_and_audit_csm"])
M.WITHHOLD[("KR1104", "2023.4Q")] = (
    "FY2024_Q4 p17 prints the 2023 table (합계 (572.65) 77.05 254.77 백만원->억원; detail rows foot) but it is on the pre-restatement basis (CSM 254.77; the FY2024 audit report restates the 2023 closing CSM to 258.73) "
    "and its net remaining-coverage total (-240.83) disagrees with the balance-sheet net LRC of the FY2024_Q1 prior-year-end column (-73.43); the same filing's 4-6-1 prints a 2023 보험계약부채 of 200.75억 "
    "against 358.31억 in the FY2024_Q1 balance sheet. Latest-filing rule cannot be applied to a table without a restated twin: not loaded")
# balance-sheet cross-check source for 2023.4Q (prior-year-end column of the FY2024 quarterly filings)
LL.SOURCES = {"KR1101": ["FY2024_Q1", "FY2024_Q2", "FY2024_Q3"], "KR1104": ["FY2024_Q1", "FY2024_Q2"]}
LL.SCOPE_Q = ["2023.4Q"]
M._NET = None

if __name__ == "__main__":
    M.main()
