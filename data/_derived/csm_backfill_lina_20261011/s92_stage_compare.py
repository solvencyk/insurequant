# -*- coding: utf-8 -*-
"""Step 92 (read-only): the new staging files keep the already loaded core rows unchanged (prefix equality with the committed core staging
and equality with the rows that are in the master), and show the extension rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads((W / p).read_text(encoding="utf-8"))


for new, old in (("rows_waterfall.json", "rows_waterfall.core_committed.json"), ("rows_amortization.json", "rows_amortization.core_committed.json"),
                 ("sidecar_cells.json", "sidecar_cells.core_committed.json")):
    n, o = load(new), load(old)
    keyf = (lambda r: (r.get("공시분기") or r.get("quarter"), r.get("항목번호") or r.get("경과차년") or r.get("item_block")))
    nk = {keyf(r): r for r in n}
    same = all(nk.get(keyf(r)) == r for r in o)
    print(f"{new}: new {len(n)} rows, committed core {len(o)} rows, every core row identical in the new staging: {same}")

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
mk = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in wf}
new = load("rows_waterfall.json")
in_master_equal = [r for r in new if mk.get(("KR0074", r["공시분기"], r["항목번호"])) == r]
in_master_diff = [r for r in new if ("KR0074", r["공시분기"], r["항목번호"]) in mk and mk[("KR0074", r["공시분기"], r["항목번호"])] != r]
print("staged rows already in the master and equal:", len(in_master_equal), "| in the master but different (would collide):", len(in_master_diff))

rep = load("build_report.json")
ext = rep["ext"]
print("\n== extension quarters")
for q, r in ext["quarters"].items():
    it = r["adopted_items_천원"]
    print(f"{q}: adopted = {r['adopted']} | conflict own-vs-later: {r['conflict']} | own-later diffs 천원 {r['own_minus_later_천원']}")
    print(f"     continues master: {r['continues_master']} (expected opening {r['expected_opening_억원(master)']}, adopted {r['adopted_opening_억원']}) | residual {r['adopted_residual_천원']} | other {r['adopted_other_row_csm_천원']}")
    print(f"     adopted (억원): open {it['open']/1e5:.5f} new {it['new']/1e5:.5f} fin {it['fin']/1e5:.5f} adj {it['adj']/1e5:.5f} amort {it['amort']/1e5:.5f} close {it['close']/1e5:.5f}")
print("\n== chains")
print(json.dumps(ext["chains"], ensure_ascii=False)[:2500])
print("\n== quarter-only")
print(json.dumps(ext["quarter_only"], ensure_ascii=False))
print("\n== ILP crosscheck")
print(json.dumps(ext["ilp_crosscheck"], ensure_ascii=False))
print("\n== holds")
print(json.dumps(ext["holds"], ensure_ascii=False, indent=1))
print("\n== existing cells now derivable (not written)")
for c in ext["existing_cells_now_derivable_NOT_WRITTEN"]:
    print("  ", c)
