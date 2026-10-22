import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")
head = json.load(open(os.environ.get("TEMP", "/tmp") + "/pl_head.json", encoding="utf-8")) if os.path.exists(os.environ.get("TEMP", "/tmp") + "/pl_head.json") else None
if head is None:
    head = json.load(open("/tmp/pl_head.json", encoding="utf-8"))
wt = json.load(open("PL_breakdown.json", encoding="utf-8"))
def pick(rows): return {(r["공시분기"], r["항목번호"]): (r.get("값"), r.get("값_당분기")) for r in rows if r["원보험사코드"] == "KR0073" and r["항목번호"] in (24, 25)}
h, w = pick(head), pick(wt)
for k in sorted(set(h) | set(w), key=lambda x: (x[0], x[1])):
    if h.get(k) != w.get(k): print("DIFF", k, "HEAD", h.get(k), "WT", w.get(k))
print("compared", len(h), len(w))
for q in ("2025.1Q", "2025.2Q", "2023.3Q"):
    print(q, "HEAD item25 dangi", h.get((q, 25)), "WT", w.get((q, 25)))
