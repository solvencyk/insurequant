# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
p = json.loads((H / "plan_KR0070.json").read_text(encoding="utf-8"))
v = p["verification"]
L = [f"keys {list(p.keys())}",
     f"buckets {[(b['quarter'], b['adopt'], b['n_cells'], b['items'], b['csm_vs_master'], b['gold_overlap_with_adopted_items']) for b in p['buckets']]}",
     f"cells {len(p['cells'])} seam {len(p['seam_cells'])} neighbour {len(p['neighbour_effects'])} auto {len(p['auto_follow_cells'])}",
     "closure all ok after: " + str({b['quarter']: all(x.get('ok', True) for x in b['closure_merged_after']) and all(x['ok'] for x in b['closure_printed_later_filing']) for b in p['buckets']}),
     "verification keys " + str(list(v.keys())),
     "xml_line_reread " + json.dumps(v["xml_line_reread"]),
     "3M " + json.dumps({k: v["printed_three_month_check"][k] for k in ("n", "n_ok", "max_abs_diff")}),
     "census " + json.dumps(v["census_vs_xml"]),
     "q2025 " + json.dumps(v["q2025_master_vs_own_print"]),
     "contract " + json.dumps(p["apply_contract"]["expected_master_changes"], ensure_ascii=False),
     "cell0 " + json.dumps(p["cells"][0], ensure_ascii=False)[:1500]]
(H / "KR0070_check_plan.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
