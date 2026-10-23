# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
g = json.load(open(ROOT + "/data/_gold/user_csm_cells.json", encoding="utf-8"))
print("CSM gold keys:", list(g.keys()))
for k, v in g.items():
    if isinstance(v, list):
        print(" ", k, "list", len(v), json.dumps(v[0], ensure_ascii=False)[:600] if v else "")
    elif isinstance(v, dict):
        print(" ", k, "dict keys", list(v.keys())[:8])
    else:
        print(" ", k, str(v)[:300])
p = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
print("PL gold keys:", list(p.keys()))
for k, v in p.items():
    if isinstance(v, list):
        print(" ", k, "list", len(v), json.dumps(v[0], ensure_ascii=False)[:400] if v else "")
    elif isinstance(v, dict):
        print(" ", k, "dict keys", list(v.keys())[:8])
        for kk, vv in v.items():
            if isinstance(vv, list):
                print("     ", kk, "list", len(vv), json.dumps(vv[:2], ensure_ascii=False)[:300])
            else:
                print("     ", kk, str(vv)[:200])
    else:
        print(" ", k, str(v)[:300])
# KR0003 entries
print("== KR0003 PL gold set entries")
for e in p["set"]:
    if e["원보험사코드"] == "KR0003":
        print("  ", e["공시분기"], e["항목번호"], e["값"], "was", e.get("was"), "|", str(e.get("note"))[:110].replace("\n", " "))
print("== KR0003 CSM gold set entries")
for e in g["set"]:
    if e["원보험사코드"] == "KR0003":
        print("  ", e["공시분기"], e["항목번호"], e["값"], "was", e.get("was"), "|", str(e.get("why"))[:110].replace("\n", " "))
print("== KR0003 null_dangi/set_dangi")
for x in p["null_dangi"]["cells"]:
    if x[0] == "KR0003":
        print("  null", x)
for x in p["set_dangi"]["cells"]:
    if x[0] == "KR0003":
        print("  set", x[:4])
