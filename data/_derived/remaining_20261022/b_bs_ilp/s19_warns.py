import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("data/_derived/pl_oci_vs_bs_aoci_warn.json", encoding="utf-8"))
for r in d:
    if r["company"] == "교보생명보험": print(r)
q = json.load(open("data/_derived/qoq_warn.json", encoding="utf-8"))
print(type(q), (list(q.keys())[:5] if isinstance(q, dict) else len(q)))
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)): walk(v, p + "/" + k)
    elif isinstance(o, list):
        for x in o:
            if isinstance(x, dict) and ("교보생명" in json.dumps(x, ensure_ascii=False)):
                print(p, json.dumps(x, ensure_ascii=False)[:260])
walk(q)
