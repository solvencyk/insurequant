import json,sys
sys.stdout.reconfigure(encoding="utf-8")
for f in ["data/dart/extracted/한화생명_20260316001304_csm.json","data/dart/extracted/한화생명_20250312000939_csm.json"]:
    d=json.load(open(f,encoding="utf-8"))
    print("==",f,len(d))
    for b in d:
        print(b.get("line_no"),b.get("form_type"),b.get("score"),b["caption"][:90],"|",[h for h in b["header"][0]][:6], len(b["rows"]))
