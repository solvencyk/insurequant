# -*- coding: utf-8 -*-
"""Adds the independent re-read results (KR0104_verify.json / KR0104_verify4q.json / KR0104_gate_bridge.txt) to plan_KR0104.json -> verification.independent_reread.
Evidence-folder file only; no master / gold / doc is touched."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
plan = json.loads((HERE / "plan_KR0104.json").read_text(encoding="utf-8"))
v = json.loads((HERE / "KR0104_verify.json").read_text(encoding="utf-8"))
v4 = json.loads((HERE / "KR0104_verify4q.json").read_text(encoding="utf-8"))
gb = (HERE / "KR0104_gate_bridge.txt").read_text(encoding="utf-8").strip().split("\n")
live = {(r["공시분기"], r["항목번호"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0104"}

# 2023.4Q cumulative vs FY2024 annual prior column (2nd numeric column) and FY2023 annual current column (1st numeric column)
def mn(s):
    s = s.replace(",", "")
    neg = s.startswith("(")
    x = float(s.strip("()")) / 1e6
    return -x if neg else x


q4 = {}
for it in ("1", "16", "17", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"):
    a = v4["FY2024_annual"]["items"][it]["cells"]
    o = v4["FY2023_annual"]["items"][it]["cells"]
    m = live[("2023.4Q", int(it))]["값"]
    q4[it] = {"master": m, "fy2024_annual_prior_col": mn(a[1][1]), "line_fy2024": a[1][0], "fy2023_annual_current_col": mn(o[0][1]), "line_fy2023": o[0][0],
              "master_minus_fy2024_prior": round(m - mn(a[1][1]), 6), "master_minus_fy2023_current": round(m - mn(o[0][1]), 6)}
max_m24 = max(abs(x["master_minus_fy2024_prior"]) for x in q4.values())
max_m23 = max(abs(x["master_minus_fy2023_current"]) for x in q4.values())

dangi_after = [x for x in v["dangi_diff_cells"]]
plan["verification"]["independent_reread"] = {
    "script": "data/_derived/remaining_20261022/e19_latest_comparative/KR0104_verify.py (+ KR0104_verify4q.py, KR0104_gate_bridge.py); own XML row reader, label map, FS-API read, closure, build_root_masters._flow_dangi",
    "when": "2026-10-22 (second pass, after the first plan run of 15:58)",
    "xml_file": "data/dart/FY2024_Q3/raw/KR0104_농협생명보험/20241114000851.xml",
    "unit_header_later": v["unit_header_F3"],
    "unit_header_original": v["orig_unit_header"],
    "basis": "4. 재무제표 (company has no consolidated statements: section 3 '해당사항 없음') = separate/OFS; 4-2 포괄손익계산서 columns [3개월, 누적, 3개월, 누적] x [제13기, 제12기]; prior-year cumulative = numeric position 4",
    "cells_reread": len(v["cells_check"]),
    "cells_mismatch_old_new_line_file": [c for c in v["cells_check"] if not (c["old_ok"] and c["new_ok"] and c["line_ok"] and c["file_ok"])],
    "label_hit_counts_each_label_rows_in_statement": v["label_hit_counts"],
    "master_equals_original_print_mismatches": v["master_eq_original_mismatches"],
    "fsapi_ofs_frmtrm_add_vs_xml_mismatches": v["fsapi_mismatch"],
    "items_differing_from_later_print_not_in_plan": [d for d in v["diff_items_vs_later"] if d[0] not in {c["item"] for c in plan["cells"]}],
    "sign_check_items_18_19": "item 19 = -(보험금융비용 L6138 + 재보험금융비용 L6161), both printed POSITIVE (1,115,113,668,944 / 1,964,083,664), no 보험금융수익 / 재보험금융수익 rows; item 18 = 17 - 19; not in d12_sign19_scan defect list (한화손보, 삼성생명 2023.3Q, 흥국화재 2025.3Q only)",
    "census_vs_xml": "all 18 plan values equal the census new values (diff 0.0 for each); the only difference is the census CANDIDATE cell item 18 = 1,135,383.75571 (keeps the rounded old item 19) vs XML-derived 1,135,383.508318 (diff 0.247 mn); plan takes 18 and 19 from one column",
    "closure_merged_vector": {"before": v["closure_before"], "after_18_cells": v["closure_after_18"], "after_census8_only": v["closure_after_census8"], "after_restated7_only": v["closure_after_restated7"],
                              "note": "after_18_cells: every identity exact to 0.000 mn except the LOB bridge -0.36261 mn (Tier-2 legs are whole-백만원 note values from the original filing; item 1 and 16 are won-exact). Gate tolerance max(0.1% of item 1, floor)."},
    "gate_pl_bridge_real_function": {"result": gb, "note": "validate_master_tables._check_pl_bridge on all KR0104 quarters (live vs merged): identical, 122 pass / 0 fail / 18 skip"},
    "owner_gold": v["gold_KR0104"],
    "seam_three_month_prints": v["seam_3m"],
    "seam_vs_plan": v["seam_vs_plan"],
    "quarterly_cells_that_change_in_a_fresh_build": dangi_after,
    "neighbour_2023.4Q_cumulative_check": {"items": q4, "max_abs_master_minus_fy2024_annual_prior_mn": max_m24, "max_abs_master_minus_fy2023_annual_current_mn": max_m23,
                                           "reading": "master 2023.4Q equals the FY2023 annual current column exactly and the FY2024 annual prior column within 0.0004 mn (390 won re-rounding): 2023.4Q cumulative is already the post-correction vintage, nothing to adopt there"},
}
(HERE / "plan_KR0104.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("max4q", max_m24, max_m23, "mismatch cells", len(plan["verification"]["independent_reread"]["cells_mismatch_old_new_line_file"]))
