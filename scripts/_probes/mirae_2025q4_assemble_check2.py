"""KR0079 2025.4Q -- replicate main()'s exact per-filing flow (assemble + _GOLD_CELL_OVERRIDE
application) to confirm the new override entry forces v[6] back to None. Read-only, does not
call main() or write any file."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import (  # noqa: E402
    discover_filings, parse_filing, assemble, load_universe, _fs_tier1, _GOLD_CELL_OVERRIDE,
)

filings = discover_filings()
uni = load_universe()
code = "KR0079"
q = "2025.4Q"
dirs = filings[code][q]
name, life_flag = uni.get(code, (None, None))
is_life = (life_flag == "생명보험")

t1_html, t2 = parse_filing(dirs, is_life, code=code, name=name, quarter=q)
t1_api = _fs_tier1(name, q, code)
t1 = t1_api if t1_api else t1_html
v = assemble(t1, t2, is_life)
print(f"pre-override  v[6]={v[6]}  v[7]={v[7]}")

ov = _GOLD_CELL_OVERRIDE.get((code, q))
print(f"override entry: {ov}")
if ov:
    for _k, _val in ov.items():
        v[_k] = _val
    v["_reconciled"] = True

print(f"post-override v[6]={v[6]}  v[7]={v[7]}  _reconciled={v.get('_reconciled')}")
for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
    print(f"  v[{n}] = {v[n]}")
