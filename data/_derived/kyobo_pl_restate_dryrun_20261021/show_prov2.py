import json, sys
sys.stdout.reconfigure(encoding="utf-8")
prov = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json", encoding="utf-8"))
for c in prov["cells"]:
    if c["company_code"] in ("KR0008", "KR0002") and c["quarter"] in ("2023.1Q",) :
        print(json.dumps(c, ensure_ascii=False)[:800]); print()
print(prov["merge_note_20261012_latest_comparative"][:900])
