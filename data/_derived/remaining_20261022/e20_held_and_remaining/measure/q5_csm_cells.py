import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
for scn in ("R2", "R2b_Lotte_2023_1Q2Q"):
    d = json.loads(open(M + f"cands_{scn}.json", encoding="utf-8").read())
    for c in d["csm_cells"]:
        print(scn, c["code"], c["q"], "item", c["item"], "old", c["old"], "new", c["new"], "gold", c.get("gold"))
