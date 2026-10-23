import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "n01_notes.json", encoding="utf-8"))
byc = collections.defaultdict(collections.Counter)
for k, r in d.items():
    c = k.split("|")[0]
    if r["err"]: byc[c]["ERR"] += 1
    for i, v in r["items"].items(): byc[c][v["status"]] += 1
for c in sorted(byc): print(c, dict(byc[c]))
for k, r in d.items():
    st = collections.Counter(v["status"] for v in r["items"].values())
    if st.get("UNCAL") or st.get("NOPRIOR") or r["err"]:
        print(k, dict(st), r["err"] or "", "blocks", r["blocks"])
