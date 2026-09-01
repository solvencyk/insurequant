# -*- coding: utf-8 -*-
"""Read-only probe: KR0069 삼성생명 2026.2Q market-risk (36-40/19) MD-vs-master gap.

Does NOT write kics_disclosure.json. Imports the pure extract_mkt_subs()/mkt_est()
functions from fill_market_subitems_to_disclosure.py (no UPSERT call).
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import extract_mkt_subs, mkt_est, _to_eok, MKT_SUBS  # noqa: E402

CODE = "KR0069"
QUARTER = "2026.2Q"

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
mine = [r for r in rows if r["원보험사코드"] == CODE and r["공시분기"] == QUARTER]
print(f"master rows for {CODE} {QUARTER}: {len(mine)}")
by_item = {int(r["항목번호"]): r for r in mine}
for it in sorted(by_item):
    r = by_item[it]
    print(f"  item{it:>2} {r.get('항목명',''):<28} 값={r.get('값')!s:<14} 값_적용후={r.get('값_적용후')!s}")

md_path = REPO / "md_inbox" / "FY2026_Q2" / "KR0069_삼성생명.md"
text = md_path.read_text(encoding="utf-8")
subs = extract_mkt_subs(text)
print(f"\nextract_mkt_subs() on CURRENT md_inbox MD ({md_path}):")
print(f"  items found: {sorted(subs.keys())}")
for item_no, name, _ in MKT_SUBS:
    if item_no in subs:
        raw, unit = subs[item_no]
        eok = _to_eok(raw, unit)
        print(f"  item{item_no} {name:<20} raw={raw} unit={unit} -> {eok} 억원")
    else:
        print(f"  item{item_no} {name:<20} NOT FOUND in current MD")

v5_master = [float(str(by_item[i]["값"]).replace(",", "")) if i in by_item else 0.0 for i in (36, 37, 38, 39, 40)]
item19 = float(str(by_item[19]["값"]).replace(",", "")) if 19 in by_item else None
print(f"\nmaster v5=[36..40]={v5_master}")
if item19 is not None:
    est = mkt_est(v5_master)
    rel = abs(est - item19) / item19 * 100 if item19 else float("nan")
    print(f"master item19={item19}  sqrt(V'MV) from master 36-40={est:.2f}  rel={rel:.4f}%")
else:
    print("master item19 missing")

v5_md = [float(_to_eok(*subs[i])) if i in subs else 0.0 for i in (36, 37, 38, 39, 40)]
print(f"\ncurrent-MD-derived v5=[36..40]={v5_md}")
if item19 is not None:
    est_md = mkt_est(v5_md)
    rel_md = abs(est_md - item19) / item19 * 100 if item19 else float("nan")
    print(f"sqrt(V'MV) from CURRENT MD 36-40={est_md:.2f} vs master item19={item19}  rel={rel_md:.2f}%")
