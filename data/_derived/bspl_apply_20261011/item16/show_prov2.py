import json, sys
sys.stdout.reconfigure(encoding="utf-8")
s = json.load(open("PL_breakdown_provenance.json", encoding="utf-8"))
for c in s["cells"]:
    cc = c.get("company_code"); q = c.get("quarter")
    if (cc, q) in {("KR1101","2023.1Q"),("KR1101","2024.2Q"),("KR1103","2024.1Q"),("KR1103","2025.4Q"),("KR1103","2024.3Q")}:
        print(json.dumps(c, ensure_ascii=False))
