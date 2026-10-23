import json, sys
sys.stdout.reconfigure(encoding="utf-8")
S1 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/sweep_neighbors/"
s1 = json.load(open(S1 + "p1_stmt.json", encoding="utf-8"))
for k, v in s1.items():
    e = [(a, v[a]) for a in v if a.startswith("err")]
    if e: print(k, v.get("file"), e)
p3 = json.load(open(S1 + "p3_existing.json", encoding="utf-8"))
for x in p3:
    if "err" in x: print(x["code"], x["q"], x["sheet"], x["err"])
print([ (x["code"],x["q"]) for x in p3 if x["sheet"]=="CSM" and "raw" in x])
