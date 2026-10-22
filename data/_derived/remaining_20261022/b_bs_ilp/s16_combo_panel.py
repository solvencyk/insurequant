import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("data/csm_combo/panel_csm_combo.json", encoding="utf-8"))
print(d["meta"].keys())
m = d["meta"]
print("columns", m["columns"])
print("restated", json.dumps(m.get("restated"), ensure_ascii=False)[:1500])
for k, v in d.items():
    if k != "meta":
        print("top key", k, type(v), (list(v.keys())[:5] if isinstance(v, dict) else len(v)))
co = d.get("companies") or d.get("data") or {}
for code, v in (co.items() if isinstance(co, dict) else []):
    if code == "KR0073":
        print(json.dumps(v, ensure_ascii=False)[:3500])
