import json, subprocess
def show(rev, f): return json.loads(subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True,check=True).stdout.decode("utf-8"))
b = show("3e53aef8","PL_breakdown_provenance.json")
print({b["cells"][i]["company_code"] for i in range(422,434)})
a = show("3e53aef8~1","PL_breakdown_provenance.json")
print({a["cells"][i]["company_code"] for i in range(422,434)})
eb = show("3e53aef8","data/_gold/gold_overlay_ledger.json")["entries"]
for k in ['CSM|KR0073|2023.3Q|2','CSM|KR0073|2023.4Q|2']: print(k, json.dumps(eb[k], ensure_ascii=False)[:600])
