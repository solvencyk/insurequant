# -*- coding: utf-8 -*-
"""read-only: the working-tree masters / gold files vs git HEAD at cell level -- which companies did the earlier agents of this workflow touch (KB라이프 KR0099, 롯데 KR0003, ABL KR0070 expected; KR0009 must be untouched)"""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")


def head(rel):
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"git show failed for {rel}: {p.stderr[:200]}")
    return json.loads(p.stdout.decode("utf-8"))


def live(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def rows_by(rows):
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}


for rel in ("PL_breakdown.json", "CSM_waterfall.json"):
    h, l = rows_by(head(rel)), rows_by(live(rel))
    only_h, only_l = set(h) - set(l), set(l) - set(h)
    diff = [k for k in h if k in l and h[k] != l[k]]
    c = Counter(k[0] for k in diff)
    print(f"{rel}: rows HEAD {len(h)} / tree {len(l)}; only-in-HEAD {len(only_h)}; only-in-tree {len(only_l)}; changed rows {len(diff)}; by company {dict(c)}")
    kr9 = [k for k in diff if k[0] == "KR0009"]
    print("   KR0009 changed rows:", len(kr9))
for rel in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    h, l = head(rel), live(rel)
    hs, ls = rows_by(h["set"]), rows_by(l["set"])
    added = set(ls) - set(hs)
    removed = set(hs) - set(ls)
    changed = [k for k in hs if k in ls and hs[k] != ls[k]]
    print(f"{rel}: set HEAD {len(hs)} / tree {len(ls)}; added {len(added)} {dict(Counter(k[0] for k in added))}; removed {len(removed)} {dict(Counter(k[0] for k in removed))}; changed {len(changed)} {dict(Counter(k[0] for k in changed))}")
    print("   KR0009 gold entries added/removed/changed:", sum(1 for k in added if k[0] == 'KR0009'), sum(1 for k in removed if k[0] == 'KR0009'), sum(1 for k in changed if k[0] == 'KR0009'))
    if "null_dangi" in h:
        hn = {tuple(x) for x in h["null_dangi"]["cells"]}
        ln = {tuple(x) for x in l["null_dangi"]["cells"]}
        print("   null_dangi added", len(ln - hn), dict(Counter(x[0] for x in ln - hn)), "removed", len(hn - ln), dict(Counter(x[0] for x in hn - ln)))
        hsd = {(x[0], x[1], x[2]): x for x in h["set_dangi"]["cells"]}
        lsd = {(x[0], x[1], x[2]): x for x in l["set_dangi"]["cells"]}
        print("   set_dangi added", len(set(lsd) - set(hsd)), dict(Counter(k[0] for k in set(lsd) - set(hsd))), "removed", len(set(hsd) - set(lsd)), "changed", sum(1 for k in hsd if k in lsd and hsd[k] != lsd[k]))
for rel in ("PL_breakdown_provenance.json", "CSM_waterfall_provenance.json"):
    h, l = head(rel), live(rel)
    hc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in h["cells"]}
    lc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in l["cells"]}
    ch = [k for k in hc if k in lc and hc[k] != lc[k]]
    print(f"{rel}: blocks HEAD {len(hc)} / tree {len(lc)}; added {dict(Counter(k[0] for k in set(lc) - set(hc)))}; changed {len(ch)} {dict(Counter(k[0] for k in ch))}")
