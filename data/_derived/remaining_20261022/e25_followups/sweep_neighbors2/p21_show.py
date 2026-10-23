import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open("mismatches_part2.csv", encoding="utf-8-sig")))
f = sys.argv[1]
for r in rows:
    if r["company"] == f and r["cls"] != "ROUNDING_PM1":
        print(r["quarter"], r["item"], r["master"], r["latest"], r["diff_mn"], r["cls"], r["source"], r["note"][:80])
