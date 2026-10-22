import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_R1.json", encoding="utf-8").read())
for c in d["pl_cells"]:
    if c["code"] == "KR0104" and c["item"] in (1, 15, 16, 20, 22, 23, 24):
        print(c["code"], c["q"], c["item"], c["old"], c["new"], c.get("gold"))
k = json.loads(open(M + "k6_kr0104_cells.json", encoding="utf-8").read())
print(type(k), list(k.keys())[:5] if isinstance(k, dict) else len(k))
