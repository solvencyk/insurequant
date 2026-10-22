# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel): return subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout
def live(rel): return open(f"{ROOT}/{rel}", "rb").read().replace(b"\r\n", b"\n")
h = json.loads(head("PL_breakdown.json").decode()); l = json.loads(live("PL_breakdown.json").decode())
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
hm = {key(r): r for r in h}; lm = {key(r): r for r in l}
chg = [k for k in lm if hm[k]["값"] != lm[k]["값"]]
hp = json.loads(head("PL_breakdown_provenance.json").decode()); lp = json.loads(live("PL_breakdown_provenance.json").decode())
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])
hpm = {pk(c): c for c in hp["cells"]}; lpm = {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
cover = {(k[0], k[1]) for k in dif}
miss = sorted(k for k in chg if (k[0], k[2]) not in cover)
print("changed blocks:", len(dif)); print("changed 값 cells:", len(chg)); print("not covered:", miss)
blocks = {(c, q) for c, i, q in chg}
print("blocks per (code,q) that exist in sidecar:", sorted((c, q, [b for (cc, qq, b) in lpm if cc == c and qq == q]) for c, q in blocks)[:40])
