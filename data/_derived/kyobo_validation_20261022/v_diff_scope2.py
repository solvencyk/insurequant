import json, subprocess
def show(rev, f): return json.loads(subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True,check=True).stdout.decode("utf-8"))
a, b = show("3e53aef8~1","PL_breakdown_provenance.json"), show("3e53aef8","PL_breakdown_provenance.json")
print("PL prov top keys", list(b.keys())[:12], len(a["cells"]), len(b["cells"]))
ch = [i for i in range(max(len(a["cells"]),len(b["cells"]))) if (a["cells"][i] if i<len(a["cells"]) else None)!=(b["cells"][i] if i<len(b["cells"]) else None)]
print("changed cell idx", ch)
for i in ch:
    c = b["cells"][i]; print(i, {k:c.get(k) for k in ("code","원보험사코드","company","quarter","공시분기","items","item") if k in c}, list(c.keys())[:8])
ea, eb = show("3e53aef8~1","data/_gold/gold_overlay_ledger.json")["entries"], show("3e53aef8","data/_gold/gold_overlay_ledger.json")["entries"]
print("ledger removed keys:", sorted(set(ea)-set(eb))); print("ledger added keys:", sorted(set(eb)-set(ea)))
print("ledger modified keys:", sorted(k for k in set(ea)&set(eb) if ea[k]!=eb[k]))
