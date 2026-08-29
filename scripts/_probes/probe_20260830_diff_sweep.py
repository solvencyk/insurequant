# -*- coding: utf-8 -*-
"""Diff the PREFIX vs POSTFIX full-SONBO waterfall_for_dir() sweeps cell-by-cell.
Read-only."""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

pre = json.loads((ROOT / "scripts/_probes/_out_20260830_sweep_PREFIX.json").read_text(encoding="utf-8"))
post = json.loads((ROOT / "scripts/_probes/_out_20260830_sweep_POSTFIX.json").read_text(encoding="utf-8"))

assert set(pre.keys()) == set(post.keys()), "key sets differ!"

lines = []
n_cell_changes = 0
n_bucket_changes = 0
companies_changed = set()
src_changes = 0
for key in sorted(pre.keys()):
    p, q = pre[key], post[key]
    pv, pn = p.get("vals"), p.get("src")
    qv, qn = q.get("vals"), q.get("src")
    if pv == qv and pn == qn:
        continue
    n_bucket_changes += 1
    kr = key.split("|")[0]
    companies_changed.add(kr)
    lines.append(f"=== {key} ===")
    if pn != qn:
        lines.append(f"  src: {pn!r} -> {qn!r}")
        src_changes += 1
    if pv != qv:
        pv2 = pv or {}
        qv2 = qv or {}
        for it in range(1, 7):
            a, b = (pv2 or {}).get(str(it)), (qv2 or {}).get(str(it))
            if a != b:
                n_cell_changes += 1
                lines.append(f"  item{it}: {a} -> {b}")

out = ROOT / "scripts/_probes/_out_20260830_diff_sweep_report.txt"
header = (f"buckets changed: {n_bucket_changes} / {len(pre)} total\n"
          f"cell (item-level) changes: {n_cell_changes}\n"
          f"src-tag-only changes: {src_changes}\n"
          f"companies touched: {sorted(companies_changed)}\n")
out.write_text(header + "\n" + "\n".join(lines), encoding="utf-8")
print(header)
print(f"wrote {out}")
