"""Read-only: summarize hold_reasons_5c.json / hold_list_B_20261011.json totals."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[3]
h = json.loads((ROOT / "data/_derived/bspl_followup_20261011/hold_reasons_5c.json").read_text(encoding="utf-8"))
print(len(h), "groups; keys", list(h[0].keys()))
print(json.dumps(h[0], ensure_ascii=False)[:900])
print(Counter(x.get("class") or x.get("cls") or x.get("category") for x in h))
tot = 0
for x in h:
    for k in ("n_cells", "cells", "n", "count"):
        if k in x and isinstance(x[k], (int, list)):
            tot += x[k] if isinstance(x[k], int) else len(x[k])
            break
print("approx cells", tot)
b = json.loads((ROOT / "data/_derived/bspl_apply_20261011/hold_list_B_20261011.json").read_text(encoding="utf-8"))
print("B groups", len(b["holds"]), "cells_considered", sum(x["cells_considered"] for x in b["holds"]), "still_blank", sum(x["cells_still_blank"] for x in b["holds"]))
