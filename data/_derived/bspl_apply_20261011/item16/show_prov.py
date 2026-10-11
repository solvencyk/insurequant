import json, sys
sys.stdout.reconfigure(encoding="utf-8")
s = json.load(open("PL_breakdown_provenance.json", encoding="utf-8"))
print([k for k in s.keys()][:30])
for k, v in s.items():
    if isinstance(v, (list, dict)) and k not in ("fields_owned","fields_pending_downloader","key","source_id_values"):
        print(k, type(v).__name__, len(v))
