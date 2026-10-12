"""Cell-level diff of kics_disclosure.json: 74a415bf^ vs 74a415bf, compared with applied_blocks.csv."""
import json, subprocess, csv, io
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
def load(rev):
    b = subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:kics_disclosure.json"])
    return json.loads(b.decode("utf-8"))
def index(recs):
    d = {}
    dup = 0
    for r in recs:
        k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
        if k in d: dup += 1
        d[k] = r
    return d, dup
old, d1 = index(load("74a415bf^")); new, d2 = index(load("74a415bf"))
out = open(REPO + "/data/_derived/kics_latest_prior_apply_audit_20261013/a1_master_diff.txt", "w", encoding="utf-8")
out.write(f"records old={len(old)} new={len(new)} dup old={d1} new={d2}\n")
out.write(f"keys only in old={len(set(old)-set(new))} only in new={len(set(new)-set(old))}\n")
changed = {}
for k in new:
    if k not in old: continue
    a, b = old[k], new[k]
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            changed[(k[0], k[1], k[2], f)] = (a.get(f), b.get(f))
out.write(f"changed cells (field level) = {len(changed)}\n")
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
app = {}
for r in rows:
    app[(r["code"], r["quarter"], int(r["item"]), r["field"])] = (r["old"], r["new"])
out.write(f"applied rows = {len(app)}\n")
only_diff = sorted(set(changed) - set(app)); only_app = sorted(set(app) - set(changed))
out.write(f"in master diff not in applied csv: {len(only_diff)}\n")
for k in only_diff: out.write(f"   {k} {changed[k]}\n")
out.write(f"in applied csv not in master diff: {len(only_app)}\n")
for k in only_app: out.write(f"   {k} {app[k]}\n")
bad = 0
for k in sorted(set(app) & set(changed)):
    o, n = changed[k]
    def num(x):
        try: return float(x)
        except: return None
    ao, an = app[k]
    if num(o) != num(ao) or num(n) != num(an):
        bad += 1; out.write(f"VALUE MISMATCH {k}: master {o}->{n}  csv {ao}->{an}\n")
out.write(f"value mismatches between csv and master diff: {bad}\n")
for k in sorted(changed):
    out.write(f"{k}: {changed[k]}\n")
