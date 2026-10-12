# -*- coding: utf-8 -*-
"""Deduction / utilization changes caused by excluding past_call_outstanding bonds (new z3 vs the previous z3 snapshot)."""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def rd(p):
    with (HERE / p).open(encoding="utf-8-sig", newline="") as fh:
        return {r["code"]: r for r in csv.DictReader(fh)}


a, b = rd("z3_prev_flag_only_47.csv"), rd("z3_tier2_before_after_47.csv")
L = ["Effect of deriving the exclusion from call_date <= numerator date (prev = ledger flag only)",
     "code company | deduction hyb prev->new | sub prev->new | printed 53/54 | pct prev->new | numerator prev->new"]
for c in a:
    x, y = a[c], b[c]
    if (x["ledger_pre2023_hybrid"], x["ledger_pre2023_sub"]) != (y["ledger_pre2023_hybrid"], y["ledger_pre2023_sub"]):
        L.append(f"{c} {y['company'][:9]:9s} | hyb {x['ledger_pre2023_hybrid']} -> {y['ledger_pre2023_hybrid']} | sub {x['ledger_pre2023_sub']} -> {y['ledger_pre2023_sub']} | "
                 f"printed {y['printed_53']}/{y['printed_54']} | pct {x['pct_after']} -> {y['pct_after']} | num {x['numerator_after']} -> {y['numerator_after']}")
(HERE / "z11_calldate_vs_flag_only.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
