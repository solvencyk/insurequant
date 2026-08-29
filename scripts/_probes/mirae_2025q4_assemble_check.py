"""KR0079 2025.4Q -- after the _ma_find_product_table tie-break fix, does assemble() still
0-fill item6 via the existing owner rule (build_pl_breakdown.py:172-174)? Confirms whether
_GOLD_CELL_OVERRIDE is still needed to keep the golden matching disk (None). Read-only, does
not call main() or write any file."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import discover_filings, parse_filing, assemble, load_universe, _fs_tier1  # noqa: E402

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
print(f"t1 source: {'api' if t1_api else 'html'}")
print(f"t2 item6 (pre-assemble, from extract_tier2_miraeasset): {t2.get(6) if t2 else None}")
for n in (1, 2, 3, 4, 5, 6, 7):
    print(f"  v[{n}] = {v[n]}")
print(f"  _reconciled = {v.get('_reconciled')}")
