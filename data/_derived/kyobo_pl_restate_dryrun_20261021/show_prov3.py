import json, sys
sys.stdout.reconfigure(encoding="utf-8")
prov = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json", encoding="utf-8"))
for k in ("key", "source_id_values", "builder_derived_items", "note"):
    print(k, "=", json.dumps(prov[k], ensure_ascii=False)[:700])
