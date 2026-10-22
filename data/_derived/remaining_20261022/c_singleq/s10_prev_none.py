# -*- coding: utf-8 -*-
"""PL cells with 값(q) present but 값(q-1) None (so 값_당분기 cannot be derived) in the 2024+ display window,
with the q-1 lineage. These are item-level YTD holes the 3-key-item coverage census does not count. Read-only."""
import json, subprocess, sys, pathlib
from collections import defaultdict
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as V
src = V.pl_cell_source_ids()
pl = json.loads(subprocess.run(["git", "show", "HEAD:PL_breakdown.json"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
val = defaultdict(dict); name = {}
for r in pl:
    val[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = r.get("값"); name[r["원보험사코드"]] = r["원수사명"]
def prevq(q):
    y, n = q.split("."); n = int(n[0]); return None if n == 1 else f"{y}.{n-1}Q"
rows = defaultdict(list); tot = 0; tot_all = 0
for (c, q), m in sorted(val.items()):
    p = prevq(q)
    if not p or (c, p) not in val:
        continue
    for no, v in m.items():
        if c == "KR0073" and no in ("25", "26", "29", "31", "32"):
            continue
        if v is not None and val[(c, p)].get(no) is None:
            tot_all += 1
            if not q.startswith("2023."):
                rows[(c, q)].append(no); tot += 1
out = [f"PREV_VAL_NONE all={tot_all}  2024+ cells={tot} buckets={len(rows)}"]
for (c, q), its in sorted(rows.items()):
    out.append(f"  {c} {name[c]} {q} prev-lineage={src.get((name[c], prevq(q)))} items={','.join(its)}")
(HERE / "s10_prev_none.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
