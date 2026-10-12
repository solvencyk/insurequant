# -*- coding: utf-8 -*-
"""47사 x 연도 x (기본자본비율, 지급여력비율) 전 -> 후. 총자본 경로 불변 증명 + 기존 필드 불변 증명. 읽기 전용."""
import csv, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path("data/_derived/capsec_reinstate_20261012")
old = {r.get("insurer_code"): r for r in json.loads((D / "before/kics_forward_capital.json").read_text(encoding="utf-8"))}
new = {r.get("insurer_code"): r for r in json.loads(Path("kics_forward_capital.json").read_text(encoding="utf-8"))}
assert set(old) == set(new), set(old) ^ set(new)
rows, total_diff, field_diff, conf_diff, basic_changed = [], [], [], [], []
for code in sorted(new):
    o, n = old[code], new[code]
    if n.get("status") != "ok":
        continue
    if o.get("confidence") != n.get("confidence"):
        conf_diff.append(code)
    for op, np_ in zip(o["projections"], n["projections"]):
        y = op["year"]
        # 기존 키는 새 값과 비교(총자본 관련은 불변이어야 한다)
        for k in ("capital_eok", "scr_eok", "ratio_pct", "cumulative_bond_dedu_eok", "cumulative_tier1_dedu_eok",
                  "hybrid_remaining_eok", "capacity_exhausted"):
            if op[k] != np_[k]:
                total_diff.append((code, y, k, op[k], np_[k]))
        rows.append({"code": code, "name": n.get("insurer_name"), "year": y,
                     "basic_ratio_before": op["basic_ratio_pct"], "basic_ratio_after": np_["basic_ratio_pct"],
                     "basic_capital_before": op["basic_capital_eok"], "basic_capital_after": np_["basic_capital_eok"],
                     "total_ratio_before": op["ratio_pct"], "total_ratio_after": np_["ratio_pct"],
                     "baseline_basis_flag": n["baseline_basis_flag"],
                     "basic_ratio_by_type_pct": np_["basic_ratio_by_type_pct"]})
        if op["basic_ratio_pct"] != np_["basic_ratio_pct"]:
            basic_changed.append(code)
    for k in o:
        if k not in ("projections", "confidence", "baseline_2025_4Q") and o[k] != n.get(k):
            field_diff.append((code, k))
with (D / "forward_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "| total-path diffs:", len(total_diff), total_diff[:5], "| row-field diffs:", field_diff[:5],
      "| confidence diffs:", conf_diff)
print("companies whose basic-ratio path changed:", sorted(set(basic_changed)))
for code in sorted(set(basic_changed)):
    print(code, new[code]["insurer_name"], "flag", new[code]["baseline_basis_flag"])
    for r in rows:
        if r["code"] == code:
            print("   ", r["year"], "basic%", r["basic_ratio_before"], "->", r["basic_ratio_after"], "| total%", r["total_ratio_before"], "->", r["total_ratio_after"],
                  "| by_type", r["basic_ratio_by_type_pct"])
