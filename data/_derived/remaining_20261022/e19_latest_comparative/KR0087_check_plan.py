# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
p = json.loads((H / "plan_KR0087.json").read_text(encoding="utf-8"))
L = [f"keys {list(p.keys())}", f"buckets {[(b['quarter'], b['adopt'], b['n_cells']) for b in p['buckets']]}", f"cells {len(p['cells'])} seam {len(p['seam_cells'])} neighbour {len(p['neighbour_effects'])} auto {len(p['auto_follow_cells'])}",
     "contract " + json.dumps(p["apply_contract"]["expected_master_changes"], ensure_ascii=False),
     "cell0 " + json.dumps(p["cells"][0], ensure_ascii=False)[:1800], "cell_3Q_19 " + json.dumps([c for c in p["cells"] if c["quarter"] == "2024.3Q" and c["item"] == 19][0], ensure_ascii=False)[:1800]]
(H / "KR0087_check_plan.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
