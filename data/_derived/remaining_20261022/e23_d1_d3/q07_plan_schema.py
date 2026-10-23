# -*- coding: utf-8 -*-
"""e23 probe (read-only): print a trimmed view of the e21 plan schema (one PL bucket cell of each kind, one seam, one CSM bucket)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
EV = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
plan = json.loads((EV / "e21_plan.json").read_text(encoding="utf-8"))
print("top keys:", list(plan.keys()))
b = [x for x in plan["buckets"] if x["code"] == "KR0068" and x["quarter"] == "2023.2Q"][0]
print("bucket keys:", list(b.keys()))
print("meta:", json.dumps(b["meta"], ensure_ascii=False))
print("kind:", b["kind"], "closure_ok", b["closure_ok"], "cset", b["cset"], "only_cand", b["only_cand"], "only_mine", b["only_mine"])
print("dropped sample:", json.dumps(b["dropped"][:2], ensure_ascii=False)[:500])
print("closure sample:", json.dumps(b["closure"][:2], ensure_ascii=False)[:400])
shown = set()
for c in b["cells"]:
    kind = "gold" if c.get("gold_cell") else ("operands" if c["operands"] else "plain")
    if kind in shown:
        continue
    shown.add(kind)
    print("--- cell", kind, json.dumps({k: v for k, v in c.items() if k != "parts"}, ensure_ascii=False)[:1200])
    print("    parts:", json.dumps(c["parts"][:3], ensure_ascii=False)[:900])
    if c.get("original_print"):
        print("    original_print:", json.dumps(c["original_print"], ensure_ascii=False)[:900])
        print("    gold_source_print:", json.dumps(c["gold_source_print"], ensure_ascii=False)[:600])
print("seams[0:2]:", json.dumps(plan["seams"][:2], ensure_ascii=False)[:1800])
sm = [s for s in plan["seams"] if s.get("printed_3m")][:1]
print("seam with printed_3m:", json.dumps(sm, ensure_ascii=False)[:1800])
sq = [s for s in plan["seams"] if s.get("q3_comparative")][:1]
print("seam with q3_comparative:", json.dumps(sq, ensure_ascii=False)[:1800])
cb = plan["csm_buckets"][0]
print("csm bucket keys:", list(cb.keys()))
print(json.dumps({k: v for k, v in cb.items() if k != "cells"}, ensure_ascii=False)[:900])
print("csm cell:", json.dumps(cb["cells"][0], ensure_ascii=False)[:1500])
print("apply_contract keys:", list(plan["apply_contract"].keys()))
for k, v in plan["apply_contract"].items():
    if isinstance(v, list) and v:
        print(" ", k, len(v), json.dumps(v[0], ensure_ascii=False)[:700])
print("csm_gold_class keys:", list(plan.get("csm_gold_class", {}).keys())[:3])
print("findings:", json.dumps(plan.get("findings", [])[:2], ensure_ascii=False)[:600])
