# -*- coding: utf-8 -*-
"""READ-ONLY: show how an earlier plan (e21 / e23 / e25) records seams (printed_3m ...) and the apply_contract set_dangi/null_dangi entries for a company."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
path, code = sys.argv[1], sys.argv[2]
p = json.load(open(path, encoding="utf-8"))
print("top keys", list(p.keys()))
seams = [s for s in p.get("seams", []) if s.get("code") == code]
print("seams for", code, len(seams))
for s in seams[:6]:
    print(json.dumps(s, ensure_ascii=False)[:900])
c = p["apply_contract"]
print("set_dangi_add", [x for x in c["set_dangi_add"] if x[0] == code][:6])
print("null_dangi_add", [x for x in c["null_dangi_add"] if x[0] == code][:6])
print("held", [h for h in c["held"] if h.get("code") == code][:3])
print("keys", list(c.keys()))
