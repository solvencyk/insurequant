import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT)
import validate_master_tables as V
rows = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
def keys():
    _p, fails, _s = V._check_tax22_crosscheck(rows, quiet=True)
    return {(f[0], f[1]) for f in fails}
base = keys()
orig = V._tax22_prior_tier1
V._tax22_prior_tier1 = lambda *a, **k: None
off = keys()
V._tax22_prior_tier1 = orig
out = [f"live fails {len(base)}; branch-off fails {len(off)}"]
for k in sorted(off, key=lambda x: (x[0], x[1])):
    out.append(repr(k))
open("tax22_set.txt", "w", encoding="utf-8").write("\n".join(out))
