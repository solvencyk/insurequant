import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/user_pl_cells.json", encoding="utf-8"))
print(d.keys())
print("null_dangi", json.dumps(d["null_dangi"], ensure_ascii=False)[:900])
sd = d["set_dangi"]
print("set_dangi doc:", sd.get("_doc", "")[:1200])
print(len(sd["cells"]), sd["cells"][:3], sd["cells"][-2:])
print(sorted({(c[0], c[1]) for c in sd["cells"]}))
