# -*- coding: utf-8 -*-
"""Non-Kyobo buckets where the next-year prior column (latest comparative) of the FS-API cache differs from the same-quarter vintage: what does the master hold? Read-only."""
import sys, json
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_master_tables as V, fetch_dart_fs as fdf
rows = json.loads((ROOT / V.PL_PATH).read_text(encoding="utf-8"))
from collections import defaultdict
master, code_of = defaultdict(dict), {}
for r in rows:
    master[(r["원수사명"], r["공시분기"])][V.norm(r["항목명"])] = r["값"]; code_of[r["원수사명"]] = r["원보험사코드"]
kr2cc = V._tax22_corp_codes()
out = []
for (co, q), m in sorted(master.items()):
    cc = kr2cc.get(code_of.get(co, "")); 
    if not cc or m.get("세전이익") is None: continue
    t1 = V._tax22_tier1(fdf, cc, q); t2 = V._tax22_prior_tier1(fdf, cc, q)
    if not t1 or not t2: continue
    # compare headline items 1,22,24,23 between vintages
    diffs = {k: (t1.get(k), t2.get(k)) for k in (1, 22, 23, 24) if t1.get(k) is not None and t2.get(k) is not None and abs(t1[k] - t2[k]) > max(0.001 * abs(t1[k]), 200)}
    if not diffs: continue
    mk = {1: m.get("보험손익"), 22: m.get("세전이익"), 23: None, 24: m.get("당기순이익")}
    holds = {k: ("same" if abs(mk[k] - v[0]) <= max(0.001 * abs(v[0]), 200) else ("prior" if abs(mk[k] - v[1]) <= max(0.001 * abs(v[1]), 200) else "neither")) for k, v in diffs.items() if mk.get(k) is not None}
    out.append((co, q, {k: (round(a, 0), round(b, 0)) for k, (a, b) in diffs.items()}, holds))
lines = [f"{co} {q} diffs(same,prior)={d} master holds={h}" for co, q, d, h in out]
Path("data/_derived/kyobo_validation_20261022/sim_other_vintage_buckets.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
from collections import Counter
print(len(out), "buckets where cache vintages differ on items 1/22/23/24")
print(Counter(h for _c, _q, _d, hh in out for h in hh.values()))
print(Counter(c for c, *_ in out))
