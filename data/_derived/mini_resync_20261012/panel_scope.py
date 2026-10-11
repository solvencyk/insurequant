# -*- coding: utf-8 -*-
"""Compare panel: are all changed leaves reinsurer (KR11xx) only? Names of changed metrics."""
import json
from pathlib import Path
D = Path(__file__).resolve().parent
ROOT = D.parents[2]
b = json.loads((D/"panels_before"/"panel_compare.json").read_text(encoding="utf-8"))
a = json.loads((ROOT/"data/compare/panel_compare.json").read_text(encoding="utf-8"))
print("top keys", list(a))
print("keys changed at top:", [k for k in a if a[k] != b.get(k)])
for i, (mb, ma) in enumerate(zip(b["metrics"], a["metrics"])):
    if mb != ma:
        meta = {k: v for k, v in ma.items() if k != "v"}
        nonrein = [c for c in ma["v"] if ma["v"][c] != mb["v"].get(c) and not c.startswith("KR11")]
        chg = [c for c in ma["v"] if ma["v"][c] != mb["v"].get(c)]
        print(i, json.dumps(meta, ensure_ascii=False)[:160], "| changed cos", sorted(chg), "| non-reinsurer", nonrein)
lc_non = [c for c in a["loss_curve"]["v"] if a["loss_curve"]["v"][c] != b["loss_curve"]["v"].get(c) and not c.startswith("KR11")]
print("loss_curve non-reinsurer changed:", lc_non)
print("companies/quarters same?", a.get("quarters") == b.get("quarters"), len(a.get("companies", [])), len(b.get("companies", [])))
bc = json.loads((D/"panels_before"/"panel_csm_combo.json").read_text(encoding="utf-8"))
ac = json.loads((ROOT/"data/csm_combo/panel_csm_combo.json").read_text(encoding="utf-8"))
nonr = [c for c in ac["companies"] if ac["companies"][c] != bc["companies"].get(c) and not c.startswith("KR11")]
print("combo non-reinsurer changed:", nonr, "| changed reinsurers:", sorted(c for c in ac["companies"] if ac["companies"][c] != bc["companies"].get(c)))
