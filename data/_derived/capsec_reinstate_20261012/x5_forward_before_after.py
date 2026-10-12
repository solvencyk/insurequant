# -*- coding: utf-8 -*-
"""x5: forward outlook before (before2/, state at the start of this round) vs after (root kics_forward_capital.json).
Proves: total-capital path (capital_eok, scr_eok, ratio_pct, cumulative deductions) unchanged for every insurer and year;
lists basic-capital-ratio path changes and the fields that vanished / changed. Output: x5_forward_before_after.txt, x5_forward_before_after_47.csv
Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capsec_reinstate_20261012/x5_forward_before_after.py
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.stdout.reconfigure(encoding="utf-8")
old = {r.get("insurer_code"): r for r in json.loads((HERE / "before2/kics_forward_capital.json").read_text(encoding="utf-8"))}
new = {r.get("insurer_code"): r for r in json.loads((ROOT / "kics_forward_capital.json").read_text(encoding="utf-8"))}
assert set(old) == set(new)
TOTAL = ("capital_eok", "scr_eok", "ratio_pct", "cumulative_bond_dedu_eok", "cumulative_tier1_dedu_eok", "hybrid_remaining_eok",
         "capacity_exhausted", "hybrid_legacy_remaining_eok", "hybrid_tier1type_remaining_eok", "hybrid_tier2type_remaining_eok")
rows, total_diff, basic_changed = [], [], []
row_field_gone, row_field_changed, proj_field_gone, proj_field_new = set(), [], set(), set()
for code in sorted(new):
    o, n = old[code], new[code]
    if n.get("status") != "ok":
        continue
    row_field_gone |= set(o) - set(n)
    for k in o:
        if k in n and k not in ("projections", "confidence") and o[k] != n[k]:
            row_field_changed.append((code, k))
    for op, np_ in zip(o["projections"], n["projections"]):
        proj_field_gone |= set(op) - set(np_)
        proj_field_new |= set(np_) - set(op)
        for k in TOTAL:
            if op[k] != np_[k]:
                total_diff.append((code, op["year"], k, op[k], np_[k]))
        rows.append(dict(code=code, name=n.get("insurer_name"), year=op["year"], basic_ratio_before=op["basic_ratio_pct"],
                         basic_ratio_after=np_["basic_ratio_pct"], basic_capital_before=op["basic_capital_eok"],
                         basic_capital_after=np_["basic_capital_eok"], total_ratio_before=op["ratio_pct"], total_ratio_after=np_["ratio_pct"],
                         hybrid_tier1_before=op["hybrid_tier1_eok"], hybrid_tier1_after=np_["hybrid_tier1_eok"],
                         overflow_before=op["hybrid_tier2_overflow_eok"], overflow_after=np_["hybrid_tier2_overflow_eok"]))
        if (op["basic_ratio_pct"], op["basic_capital_eok"], op["hybrid_tier1_eok"], op["hybrid_tier2_overflow_eok"]) != \
           (np_["basic_ratio_pct"], np_["basic_capital_eok"], np_["hybrid_tier1_eok"], np_["hybrid_tier2_overflow_eok"]):
            basic_changed.append(code)
with (HERE / "x5_forward_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
L = [f"rows {len(rows)} | total-capital-path diffs (capital, scr, ratio, cumulative deductions, remaining by type): {len(total_diff)} {total_diff[:5]}",
     f"row-level fields that vanished: {sorted(row_field_gone)}", f"projection-level fields that vanished: {sorted(proj_field_gone)} ; new: {sorted(proj_field_new)}",
     f"row-level fields whose value changed (other than vanished): {row_field_changed[:12]}",
     f"companies whose basic path / hybrid_tier1 / overflow changed: {sorted(set(basic_changed))}"]
for code in sorted(set(basic_changed)):
    L.append(f"-- {code} {new[code]['insurer_name']}")
    for r in rows:
        if r["code"] == code:
            L.append(f"   {r['year']} basic% {r['basic_ratio_before']} -> {r['basic_ratio_after']} | basic capital {r['basic_capital_before']} -> {r['basic_capital_after']}"
                     f" | hybrid_tier1 {r['hybrid_tier1_before']} -> {r['hybrid_tier1_after']} | overflow {r['overflow_before']} -> {r['overflow_after']} | total% {r['total_ratio_before']} -> {r['total_ratio_after']}")
(HERE / "x5_forward_before_after.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
