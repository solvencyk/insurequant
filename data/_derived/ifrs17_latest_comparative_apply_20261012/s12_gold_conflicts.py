"""Read-only: do any planned cells collide with owner gold / confirmed registries / BS overlays?"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
plan = json.load(open("plan_diff.json", encoding="utf-8"))
pl_gold = {(c["원보험사코드"], c["항목번호"], c["공시분기"]) for c in json.load(open(R + "data/_gold/user_pl_cells.json", encoding="utf-8"))["set"]}
csm_gold = {(c["원보험사코드"], c["항목번호"], c["공시분기"]) for c in json.load(open(R + "data/_gold/user_csm_cells.json", encoding="utf-8"))["set"]}
conf = json.load(open(R + "data/_gold/user_pl_confirmed_cells.json", encoding="utf-8"))
print("confirmed keys:", list(conf.keys()))
cells = conf.get("cells", [])
print("confirmed cells", len(cells), cells[:2])
bs_ov = json.load(open(R + "data/dart/viz/bs_manual_overrides.json", encoding="utf-8"))["cells"]
side = json.load(open(R + "data/_derived/bs_from_disclosure.json", encoding="utf-8"))["cells"]
n = 0
for c in plan["CSM"]:
    if (c["code"], c["item"], c["quarter"]) in csm_gold:
        print("CSM GOLD CONFLICT", c); n += 1
for c in plan["PL"]:
    if (c["code"], c["item"], c["quarter"]) in pl_gold:
        print("PL GOLD CONFLICT", c); n += 1
for c in plan["BS"]:
    k = f"{c['code']}|{c['item']}|{c['quarter']}"
    if k in bs_ov or k in side:
        print("BS OVERLAY CONFLICT", k, bs_ov.get(k), side.get(k)); n += 1
names = {}
for r in json.load(open(R + "PL_breakdown.json", encoding="utf-8")):
    names[r["원보험사코드"]] = r["원수사명"]
for cc in cells:
    for c in plan["PL"]:
        if cc.get("company") == names.get(c["code"]) and cc.get("quarter") == c["quarter"] and int(cc.get("item", -1)) == c["item"]:
            print("PL CONFIRMED CONFLICT", cc, c); n += 1
print("conflicts:", n)
# also gold entries touching the same (code, quarter) blocks, even if different items
blocks_pl = {(c["code"], c["quarter"]) for c in plan["PL"]}
blocks_csm = {(c["code"], c["quarter"]) for c in plan["CSM"]}
for g in sorted(pl_gold, key=str):
    if (g[0], g[2]) in blocks_pl:
        print("pl gold in block", g)
for g in sorted(csm_gold, key=str):
    if (g[0], g[2]) in blocks_csm:
        print("csm gold in block", g)
