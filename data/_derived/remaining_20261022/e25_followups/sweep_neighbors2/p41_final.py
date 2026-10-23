import csv, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open("mismatches_part2.csv", encoding="utf-8-sig")))
print("rows", len(rows))
real = [r for r in rows if r["cls"] not in ("ROUNDING_PM1",) and "extra" not in r["cls"] and r["cls"] != "UNREADABLE_LAYOUT"]
print("non-rounding (denominator cells)", len(real))
cc = collections.defaultdict(collections.Counter)
for r in real: cc[r["company"]][r["cls"]] += 1
for c in sorted(cc): print(c, sum(cc[c].values()), dict(cc[c]))
tot = collections.Counter(r["cls"] for r in real); print(dict(tot))
print("rounding rows", sum(1 for r in rows if r["cls"] == "ROUNDING_PM1"))
print("top15")
real.sort(key=lambda r: -abs(float(r["diff_mn"])))
for r in real[:15]: print(r["company"], r["quarter"], r["item"], r["master"], r["latest"], r["diff_mn"], r["cls"], r["confidence"])
print("others (non-KR0099):")
for r in real:
    if r["company"] != "KR0099": print(r["company"], r["quarter"], r["item"], r["master"], r["latest"], r["diff_mn"], r["cls"], r["confidence"])
