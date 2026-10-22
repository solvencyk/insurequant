# -*- coding: utf-8 -*-
"""Read-only shape probe of the pinned masters (git show <sha>:). No writes except this dir."""
import json, subprocess, sys, pathlib
from collections import Counter, defaultdict
ROOT = pathlib.Path(__file__).resolve().parents[4]
SHA = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
def show(f):
    return json.loads(subprocess.run(["git", "show", f"{SHA}:{f}"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
out = []
for f in ("CSM_waterfall.json", "PL_breakdown.json"):
    rows = show(f)
    out.append(f"== {f} rows={len(rows)} keys={sorted(rows[0].keys())}")
    items = Counter((str(r["항목번호"]), r["항목명"]) for r in rows)
    for (no, nm), c in sorted(items.items(), key=lambda x: (len(x[0][0]), x[0][0])):
        out.append(f"  item {no:>5} {nm} n={c}")
    qs = Counter(r["공시분기"] for r in rows)
    out.append("  quarters: " + " ".join(f"{q}:{c}" for q, c in sorted(qs.items())))
    cos = {r["원보험사코드"] for r in rows}
    out.append(f"  companies={len(cos)}")
    nn = sum(1 for r in rows if r.get("값") is not None); nd = sum(1 for r in rows if r.get("값_당분기") is not None)
    out.append(f"  값 non-null={nn}  값_당분기 non-null={nd}")
gold = json.loads(subprocess.run(["git", "show", f"{SHA}:data/_gold/user_pl_cells.json"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
out.append("user_pl_cells keys: " + str(list(gold.keys())))
for k in ("null_dangi", "set_dangi"):
    v = gold.get(k) or {}
    out.append(f"  {k}: " + json.dumps({kk: (vv if kk != 'cells' else vv[:40]) for kk, vv in v.items()}, ensure_ascii=False)[:3000])
p = pathlib.Path(__file__).with_suffix(".txt"); p.write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
