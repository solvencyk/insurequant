import csv,sys
sys.stdout.reconfigure(encoding="utf-8")
rows=list(csv.DictReader(open("data/_derived/capital_securities_classification_census_20261012/census_securities.csv",encoding="utf-8-sig")))
for r in rows:
    if r["kind"]!="bond":
        print(r["code"],"|",r["kind"],"|",r["name"],"|face",r["face_eok"],"|out",r["outstanding_eok"],"|",r["census_type"],r["grade"],"|",r["note"][:200])
