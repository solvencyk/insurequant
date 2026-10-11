import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("data/_gold/kics_exemption_provenance.json", encoding="utf-8"))
print([k for k in d.keys()])
from collections import Counter
print(Counter(e.get("registry") for e in d["entries"]))
for e in d["entries"]:
    if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and e.get("company") == "KR1104":
        print(json.dumps(e, ensure_ascii=False, indent=1))
m = json.load(open("data/disclosure/_meta/reinsurer_KR1104_manifest.json", encoding="utf-8"))
print([k for k in m.keys()])
for p in m["periods"]:
    if p["period"] in ("2025.2Q","2025.3Q","2025.4Q"):
        print(json.dumps(p, ensure_ascii=False)[:800])
