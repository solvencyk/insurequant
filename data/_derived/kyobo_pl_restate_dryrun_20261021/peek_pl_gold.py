import json, sys
sys.stdout.reconfigure(encoding="utf-8")
g = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/user_pl_cells.json", encoding="utf-8"))
s = g["set"]
print(len(s), "entries; top keys:", [k for k in g if k != "set"])
for e in s[-2:]:
    print(json.dumps(e, ensure_ascii=False)[:700])
print("keys used:", sorted({k for e in s for k in e}))
print("first entry:", json.dumps(s[0], ensure_ascii=False)[:300])
