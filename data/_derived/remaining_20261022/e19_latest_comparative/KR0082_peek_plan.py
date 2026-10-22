# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path(__file__).resolve().parent
p = json.loads((H / "plan_KR0082.json").read_text(encoding="utf-8"))
v = p["verification"]
L = []
for k in ("unchanged_items_3m_later_print_vs_live_single_2023_3Q", "original_3m_print_vs_live_single_2023_3Q", "hybrid_single_2023_3Q_closure", "seam_3m_vs_9M_minus_6M", "alt_path", "census_vs_xml", "dangi_model_mismatch_vs_live_master"):
    L.append(k + " " + json.dumps(v[k], ensure_ascii=False))
for s in p["seam_cells"]:
    L.append("SET_DANGI " + json.dumps(s["set_dangi_cell"], ensure_ascii=False))
L.append(json.dumps(p["cells"][0], ensure_ascii=False, indent=1)[:3500])
(H / "KR0082_peek_plan.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
