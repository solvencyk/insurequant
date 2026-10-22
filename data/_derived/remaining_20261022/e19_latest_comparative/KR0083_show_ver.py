# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
p = json.loads((H/"plan_KR0083.json").read_text(encoding="utf-8"))
v = p["verification"]
L=[]
for k in ("master_equals_original_print_all","warnings","dangi_model_mismatch_vs_live_master","census_vs_xml","gold","unchanged_items_three_month_vs_live_single","seam_3m_vs_cumulative_difference","hybrid_single_2024_3Q_closure","year_tie_2024","q2025_master_vs_own_print","q2023_4Q_master_vs_fy2024_annual_prior_informational","csm_waterfall_master_cells_unchanged"):
    L.append(k+": "+json.dumps(v[k],ensure_ascii=False))
L.append("note50: "+json.dumps({a:b for a,b in v["note50_second_source"].items() if a!="rows"},ensure_ascii=False))
L.append("q4 rows:")
for r in v["q2024_4Q"]["rows"]: L.append("  "+json.dumps(r,ensure_ascii=False))
L.append("q4 eq annual: "+str(v["q2024_4Q"]["items_master_eq_annual_print"])+" differing from fy2025 prior: "+str(v["q2024_4Q"]["items_differing_from_fy2025_prior"]))
L.append("q4 single:")
for k,x in v["q2024_4Q"]["single_quarter"].items(): L.append(f"  i{k} "+json.dumps(x,ensure_ascii=False))
L.append("apply_contract keys "+str(list(p["apply_contract"].keys())))
L.append(json.dumps(p["apply_contract"]["expected_master_changes"],ensure_ascii=False))
L.append(json.dumps(p["apply_contract"]["set_dangi_cells"][:2],ensure_ascii=False))
(H/"KR0083_show_ver.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
