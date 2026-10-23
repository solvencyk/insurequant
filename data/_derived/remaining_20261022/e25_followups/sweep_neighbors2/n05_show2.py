import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("n10_terms.json", encoding="utf-8"))
for k, rec in d.items():
    if len(sys.argv) > 1 and not k.startswith(sys.argv[1]): continue
    print(k, rec["file"].split("/")[-1] if rec["file"] else None, rec["err"] or "")
    for i, v in sorted(rec["items"].items(), key=lambda x: int(x[0])):
        if v["status"] == "OK":
            print("   ", i, "prior", round(v["val"], 1), "master", v["master"], "| cur", round(v["cur_val"], 1), "mcur", v["master_cur"], v["how"][:70], "nc", v["ncand"], v["cites"][0]["label"][:30])
        else:
            print("   ", i, v["status"], v.get("why", "")[:80], "master", v["master"])
