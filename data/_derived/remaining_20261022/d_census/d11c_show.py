import csv, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
rows = list(csv.DictReader(open(OUT / "d_census_table.csv", encoding="utf-8-sig", newline="")))
scope = sys.argv[1] if len(sys.argv) > 1 else "A51"
for r in rows:
    if scope != "ALL" and not r["scope"].startswith(scope): continue
    print(f"{r['scope'][:8]:9s}{r['company'][:8]:9s}{r['quarter']} {r['cause_class'][:14]:15s} closes={r['latest_vector_closes_block'][:10]:10s} {r['screen_change_class']:8s} {r['disposition']:15s} | {r['disposition_reason'][:140]}")
