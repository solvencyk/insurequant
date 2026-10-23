# -*- coding: utf-8 -*-
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
def head(p):
    return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+p],capture_output=True).stdout.decode("utf-8"))
h = head("data/_gold/user_pl_cells.json")
w = json.load(open(R+"/data/_gold/user_pl_cells.json", encoding="utf-8"))
print("top keys HEAD", list(h), "WT", list(w))
for k in w:
    if k not in h: print("NEW TOP KEY", k, str(w[k])[:800])
# set list
def key(e): return (e.get("code") or e.get("원보험사코드"), str(e.get("item") or e.get("항목번호")), e.get("quarter") or e.get("공시분기"))
print("set sample", h["set"][0])
hs = {key(e): e for e in h["set"]}
ws = {key(e): e for e in w["set"]}
print("set sizes", len(h["set"]), len(w["set"]), "unique", len(hs), len(ws))
new = [k for k in ws if k not in hs]
gone = [k for k in hs if k not in ws]
chg = [k for k in ws if k in hs and ws[k] != hs[k]]
print("new", len(new), "gone", len(gone), "changed", len(chg))
for k in chg: print(" CHG", k, hs[k]["값"], "->", ws[k]["값"])
for k in sorted(new, key=str): e=ws[k]; print(" NEW", e["원보험사코드"], e["항목번호"], e["공시분기"], e["값"], "was", e.get("was"), "estimate", e.get("estimate"), "keys", sorted(e), "NOTEHAS_pin", any(w in e["note"] for w in ("박제","pin","plug","잔차")) )
# null_dangi
print("null_dangi HEAD keys", list(h["null_dangi"])[:12])
print("null_dangi WT keys", list(w["null_dangi"])[:12])
for k in w["null_dangi"]:
    a, b = h["null_dangi"].get(k), w["null_dangi"][k]
    if a != b:
        print("ND", k, "type", type(b).__name__, "HEAD len", None if a is None else len(a), "WT len", len(b))
        if isinstance(b, list):
            sa = set(map(json.dumps, a or [])); sb = set(map(json.dumps, b))
            print("   added", sorted(sb-sa)); print("   removed", sorted(sa-sb))
        elif isinstance(b, dict):
            for kk in set(a or {})|set(b):
                if (a or {}).get(kk)!=b.get(kk): print("   ", kk, (a or {}).get(kk), "->", b.get(kk))
print("set_dangi equal", h["set_dangi"]==w["set_dangi"])
