import json, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plb = json.loads((HERE / "cand" / "pl_latest_blocks.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
key = sys.argv[1]
kr, q = key.split("|")[:2]
b = plb[key]["block"]
print(key, "bridge_latest", plb[key]["bridge_latest"], "amort", plb[key]["amort_lat_vs_lat_wf"], "trace", [t[0] for t in plb[key]["trace"]])
for i in range(1, 33):
    c, l = M.get((kr, q, i)), b.get(str(i))
    if c is None and l is None:
        continue
    print(f"  {i:>2} cur={c!s:>16} lat={l!s:>18} {'' if c == l else '<--'}")
