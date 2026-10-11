import json, sys
sys.stdout.reconfigure(encoding="utf-8")
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
rows = [r for r in pl if r["원보험사코드"] == "KR1104" and r["공시분기"] in ("2025.2Q", "2025.3Q", "2025.4Q")]
for r in sorted(rows, key=lambda r: (r["공시분기"], str(r["항목번호"]))):
    print(r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
sc = json.load(open("PL_breakdown_provenance.json", encoding="utf-8"))
for c in sc["cells"]:
    if c["company_code"] == "KR1104" and c["quarter"] in ("2025.2Q", "2025.3Q", "2025.4Q"):
        print(json.dumps(c, ensure_ascii=False)[:600])
