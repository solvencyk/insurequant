# -*- coding: utf-8 -*-
"""For all 2026.2Q companies with 36-40 loaded, check the sqrt(V'*MARKET_M*V)==item19
identity (same matrix as kics_json_rules.MARKET_M / fill_market_subitems.M) using
MASTER values only (no MD involved) -- to see whether the loaded numbers are at
least internally self-consistent, independent of whether the current MD can
reproduce them. Read-only."""
import io, json, math, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
QUARTER = "2026.2Q"

M = [[1, .25, .25, .25, 0], [.25, 1, .25, -.25, 0], [.25, .25, 1, .25, 0], [.25, -.25, .25, 1, 0], [0, 0, 0, 0, 1]]


def mkt_est(v5):
    q = sum(v5[a] * M[a][b] * v5[b] for a in range(5) for b in range(5))
    return math.sqrt(q) if q > 0 else 0.0


rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
by_code_item = {}
names = {}
for r in rows:
    if r["공시분기"] != QUARTER:
        continue
    code = r["원보험사코드"]
    names[code] = r.get("원수사명", code)
    try:
        it = int(r["항목번호"])
    except (TypeError, ValueError):
        continue
    by_code_item.setdefault(code, {})[it] = r

for code, items in sorted(by_code_item.items()):
    name = names.get(code, code)
    if 19 not in items:
        continue
    item19_raw = str(items[19].get("값", "")).strip()
    if item19_raw in ("", "-"):
        continue
    item19 = float(item19_raw.replace(",", ""))
    v5 = []
    any_present = False
    for i in (36, 37, 38, 39, 40):
        rec = items.get(i)
        if rec is None:
            v5.append(0.0)
            continue
        s = str(rec.get("값", "")).strip()
        if s in ("", "-"):
            v5.append(0.0)
        else:
            v5.append(float(s.replace(",", "")))
            any_present = True
    if not any_present:
        continue
    est = mkt_est(v5)
    if item19 == 0:
        continue
    rel = abs(est - item19) / item19 * 100
    flag = "OK" if rel < 1.0 else ("YELLOW" if rel < 5.0 else "RED")
    print(f"{code} {name:<16} item19={item19:>10.2f} sqrt(V'MV)={est:>10.2f} rel={rel:6.3f}% {flag}")
