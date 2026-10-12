"""Read-only: candidate PL_breakdown.json = live master with the three DB손해보험 (KR0011) blocks 2023.1Q-3Q replaced by the FULL latest-comparative block
(cand/db_pl_block_lat.json from s71: items 1..24 assembled by the production assemble() + OCI 25..32 from the prior-year FS-API column).
New (previously absent) items are added as rows cloned from the same company/item of another quarter.  값_당분기 recomputed like build_pl().
Output cand/PL_breakdown.DB2023.json (served to the gates by gate_overlay.py; the repo master is untouched)."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_root_masters as BR  # noqa: E402

rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
blocks = json.loads((HERE / "cand" / "db_pl_block_lat.json").read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
tmpl = {}
for r in rows:
    if r["원보험사코드"] == "KR0011":
        tmpl.setdefault(r["항목번호"], r)
changed = added = 0
for q, items in blocks.items():
    for it_s, val in items.items():
        it = int(it_s)
        key = ("KR0011", it, q)
        if key in idx:
            if idx[key]["값"] != val:
                idx[key]["값"] = val
                changed += 1
        else:
            t = tmpl.get(it)
            if t is None:
                continue
            nr = {k: t[k] for k in t if k not in ("값", "값_당분기")}
            nr["공시분기"] = q
            nr["값"] = val
            nr["값_당분기"] = None
            rows.append(nr)
            idx[("KR0011", it, q)] = nr
            added += 1
ytd = defaultdict(dict)
for r in rows:
    ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
for r in rows:
    if r["원보험사코드"] != "KR0011":          # other companies keep the live 값_당분기 byte for byte
        continue
    v = r.get("값")
    r["값_당분기"] = BR._flow_dangi(ytd[(r["원보험사코드"], r["항목번호"])], r["공시분기"]) if v is not None else None
(HERE / "cand" / "PL_breakdown.DB2023.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("DB candidate: cells changed", changed, "rows added", added, "total rows", len(rows))
