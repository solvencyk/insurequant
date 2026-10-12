"""s1b_core_status.py -- census of the core-table extraction status per (period, company). READ-ONLY."""
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
rows = read_rows()
idx, names = master_index(rows)
codes = sorted(names)
periods = sorted(p.name for p in DISC.iterdir() if re.match(r"FY\d{4}_Q\d$", p.name))

tab = defaultdict(dict)
for f in sorted(CACHE.glob("core_*.json")):
    d = read_json(f)
    tab[d["period"]][d["code"]] = d

print("status census by period")
for p in periods:
    c = Counter(v["status"] for v in tab[p].values())
    print(f"  {p}  {dict(c)}")
print()
print("not-OK detail (period code status err-short)")
for p in periods:
    for code in codes:
        v = tab[p].get(code)
        if v and v["status"] != "OK":
            print(f"  {p} {code} {names[code][:12]:12s} {v['status']:14s} {str(v.get('err'))[:90]}")
