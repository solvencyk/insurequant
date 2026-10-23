import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("n01_notes.json", encoding="utf-8"))
for k, rec in d.items():
    if len(sys.argv) > 1 and not k.startswith(sys.argv[1]): continue
    print(k, rec["file"].split("/")[-1] if rec["file"] else None, rec["err"] or "")
    for i, v in sorted(rec["items"].items(), key=lambda x: int(x[0])):
        if v["status"] == "OK":
            print("   ", i, "prior", round(v["val"], 3), "master", v["master"], "| cur", round(v["cur_val"], 3), "mcur", v["master_cur"], v["how"][:60], v["cal"], v["cal_items"])
        else:
            print("   ", i, v["status"], v.get("why", "")[:90], "master", v["master"])
