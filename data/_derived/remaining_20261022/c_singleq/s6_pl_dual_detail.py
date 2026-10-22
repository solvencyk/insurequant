# -*- coding: utf-8 -*-
"""Detail of the dangi-only 보험손익 dual-form failures from s1: per bucket, items 1/2/13/14/15/16 (+2-N) for q-1 and q,
값 and 값_당분기, and the bare / adj residuals on each column. Read-only, pinned via git show HEAD."""
import json, subprocess, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
pl = json.loads(subprocess.run(["git", "show", "HEAD:PL_breakdown.json"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
TARGETS = [("KR0073", "2023.2Q"), ("KR0073", "2023.3Q"), ("KR0072", "2023.1Q"), ("KR0072", "2023.2Q"), ("KR0072", "2023.3Q"),
           ("KR0009", "2025.2Q"), ("KR0009", "2025.3Q")]
ITEMS = ["1", "2", "13", "14", "15", "16", "2-1"]
idx = {}
for r in pl:
    idx[(r["원보험사코드"], r["공시분기"], str(r["항목번호"]))] = (r.get("값"), r.get("값_당분기"))
out = []
for c, q in TARGETS:
    row = {i: idx.get((c, q, i), (None, None)) for i in ITEMS}
    out.append(f"{c} {q}: " + "  ".join(f"i{i}={row[i][0]}/{row[i][1]}" for i in ITEMS))
    for col, nm in ((0, "값"), (1, "당분기")):
        g = {i: row[i][col] for i in ITEMS}
        if g["1"] is None:
            continue
        bare = sum((g[i] or 0.0) for i in ("2", "13", "14", "2-1"))
        s = f"   [{nm}] bare-1={bare - g['1']:+.1f}"
        if g["15"] is not None and g["16"] is not None:
            s += f"  adj-1={bare + g['15'] - g['16'] - g['1']:+.1f}"
        else:
            s += "  adj=not formed (15 or 16 None)"
        out.append(s)
(HERE / "s6_pl_dual_detail.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
