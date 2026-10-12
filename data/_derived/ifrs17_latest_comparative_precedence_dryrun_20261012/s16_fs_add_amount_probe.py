"""Read-only probe: in interim FS-API cache files, how often do IS/CIS rows carry thstrm_add_amount / frmtrm_add_amount?
(If frmtrm_add_amount is missing, the 'later comparative' read by _parse falls back to the 3-month column - a unit mix-up to exclude.)"""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
cnt = Counter()
bad = Counter()
for f in sorted(glob.glob(str(ROOT / "data/dart/_fs_api_cache/*.json"))):
    name = Path(f).name
    corp, year, reprt, div = name[:-5].split("_")
    if reprt == "11011":
        continue
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    rows = [a for a in d.get("list", []) if a.get("sj_div") in ("IS", "CIS")]
    if not rows:
        continue
    n = len(rows)
    ta = sum(1 for a in rows if a.get("thstrm_add_amount") not in (None, ""))
    fa = sum(1 for a in rows if a.get("frmtrm_add_amount") not in (None, ""))
    key = "both" if (ta == n and fa == n) else ("th_only" if ta and not fa else ("none" if not ta and not fa else "partial"))
    cnt[key] += 1
    if key != "both":
        bad[(corp, year, reprt, div, key, n, ta, fa)] += 1
print(dict(cnt))
for k in sorted(bad)[:60]:
    print(k)
