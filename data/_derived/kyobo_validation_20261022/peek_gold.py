import json, subprocess
for f in ["data/_gold/user_csm_cells.json","data/_gold/user_pl_cells.json","data/_gold/gold_overlay_ledger.json","data/_gold/csm_amort_identity_ledger.json"]:
    d = json.loads(subprocess.run(["git","show","HEAD:"+f],capture_output=True,check=True).stdout.decode("utf-8"))
    print(f, type(d).__name__, list(d.keys())[:8] if isinstance(d,dict) else len(d))
    if isinstance(d, dict):
        for k,v in list(d.items())[:3]:
            print("  ",k, type(v).__name__, (list(v.keys())[:5] if isinstance(v,dict) else (v[:1] if isinstance(v,list) else v)))
