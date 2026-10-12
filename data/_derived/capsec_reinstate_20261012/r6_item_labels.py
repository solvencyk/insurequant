import json,sys
sys.stdout.reconfigure(encoding="utf-8")
recs=json.load(open("kics_disclosure.json",encoding="utf-8"))
seen={}
for r in recs:
    if r["공시분기"]=="2026.2Q" and 3<=r["항목번호"]<=14 or (r["공시분기"]=="2026.2Q" and 44<=r["항목번호"]<=60):
        seen.setdefault(r["항목번호"], r.get("항목명") or r.get("항목"))
for k in sorted(seen): print(k, seen[k])
print([k for k in recs[0].keys()])
