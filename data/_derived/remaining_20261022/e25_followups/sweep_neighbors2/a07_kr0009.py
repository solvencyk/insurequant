import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("compared_part2.json"))
print("KR0009 compared:", sorted((q, i) for c, q, i in d if c == "KR0009"))
b = json.load(open("b01_stmt.json", encoding="utf-8"))
for k, r in b.items():
    if k.startswith("KR0009"):
        print(k, {i: round(r["items"][i]["val"], 3) for i in ("16", "18", "19", "23")}, r["items"]["16"]["printed"])
