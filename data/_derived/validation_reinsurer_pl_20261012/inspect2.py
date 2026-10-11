# -*- coding: utf-8 -*-
import json, collections, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
side = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
cells = side["cells"]
HOW = "disclosure_summary_pl_reinsurer"
cos = collections.defaultdict(collections.Counter)
for c in cells:
    cos[c["company_code"]][(c.get("source_id"), c.get("resolution"))] += 1
for co in sorted(cos):
    if co.startswith("KR11"):
        print(co, dict(cos[co]))
# who uses HOW
users = collections.Counter(); items = collections.Counter(); ev = collections.Counter(); blocks = collections.Counter()
for c in cells:
    for sf in c.get("source_files") or []:
        if sf.get("how") == HOW:
            users[c["company_code"]] += 1
            items[tuple(sf.get("items") or [])] += 1
            ev[(bool(sf.get("page") or sf.get("pages")), type(sf.get("printed")).__name__, bool(sf.get("printed")))] += 1
            blocks[(c["item_block"], c.get("resolution"), c.get("source_id"))] += 1
print("users", dict(users)); print("items", dict(items)); print("evidence", dict(ev)); print("blocks", dict(blocks))
# companies with any non-DISCLOSURE source_id cell
nondisc = collections.defaultdict(collections.Counter)
for c in cells:
    if c["company_code"].startswith("KR11"):
        nondisc[c["company_code"]][c.get("source_id")] += 1
print(dict(nondisc))
# R1 entries
for c in cells:
    for sf in c.get("source_files") or []:
        if sf.get("how") == "latest_prior_column_R1":
            print("R1", c["company_code"], c["quarter"], c["item_block"], c.get("source_id"), json.dumps(sf, ensure_ascii=False)[:300])
