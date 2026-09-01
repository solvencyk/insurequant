# -*- coding: utf-8 -*-
"""Directly test confirm_aggregate_unchanged for a company against its fy2025 bs_subordinated_mn,
to see whether the BS 후순위 total genuinely moved (real reason to stay stale) or the row/keyword
just isn't being found (a fixable gap)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_capital_securities_fy2026h1 as B  # noqa: E402

code = sys.argv[1]
fy25 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2025.json").read_text(encoding="utf-8"))
c = next(x for x in fy25["companies"] if x["code"] == code)
bs_sub = c.get("bs_subordinated_mn")
bs_hyb = c.get("bs_hybrid_mn")
print(f"{code}: bs_subordinated_mn(FY2025)={bs_sub}  bs_hybrid_mn(FY2025)={bs_hyb}")

xml_path, text = B.load_h1_xml(code)
for kw in ("후순위사채", "후순위채권", "후순위"):
    r = B.confirm_aggregate_unchanged(text, bs_sub, kw)
    print(f"  confirm_aggregate_unchanged(sub, kw={kw!r}) -> {r}")

cur = B.bs_current_balance(text, bs_sub, "subordinated")
print(f"  bs_current_balance(subordinated, prior={bs_sub}) -> {cur}")
